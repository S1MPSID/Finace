"""
Counterfactual / what-if re-scoring for the official compliance waterfall.

The official score is exactly:  clamp(φ₀ + Σ breakdown contributions, 0, 100).

A what-if therefore never guesses — it edits specific contributions and re-sums
the deterministic waterfall ("which safety levers move the score?").

Supported flips (keys):
    semantic:<requirement_id>  →  "COMPLIANT"   (remove that penalty)
    rule:<rule_id>             →  false          (remove that rule penalty)
    retrieval_top              →  0.0..1.0       (override the RAG bonus)

The frontend Analyze tab mirrors this same arithmetic so the levers are instant.
"""
from __future__ import annotations

from typing import Any

from rules.scoring import RETRIEVAL_TOP_WEIGHT


def _already_applied(contributions: list[float]) -> float:
    return float(sum(contributions))


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def what_if_score(
    baseline: float,
    breakdown: list[dict[str, Any]],
    flips: dict[str, Any] | None = None,
) -> dict[str, Any]:
    flips = flips or {}
    original_contributions: list[float] = []
    new_breakdown: list[dict[str, Any]] = []
    contributions: list[float] = []
    changed: list[dict[str, Any]] = []

    for row in breakdown or []:
        feature = str(row.get("feature") or "")
        original = float(row.get("contribution", row.get("shap_value", 0.0)))
        new_row = dict(row)
        new_value = original

        if feature.startswith("semantic:"):
            flip = flips.get(feature)
            if flip == "COMPLIANT":
                new_value = 0.0
            elif isinstance(flip, (int, float)) and 0 <= float(flip) <= 1:
                new_value = original * float(flip)
        elif feature.startswith("rule:"):
            flip = flips.get(feature)
            if flip is False:
                new_value = 0.0
        elif feature == "retrieval_top_score":
            target = flips.get("retrieval_top")
            if isinstance(target, (int, float)) and 0 <= float(target) <= 1:
                new_value = RETRIEVAL_TOP_WEIGHT * float(target)

        if abs(new_value - original) > 1e-9:
            new_row["contribution"] = round(new_value, 4)
            new_row["shap_value"] = round(new_value, 4)
            changed.append(
                {
                    "feature": feature,
                    "label": row.get("label") or feature,
                    "from": round(original, 4),
                    "to": round(new_value, 4),
                    "delta": round(new_value - original, 4),
                }
            )

        original_contributions.append(original)
        new_breakdown.append(new_row)
        contributions.append(new_value)

    current = _clamp(float(baseline) + _already_applied(original_contributions))
    outcome = _clamp(float(baseline) + _already_applied(contributions))

    return {
        "baseline_score": round(float(baseline), 2),
        "current_score": current,
        "score": outcome,
        "change": round(outcome - current, 2),
        "breakdown": new_breakdown,
        "changed": changed,
        "applicable_flips": list(changed or []),
    }