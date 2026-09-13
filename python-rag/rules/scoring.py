"""
Official compliance score — anchor + contributions (clamp 0–100).

Waterfall:  φ₀ + Σ contributions = score
φ₀ = calibrated mean on reference workflows (not 100).
"""
from __future__ import annotations

from typing import Any

from rules.calibration_store import resolve_anchor

RISK_PENALTY: dict[str, float] = {
    "HIGH": 12.0,
    "MEDIUM": 6.0,
    "LOW": 3.0,
}

RETRIEVAL_TOP_WEIGHT = 4.0


def _retrieval_top_score(retrieval_hits: list[dict[str, Any]] | None) -> float:
    scores: list[float] = []
    for hit in retrieval_hits or []:
        raw = hit.get("score", hit.get("rerank_score", hit.get("similarity", 0.0)))
        try:
            scores.append(float(raw))
        except (TypeError, ValueError):
            continue
    return max(scores) if scores else 0.0


def score_from_anchor(
    anchor: float,
    triggered_rules: list[dict[str, Any]],
    retrieval_hits: list[dict[str, Any]] | None,
    semantic_items: list[dict[str, Any]] | None = None,
) -> tuple[float, list[dict[str, Any]]]:
    score = float(anchor)
    breakdown: list[dict[str, Any]] = []

    for rule in triggered_rules or []:
        rid = rule.get("rule_id", "")
        level = str(rule.get("risk_level") or "MEDIUM").upper()
        penalty = RISK_PENALTY.get(level, 6.0)
        score -= penalty
        breakdown.append(
            {
                "feature": f"rule:{rid}",
                "label": rule.get("name") or rid,
                "contribution": round(-penalty, 4),
                "shap_value": round(-penalty, 4),
                "active": True,
                "direction": "decreases_score",
                "risk_level": level,
            }
        )

    for item in semantic_items or []:
        pen = float(item.get("penalty_points") or 0.0)
        if pen <= 0:
            continue
        score -= pen
        breakdown.append(
            {
                "feature": f"semantic:{item.get('requirement_id', 'req')}",
                "label": item.get("display_name") or item.get("label") or item.get("requirement_id"),
                "contribution": round(-pen, 4),
                "shap_value": round(-pen, 4),
                "active": True,
                "direction": "decreases_score",
                "layer": "semantic",
                "status": item.get("status"),
                "confidence": item.get("confidence"),
                "model_source": item.get("model_source"),
                "category": item.get("category"),
            }
        )

    top = _retrieval_top_score(retrieval_hits)
    if top > 0:
        bonus = RETRIEVAL_TOP_WEIGHT * top
        score += bonus
        breakdown.append(
            {
                "feature": "retrieval_top_score",
                "label": "Regulation match strength",
                "contribution": round(bonus, 4),
                "shap_value": round(bonus, 4),
                "active": True,
                "direction": "increases_score",
            }
        )

    return score, breakdown


def get_compliance_anchor(frozen: dict[str, Any] | None = None) -> float:
    """Blended φ₀ (0.7×seed + 0.3×live) or per-chat frozen value."""
    anchor, _, _, _ = resolve_anchor(frozen)
    return anchor


def compute_official_score(
    triggered_rules: list[dict[str, Any]],
    retrieval_hits: list[dict[str, Any]] | None = None,
    semantic_items: list[dict[str, Any]] | None = None,
    calibration_frozen: dict[str, Any] | None = None,
) -> tuple[float, list[dict[str, Any]], float, dict[str, float]]:
    anchor, phi0_seed, phi0_live, phi0_blended = resolve_anchor(calibration_frozen)
    score, breakdown = score_from_anchor(anchor, triggered_rules, retrieval_hits, semantic_items)
    score = float(max(0.0, min(100.0, score)))
    cal = {"phi0_seed": phi0_seed, "phi0_live": phi0_live, "phi0_blended": phi0_blended, "anchor": anchor}
    return score, breakdown, anchor, cal


def risk_from_score_and_rules(
    score: float,
    triggered_rules: list[dict[str, Any]],
) -> str:
    if triggered_rules:
        levels = {str(r.get("risk_level", "MEDIUM")).upper() for r in triggered_rules}
        if "HIGH" in levels:
            return "HIGH"
        if "MEDIUM" in levels:
            return "MEDIUM"
    if score >= 85:
        return "LOW"
    if score >= 65:
        return "MEDIUM"
    return "HIGH"
