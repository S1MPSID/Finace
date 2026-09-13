"""
Explainable AI (XAI) for the hybrid compliance engine.

Approach
--------
The final compliance score is produced by rules + retrieval + LLM merge.
We expose that decision with a local surrogate model over interpretable features:

1. Build a feature vector from triggered rules, retrieval strength, and control keywords.
2. Score neighbors with a deterministic scoring function that mirrors the rule/RAG merge.
3. Explain the local decision with LIME (local linear coefficients) and SHAP
   (KernelExplainer / linear fallback).

This keeps explanations faithful to the hybrid engine without requiring the LLM
itself to be differentiable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
from loguru import logger

from rules.rules_config import RULES
from config import settings


_CONTROL_FEATURES: list[tuple[str, list[str]]] = [
    ("has_kyc", [r"\bkyc\b", r"\be-?kyc\b", r"\baadhaar\b"]),
    ("has_aml", [r"\baml\b", r"\banti[- ]money\b", r"\btransaction\s+monitoring\b"]),
    ("has_grievance", [r"\bgrievance\b", r"\bcomplaint\b", r"\bredressal\b"]),
    ("has_fema", [r"\bfema\b", r"\bfx\s+compliance\b", r"\bforex\b"]),
    ("has_2fa", [r"\b2fa\b", r"\bmfa\b", r"\botp\b", r"\btwo[- ]factor\b"]),
]


@dataclass
class FeatureSpec:
    names: list[str]
    rule_ids: list[str]


def _match_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def build_feature_spec() -> FeatureSpec:
    rule_ids = [r["rule_id"] for r in RULES]
    names = [f"rule:{rid}" for rid in rule_ids]
    names.extend([name for name, _ in _CONTROL_FEATURES])
    names.extend(
        [
            "retrieval_hit_count",
            "retrieval_top_score",
            "retrieval_mean_score",
            "workflow_length_norm",
        ]
    )
    return FeatureSpec(names=names, rule_ids=rule_ids)


def extract_features(
    workflow_text: str,
    rules_out: dict[str, Any],
    retrieval_hits: list[dict[str, Any]],
    feature_spec: FeatureSpec | None = None,
) -> tuple[np.ndarray, FeatureSpec, dict[str, float]]:
    spec = feature_spec or build_feature_spec()
    text = workflow_text or ""
    values: dict[str, float] = {name: 0.0 for name in spec.names}

    triggered = {
        item.get("rule_id")
        for item in (rules_out or {}).get("triggered_rules", [])
        if item.get("rule_id")
    }
    for rid in spec.rule_ids:
        values[f"rule:{rid}"] = 1.0 if rid in triggered else 0.0

    for name, patterns in _CONTROL_FEATURES:
        values[name] = 1.0 if _match_any(patterns, text) else 0.0

    scores: list[float] = []
    for hit in retrieval_hits or []:
        raw = hit.get("score", hit.get("rerank_score", hit.get("similarity", 0.0)))
        try:
            scores.append(float(raw))
        except (TypeError, ValueError):
            continue

    values["retrieval_hit_count"] = min(len(retrieval_hits or []) / 5.0, 1.0)
    values["retrieval_top_score"] = max(scores) if scores else 0.0
    values["retrieval_mean_score"] = float(np.mean(scores)) if scores else 0.0
    values["workflow_length_norm"] = min(len(text) / 1200.0, 1.0)

    vector = np.array([values[name] for name in spec.names], dtype=float)
    return vector, spec, values


def score_from_features(x: np.ndarray, spec: FeatureSpec) -> float:
    """
    Deterministic surrogate of the hybrid merge used for local explanations.
    Higher is safer / more compliant.
    """
    named = {name: float(val) for name, val in zip(spec.names, x)}

    score = 82.0
    # Triggered risk rules lower the score (mirrors rule_engine merge).
    for rid in spec.rule_ids:
        if named.get(f"rule:{rid}", 0.0) >= 0.5:
            rule = next((r for r in RULES if r["rule_id"] == rid), None)
            if not rule:
                continue
            if rule["risk_level"] == "HIGH":
                score -= 28.0
            elif rule["risk_level"] == "MEDIUM":
                score -= 14.0
            else:
                score -= 6.0

    # Controls improve score.
    for control, weight in (
        ("has_kyc", 8.0),
        ("has_aml", 7.0),
        ("has_grievance", 5.0),
        ("has_fema", 6.0),
        ("has_2fa", 4.0),
    ):
        score += named.get(control, 0.0) * weight

    # Stronger retrieval evidence modestly improves confidence/score.
    score += named.get("retrieval_top_score", 0.0) * 6.0
    score += named.get("retrieval_mean_score", 0.0) * 4.0
    score += named.get("retrieval_hit_count", 0.0) * 3.0

    # Very short workflows are under-specified.
    if named.get("workflow_length_norm", 0.0) < 0.15:
        score -= 8.0

    return float(np.clip(score, 0.0, 100.0))


def _risk_from_score(score: float) -> str:
    if score <= 40:
        return "HIGH"
    if score <= 65:
        return "MEDIUM"
    return "LOW"


def _generate_neighbors(x0: np.ndarray, n_samples: int = 400, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, 0.35, size=(n_samples, x0.shape[0]))
    # Keep binary-ish features closer to {0,1} after noise + clip.
    samples = np.clip(x0 + noise, 0.0, 1.0)
    samples[0] = x0
    return samples


def _local_linear_importances(
    x0: np.ndarray,
    neighbors: np.ndarray,
    scores: np.ndarray,
) -> np.ndarray:
    """Weighted least-squares local linear model (LIME-style fallback)."""
    distances = np.linalg.norm(neighbors - x0, axis=1)
    weights = np.exp(-(distances ** 2) / 0.5)
    X = np.column_stack([np.ones(len(neighbors)), neighbors])
    W = np.diag(weights)
    try:
        beta = np.linalg.pinv(X.T @ W @ X) @ (X.T @ W @ scores)
        return beta[1:]
    except Exception:
        return np.zeros(x0.shape[0])


def _explain_with_lime(x0: np.ndarray, spec: FeatureSpec, n_samples: int = 400) -> list[dict[str, Any]]:
    neighbors = _generate_neighbors(x0, n_samples=n_samples)
    scores = np.array([score_from_features(row, spec) for row in neighbors], dtype=float)

    if settings.rag_light_xai:
        coefs = _local_linear_importances(x0, neighbors, scores)
        order = np.argsort(np.abs(coefs))[::-1][:10]
        return [
            {
                "feature": spec.names[i],
                "weight": round(float(coefs[i]), 4),
                "direction": "increases_score" if coefs[i] > 0 else "decreases_score",
            }
            for i in order
        ]

    try:
        from lime.lime_tabular import LimeTabularExplainer

        explainer = LimeTabularExplainer(
            training_data=neighbors,
            feature_names=spec.names,
            mode="regression",
            discretize_continuous=False,
        )

        def predict_fn(data: np.ndarray) -> np.ndarray:
            return np.array([score_from_features(row, spec) for row in data], dtype=float)

        explanation = explainer.explain_instance(
            data_row=x0,
            predict_fn=predict_fn,
            num_features=min(10, len(spec.names)),
            num_samples=n_samples,
        )
        items = []
        for name, weight in explanation.as_list():
            # LIME may return "feature=value" style names; normalize.
            clean = str(name).split("=")[0].split("<")[0].split(">")[0].strip()
            items.append(
                {
                    "feature": clean,
                    "weight": round(float(weight), 4),
                    "direction": "increases_score" if weight > 0 else "decreases_score",
                }
            )
        return items
    except Exception as exc:
        logger.warning(f"LIME package path failed, using local linear fallback: {exc}")
        coefs = _local_linear_importances(x0, neighbors, scores)
        order = np.argsort(np.abs(coefs))[::-1][:10]
        return [
            {
                "feature": spec.names[i],
                "weight": round(float(coefs[i]), 4),
                "direction": "increases_score" if coefs[i] > 0 else "decreases_score",
            }
            for i in order
        ]


def _explain_with_shap(x0: np.ndarray, spec: FeatureSpec, n_samples: int = 160) -> list[dict[str, Any]]:
    background = _generate_neighbors(x0, n_samples=n_samples, seed=7)
    y = np.array([score_from_features(row, spec) for row in background], dtype=np.float64)

    if settings.rag_light_xai:
        coefs = _local_linear_importances(x0, background, y)
        means = background.mean(axis=0)
        approx = coefs * (x0 - means)
        order = np.argsort(np.abs(approx))[::-1][:10]
        return [
            {
                "feature": spec.names[i],
                "shap_value": round(float(approx[i]), 4),
                "direction": "increases_score" if approx[i] > 0 else "decreases_score",
            }
            for i in order
        ]

    # Prefer a stable linear surrogate + exact linear SHAP attributions.
    try:
        from sklearn.linear_model import Ridge

        model = Ridge(alpha=0.2, random_state=0)
        model.fit(background, y)
        baseline = background.mean(axis=0)
        values = np.asarray(model.coef_, dtype=np.float64) * (x0 - baseline)

        try:
            import shap

            explainer = shap.LinearExplainer(model, background)
            shap_values = explainer.shap_values(x0.reshape(1, -1))
            values = np.asarray(shap_values, dtype=np.float64).reshape(-1)
        except Exception:
            # Ridge coef * centered features is already a valid linear SHAP form.
            pass

        order = np.argsort(np.abs(values))[::-1][:10]
        return [
            {
                "feature": spec.names[i],
                "shap_value": round(float(values[i]), 4),
                "direction": "increases_score" if values[i] > 0 else "decreases_score",
            }
            for i in order
        ]
    except Exception as exc:
        logger.warning(f"SHAP linear path failed, using coefficient fallback: {exc}")
        coefs = _local_linear_importances(x0, background, y)
        means = background.mean(axis=0)
        approx = coefs * (x0 - means)
        order = np.argsort(np.abs(approx))[::-1][:10]
        return [
            {
                "feature": spec.names[i],
                "shap_value": round(float(approx[i]), 4),
                "direction": "increases_score" if approx[i] > 0 else "decreases_score",
            }
            for i in order
        ]


def _humanize_feature(name: str) -> str:
    if name.startswith("rule:"):
        rid = name.split(":", 1)[1]
        rule = next((r for r in RULES if r["rule_id"] == rid), None)
        return rule["name"] if rule else rid
    mapping = {
        "has_kyc": "KYC controls present",
        "has_aml": "AML controls present",
        "has_grievance": "Grievance process present",
        "has_fema": "FEMA/FX controls present",
        "has_2fa": "2FA / OTP controls present",
        "retrieval_hit_count": "Number of matching regulations",
        "retrieval_top_score": "Top regulation match strength",
        "retrieval_mean_score": "Average regulation match strength",
        "workflow_length_norm": "Workflow detail completeness",
    }
    return mapping.get(name, name)


def explain_decision(
    workflow_text: str,
    rules_out: dict[str, Any],
    retrieval_hits: list[dict[str, Any]],
    final_score: int | float | None = None,
    final_risk: str | None = None,
) -> dict[str, Any]:
    vector, spec, raw_values = extract_features(workflow_text, rules_out, retrieval_hits)
    surrogate_score = score_from_features(vector, spec)
    lime_items = _explain_with_lime(vector, spec)
    shap_items = _explain_with_shap(vector, spec)

    for item in lime_items:
        item["label"] = _humanize_feature(item["feature"])
        item["active"] = float(raw_values.get(item["feature"], 0.0)) >= 0.5
    for item in shap_items:
        item["label"] = _humanize_feature(item["feature"])
        item["active"] = float(raw_values.get(item["feature"], 0.0)) >= 0.5

    top_drivers = []
    for item in shap_items[:5]:
        feature = item["feature"]
        active = item.get("active", False)
        shap_val = float(item["shap_value"])
        label = item["label"]
        if feature.startswith("rule:"):
            if active:
                verb = "lowered" if shap_val < 0 else "shifted"
                top_drivers.append(
                    f"Triggered rule “{label}” {verb} the score ({shap_val:+.2f})."
                )
            else:
                top_drivers.append(
                    f"Rule “{label}” was not triggered"
                    f"{' — that supported the score' if shap_val > 0 else ''}"
                    f" ({shap_val:+.2f})."
                )
        elif feature.startswith("has_"):
            state = "present" if active else "absent"
            verb = "raised" if shap_val > 0 else "lowered"
            top_drivers.append(
                f"Control “{label}” is {state} and {verb} the score ({shap_val:+.2f})."
            )
        else:
            verb = "raised" if shap_val > 0 else "lowered"
            top_drivers.append(
                f"{label} {verb} the compliance score ({shap_val:+.2f})."
            )

    return {
        "method": "hybrid_surrogate_shap_lime",
        "target": "compliance_score",
        "observed_score": float(final_score) if final_score is not None else round(surrogate_score, 2),
        "surrogate_score": round(surrogate_score, 2),
        "observed_risk": final_risk or _risk_from_score(surrogate_score),
        "feature_values": {
            _humanize_feature(k): round(float(v), 4) for k, v in raw_values.items()
        },
        "lime": {
            "summary": "Local linear explanation of which features push the score up or down near this workflow.",
            "features": lime_items,
        },
        "shap": {
            "summary": "Feature attributions estimating each signal's contribution to the compliance score.",
            "features": shap_items,
        },
        "top_drivers": top_drivers,
        "notes": [
            "Explanations are computed over interpretable rule, control, and retrieval features.",
            "They approximate the hybrid rules+RAG decision surface used by the engine.",
        ],
    }
