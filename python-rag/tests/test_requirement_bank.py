"""Unit tests for Regulatory Requirement Bank (no fabricated requirements)."""
from __future__ import annotations

from ml_validation.requirement_bank.extract import extract_from_chunk
from ml_validation.requirement_bank.quality import evidence_is_grounded, looks_like_ocr_garbage
from ml_validation.requirement_bank.validate import validate_bank
from ml_validation.schema import RegulatoryRequirement, ReviewStatus


def test_ocr_garbage_rejected():
    assert looks_like_ocr_garbage("..�>�")
    assert looks_like_ocr_garbage("Nell) adr esther yvrart Fert")
    assert not looks_like_ocr_garbage(
        "Members shall implement mandatory KYC verification before onboarding customers."
    )


def test_evidence_grounding():
    chunk = "Banks shall maintain audit logs for all AePS transactions for a minimum of five years."
    assert evidence_is_grounded(
        "Banks shall maintain audit logs for all AePS transactions for a minimum of five years.",
        chunk,
    )
    assert not evidence_is_grounded("Invented obligation that is not in the chunk.", chunk)


def test_extract_from_chunk_grounded_only():
    chunk = {
        "chunk_id": "test-chunk-001",
        "document_id": "test-aeps-circular",
        "chunk_index": 0,
        "section": "Compliance",
        "text": (
            "Dear Sir/Madam, this is an introduction. "
            "Member banks shall ensure that maker and checker credentials are unique. "
            "Yours faithfully, NPCI."
        ),
        "metadata": {
            "regulator": "NPCI",
            "category": "AEPS",
            "status": "active",
            "title": "Test AePS Circular",
        },
    }
    reqs = extract_from_chunk(chunk, min_confidence=0.35, auto_approve_threshold=0.85)
    assert len(reqs) >= 1
    for r in reqs:
        assert r.source_chunk_id == "test-chunk-001"
        assert r.requirement in chunk["text"]
        assert r.evidence in chunk["text"]
        assert r.domain == "AEPS"
        assert r.requirement_id.startswith("REQ-")


def test_validate_demotes_ungrounded():
    bad = RegulatoryRequirement(
        requirement_id="REQ-bad",
        domain="AEPS",
        document="doc",
        section="GENERAL",
        requirement="This invented sentence is not from any real chunk at all and claims banks must invent controls.",
        source_chunk_id="does-not-exist-xyz",
        evidence="This invented sentence is not from any real chunk at all and claims banks must invent controls.",
        review_status=ReviewStatus.APPROVED.value,
        confidence=0.9,
    )
    report = validate_bank([bad], verify_mongo=True)
    assert report["issue_count"] >= 1
    assert bad.review_status == ReviewStatus.NEEDS_REVIEW.value
    assert "invalid_source_chunk_id" in bad.quality_flags
