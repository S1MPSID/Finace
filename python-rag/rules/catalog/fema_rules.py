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
    {
        "rule_id": "R_FEMA_003_OVERSEAS_SPEND",
        "name": "Overseas Card / Spend Without FEMA Reporting",
        "risk_level": "MEDIUM",
        "categories": _FEMA,
        "patterns": [
            r"\bforex\s+card\b.*\b(no|without)\s+(fema|reporting)\b",
            r"\boverseas\s+(card|spend|payment)\b.*\b(no|without)\s+reporting\b",
        ],
        "requires_any": [r"\bforex\s+card\b", r"\bintl\s+spend\b.*\breport\b", r"\bfema\s+reporting\b"],
        "flag": "Overseas spend / forex card without FEMA reporting",
        "recommendation": "Report international spend and track LRS against limits.",
    },
    {
        "rule_id": "R_FEMA_004_CURRENCY_CONVERSION_GAP",
        "name": "Currency Conversion / Rates Disclosure",
        "risk_level": "LOW",
        "categories": _FEMA,
        "patterns": [
            r"\bcross[- ]border\b.*\b(no|without)\s+(rate|conversion)\s+disclosure\b",
            r"\b(no|without)\s+interbank\s+rate\b",
        ],
        "requires_any": [
            r"\bconversion\s+rate\b",
            r"\binterbank\s+rate\b",
            r"\bmarkup\s+disclos\b",
            r"\bforex\s+rate\b.*\bdisclos\b",
        ],
        "flag": "FX conversion rate / spread not disclosed",
        "recommendation": "Disclose conversion rates and spreads transparently.",
    },
]
