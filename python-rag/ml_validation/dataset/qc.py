"""
Automated dataset quality checks.

Flags uncertain / contradictory / ungrounded rows — does not invent fixes.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from ml_validation.requirement_bank.quality import evidence_is_grounded, normalize_for_id
from ml_validation.schema import ComplianceCase, ExpectedRisk, ExpectedStatus


_STATUS_RISK_COMPAT = {
    ExpectedStatus.COMPLIANT.value: {ExpectedRisk.LOW.value, ExpectedRisk.MEDIUM.value},
    ExpectedStatus.PARTIAL.value: {ExpectedRisk.MEDIUM.value, ExpectedRisk.HIGH.value},
    ExpectedStatus.NON_COMPLIANT.value: {ExpectedRisk.MEDIUM.value, ExpectedRisk.HIGH.value},
    ExpectedStatus.AMBIGUOUS.value: {ExpectedRisk.LOW.value, ExpectedRisk.MEDIUM.value, ExpectedRisk.HIGH.value},
}


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def run_dataset_qc(
    cases: list[ComplianceCase],
    *,
    chunk_texts: dict[str, str] | None = None,
    semantic_dedupe_threshold: float = 0.92,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    flag_counts: Counter[str] = Counter()
    exact_scenario: dict[str, list[str]] = defaultdict(list)
    by_req_labels: dict[str, set[str]] = defaultdict(set)

    # Index for near-duplicate detection within same family is OK; across families not.
    for c in cases:
        local: list[str] = []
        if not c.case_id:
            local.append("missing_case_id")
        if not c.requirement_id:
            local.append("missing_requirement_id")
        if not c.source_chunk_id:
            local.append("missing_source_chunk_id")
        if not c.compliance_requirement or len(c.compliance_requirement) < 40:
            local.append("missing_compliance_requirement")
        if not c.scenario or len(c.scenario) < 40:
            local.append("weak_scenario")
        if c.expected_status not in {s.value for s in ExpectedStatus}:
            local.append("invalid_expected_status")
        if c.expected_risk not in {s.value for s in ExpectedRisk}:
            local.append("invalid_expected_risk")
        allowed = _STATUS_RISK_COMPAT.get(c.expected_status, set())
        if c.expected_risk not in allowed:
            local.append("contradictory_status_risk")

        if chunk_texts is not None:
            text = chunk_texts.get(c.source_chunk_id)
            if text is None:
                local.append("invalid_source_chunk_id")
            else:
                if c.evidence and not evidence_is_grounded(c.evidence, text):
                    local.append("ungrounded_evidence")
                if not evidence_is_grounded(c.compliance_requirement, text):
                    local.append("ungrounded_requirement")

        # Template copy-quality: scenario must mention domain or "regulatory"/control language
        if c.scenario and c.compliance_requirement:
            # Requirement snippet should influence scenario (contains shortened req or domain)
            req_tokens = _token_set(c.compliance_requirement)
            scen_tokens = _token_set(c.scenario)
            if _jaccard(req_tokens, scen_tokens) < 0.05 and c.domain.lower() not in c.scenario.lower():
                local.append("low_requirement_grounding_in_scenario")

        key = normalize_for_id(c.scenario)
        exact_scenario[key].append(c.case_id)
        by_req_labels[c.requirement_id].add(f"{c.scenario_type}:{c.expected_status}")

        if local:
            c.quality_flags = list(dict.fromkeys((c.quality_flags or []) + local))
            for f in local:
                flag_counts[f] += 1
            issues.append({"case_id": c.case_id, "flags": local})

    exact_dupes = {k: v for k, v in exact_scenario.items() if len(v) > 1}

    # Semantic near-dupes across different families (sample for report)
    near_dupes = 0
    family_of = {c.case_id: c.family_id for c in cases}
    # Bucket by first 12 chars of normalized scenario for cheap candidates
    buckets: dict[str, list[ComplianceCase]] = defaultdict(list)
    for c in cases:
        buckets[normalize_for_id(c.scenario)[:24]].append(c)
    for group in buckets.values():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, min(i + 6, len(group))):
                a, b = group[i], group[j]
                if a.family_id == b.family_id:
                    continue
                if _jaccard(_token_set(a.scenario), _token_set(b.scenario)) >= semantic_dedupe_threshold:
                    near_dupes += 1

    balance = {
        "status": dict(Counter(c.expected_status for c in cases)),
        "risk": dict(Counter(c.expected_risk for c in cases)),
        "difficulty": dict(Counter(c.difficulty for c in cases)),
        "scenario_type": dict(Counter(c.scenario_type for c in cases)),
    }

    return {
        "total": len(cases),
        "issue_count": len(issues),
        "flag_counts": dict(flag_counts.most_common()),
        "exact_duplicate_scenario_groups": len(exact_dupes),
        "cross_family_near_duplicates_approx": near_dupes,
        "class_balance": balance,
        "issues_sample": issues[:40],
        "ok_for_training": sum(
            1
            for c in cases
            if not set(c.quality_flags or [])
            & {
                "missing_requirement_id",
                "invalid_source_chunk_id",
                "ungrounded_requirement",
                "contradictory_status_risk",
                "invalid_expected_status",
            }
        ),
    }
