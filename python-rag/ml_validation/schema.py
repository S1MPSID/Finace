"""
Canonical schemas for the ML validation layer.

These dataclasses are the contract between:
  requirement extraction → QC → dataset generation → training → inference → comparison.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal


class ReviewStatus(str, Enum):
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class ExpectedStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"
    AMBIGUOUS = "AMBIGUOUS"


class ExpectedRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ScenarioType(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial_compliance"
    EDGE = "edge"
    AMBIGUOUS = "ambiguous"
    MULTI_VIOLATION = "multi_violation"
    HARD_NEGATIVE = "hard_negative"


Difficulty = Literal["easy", "medium", "hard"]


@dataclass
class RegulatoryRequirement:
    """
    One obligation extracted from an existing corpus chunk.

    The `requirement` and `evidence` fields MUST be verbatim (or near-verbatim)
    excerpts from `source_chunk_id`. Nothing here is LLM-invented.
    """

    requirement_id: str
    domain: str
    document: str
    section: str
    requirement: str
    source_chunk_id: str
    evidence: str

    # Provenance / quality
    regulator: str = ""
    document_title: str = ""
    document_category: str = ""
    document_status: str = ""
    chunk_index: int | None = None
    sentence_index: int | None = None
    extraction_method: str = "obligation_pattern"
    confidence: float = 0.0
    review_status: str = ReviewStatus.NEEDS_REVIEW.value
    quality_flags: list[str] = field(default_factory=list)
    review_notes: str = ""
    reviewed_by: str = ""
    reviewed_at: str = ""
    bank_version: str = "1.0.0"
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegulatoryRequirement":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class ComplianceCase:
    """Synthetic compliance benchmark row grounded in an approved requirement."""

    case_id: str
    requirement_id: str
    domain: str
    scenario: str
    scenario_type: str
    difficulty: Difficulty
    regulatory_document: str
    regulatory_section: str
    source_chunk_id: str
    compliance_requirement: str
    expected_status: str
    expected_risk: str
    severity: str

    # Extra provenance (not in the minimal user list, but required for QC/leakage)
    family_id: str = ""
    paraphrase_of: str = ""
    bank_version: str = "1.0.0"
    evidence: str = ""
    quality_flags: list[str] = field(default_factory=list)
    review_status: str = ReviewStatus.APPROVED.value
    review_notes: str = ""
    split: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComplianceCase":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


# Domains aligned with Finace payment categories + corpus folders.
CANONICAL_DOMAINS: tuple[str, ...] = (
    "UPI",
    "IMPS",
    "NEFT_RTGS",
    "CTS",
    "AEPS",
    "EKYC",
    "NFS",
    "NPCI",
    "RBI_MD",
    "CRYPTO_VA",
    "FX_FEMA",
    "NACH",
    "RUPAY",
    "FASTAG",
    "BHIM_AADHAR",
    "KYC",
    "PPI",
    "BBPS",
    "GENERAL",
)
