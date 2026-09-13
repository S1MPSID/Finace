"""
Deterministic rule evaluator.
"""
from __future__ import annotations

import re

from rules.rules_config import RULES


_RISK_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _match_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _rule_applies(rule: dict, active_categories: list[str] | None) -> bool:
    cats = rule.get("categories") or []
    if not cats:
        return True
    active = {c.strip().upper() for c in (active_categories or []) if c}
    if not active:
        active = {"GENERAL"}
    allowed = {c.upper() for c in cats}
    return bool(active & allowed)


def evaluate_rules(workflow_text: str, active_categories: list[str] | None = None) -> dict:
    text = workflow_text or ""
    triggered: list[dict] = []

    for rule in RULES:
        if not _rule_applies(rule, active_categories):
            continue
        if not _match_any(rule.get("patterns", []), text):
            continue

        requires_any = rule.get("requires_any", [])
        if requires_any and _match_any(requires_any, text):
            # Required controls are present, so do not trigger this risk rule.
            continue

        triggered.append(
            {
                "rule_id": rule["rule_id"],
                "name": rule["name"],
                "risk_level": rule["risk_level"],
                "flag": rule["flag"],
                "recommendation": rule["recommendation"],
            }
        )

    highest = "LOW"
    for item in triggered:
        if _RISK_RANK[item["risk_level"]] > _RISK_RANK[highest]:
            highest = item["risk_level"]

    return {
        "risk_level": highest,
        "triggered_rules": triggered,
        "risk_flags": [r["flag"] for r in triggered],
        "recommendations": [r["recommendation"] for r in triggered],
    }
