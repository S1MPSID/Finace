"""
Lightweight online predictor for the ML compliance risk layer.

Used by the RAG pipeline to attach a backward-compatible ``ml_risk`` block to
every response. Everything is lazy-loaded and degrades gracefully when no trained
artifact exists, so the existing system never crashes because ML is missing.
"""
from __future__ import annotations

import json
import os
from typing import Any

import numpy as np

from ml.common import ARTIFACTS_DIR
from ml.feature_schema import FEATURE_ORDER, PROTECTIVE_CONTROLS, RISK_LEVELS
from ml.features import FeatureVector

_MODEL_VERSION_DEFAULT = "unversioned"


class MLRiskPredictor:
    def __init__(self, out_dir: str = ARTIFACTS_DIR):
        self.out_dir = out_dir
        self._model = None
        self._meta: dict[str, Any] | None = None
        self._background: np.ndarray | None = None
        self._loaded = False

    @property
    def available(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    @property
    def model_name(self) -> str:
        self._ensure_loaded()
        if not self._meta:
            return ""
        return str(self._meta.get("selected_model", ""))

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            import joblib

            model_path = os.path.join(self.out_dir, "model.joblib")
            meta_path = os.path.join(self.out_dir, "pipeline.json")
            bg_path = os.path.join(self.out_dir, "background_X.npy")
            if not all(os.path.exists(p) for p in (model_path, meta_path, bg_path)):
                return
            self._model = joblib.load(model_path)
            with open(meta_path, "r", encoding="utf-8") as fh:
                self._meta = json.load(fh)
            self._background = np.load(bg_path)
        except Exception:
            self._model = None
            self._meta = None
            self._background = None

    # ── Prediction ──

    def predict(self, features: FeatureVector) -> dict[str, Any]:
        self._ensure_loaded()
        if self._model is None:
            return {
                "available": False,
                "risk_class": None,
                "probabilities": {lv: None for lv in RISK_LEVELS},
                "model_version": None,
                "notes": [
                    "No trained ML risk artifact present; ML risk layer is inactive."
                ],
            }

        x = features.array().reshape(1, -1)
        for i, name in enumerate(FEATURE_ORDER):
            if name not in features.values:
                features.values[name] = 0.0

        proba = self._model.predict_proba(x)[0]
        # Round for transport, then correct the final class so the public
        # probabilities remain a valid distribution after serialization.
        rounded = [round(float(p), 6) for p in proba]
        if rounded:
            rounded[-1] = round(1.0 - sum(rounded[:-1]), 6)
        prob_map = {str(c): p for c, p in zip(self._model.classes_, rounded)}
        risk_class = str(self._model.classes_[int(np.argmax(proba))])

        return {
            "available": True,
            "risk_class": risk_class,
            "probabilities": {lv: prob_map.get(lv, 0.0) for lv in RISK_LEVELS},
            "probability_note": (
                "Predicted class probabilities from the ML risk model. "
                "Not calibrated confidence; ECE is reported in the evaluation report."
            ),
            "model_version": (self._meta or {}).get("model_version", _MODEL_VERSION_DEFAULT),
            "dataset_version": (self._meta or {}).get("dataset_version", "unknown"),
            "features": {name: round(float(features.values.get(name, 0.0)), 4) for name in FEATURE_ORDER},
            "control_coverage": round(features.control_coverage, 4),
            "triggered_rule_counts": features.triggered_counts(),
            "supported_risk_levels": list(RISK_LEVELS),
        }

    # ── Explanation ──

    def explain(self, features: FeatureVector) -> dict[str, Any]:
        self._ensure_loaded()
        if self._model is None or self._background is None:
            return {
                "available": False,
                "method": None,
                "notes": ["No SHAP explanation available (no model artifact)."],
            }

        from ml.explain import SHAPAttribution

        attributor = SHAPAttribution(self._model, self._background)
        return attributor.explain(features, features.array())

    def combined(self, features: FeatureVector) -> dict[str, Any]:
        """prediction + SHAP explanation in one structured block (for the API)."""
        pred = self.predict(features)
        if not pred["available"]:
            return pred
        expl = self.explain(features)
        pred["explanation"] = expl
        return pred


# Module-level singleton so the RAG pipeline reuses a single model load.
_predictor_singleton: MLRiskPredictor | None = None


def get_predictor(out_dir: str = ARTIFACTS_DIR) -> MLRiskPredictor:
    global _predictor_singleton
    if _predictor_singleton is None:
        _predictor_singleton = MLRiskPredictor(out_dir=out_dir)
    return _predictor_singleton
