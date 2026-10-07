"""
Validation / quality checks for the Regulatory Requirement Bank.

Never invents missing references — flags problems for human review.
"""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml_validation.requirement_bank.quality import (
    evidence_is_grounded,
    looks_like_ocr_garbage,
    normalize_for_id,
)
from ml_validation.schema import RegulatoryRequirement, ReviewStatus


def _fetch_chunk_texts(chunk_ids: list[str]) -> dict[str, str]:
    if not chunk_ids:
        return {}
    from db.mongo import chunks

    out: dict[str, str] = {}
    # Batch in groups to avoid huge $in queries
    batch = 500
    for i in range(0, len(chunk_ids), batch):
        subset = chunk_ids[i : i + batch]
        for doc in chunks().find({"chunk_id": {"$in": subset}}, {"chunk_id": 1, "text": 1}):
            out[doc["chunk_id"]] = doc.get("text") or ""
    return out


def validate_bank(
    requirements: list[RegulatoryRequirement],
    *,
    verify_mongo: bool = True,
) -> dict[str, Any]:
    """
    Run automated QC over a requirement bank.

    Returns a report dict with counts, issue lists, and (optionally) mutates
    `review_status` / `quality_flags` on uncertain rows when `verify_mongo` finds
    broken grounding.
    """
    issues: list[dict[str, Any]] = []
    flags_counter: Counter[str] = Counter()
    exact_dupes: dict[str, list[str]] = defaultdict(list)

    chunk_map: dict[str, str] = {}
    if verify_mongo:
        ids = list({r.source_chunk_id for r in requirements if r.source_chunk_id})
        chunk_map = _fetch_chunk_texts(ids)

    for req in requirements:
        local_flags: list[str] = []

        if not req.requirement_id:
            local_flags.append("missing_requirement_id")
        if not req.source_chunk_id:
            local_flags.append("missing_source_chunk_id")
        if not req.requirement or len(req.requirement.strip()) < 40:
            local_flags.append("requirement_too_short")
        if not req.evidence:
            local_flags.append("missing_evidence")
        if looks_like_ocr_garbage(req.requirement):
            local_flags.append("ocr_garbage")
        if req.requirement.strip() != req.evidence.strip():
            # Allowed only if evidence contains requirement; otherwise flag.
            if req.requirement.strip() not in (req.evidence or ""):
                local_flags.append("requirement_evidence_mismatch")

        if verify_mongo:
            if req.source_chunk_id not in chunk_map:
                local_flags.append("invalid_source_chunk_id")
            else:
                chunk_text = chunk_map[req.source_chunk_id]
                if not evidence_is_grounded(req.evidence, chunk_text):
                    local_flags.append("ungrounded_evidence")
                if not evidence_is_grounded(req.requirement, chunk_text):
                    local_flags.append("ungrounded_requirement")

        key = normalize_for_id(req.requirement)
        exact_dupes[key].append(req.requirement_id)

        if local_flags:
            # Merge flags; demote to needs_review on hard failures
            merged = list(dict.fromkeys((req.quality_flags or []) + local_flags))
            req.quality_flags = merged
            hard = {
                "invalid_source_chunk_id",
                "ungrounded_evidence",
                "ungrounded_requirement",
                "ocr_garbage",
                "missing_source_chunk_id",
            }
            if hard.intersection(local_flags):
                if req.review_status == ReviewStatus.APPROVED.value:
                    req.review_status = ReviewStatus.NEEDS_REVIEW.value
                    req.review_notes = (req.review_notes + " | auto-demoted: grounding/QC failure").strip(" |")
            for f in local_flags:
                flags_counter[f] += 1
            issues.append(
                {
                    "requirement_id": req.requirement_id,
                    "document": req.document,
                    "flags": local_flags,
                    "review_status": req.review_status,
                }
            )

    duplicate_groups = {k: v for k, v in exact_dupes.items() if len(v) > 1}

    by_status = Counter(r.review_status for r in requirements)
    by_domain = Counter(r.domain for r in requirements)

    return {
        "total": len(requirements),
        "by_review_status": dict(by_status),
        "by_domain": dict(by_domain.most_common()),
        "issue_count": len(issues),
        "flag_counts": dict(flags_counter.most_common()),
        "exact_duplicate_groups": len(duplicate_groups),
        "exact_duplicate_examples": list(duplicate_groups.items())[:10],
        "issues_sample": issues[:50],
        "mongo_chunks_checked": len(chunk_map) if verify_mongo else 0,
        "ok_for_dataset_generation": by_status.get(ReviewStatus.APPROVED.value, 0),
        "blocked_until_review": by_status.get(ReviewStatus.NEEDS_REVIEW.value, 0)
        + by_status.get(ReviewStatus.REJECTED.value, 0),
    }
