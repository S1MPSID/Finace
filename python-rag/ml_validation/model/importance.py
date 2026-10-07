"""
Feature importance for ML validation models.

Identifies suspiciously dominant features that may indicate shortcut learning.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ml_validation.model.features import FEATURE_NAMES
from ml_validation.model.train import latest_model_dir
from ml_validation.paths import REPORTS_DIR, ensure_dirs


def feature_importance_report(model_dir: Path | None = None) -> dict[str, Any]:
    model_dir = model_dir or latest_model_dir()
    if model_dir is None:
        return {"available": False, "error": "No model trained"}

    status_model = joblib.load(model_dir / "status_model.joblib")
    risk_model = joblib.load(model_dir / "risk_model.joblib")

    def pack(model: Any, name: str) -> dict[str, Any]:
        if hasattr(model, "feature_importances_"):
            imps = np.asarray(model.feature_importances_, dtype=float)
            method = "tree_feature_importances"
        elif hasattr(model, "coef_"):
            # Mean absolute coefficient across classes
            imps = np.mean(np.abs(np.asarray(model.coef_, dtype=float)), axis=0)
            method = "mean_abs_logistic_coefficient"
        else:
            return {"model": name, "method": "unavailable", "features": []}

        total = float(imps.sum()) or 1.0
        rows = [
            {
                "feature": FEATURE_NAMES[i],
                "importance": round(float(imps[i]), 6),
                "share": round(float(imps[i] / total), 4),
            }
            for i in range(len(FEATURE_NAMES))
        ]
        rows.sort(key=lambda r: r["importance"], reverse=True)
        top = rows[0] if rows else None
        suspicious = []
        # Heuristic: single feature > 35% share is a shortcut smell for this feature set
        for r in rows:
            if r["share"] >= 0.35:
                suspicious.append(
                    {
                        **r,
                        "reason": "dominant_share_ge_35pct",
                    }
                )
        # Known shortcut-prone engineered features
        for r in rows[:5]:
            if r["feature"] in {
                "has_negation",
                "has_out_of_scope",
                "has_partial_language",
                "has_pilot_language",
                "requirement_token_overlap",
            } and r["share"] >= 0.15:
                suspicious.append({**r, "reason": "shortcut_prone_feature_high_rank"})

        return {
            "model": name,
            "estimator": type(model).__name__,
            "method": method,
            "features": rows,
            "top_feature": top,
            "suspicious_features": suspicious,
        }

    report = {
        "available": True,
        "model_dir": str(model_dir),
        "status": pack(status_model, "status"),
        "risk": pack(risk_model, "risk"),
        "notes": [
            "Importances explain the ML validation model only — not RAG evidence or Finace surrogate XAI.",
            "Dominant shortcut-prone features suggest the model may still rely on lexical cues.",
        ],
    }
    return report


def save_importance_report(report: dict[str, Any], stem: str = "feature_importance") -> Path:
    ensure_dirs()
    path = REPORTS_DIR / f"{stem}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
