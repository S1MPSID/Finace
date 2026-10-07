"""
Explainability for the ML validation models.

Clearly distinct from:
- Finace surrogate SHAP/LIME (hybrid score)
- Regulatory evidence / RAG citations
"""
from __future__ import annotations

from typing import Any

import numpy as np

from ml_validation.model.features import FEATURE_NAMES


def explain_prediction(
    x: np.ndarray,
    *,
    status_model: Any,
    background: np.ndarray,
    target_label: str,
    top_k: int = 8,
) -> dict[str, Any]:
    """
    Model-appropriate local explanation:
    - LogisticRegression: coefficient * (x - mean_background) toward predicted class
    - Tree models: impurity-based feature_importances_ as global prior + local value gating
    """
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    mean = np.asarray(background, dtype=np.float64).mean(axis=0)
    name = type(status_model).__name__

    contributions: list[dict[str, Any]] = []

    if hasattr(status_model, "coef_") and hasattr(status_model, "classes_"):
        classes = list(status_model.classes_)
        if target_label not in classes:
            target_label = str(classes[int(np.argmax(status_model.predict_proba(x.reshape(1, -1))[0]))])
        idx = classes.index(target_label)
        coef = np.asarray(status_model.coef_[idx], dtype=np.float64)
        local = coef * (x - mean)
        method = "logistic_coefficient_delta"
        units = "log_odds_contribution_approx"
        for i, feat in enumerate(FEATURE_NAMES):
            contributions.append(
                {
                    "feature": feat,
                    "value": round(float(x[i]), 4),
                    "contribution": round(float(local[i]), 4),
                    "direction": "supports_prediction"
                    if local[i] >= 0
                    else "opposes_prediction",
                }
            )
    elif hasattr(status_model, "feature_importances_"):
        imps = np.asarray(status_model.feature_importances_, dtype=np.float64)
        # Gate global importance by local feature activation
        local = imps * np.abs(x - mean)
        method = "tree_importance_gated"
        units = "relative_importance"
        for i, feat in enumerate(FEATURE_NAMES):
            contributions.append(
                {
                    "feature": feat,
                    "value": round(float(x[i]), 4),
                    "contribution": round(float(local[i]), 4),
                    "direction": "active_driver" if x[i] >= 0.5 else "inactive",
                }
            )
    else:
        method = "unavailable"
        units = "none"

    contributions.sort(key=lambda r: abs(float(r["contribution"])), reverse=True)
    return {
        "method": method,
        "units": units,
        "target_label": target_label,
        "model_class": name,
        "top_features": contributions[:top_k],
        "disclaimer": (
            "These attributions explain the ML validation model only. "
            "They are not regulatory citations and are not Finace surrogate SHAP/LIME."
        ),
    }
