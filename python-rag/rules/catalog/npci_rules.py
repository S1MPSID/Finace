_NPCI = ["NPCI", "UPI", "GENERAL"]

NPCI_RULES: list[dict] = [
    {
        "rule_id": "R_NPCI_001_RUPAY_PCI",
        "name": "RuPay / Card PCI Gap",
        "risk_level": "HIGH",
        "categories": _NPCI,
        "patterns": [r"\brupay\b.*\b(no|without)\s+pci\b", r"\bcard\b.*\bstore\s+cvv\b"],
        "requires_any": [r"\bpci[- ]dss\b", r"\btokeni[sz]ation\b", r"\bno\s+cvv\s+storage\b"],
        "flag": "Card data security (PCI) not described for RuPay/card flows",
        "recommendation": "Implement PCI-DSS, tokenization, and no CVV storage.",
    },
    {
        "rule_id": "R_NPCI_002_NACH_MANDATE",
        "name": "NACH Mandate / Debit Gap",
        "risk_level": "MEDIUM",
        "categories": _NPCI,
        "patterns": [r"\bnach\b.*\b(no|without)\s+mandate\b", r"\bauto\s+debit\b.*\bunauthorized\b"],
        "requires_any": [r"\bnach\s+mandate\b", r"\be-mandate\b", r"\bdebitor\s+authentication\b"],
        "flag": "NACH / auto-debit mandate controls missing",
        "recommendation": "Use signed NACH mandates and pre-debit notification.",
    },
    {
        "rule_id": "R_NPCI_003_FASTAG_KYC",
        "name": "FASTag / NETC Compliance Gap",
        "risk_level": "MEDIUM",
        "categories": _NPCI,
        "patterns": [r"\bfastag\b.*\b(no|without)\s+kyc\b", r"\bnetc\b.*\bnon\s+compliant\b"],
        "requires_any": [r"\bfastag\b.*\bkyc\b", r"\bnetc\b", r"\bvehicle\s+registration\b"],
        "flag": "FASTag / NETC KYC or tag rules not described",
        "recommendation": "Align FASTag issuance with NETC operating circulars.",
    },
    {
        "rule_id": "R_NPCI_004_MEMBER_GUIDELINES",
        "name": "NPCI Member Guidelines Gap",
        "risk_level": "MEDIUM",
        "categories": _NPCI,
        "patterns": [r"\bnpci\b.*\b(not|non)\s+adher", r"\bignore\s+npci\s+circular\b"],
        "requires_any": [
            r"\bnpci\b.*\b(compliant|adher|guideline)\b",
            r"\boperating\s+circular\b",
            r"\bprocedural\s+guideline\b",
        ],
        "flag": "NPCI member guideline adherence not demonstrated",
        "recommendation": "Map processes to NPCI PG/OC and maintain compliance attestations.",
    },
]
