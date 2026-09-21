"""
Deterministic rule definitions for hybrid compliance scoring.
"""
from __future__ import annotations


RULES: list[dict] = [
    {
        "rule_id": "R001_NO_KYC",
        "name": "Missing KYC",
        "risk_level": "HIGH",
        "patterns": [r"\bno\s+kyc\b", r"\bwithout\s+kyc\b", r"\bskip\s+kyc\b"],
        "applicability_patterns": [r"\b(?:customer|user|client|account|onboard|open\s+accounts?)\b"],
        # If the latest description asserts KYC is in place, do not keep the gap open.
        "requires_any": [
            r"\b(full|mandatory|complete|strong)?\s*kyc\b.*\b(in\s+place|enabled|implemented|added|present|done)\b",
            r"\b(have|has|with|using|added|implemented)\s+(full\s+)?kyc\b",
            r"\bkyc\s+(is\s+)?(complete|mandatory|enabled|implemented)\b",
        ],
        "flag": "KYC process appears missing or bypassed",
        "recommendation": "RECOMMENDED MITIGATION: Implement mandatory full KYC before onboarding or activation; confirm the exact requirement under the applicable framework.",
    },
    {
        "rule_id": "R002_P2P_CRYPTO",
        "name": "P2P Crypto Exposure",
        "risk_level": "HIGH",
        "patterns": [r"\bp2p\b.*\bcrypto\b", r"\bcrypto\b.*\bp2p\b", r"\bvirtual\s+asset\b"],
        "applicability_patterns": [r"\b(?:p2p|crypto(?:currency)?|virtual\s+(?:digital\s+)?asset|vda|bitcoin|ethereum)\b"],
        "requires_any": [
            r"\baml\b",
            r"\banti[- ]money\b",
            r"\btransaction\s+monitoring\b",
            r"\benhanced\s+due\s+diligence\b",
            r"\bedd\b",
        ],
        "flag": "Potential high AML risk from P2P/crypto activity",
        "recommendation": "RECOMMENDED MITIGATION: Add risk-based AML controls, due diligence, and transaction monitoring; apply mandatory measures only after confirming the applicable VDA/AML framework.",
    },
    {
        "rule_id": "R003_CROSS_BORDER_NO_FEMA",
        "name": "Cross-border Without FEMA Controls",
        "risk_level": "HIGH",
        "patterns": [
            r"\bcross[- ]border\b",
            r"\bforeign\s+transfer\b",
            r"\binternational\s+remittances?\b",
        ],
        "applicability_patterns": [r"\b(?:cross[- ]border|international\s+remittances?|foreign\s+transfer(?:s)?|foreign\s+exchange|forex|overseas)\b"],
        "requires_any": [
            r"\bfema\b",
            r"\bfx\s+compliance\b",
            r"\bforex\s+declaration\b",
            r"\bforex\s+compliance\b",
            r"\brbi\s+reporting\b",
        ],
        "flag": "Cross-border flow detected without explicit FEMA/FX compliance terms",
        "recommendation": "RECOMMENDED MITIGATION: Assess FEMA/foreign-exchange checks, reporting and authorised-intermediary controls after confirming residency, transaction structure and authorisation status.",
    },
    {
        "rule_id": "R004_NO_GRIEVANCE",
        "name": "Missing Grievance Redressal",
        "risk_level": "MEDIUM",
        "patterns": [r"\bno\s+grievance\b", r"\bwithout\s+grievance\b", r"\bno\s+complaint\b"],
        "applicability_patterns": [r"\b(?:fintech|financial|payment|remittance|crypto|customer(?:s)?|user(?:s)?|client(?:s)?|account(?:s)?|platform)\b"],
        "requires_any": [
            r"\bgrievance\s+(redressal|process|mechanism)\b",
            r"\bcomplaint\s+handling\b",
            r"\b(have|has|with|added|implemented)\s+grievance\b",
        ],
        "flag": "Grievance redressal/complaint handling appears absent",
        "recommendation": "RECOMMENDED MITIGATION: Define a grievance process with SLA, escalation matrix and audit trail; verify whether a specific grievance obligation applies to this licence/business model.",
    },
]
