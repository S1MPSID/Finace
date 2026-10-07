"""
Human-review mechanism for uncertain requirement mappings.

Workflow:
1. Extraction writes uncertain rows to ``data/review/needs_review.jsonl``.
2. A reviewer exports decisions via CLI (approve / reject / edit notes).
3. Decisions are applied back onto the bank; only ``approved`` rows may seed
   the synthetic compliance benchmark later.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from ml_validation.paths import REVIEW_DECISIONS, ensure_dirs
from ml_validation.schema import RegulatoryRequirement, ReviewStatus

DecisionAction = Literal["approve", "reject", "needs_review"]


def record_decision(
    requirement_id: str,
    action: DecisionAction,
    *,
    reviewer: str = "human",
    notes: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    ensure_dirs()
    out = path or REVIEW_DECISIONS
    decision = {
        "requirement_id": requirement_id,
        "action": action,
        "reviewer": reviewer,
        "notes": notes,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    return decision


def load_decisions(path: Path | None = None) -> list[dict[str, Any]]:
    src = path or REVIEW_DECISIONS
    if not src.exists():
        return []
    rows: list[dict[str, Any]] = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def apply_decisions(
    requirements: list[RegulatoryRequirement],
    decisions: list[dict[str, Any]] | None = None,
) -> list[RegulatoryRequirement]:
    """
    Apply the latest decision per requirement_id.
    Later decisions override earlier ones.
    """
    decisions = decisions if decisions is not None else load_decisions()
    latest: dict[str, dict[str, Any]] = {}
    for d in decisions:
        rid = d.get("requirement_id")
        if rid:
            latest[rid] = d

    action_map = {
        "approve": ReviewStatus.APPROVED.value,
        "reject": ReviewStatus.REJECTED.value,
        "needs_review": ReviewStatus.NEEDS_REVIEW.value,
    }

    for req in requirements:
        d = latest.get(req.requirement_id)
        if not d:
            continue
        action = str(d.get("action") or "").lower()
        if action not in action_map:
            continue
        req.review_status = action_map[action]
        req.reviewed_by = str(d.get("reviewer") or "human")
        req.reviewed_at = str(d.get("decided_at") or "")
        if d.get("notes"):
            req.review_notes = str(d["notes"])
    return requirements


def export_review_sample(
    requirements: list[RegulatoryRequirement],
    *,
    n: int = 20,
    only_needs_review: bool = True,
) -> list[dict[str, Any]]:
    rows = requirements
    if only_needs_review:
        rows = [r for r in rows if r.review_status == ReviewStatus.NEEDS_REVIEW.value]
    sample = []
    for r in rows[:n]:
        sample.append(
            {
                "requirement_id": r.requirement_id,
                "domain": r.domain,
                "document": r.document,
                "section": r.section,
                "requirement": r.requirement,
                "source_chunk_id": r.source_chunk_id,
                "confidence": r.confidence,
                "quality_flags": r.quality_flags,
                "suggested_actions": ["approve", "reject", "needs_review"],
            }
        )
    return sample
