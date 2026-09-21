"""
Deterministic rule evaluator.
"""
from __future__ import annotations

import re

from rules.rules_config import RULES


_RISK_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
_NEGATION_RE = re.compile(
    r"\b(?:no|not|without|missing|absent|lack|lacks|never|bypass|bypassed|"
    r"do\s+not|does\s+not|did\s+not|don't|doesn't)\b",
    flags=re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"\S+")
_NEGATION_WINDOW = 6


def _match_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _match_positive(patterns: list[str], text: str) -> bool:
    """Match a control only when the text asserts it is present.

    Rule requirements such as ``AML`` or ``FEMA`` must not count a negated
    statement like ``we do not run AML screening`` as evidence that the
    control exists.
    """
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            left = _TOKEN_RE.findall(text[: match.start()])[-_NEGATION_WINDOW:]
            right = _TOKEN_RE.findall(text[match.end() :])[:_NEGATION_WINDOW]
            if not _NEGATION_RE.search(" ".join(left + right)):
                return True
    return False


def _rule_is_applicable(rule: dict, text: str) -> bool:
    patterns = rule.get("applicability_patterns") or rule.get("patterns") or []
    return _match_any(patterns, text)


def evaluate_rules(workflow_text: str) -> dict:
    text = workflow_text or ""
    triggered: list[dict] = []
    assessments: list[dict] = []

    for rule in RULES:
        applicable = _rule_is_applicable(rule, text)
        if not applicable:
            continue
        if not _match_any(rule.get("patterns", []), text):
            assessments.append({
                "rule_id": rule["rule_id"],
                "name": rule["name"],
                "risk_level": rule["risk_level"],
                "applicable": True,
                "triggered": False,
                "status": "applicable_not_triggered",
                "impact_basis": "No deterministic violation pattern was found in the workflow.",
            })
            continue

        requires_any = rule.get("requires_any", [])
        if requires_any and _match_positive(requires_any, text):
            # Required controls are present, so do not trigger this risk rule.
            assessments.append({
                "rule_id": rule["rule_id"],
                "name": rule["name"],
                "risk_level": rule["risk_level"],
                "applicable": True,
                "triggered": False,
                "status": "applicable_not_triggered",
                "impact_basis": "The workflow mentions the relevant domain and states the required control is present.",
            })
            continue

        item = {
                "rule_id": rule["rule_id"],
                "name": rule["name"],
                "risk_level": rule["risk_level"],
                "flag": rule["flag"],
                "recommendation": rule["recommendation"],
            }
        triggered.append(item)
        assessments.append({
            **item,
            "applicable": True,
            "triggered": True,
            "status": "triggered",
            "impact_basis": "The domain is present and the deterministic violation pattern was triggered.",
        })

    highest = "LOW"
    for item in triggered:
        if _RISK_RANK[item["risk_level"]] > _RISK_RANK[highest]:
            highest = item["risk_level"]

    return {
        "risk_level": highest,
        "triggered_rules": triggered,
        "risk_flags": [r["flag"] for r in triggered],
        "recommendations": [r["recommendation"] for r in triggered],
        "rule_assessments": assessments,
    }