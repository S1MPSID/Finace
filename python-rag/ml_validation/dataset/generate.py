"""
Generate a large synthetic compliance benchmark FROM the requirement bank.

Every case retains requirement_id, source_chunk_id, document, section, and
evidence. Labels come from scenario templates — not from free-form LLM Q&A.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from ml_validation.dataset.templates import TEMPLATES, build_scenario
from ml_validation.paths import DATASET_DIR, ensure_dirs
from ml_validation.requirement_bank.eligibility import eligible_for_dataset, filter_eligible
from ml_validation.schema import ComplianceCase, RegulatoryRequirement, ReviewStatus


def _case_id(requirement_id: str, scenario_type: str, paraphrase_idx: int) -> str:
    digest = hashlib.sha1(
        f"{requirement_id}|{scenario_type}|{paraphrase_idx}".encode("utf-8")
    ).hexdigest()[:16]
    return f"CASE-{digest}"


def _family_id(requirement_id: str, scenario_type: str) -> str:
    return f"FAM-{hashlib.sha1(f'{requirement_id}|{scenario_type}'.encode()).hexdigest()[:12]}"


def generate_cases(
    requirements: list[RegulatoryRequirement],
    *,
    paraphrases_per_template: int = 2,
    max_requirements: int | None = None,
    seed_tag: str = "v1",
) -> list[ComplianceCase]:
    eligible = filter_eligible(requirements)
    eligible.sort(key=lambda r: (r.domain, r.document, r.requirement_id))
    if max_requirements is not None:
        eligible = eligible[:max_requirements]

    created = datetime.now(timezone.utc).isoformat()
    cases: list[ComplianceCase] = []
    skipped = 0

    for req in eligible:
        ok, reason = eligible_for_dataset(req)
        if not ok:
            skipped += 1
            continue
        for tmpl in TEMPLATES:
            for p_idx in range(paraphrases_per_template):
                scenario = build_scenario(
                    domain=req.domain,
                    requirement=req.requirement,
                    builder_key=tmpl.builder_key,
                    paraphrase_idx=p_idx,
                )
                family = _family_id(req.requirement_id, tmpl.scenario_type)
                case = ComplianceCase(
                    case_id=_case_id(req.requirement_id, tmpl.scenario_type, p_idx),
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
                    family_id=family,
                    paraphrase_of=_case_id(req.requirement_id, tmpl.scenario_type, 0)
                    if p_idx
                    else "",
                    bank_version=req.bank_version or "1.0.0",
                    evidence=req.evidence,
                    quality_flags=[f"eligibility:{reason}", f"seed:{seed_tag}"],
                    review_status=ReviewStatus.APPROVED.value
                    if tmpl.scenario_type != "ambiguous"
                    else ReviewStatus.NEEDS_REVIEW.value,
                    created_at=created,
                )
                cases.append(case)

    logger.info(
        f"Generated {len(cases)} cases from {len(eligible)} eligible requirements "
        f"(skipped_ineligible_loop={skipped})"
    )
    return cases


def summarize_cases(cases: list[ComplianceCase]) -> dict[str, Any]:
    return {
        "total": len(cases),
        "by_status": dict(Counter(c.expected_status for c in cases)),
        "by_risk": dict(Counter(c.expected_risk for c in cases)),
        "by_scenario_type": dict(Counter(c.scenario_type for c in cases)),
        "by_domain": dict(Counter(c.domain for c in cases).most_common()),
        "by_difficulty": dict(Counter(c.difficulty for c in cases)),
        "unique_requirements": len({c.requirement_id for c in cases}),
        "unique_families": len({c.family_id for c in cases}),
        "needs_review_ambiguous": sum(
            1 for c in cases if c.review_status == ReviewStatus.NEEDS_REVIEW.value
        ),
    }


def save_cases(
    cases: list[ComplianceCase],
    *,
    stem: str = "compliance_benchmark",
) -> Path:
    ensure_dirs()
    path = DATASET_DIR / f"{stem}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "path": str(path),
        "principle": "Cases generated from requirement bank only; labels from templates; no invented regulations.",
        "summary": summarize_cases(cases),
    }
    meta_path = DATASET_DIR / f"{stem}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return path


def load_cases(path: Path) -> list[ComplianceCase]:
    out: list[ComplianceCase] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(ComplianceCase.from_dict(json.loads(line)))
    return out
