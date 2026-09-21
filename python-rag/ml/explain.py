"""
SHAP explanations for the trained ML risk model.

Method notes (important for honesty):
- SHAP explains the **ML model** (e.g. the RandomForest / LogisticRegression),
  never the LLM. The LLM's own reasoning remains a separate narrative line.
- We explain ``P(risk class = HIGH)`` — the model's predicted probability of the
  HIGH risk class.
- For RandomForest: exact TreeExplainer attributions in **probability units** with
  background expected values; ``baseline = expected P(HIGH)`` over the training
  background, so ``baseline + sum(shap_i) == predicted P(HIGH)``.
- For LogisticRegression: exact closed-form linear SHAP on the log-odds of the
  HIGH class (documented units = log-odds). Baseline = the model's log-odds at the
  background mean.
- SHAP values are NOT percentages unless final probability units are explained as
  such; top drivers are phrased as contributions to the predicted risk probability.

A LIME comparator is available via ``lime_comparison`` but is OFF by default
(research only; not surfaced in the UI).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.common import ARTIFACTS_DIR
from ml.feature_schema import (
    EXPOSURE_FEATURES,
    FEATURE_ORDER,
    PROTECTIVE_CONTROLS,
    RISK_LEVELS,
)
from ml.features import FeatureVector

CLASS_OF_INTEREST = "HIGH"

_HUMAN = {
    "kyc_present": "KYC controls present",
    "aml_present": "AML program present",
    "transaction_monitoring": "Transaction monitoring present",
    "grievance_mechanism": "Grievance redressal present",
    "fema_controls": "FEMA/FX controls present",
    "authentication_control": "Authentication (2FA/MFA) present",
    "compliance_policy_present": "Compliance policy/governance present",
    "cross_border_activity": "Cross-border activity",
    "p2p_crypto_activity": "P2P / crypto asset activity",
    "regulatory_evidence_count": "Regulatory evidence coverage",
    "relevant_regulation_count": "Distinct regulations matched",
    "retrieval_strength": "Retrieval match strength",
    "active_regulation_ratio": "Active regulation ratio",
}


def _is_random_forest(model: Any) -> bool:
    from sklearn.ensemble import RandomForestClassifier

    return isinstance(model, RandomForestClassifier)


def _is_logistic(model: Any) -> bool:
    from sklearn.linear_model import LogisticRegression

    return isinstance(model, LogisticRegression)


def load_artifacts(out_dir: str = ARTIFACTS_DIR) -> tuple[Any, dict, np.ndarray]:
    import joblib

    model = joblib.load(os.path.join(out_dir, "model.joblib"))
    with open(os.path.join(out_dir, "pipeline.json"), "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    background = np.load(os.path.join(out_dir, "background_X.npy"))
    return model, meta, background


class SHAPAttribution:
    def __init__(
        self,
        model: Any,
        background: np.ndarray,
        *,
        class_of_interest: str = CLASS_OF_INTEREST,
    ):
        self.model = model
        self.background = np.asarray(background, dtype=float)
        if class_of_interest not in list(model.classes_):
            raise ValueError(f"{class_of_interest} not in model classes")
        self.class_index = list(model.classes_).index(class_of_interest)
        self.class_of_interest = class_of_interest
        self._exact = self._build()

    def _build(self) -> tuple[str, dict, object, float]:
        if _is_random_forest(self.model):
            import shap

            explainer = shap.TreeExplainer(
                self.model, data=self.background, model_output="probability"
            )
            ev = np.asarray(explainer.expected_value).reshape(-1)
            baseline = float(ev[self.class_index])
            return "tree_shap", {"units": "probability"}, explainer, baseline

        if _is_logistic(self.model):
            coef = np.asarray(self.model.coef_, dtype=float)[self.class_index]
            intercept = float(np.asarray(self.model.intercept_, dtype=float).reshape(-1)[self.class_index])
            mean_x = self.background.mean(axis=0)
            baseline = float(np.dot(coef, mean_x) + intercept)
            return (
                "exact_linear_logit_shap",
                {
                    "units": "log_odds(RAW_LOG_ODDS)",
                    "coef": coef,
                    "intercept": intercept,
                    "mean": mean_x,
                },
                None,
                baseline,
            )

        raise NotImplementedError(f"SHAP not implemented for {type(self.model).__name__}")

    def values_for(self, X: np.ndarray) -> tuple[np.ndarray, float]:
        """Return SHAP values (feature space) for X rows and the class baseline."""
        X = np.asarray(X, dtype=float).reshape(1, -1)
        method, extra, expl, baseline = self._exact

        if method == "tree_shap":
            sv = expl.shap_values(X, check_additivity=False)
            sv = np.asarray(sv)
            if sv.ndim == 3:
                sv = sv[:, :, self.class_index]
            return sv.reshape(1, -1)[0], baseline
        if method == "exact_linear_logit_shap":
            coef = extra["coef"]
            return (coef * (X[0] - extra["mean"])), baseline
        raise RuntimeError("unreachable")

    def explain(
        self,
        features: FeatureVector,
        x_array: np.ndarray,
        *,
        top_n: int = 6,
    ) -> dict[str, Any]:
        values, baseline = self.values_for(x_array)
        method, extra, _, _ = self._exact
        raw = features.values

        default = {
            "method": method,
            "units": extra["units"],
            "target": f"P(risk class = {self.class_of_interest})",
            "baseline": round(baseline, 4),
            "baseline_note": (
                "Expected value over the SHAP background sample (training rows). "
                + (
                    "baseline + sum(shap_values) equals the model's predicted probability."
                    if method == "tree_shap"
                    else "baseline + sum(shap_values) equals the model's raw HIGH-class log-odds; it is not a probability."
                )
            ),
        }

        # Predicted probability of the class of interest works as a sanity number.
        proba = self.model.predict_proba(x_array.reshape(1, -1))[0, self.class_index]
        if method == "exact_linear_logit_shap":
            decision = np.asarray(self.model.decision_function(x_array.reshape(1, -1)))
            raw_prediction = float(decision.reshape(1, -1)[0, self.class_index])
        else:
            raw_prediction = float(proba)

        items = []
        for name, sv in zip(FEATURE_ORDER, values):
            items.append(
                {
                    "feature": name,
                    "label": self.humanize(name),
                    "value": round(float(raw.get(name, 0.0)), 4),
                    "shap_value": round(float(sv), 4),
                    "direction": (
                        "increases_risk_probability"
                        if sv > 0
                        else "decreases_risk_probability"
                        if sv < 0
                        else "neutral"
                    ),
                }
            )
        items.sort(key=lambda d: abs(d["shap_value"]), reverse=True)

        top_drivers = self._drivers(items[:top_n])

        return {
            **default,
            "predicted_probability": round(float(proba), 4),
            "predicted_value": round(raw_prediction, 4),
            "class_order": [str(c) for c in self.model.classes_],
            "features": items,
            "top_risk_drivers": top_drivers,
            "notes": [
                "SHAP explains the trained ML risk model, not the LLM.",
                "Feature values are model inputs; rule triggers come from the "
                "deterministic rule engine (rules.rules_config).",
                "A rule that is NOT triggered may still appear with a small "
                "attribution because its absence shifts the probability.",
            ],
        }

    def _drivers(self, top: list[dict[str, Any]]) -> list[str]:
        drivers: list[str] = []
        units = self._exact[1].get("units", "probability")
        impact_target = "raw HIGH-class log-odds" if "log_odds" in units else "P(HIGH)"
        for d in top:
            name = d["feature"]
            sv = d["shap_value"]
            label = d["label"]
            if name.startswith("rule:"):
                rid = name.split(":", 1)[1]
                from rules.rules_config import RULES

                rule = next((r for r in RULES if r["rule_id"] == rid), None)
                label = rule["name"] if rule else rid
                if d["value"] >= 0.5:
                    drivers.append(
                        f"Triggered rule “{label}” raised {impact_target} by {sv:+.4f}."
                    )
                else:
                    drivers.append(
                        f"Rule “{label}” not triggered ({sv:+.4f})."
                    )
            elif name in PROTECTIVE_CONTROLS:
                state = "present" if d["value"] >= 0.5 else "absent"
                verb = "raised" if sv > 0 else "lowered"
                drivers.append(
                    f"Control “{label}” is {state} and {verb} {impact_target} by {abs(sv):.4f}."
                )
            elif name in EXPOSURE_FEATURES:
                state = "present" if d["value"] >= 0.5 else "absent"
                verb = "raised" if sv > 0 else "lowered"
                drivers.append(
                    f"Exposure “{label}” is {state} and {verb} {impact_target} by {abs(sv):.4f}."
                )
            else:
                verb = "raised" if sv > 0 else "lowered"
                drivers.append(
                    f"“{label}” {verb} {impact_target} by {abs(sv):.4f}."
                )
        return drivers

    def humanize(self, name: str) -> str:
        if name in _HUMAN:
            return _HUMAN[name]
        return name


def explain_prediction(
    features: FeatureVector,
    x_array: np.ndarray,
    model: Any | None = None,
    background: np.ndarray | None = None,
    *,
    class_of_interest: str = CLASS_OF_INTEREST,
    out_dir: str = ARTIFACTS_DIR,
) -> dict[str, Any]:
    """Explain one prediction with exact SHAP (loads artifacts when not given)."""
    if model is None or background is None:
        model, _meta, background = load_artifacts(out_dir)
    attributor = SHAPAttribution(
        model, background, class_of_interest=class_of_interest
    )
    return attributor.explain(features, x_array)


def lime_comparison(
    features: FeatureVector,
    x_array: np.ndarray,
    model: Any,
    background: np.ndarray,
    *,
    n_samples: int = 300,
) -> dict[str, Any] | None:
    """Optional LIME comparator (research only, OFF by default).

    Returns None when the ``lime`` package is not importable so the online path
    never hard-fails on it.
    """
    try:
        import lime  # noqa: F401
        from lime.lime_tabular import LimeTabularExplainer  # noqa: F401
    except Exception:
        return None

    class_index = list(model.classes_).index(CLASS_OF_INTEREST)

    def predict_proba(data: np.ndarray) -> np.ndarray:
        return model.predict_proba(data)

    explainer = LimeTabularExplainer(
        training_data=np.asarray(background),
        feature_names=FEATURE_ORDER,
        class_names=list(model.classes_),
        mode="classification",
        discretize_continuous=False,
    )
    explanation = explainer.explain_instance(
        data_row=x_array.reshape(-1),
        predict_fn=predict_proba,
        labels=(class_index,),
        num_features=min(8, len(FEATURE_ORDER)),
        num_samples=n_samples,
    )
    items = []
    for name, weight in explanation.as_list(label=class_index):
        clean = str(name).split("=")[0].strip()
        items.append(
            {
                "feature": clean,
                "weight": round(float(weight), 4),
            }
        )
    return {
        "method": "lime",
        "target": f"P(risk class = {CLASS_OF_INTEREST})",
        "features": items,
        "notes": [
            "LIME is a local linear approximation; kept as a research comparator "
            "only (not surfaced in the primary UI).",
        ],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Explain a risk prediction with SHAP")
    parser.add_argument("--values", nargs="+", type=float, help="17 feature values in FEATURE_ORDER")
    args = parser.parse_args()

    model, meta, background = load_artifacts()
    values = args.values or [0.0] * len(FEATURE_ORDER)
    x = np.asarray(values, dtype=float).reshape(1, -1)

    from ml.features import feature_vector_from_array

    fv = feature_vector_from_array(x[0])
    result = explain_prediction(fv, x, model, background)
    print(json.dumps(
        {
            "method": result["method"],
            "predicted_probability": result["predicted_probability"],
            "baseline": result["baseline"],
            "top_risk_drivers": result["top_risk_drivers"],
            "features": result["features"][:8],
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
