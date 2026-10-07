"""Load / save requirement bank artifacts (JSONL + metadata)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ml_validation.paths import (
    BANK_JSONL,
    BANK_META,
    BANK_SUMMARY,
    REVIEW_QUEUE,
    ensure_dirs,
)
from ml_validation.requirement_bank.extract import summarize_bank
from ml_validation.schema import RegulatoryRequirement, ReviewStatus


def save_bank(
    requirements: Iterable[RegulatoryRequirement],
    *,
    path: Path | None = None,
    meta_extra: dict[str, Any] | None = None,
) -> Path:
    ensure_dirs()
    out = path or BANK_JSONL
    rows = [r.to_dict() for r in requirements]
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    objs = [RegulatoryRequirement.from_dict(r) for r in rows]
    summary = summarize_bank(objs)
    summary_path = BANK_SUMMARY
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bank_version": "1.0.0",
        "path": str(out),
        "count": len(rows),
        "principle": "Requirements are extracted ONLY from existing Mongo corpus chunks. No fabricated clauses.",
        **(meta_extra or {}),
        "summary": summary,
    }
    BANK_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def load_bank(path: Path | None = None) -> list[RegulatoryRequirement]:
    src = path or BANK_JSONL
    if not src.exists():
        return []
    out: list[RegulatoryRequirement] = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(RegulatoryRequirement.from_dict(json.loads(line)))
    return out


def save_review_queue(
    requirements: Iterable[RegulatoryRequirement],
    *,
    path: Path | None = None,
) -> Path:
    ensure_dirs()
    out = path or REVIEW_QUEUE
    pending = [
        r.to_dict()
        for r in requirements
        if r.review_status == ReviewStatus.NEEDS_REVIEW.value
    ]
    with out.open("w", encoding="utf-8") as f:
        for row in pending:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out


def load_review_queue(path: Path | None = None) -> list[RegulatoryRequirement]:
    src = path or REVIEW_QUEUE
    if not src.exists():
        return []
    out: list[RegulatoryRequirement] = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(RegulatoryRequirement.from_dict(json.loads(line)))
    return out


def approved_only(requirements: list[RegulatoryRequirement]) -> list[RegulatoryRequirement]:
    return [r for r in requirements if r.review_status == ReviewStatus.APPROVED.value]
