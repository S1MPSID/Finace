_RBI = ["RBI_MD", "GENERAL"]

RBI_MD_RULES: list[dict] = [
    {
        "rule_id": "R_RBI_001_PAYMENT_AGGREGATOR",
        "name": "Payment Aggregator / PA License Gap",
        "risk_level": "HIGH",
        "categories": _RBI,
        "patterns": [
            r"\bpayment\s+aggregat(or|ion)\b.*\b(no|without)\s+license\b",
            r"\bpa\b.*\bunlicensed\b",
            r"\bcollect\s+payments\b.*\bno\s+rbi\s+authorization\b",
        ],
        "requires_any": [
            r"\bpayment\s+aggregat(or|ion)\s+license\b",
            r"\brbi\s+authorization\b",
            r"\bpa\s+license\b",
        ],
        "flag": "Payment aggregator / intermediary authorization unclear",
        "recommendation": "Obtain RBI PA license or partner with licensed entity.",
    },
    {
        "rule_id": "R_RBI_002_OUTSOURCING",
        "name": "Outsourcing / Third-Party Risk Gap",
        "risk_level": "MEDIUM",
        "categories": _RBI,
        "patterns": [r"\boutsourc(e|ing)\b.*\b(no|without)\s+(agreement|audit)\b", r"\bvendor\b.*\bunvetted\b"],
        "requires_any": [r"\boutsourcing\s+policy\b", r"\bthird[- ]party\s+risk\b", r"\bvendor\s+due\s+diligence\b"],
        "flag": "RBI outsourcing guidelines not reflected",
        "recommendation": "Contract and monitor third parties per RBI outsourcing directions.",
    },
    {
        "rule_id": "R_RBI_003_INCIDENT_REPORTING",
        "name": "Incident Reporting Gap",
        "risk_level": "MEDIUM",
        "categories": _RBI,
        "patterns": [r"\b(no|without)\s+incident\s+reporting\b", r"\bbreach\b.*\bnot\s+reported\b"],
        "requires_any": [r"\bincident\s+reporting\b", r"\bcert-in\b", r"\brbi\s+reporting\b"],
        "flag": "Cyber / payment incident reporting not described",
        "recommendation": "Define RBI/CERT-In incident reporting playbooks.",
    },
    {
        "rule_id": "R_RBI_004_CUSTOMER_PROTECTION",
        "name": "Customer Protection / T&C Gap",
        "risk_level": "LOW",
        "categories": _RBI,
        "patterns": [r"\b(no|without)\s+(terms|disclosure)\b.*\bcustomer\b", r"\bhidden\s+fee\b"],
        "requires_any": [r"\bcustomer\s+protection\b", r"\bdisclosure\b", r"\bterms\s+and\s+conditions\b"],
        "flag": "Customer protection disclosures weak",
        "recommendation": "Publish fees, T&C, and RBI customer protection commitments.",
    },
]
