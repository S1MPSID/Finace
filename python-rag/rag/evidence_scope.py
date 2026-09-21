"""Applicability checks for retrieved regulatory evidence.

Semantic similarity alone is not a legal applicability test. This module marks
retrieved chunks as direct, general-control, or sector-mismatched evidence so a
BHIM/merchant document cannot silently become the legal basis for a VDA or
cross-border-remittance conclusion.
"""
from __future__ import annotations

import re
from typing import Any


DOMAIN_PATTERNS: dict[str, tuple[str, ...]] = {
    "vda_aml": (
        r"\b(?:vda|virtual\s+(?:digital\s+)?asset|crypto(?:currency)?|bitcoin|ethereum)\b",
    ),
    "cross_border_fx": (
        r"\b(?:cross[- ]border|international\s+remittances?|foreign\s+exchange|forex|outward\s+remittances?|overseas)\b",
    ),
    "grievance": (r"\b(?:grievance|complaint|redressal|ombudsman)\b",),
    "kyc_aml_controls": (
        r"\b(?:kyc|e-?kyc|aml|anti[- ]money\s+laundering|sanction|pmla|fiu)\b",
    ),
}

DIRECT_EVIDENCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "vda_aml": (
        r"\b(?:vda|virtual\s+(?:digital\s+)?asset|crypto(?:currency)?|fiu|pmla|virtual\s+asset\s+service)\b",
    ),
    "cross_border_fx": (
        r"\b(?:fema|foreign\s+exchange|authori[sz]ed\s+dealer|remittance|permitted\s+purpose|liberalised\s+remittance)\b",
    ),
    "grievance": (r"\b(?:grievance|complaint|redressal|ombudsman)\b",),
    "kyc_aml_controls": (
        r"\b(?:kyc|e-?kyc|aml|anti[- ]money\s+laundering|sanction|pmla|fiu)\b",
    ),
}

MERCHANT_ONLY = re.compile(
    r"\b(?:merchant\s+acquisition|bhim\s+aadhaar|bhim\s+aadhaar\s+pay|aeps)\b",
    re.IGNORECASE,
)


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def infer_domains(workflow_text: str) -> list[str]:
    text = workflow_text or ""
    return [domain for domain, patterns in DOMAIN_PATTERNS.items() if _matches(patterns, text)]


def _hit_text(hit: dict[str, Any]) -> str:
    metadata = hit.get("metadata") or {}
    return " ".join(
        str(value or "")
        for value in (
            hit.get("document_id"),
            hit.get("section"),
            metadata.get("title"),
            metadata.get("source"),
            metadata.get("relative_path"),
            hit.get("text"),
        )
    )


def annotate_hits(hits: list[dict[str, Any]], workflow_text: str) -> list[dict[str, Any]]:
    domains = set(infer_domains(workflow_text))
    annotated: list[dict[str, Any]] = []
    for hit in hits or []:
        text = _hit_text(hit)
        direct = [
            domain
            for domain, patterns in DIRECT_EVIDENCE_PATTERNS.items()
            if domain in domains and _matches(patterns, text)
        ]
        merchant_only = bool(MERCHANT_ONLY.search(text))
        if merchant_only and ("vda_aml" in domains or "cross_border_fx" in domains):
            basis = "mismatched_sector"
            note = "Merchant/AePS evidence is not direct VDA or cross-border-remittance authority."
        elif direct:
            basis = "direct"
            note = "Retrieved text matches the workflow's identified regulatory domain."
        elif _matches(DIRECT_EVIDENCE_PATTERNS["kyc_aml_controls"], text):
            basis = "general_control"
            note = "General KYC/AML control evidence; sector-specific applicability still requires verification."
        else:
            basis = "unclassified"
            note = "Semantic match only; applicability was not established by the indexed metadata/text."
        enriched = dict(hit)
        enriched["evidence_scope"] = {
            "basis": basis,
            "direct_domains": direct,
            "applicability_note": note,
        }
        annotated.append(enriched)
    return annotated


def build_evidence_scope(workflow_text: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
    domains = infer_domains(workflow_text)
    annotated = annotate_hits(hits, workflow_text)
    direct_domains = sorted(
        {domain for hit in annotated for domain in (hit.get("evidence_scope", {}).get("direct_domains") or [])}
    )
    required = [domain for domain in domains if domain in {"vda_aml", "cross_border_fx", "grievance"}]
    unresolved = [domain for domain in required if domain not in direct_domains]
    labels = {
        "vda_aml": "VDA/FIU/PMLA-specific AML evidence",
        "cross_border_fx": "FEMA/foreign-exchange/remittance evidence",
        "grievance": "grievance/redressal evidence",
    }
    warnings = [
        f"No {labels[domain]} was established in the indexed corpus; do not treat a merchant/AePS clause as the legal basis."
        for domain in unresolved
    ]
    return {
        "workflow_domains": domains,
        "required_direct_domains": required,
        "direct_evidence_domains": direct_domains,
        "unresolved_domains": unresolved,
        "warnings": warnings,
        "method_note": "Applicability is not inferred from embedding similarity alone.",
    }


def select_applicable_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return evidence safe to present as an applicable-clause schedule."""
    return [
        hit
        for hit in hits or []
        if (hit.get("evidence_scope") or {}).get("basis") == "direct"
    ]


def qualify_legal_language(text: str) -> str:
    """Guard generated explanations against unsupported absolute phrasing."""
    replacements = (
        (
            r"the principles of KYC(?: validation)?,? AML,? and risk[- ]based monitoring are universally applicable to (?:any )?regulated financial (?:entity|services?)",
            "The retrieved evidence demonstrates that KYC, sanction screening, risk assessment, and suspicious-transaction monitoring are relevant controls in the cited regulatory context; applicability to this platform must be established against the regulations governing its specific activities.",
        ),
        (
            r"the underlying regulatory expectation for customer identification and due diligence is a universal requirement for entities facilitating financial transactions",
            "The retrieved evidence demonstrates that customer identification and due diligence are relevant controls in the cited regulatory context; applicability to this platform must be established against the regulations governing its specific activities.",
        ),
        (
            r"the principles of KYC validation and risk[- ]based monitoring are universally applicable to regulated financial services",
            "The retrieved evidence demonstrates that KYC validation and risk-based monitoring are relevant controls in the cited regulatory context; applicability to this platform must be established against the regulations governing its specific activities.",
        ),
        (r"the current operational workflow .*? presents critical (?:and uncontrolled )?compliance (?:risks|deficiencies)", "The described workflow presents significant potential compliance exposure"),
        (r"\bhighly\s+non-compliant\b", "significant potential compliance exposure"),
        (
            r"operating without these critical controls will inevitably lead to severe operational disruptions",
            "Operating without these controls may expose the platform to significant regulatory, financial, operational, and reputational consequences, depending on the applicable regulatory framework and entity status.",
        ),
        (r"\binherently\s+high\s+AML\s+risks?\b", "potential AML/CFT risk"),
        (r"\bwill\s+inevitably\s+attract\b", "may attract"),
        (r"\bwill\s+lead\s+to\b", "may contribute to"),
        (r"\binevitably\s+lead\b", "may contribute to"),
        (r"\bextremely\s+high\s+regulatory,\s+financial,\s+and\s+reputational\s+risks?\b", "significant potential regulatory, financial, and reputational exposure"),
    )
    result = text or ""
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return re.sub(r"\.{2,}", ".", result)
