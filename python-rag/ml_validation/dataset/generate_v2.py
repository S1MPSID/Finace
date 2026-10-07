"""
Generate Hard Benchmark V2 from the existing requirement bank.

Reuses ComplianceCase schema and save/load helpers. Does not paraphrase V1 text.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from loguru import logger

from ml_validation.dataset.generate import save_cases, summarize_cases
from ml_validation.dataset.templates_v2 import TEMPLATES_V2, build_scenario_v2
from ml_validation.requirement_bank.eligibility import eligible_for_dataset, filter_eligible
from ml_validation.schema import ComplianceCase, RegulatoryRequirement, ReviewStatus


def _case_id(requirement_id: str, scenario_type: str, paraphrase_idx: int, tag: str = "v2") -> str:
    digest = hashlib.sha1(
        f"{tag}|{requirement_id}|{scenario_type}|{paraphrase_idx}".encode("utf-8")
    ).hexdigest()[:16]
    return f"CASE-{digest}"


def _family_id(requirement_id: str, scenario_type: str, tag: str = "v2") -> str:
    return f"FAM-{hashlib.sha1(f'{tag}|{requirement_id}|{scenario_type}'.encode()).hexdigest()[:12]}"


def generate_cases_v2(
    requirements: list[RegulatoryRequirement],
    *,
    paraphrases_per_template: int = 2,
    max_requirements: int | None = None,
    seed_tag: str = "v2",
) -> list[ComplianceCase]:
    eligible = filter_eligible(requirements)
    eligible.sort(key=lambda r: (r.domain, r.document, r.requirement_id))
    if max_requirements is not None:
        eligible = eligible[:max_requirements]

    created = datetime.now(timezone.utc).isoformat()
    cases: list[ComplianceCase] = []

    for req in eligible:
        ok, reason = eligible_for_dataset(req)
        if not ok:
            continue
        for tmpl in TEMPLATES_V2:
            for p_idx in range(paraphrases_per_template):
                scenario = build_scenario_v2(
                    domain=req.domain,
                    requirement=req.requirement,
                    builder_key=tmpl.builder_key,
                    paraphrase_idx=p_idx,
                )
                # Guard: requirement text must not appear verbatim in scenario
                req_snip = " ".join((req.requirement or "").split())[:80]
                flags = [f"eligibility:{reason}", f"seed:{seed_tag}", "hard_benchmark_v2"]
                if req_snip and req_snip.lower() in scenario.lower():
                    flags.append("shortcut_requirement_copied")

                case = ComplianceCase(
                    case_id=_case_id(req.requirement_id, tmpl.scenario_type, p_idx, seed_tag),
                    requirement_id=req.requirement_id,
                    domain=req.domain,
                    scenario=scenario,
                    scenario_type=tmpl.scenario_type,
                    difficulty=tmpl.difficulty,  # type: ignore[arg-type]
                    regulatory_document=req.document,
                    regulatory_section=req.section,
                    source_chunk_id=req.source_chunk_id,
                    compliance_requirement=req.requirement,
                    expected_status=tmpl.expected_status,
                    expected_risk=tmpl.expected_risk,
                    severity=tmpl.severity,
                    family_id=_family_id(req.requirement_id, tmpl.scenario_type, seed_tag),
                    paraphrase_of=_case_id(req.requirement_id, tmpl.scenario_type, 0, seed_tag)
                    if p_idx
                    else "",
                    bank_version=req.bank_version or "1.0.0",
                    evidence=req.evidence,
                    quality_flags=flags,
                    review_status=ReviewStatus.APPROVED.value,
                    created_at=created,
                )
                cases.append(case)

    logger.info(
        f"V2 generated {len(cases)} cases from {len(eligible)} eligible requirements"
    )
    return cases


__all__ = ["generate_cases_v2", "save_cases", "summarize_cases"]
