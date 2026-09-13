"""
Semantic compliance evaluator — ML classifier when trained, else heuristic fallback.
"""
from __future__ import annotations

import re
from typing import Any

from rules.category_registry import PAYMENT_CATEGORIES
from semantic.ml_model import predict_status

STATUS_PENALTY: dict[str, float] = {
    "COMPLIANT": 0.0,
    "PARTIAL": 4.0,
    "MISSING": 10.0,
    "UNKNOWN": 2.0,
}

# Full penalty only when the model is quite sure. Misses at ~50% confidence
# (barely above the 25% random baseline for a 4-class model) cannot cost −10.
_CONF_FULL = 0.85
_CONF_FLOOR = 0.50
_CONF_MIN_FACTOR = 0.15

# When the user explicitly asks to raise the score / remediate, speculative
# MISSING/PARTIAL checks are dampened so intent does not make things worse.
_IMPROVE_DISCOUNT: dict[str, float] = {
    "MISSING": 0.4,
    "PARTIAL": 0.6,
    "UNKNOWN": 0.8,
    "COMPLIANT": 1.0,
}


def _confidence_factor(confidence: float) -> float:
    c = float(confidence or 0.0)
    if c >= _CONF_FULL:
        return 1.0
    if c <= _CONF_FLOOR:
        return _CONF_MIN_FACTOR
    frac = (c - _CONF_FLOOR) / (_CONF_FULL - _CONF_FLOOR)
    return round(_CONF_MIN_FACTOR + (1.0 - _CONF_MIN_FACTOR) * frac, 3)


def penalty_for_status(
    status: str,
    confidence: float,
    improvement_requested: bool = False,
) -> float:
    base = STATUS_PENALTY.get(status, 2.0)
    if base <= 0 or status == "COMPLIANT":
        return 0.0
    scale = _confidence_factor(confidence)
    if improvement_requested:
        scale *= _IMPROVE_DISCOUNT.get(status, 0.8)
    return round(base * scale, 2)


def category_label(category_id: str) -> str:
    for row in PAYMENT_CATEGORIES:
        if row["id"] == category_id:
            return row["label"]
    return category_id.replace("_", " ")


def normalize_active_categories(active_categories: list[str] | None) -> list[str]:
    cats = [c.strip() for c in (active_categories or []) if c and c.strip()]
    if not cats:
        return ["GENERAL"]
    if len(cats) > 1 and "GENERAL" in cats:
        cats = [c for c in cats if c != "GENERAL"]
    return cats[:8]


def _heuristic_status(requirement: str, text: str) -> tuple[str, float, float]:
    """Keyword-evidence status. Returns (status, confidence, strength).

    Used as the no-model fallback and as an arbiter when the ML classifier is
    uncertain. `strength` is the signed hit count so callers can decide how far
    to trust deterministic evidence over an ambiguous model.
    """
    t = (text or "").lower()

    strong_neg = [
        r"\bno\s+\w+\b",
        r"\bwithout\s+",
        r"\bdo(es)?\s+not\s+(provide|offer|implement|perform|conduct|carry)\b",
        r"\bnot\s+(implemented|available|provided|performed|conducted|offered)\b",
        r"\bdon'?t\s+(provide|offer|implement|have)\b",
        r"\babsent\b",
    ]
    hedge_neg = [
        r"\bplan(ned|ning)?\s+to\b",
        r"\bintend\s+to\b",
        r"\bwill\s+(introduce|roll\s?out|adopt|implement)\b",
        r"\bunder\s+review\b",
        r"\btimeframe\b",
        r"\bnext\s+year\b",
        r"\bphased\b",
        r"\bon\s+the\s+roadmap\b",
        r"\bpilot\b",
        r"\bbeta\b",
        r"\bpartial\b",
        r"\bnot\s+yet\b",
    ]
    strong_pos = [
        r"\bin\s+place\b",
        r"\bimplemented\b",
        r"\benabled\b",
        r"\bmandatory\b",
        r"\bcomplete\s+(\w+\s+)?(kyc|verification|e-?kyc)\b",
        r"\bfull\s+kyc\b",
        r"\be-?kyc\b",
        r"\bverified\b",
        r"\bverification\b",
        r"\bmonitoring\b",
        r"\bmonitor(s|ing)?\b",
        r"\bredressal\b",
        r"\bredress\b",
        r"\bgrievance\s+officer\b",
        r"\btracking\s+id\b",
        r"\bescalat(e|ion|ed)\b",
        r"\bmaker-?checker\b",
        r"\baudit\s+trail\b",
        r"\baudited\b",
        r"\bconsent\b",
        r"\baadhaar\b",
        r"\botp\b",
        r"\b2fa\b",
        r"\bmfa\b",
        r"\btwo-?factor\b",
        r"\bauthentication\b",
        r"\bcertified\s+devices\b",
        r"\bscreening\b",
        r"\breport(s|ing)?\b",
        r"\bretention\b",
        r"\breconcil(ed|ation)\b",
    ]

    neg_hits = sum(bool(re.search(p, t)) for p in strong_neg) + sum(
        bool(re.search(p, t)) for p in hedge_neg
    )
    pos_hits = sum(bool(re.search(p, t)) for p in strong_pos)

    if neg_hits >= pos_hits and neg_hits > 0:
        if any(re.search(p, t) for p in hedge_neg) and not any(
            re.search(p, t) for p in strong_neg
        ):
            return "PARTIAL", 0.6, neg_hits
        return "MISSING", 0.72, neg_hits
    if pos_hits >= 2:
        return "COMPLIANT", 0.68, pos_hits
    if pos_hits == 1:
        return "COMPLIANT", 0.55, pos_hits
    return "PARTIAL", 0.5, 0


class SemanticComplianceEvaluator:
    def evaluate(
        self,
        workflow_text: str,
        llm_output_text: str = "",
        active_categories: list[str] | None = None,
        retrieval_hits: list[dict[str, Any]] | None = None,
        improvement_requested: bool = False,
    ) -> list[dict[str, Any]]:
        combined = f"{workflow_text}\n{llm_output_text}".strip()
        categories = normalize_active_categories(active_categories)
        results: list[dict[str, Any]] = []

        for cat in categories:
            req_id = f"SEM_{cat}_CONTROLS"
            status, confidence, source = predict_status(cat, combined, retrieval_hits=retrieval_hits)
            penalty = STATUS_PENALTY.get(status, 2.0)
            cat_label = category_label(cat)
            penalty_pts = penalty_for_status(status, confidence, improvement_requested)
            results.append(
                {
                    "requirement_id": req_id,
                    "category": cat,
                    "status": status,
                    "confidence": round(confidence, 3),
                    "penalty_points": penalty_pts,
                    "max_penalty_points": penalty if status != "COMPLIANT" else 0.0,
                    "model_source": source,
                    "label": f"{cat_label} — {status}",
                    "display_name": f"Control check · {cat_label}",
                }
            )
        return results
