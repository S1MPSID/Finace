"""
Which bank rows may seed the synthetic dataset.

Rules:
- Never use rejected rows.
- Prefer human/auto ``approved``.
- Also allow high-quality provisional rows (strong deontic cue, grounded,
  non-GENERAL domain, no noise/OCR flags) so corpus coverage can support
  2k–5k cases without inventing requirements.
- Soft-only / low-confidence / GENERAL / noisy rows stay out until reviewed.
"""
from __future__ import annotations

from ml_validation.schema import RegulatoryRequirement, ReviewStatus


def eligible_for_dataset(req: RegulatoryRequirement) -> tuple[bool, str]:
    if req.review_status == ReviewStatus.REJECTED.value:
        return False, "rejected"
    if req.review_status == ReviewStatus.APPROVED.value:
        return True, "approved"
    flags = set(req.quality_flags or [])
    hard_block = {
        "noise",
        "ocr_garbage",
        "ungrounded_evidence",
        "ungrounded_requirement",
        "invalid_source_chunk_id",
        "missing_source_chunk_id",
        "soft_only",
        "domain_uncertain",
    }
    if flags & hard_block:
        return False, "blocked_flags"
    if req.domain == "GENERAL":
        return False, "general_domain"
    if req.confidence < 0.55:
        return False, "low_confidence"
    if not any(str(f).startswith("strong:") for f in flags):
        return False, "no_strong_cue"
    if len((req.requirement or "").strip()) < 50:
        return False, "too_short"
    return True, "provisional_strong"


def filter_eligible(requirements: list[RegulatoryRequirement]) -> list[RegulatoryRequirement]:
    return [r for r in requirements if eligible_for_dataset(r)[0]]
