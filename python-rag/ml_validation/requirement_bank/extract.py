"""
Extract structured regulatory requirements from the existing Mongo corpus.

Rules:
- ONLY use chunks already stored in MongoDB (`chunks` collection).
- Requirement / evidence text must come from the chunk (verbatim sentence).
- Uncertain or low-quality candidates are flagged for human review — never invent labels.
"""
from __future__ import annotations

import hashlib
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterator

from loguru import logger

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml_validation.requirement_bank.domains import map_domain
from ml_validation.requirement_bank.patterns import obligation_score, split_sentences
from ml_validation.requirement_bank.quality import (
    evidence_is_grounded,
    looks_like_ocr_garbage,
    normalize_for_id,
)
from ml_validation.schema import RegulatoryRequirement, ReviewStatus


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_requirement_id(chunk_id: str, sentence_index: int, requirement: str) -> str:
    digest = hashlib.sha1(
        f"{chunk_id}|{sentence_index}|{normalize_for_id(requirement)}".encode("utf-8")
    ).hexdigest()[:16]
    return f"REQ-{digest}"


def _iter_chunks(
    *,
    limit: int | None = None,
    regulator: str | None = None,
    status: str | None = "active",
    batch_size: int = 200,
) -> Iterator[dict[str, Any]]:
    from db.mongo import chunks

    query: dict[str, Any] = {}
    if status:
        query["metadata.status"] = status
    if regulator:
        query["metadata.regulator"] = regulator.upper()

    projection = {
        "chunk_id": 1,
        "document_id": 1,
        "chunk_index": 1,
        "section": 1,
        "text": 1,
        "metadata": 1,
    }
    cursor = chunks().find(query, projection).batch_size(batch_size)
    count = 0
    for doc in cursor:
        yield doc
        count += 1
        if limit is not None and count >= limit:
            break


def extract_from_chunk(
    chunk: dict[str, Any],
    *,
    min_confidence: float = 0.35,
    auto_approve_threshold: float = 0.85,
) -> list[RegulatoryRequirement]:
    text = chunk.get("text") or ""
    chunk_id = chunk.get("chunk_id") or ""
    if not chunk_id or looks_like_ocr_garbage(text):
        return []

    meta = chunk.get("metadata") or {}
    domain = map_domain(
        category=meta.get("category"),
        document_id=chunk.get("document_id"),
        title=meta.get("title"),
    )
    created = _utcnow()
    out: list[RegulatoryRequirement] = []

    for idx, sentence in enumerate(split_sentences(text)):
        if looks_like_ocr_garbage(sentence):
            continue
        if len(sentence) < 45 or len(sentence) > 900:
            continue

        conf, pattern_flags = obligation_score(sentence)
        if conf < min_confidence:
            continue
        if not evidence_is_grounded(sentence, text):
            continue

        quality_flags = list(pattern_flags)
        review = ReviewStatus.NEEDS_REVIEW.value
        if conf >= auto_approve_threshold and "noise" not in quality_flags:
            # Still keep auto-approve conservative: require a strong cue and clean text.
            if any(f.startswith("strong:") for f in quality_flags):
                review = ReviewStatus.APPROVED.value
            else:
                quality_flags.append("soft_only")
        else:
            if conf < 0.55:
                quality_flags.append("low_confidence")
            if domain == "GENERAL":
                quality_flags.append("domain_uncertain")

        # Soft-only or general domain → always human review
        if "soft_only" in quality_flags or "domain_uncertain" in quality_flags:
            review = ReviewStatus.NEEDS_REVIEW.value

        req = RegulatoryRequirement(
            requirement_id=_make_requirement_id(chunk_id, idx, sentence),
            domain=domain,
            document=str(chunk.get("document_id") or ""),
            section=str(chunk.get("section") or meta.get("title") or "GENERAL"),
            requirement=sentence.strip(),
            source_chunk_id=chunk_id,
            evidence=sentence.strip(),
            regulator=str(meta.get("regulator") or ""),
            document_title=str(meta.get("title") or ""),
            document_category=str(meta.get("category") or ""),
            document_status=str(meta.get("status") or ""),
            chunk_index=chunk.get("chunk_index"),
            sentence_index=idx,
            extraction_method="obligation_pattern_v1",
            confidence=round(conf, 3),
            review_status=review,
            quality_flags=quality_flags,
            bank_version="1.0.0",
            created_at=created,
        )
        out.append(req)
    return out


def extract_requirements(
    *,
    limit: int | None = None,
    regulator: str | None = None,
    status: str | None = "active",
    min_confidence: float = 0.35,
    auto_approve_threshold: float = 0.85,
    dedupe: bool = True,
) -> list[RegulatoryRequirement]:
    """
    Scan the Mongo corpus and return grounded requirement candidates.

    Deduplication is exact on normalized requirement text within the same document
    (keeps the higher-confidence instance).
    """
    results: list[RegulatoryRequirement] = []
    seen_text: dict[str, RegulatoryRequirement] = {}
    skipped_chunks = 0
    scanned = 0

    for chunk in _iter_chunks(limit=limit, regulator=regulator, status=status):
        scanned += 1
        text = chunk.get("text") or ""
        if looks_like_ocr_garbage(text):
            skipped_chunks += 1
            continue
        for req in extract_from_chunk(
            chunk,
            min_confidence=min_confidence,
            auto_approve_threshold=auto_approve_threshold,
        ):
            if not dedupe:
                results.append(req)
                continue
            key = f"{req.document}|{normalize_for_id(req.requirement)}"
            prev = seen_text.get(key)
            if prev is None or req.confidence > prev.confidence:
                seen_text[key] = req

    if dedupe:
        results = list(seen_text.values())

    results.sort(key=lambda r: (r.domain, r.document, -(r.confidence), r.requirement_id))
    logger.info(
        f"Requirement extraction: scanned={scanned} skipped_ocr={skipped_chunks} "
        f"candidates={len(results)}"
    )
    return results


def summarize_bank(requirements: list[RegulatoryRequirement]) -> dict[str, Any]:
    by_status = Counter(r.review_status for r in requirements)
    by_domain = Counter(r.domain for r in requirements)
    by_regulator = Counter(r.regulator or "UNKNOWN" for r in requirements)
    return {
        "total": len(requirements),
        "by_review_status": dict(by_status),
        "by_domain": dict(by_domain.most_common()),
        "by_regulator": dict(by_regulator),
        "mean_confidence": round(
            sum(r.confidence for r in requirements) / max(len(requirements), 1), 3
        ),
        "approved_only": by_status.get(ReviewStatus.APPROVED.value, 0),
        "needs_review": by_status.get(ReviewStatus.NEEDS_REVIEW.value, 0),
    }
