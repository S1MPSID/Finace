"""
Compare ML validation predictions vs Finace deterministic rules / expected labels.

Does not call Gemini by default (expensive); uses rules engine for Finace side.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from loguru import logger

from ml_validation.model.predict import predict_workflow
from ml_validation.paths import REPORTS_DIR, ensure_dirs
from ml_validation.schema import ComplianceCase


def _rule_risk(workflow: str) -> dict[str, Any]:
    try:
        from rules.rule_engine import evaluate_rules

        out = evaluate_rules(workflow)
        return {
            "risk_level": out.get("risk_level") or "LOW",
            "triggered_rules": [r.get("rule_id") for r in (out.get("triggered_rules") or [])],
            "risk_flags": out.get("risk_flags") or [],
        }
    except Exception as exc:
        logger.warning(f"Rule engine unavailable for compare: {exc}")
        return {"risk_level": None, "triggered_rules": [], "risk_flags": [], "error": str(exc)}


def _pair_key(ml_risk: str | None, rule_risk: str | None) -> str:
    return f"ML_{ml_risk or 'NA'}__Rules_{rule_risk or 'NA'}"


def _categorize_disagreement(
    *,
    ml_risk: str | None,
    rule_risk: str | None,
    expected_risk: str,
    triggered: list[str],
) -> str:
    """
    Heuristic category — NOT a verdict of correctness.
    Disagreement does not mean either side is wrong.
    """
    if not ml_risk or not rule_risk or ml_risk == rule_risk:
        return "agree_or_incomplete"
    # Rules fire specific IDs while ML says LOW → often different signals
    if triggered and ml_risk == "LOW" and rule_risk in {"MEDIUM", "HIGH"}:
        return "both_capture_different_signals"
    if expected_risk == ml_risk and expected_risk != rule_risk:
        return "ml_aligned_with_template_label"
    if expected_risk == rule_risk and expected_risk != ml_risk:
        return "rules_aligned_with_template_label"
    if expected_risk not in {ml_risk, rule_risk}:
        return "ambiguous_needs_review"
    return "both_capture_different_signals"


def compare_cases(
    cases: list[ComplianceCase],
    *,
    limit: int | None = 200,
) -> dict[str, Any]:
    rows = cases[: limit or len(cases)]
    agreements_status = 0
    agreements_risk_ml_gt = 0
    agreements_risk_ml_rules = 0
    fp = 0  # ML NON_COMPLIANT while GT COMPLIANT
    fn = 0  # ML COMPLIANT while GT NON_COMPLIANT
    hard_cases: list[dict[str, Any]] = []
    domain_stats: dict[str, Counter] = {}
    disagree_buckets: Counter[str] = Counter()
    disagree_categories: Counter[str] = Counter()
    disagree_samples: list[dict[str, Any]] = []

    details: list[dict[str, Any]] = []
    for c in rows:
        ml = predict_workflow(
            c.scenario,
            domain=c.domain,
            requirement=c.compliance_requirement,
            include_explanation=False,
        )
        rules = _rule_risk(c.scenario)
        if not ml.get("available"):
            continue

        ml_status = ml.get("compliance_status")
        ml_risk = ml.get("risk_category")
        rule_risk = rules.get("risk_level")
        status_agree = ml_status == c.expected_status
        risk_agree_gt = ml_risk == c.expected_risk
        risk_agree_rules = ml_risk == rule_risk

        agreements_status += int(status_agree)
        agreements_risk_ml_gt += int(risk_agree_gt)
        agreements_risk_ml_rules += int(bool(risk_agree_rules))

        if ml_status == "NON_COMPLIANT" and c.expected_status == "COMPLIANT":
            fp += 1
        if ml_status == "COMPLIANT" and c.expected_status == "NON_COMPLIANT":
            fn += 1

        domain_stats.setdefault(c.domain, Counter())
        domain_stats[c.domain]["n"] += 1
        domain_stats[c.domain]["status_agree"] += int(status_agree)

        if ml_risk != rule_risk:
            pair = _pair_key(str(ml_risk), str(rule_risk))
            disagree_buckets[pair] += 1
            cat = _categorize_disagreement(
                ml_risk=str(ml_risk) if ml_risk else None,
                rule_risk=str(rule_risk) if rule_risk else None,
                expected_risk=c.expected_risk,
                triggered=list(rules.get("triggered_rules") or []),
            )
            disagree_categories[cat] += 1
            if len(disagree_samples) < 60:
                disagree_samples.append(
                    {
                        "case_id": c.case_id,
                        "domain": c.domain,
                        "scenario_type": c.scenario_type,
                        "pair": pair,
                        "category": cat,
                        "expected_risk": c.expected_risk,
                        "ml_risk": ml_risk,
                        "rule_risk": rule_risk,
                        "triggered_rules": rules.get("triggered_rules"),
                        "expected_status": c.expected_status,
                        "ml_status": ml_status,
                        "requirement_id": c.requirement_id,
                        "note": "Category is heuristic; disagreement ≠ error.",
                    }
                )

        if not status_agree or c.difficulty == "hard":
            hard_cases.append(
                {
                    "case_id": c.case_id,
                    "domain": c.domain,
                    "difficulty": c.difficulty,
                    "scenario_type": c.scenario_type,
                    "expected_status": c.expected_status,
                    "ml_status": ml_status,
                    "expected_risk": c.expected_risk,
                    "ml_risk": ml_risk,
                    "rule_risk": rule_risk,
                    "requirement_id": c.requirement_id,
                    "source_chunk_id": c.source_chunk_id,
                }
            )

        details.append(
            {
                "case_id": c.case_id,
                "expected_status": c.expected_status,
                "ml_status": ml_status,
                "expected_risk": c.expected_risk,
                "ml_risk": ml_risk,
                "rule_risk": rule_risk,
                "triggered_rules": rules.get("triggered_rules"),
            }
        )

    n = max(len(details), 1)
    n_disagree = sum(disagree_buckets.values())
    report = {
        "n_compared": len(details),
        "ml_vs_ground_truth_status_agreement": round(agreements_status / n, 4),
        "ml_vs_ground_truth_risk_agreement": round(agreements_risk_ml_gt / n, 4),
        "ml_vs_rules_risk_agreement": round(agreements_risk_ml_rules / n, 4),
        "false_positives_noncompliant_on_compliant": fp,
        "false_negatives_compliant_on_noncompliant": fn,
        "per_domain_status_agreement": {
            d: round(cnt["status_agree"] / max(cnt["n"], 1), 4) for d, cnt in domain_stats.items()
        },
        "risk_disagreement": {
            "n_disagree": n_disagree,
            "rate": round(n_disagree / n, 4),
            "pairs": dict(disagree_buckets.most_common()),
            "categories": dict(disagree_categories.most_common()),
            "samples": disagree_samples,
            "interpretation": [
                "ml_aligned_with_template_label — ML matches synthetic label; rules differ",
                "rules_aligned_with_template_label — rules match synthetic label; ML differs",
                "both_capture_different_signals — likely complementary, not necessarily wrong",
                "ambiguous_needs_review — neither matches template label",
            ],
        },
        "difficult_or_disagree_sample": hard_cases[:40],
        "notes": [
            "Ground truth = template labels tied to requirement bank (not legal advice).",
            "Rules = Finace deterministic rule engine.",
            "ML does not override rules/RAG/LLM in production path.",
            "Gemini assessment not invoked here (cost); compare analytically against rules + labels.",
            "Disagreement analysis does NOT assume either component is wrong.",
        ],
        "details_sample": details[:30],
    }
    return report


def save_comparison(report: dict[str, Any], stem: str = "ml_vs_finace") -> Path:
    ensure_dirs()
    path = REPORTS_DIR / f"{stem}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path
