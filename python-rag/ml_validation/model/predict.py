"""Inference for the ML validation layer (additive analytical signal)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ml_validation.model.explain import explain_prediction
from ml_validation.model.features import FEATURE_NAMES, vectorize_text
from ml_validation.model.train import latest_model_dir

_CACHE: dict[str, Any] = {}


def _load(model_dir: Path | None = None) -> dict[str, Any]:
    model_dir = model_dir or latest_model_dir()
    key = str(model_dir) if model_dir else ""
    if key in _CACHE:
        return _CACHE[key]
    if model_dir is None or not model_dir.exists():
        return {"available": False}
    meta = json.loads((model_dir / "pipeline.json").read_text(encoding="utf-8"))
    bundle = {
        "available": True,
        "model_dir": model_dir,
        "meta": meta,
        "status_model": joblib.load(model_dir / "status_model.joblib"),
        "risk_model": joblib.load(model_dir / "risk_model.joblib"),
        "background": np.load(model_dir / "background_X.npy"),
    }
    _CACHE[key] = bundle
    return bundle


def predict_workflow(
    scenario: str,
    *,
    domain: str = "",
    requirement: str = "",
    model_dir: Path | None = None,
    include_explanation: bool = True,
) -> dict[str, Any]:
    """
    Predict compliance status + risk for a workflow description.

    This is an analytical ML layer. It must not be treated as regulatory
    ground truth and must not override RAG citations, rules, or Gemini.
    """
    bundle = _load(model_dir)
    if not bundle.get("available"):
        return {
            "available": False,
            "notes": [
                "ML validation model not trained yet.",
                "Run: python -m ml_validation.cli train",
            ],
        }

    X = vectorize_text(scenario, domain=domain, requirement=requirement)
    status_model = bundle["status_model"]
    risk_model = bundle["risk_model"]
    status = str(status_model.predict(X)[0])
    risk = str(risk_model.predict(X)[0])
    status_proba = {
        str(c): round(float(p), 4)
        for c, p in zip(status_model.classes_, status_model.predict_proba(X)[0])
    }
    risk_proba = {
        str(c): round(float(p), 4)
        for c, p in zip(risk_model.classes_, risk_model.predict_proba(X)[0])
    }

    out: dict[str, Any] = {
        "available": True,
        "layer": "ml_validation",
        "compliance_status": status,
        "risk_category": risk,
        "status_probabilities": status_proba,
        "risk_probabilities": risk_proba,
        "features": {
            name: round(float(val), 4) for name, val in zip(FEATURE_NAMES, X[0])
        },
        "model": {
            "status_model": bundle["meta"].get("status_model"),
            "risk_model": bundle["meta"].get("risk_model"),
            "model_dir": str(bundle["model_dir"]),
        },
        "notes": [
            "ML validation prediction is a learned analytical signal.",
            "It does NOT replace regulatory documents, RAG evidence, deterministic rules, or Gemini reasoning.",
            "Explanations below are for this ML model only — not Finace surrogate SHAP/LIME and not legal citations.",
        ],
    }
    if include_explanation:
        out["explanation"] = explain_prediction(
            X[0],
            status_model=status_model,
            background=bundle["background"],
            target_label=status,
        )
    return out
