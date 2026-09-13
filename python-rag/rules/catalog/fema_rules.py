_FEMA = ["FX_FEMA", "GENERAL"]

FEMA_RULES: list[dict] = [
    {
        "rule_id": "R_FEMA_001_LRS_BREACH",
        "name": "LRS / Remittance Limit Gap",
        "risk_level": "HIGH",
        "categories": _FEMA,
        "patterns": [
            r"\b(lrs|liberalised\s+remittance)\b.*\b(bypass|exceed|no\s+limit)\b",
            r"\bremittance\b.*\bwithout\s+rbi\s+limit\b",
        ],
        "requires_any": [r"\blrs\b", r"\bremittance\s+limit\b", r"\bfema\s+reporting\b"],
        "flag": "FEMA LRS / remittance limits not enforced",
        "recommendation": "Track LRS caps and FEMA reporting for outward remittance.",
    },
    {
        "rule_id": "R_FEMA_002_FX_NOT_HEDGED",
        "name": "FX Exposure / Hedging Gap",
        "risk_level": "MEDIUM",
        "categories": _FEMA,
        "patterns": [r"\bfx\b.*\b(no|without)\s+hedg", r"\bforeign\s+exchange\b.*\bunmanaged\b"],
        "requires_any": [r"\bhedg(ing|e)\b", r"\bfx\s+risk\b", r"\bfema\s+compliance\b"],
        "flag": "FX exposure management not described",
        "recommendation": "Document FEMA compliance and FX risk controls.",
    },
]
