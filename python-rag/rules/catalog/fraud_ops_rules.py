_FRAUD = ["FRAUD_OPS", "GENERAL"]

FRAUD_OPS_RULES: list[dict] = [
    {
        "rule_id": "R_FRAUD_001_NO_MONITORING",
        "name": "No Fraud Monitoring Ops",
        "risk_level": "HIGH",
        "categories": _FRAUD,
        "patterns": [
            r"\b(no|without)\s+fraud\s+(monitoring|surveillance|operations)\b",
            r"\bno\s+fraud\s+(team|cell)\b",
            r"\bfraud\b.*\bnot\s+monitored\b",
        ],
        "requires_any": [
            r"\bfraud\s+(monitoring|surveillance|management|cell|team)\b",
            r"\btransaction\s+monitoring\b",
            r"\banomaly\s+detection\b",
        ],
        "flag": "Fraud monitoring capability not described",
        "recommendation": "Stand up a 24x7 fraud monitoring team and controls.",
    },
    {
        "rule_id": "R_FRAUD_002_NO_CHARGEBACK_PROCESS",
        "name": "No Chargeback / Rebuttal Process",
        "risk_level": "MEDIUM",
        "categories": _FRAUD,
        "patterns": [
            r"\b(no|without)\s+chargeback\s+(process|workflow|management)\b",
            r"\bchargebacks?\b.*\bnot\s+(handled|rebutted|processed)\b",
        ],
        "requires_any": [
            r"\bchargeback\s+(process|rebuttal|workflow|management)\b",
            r"\bdispute\s+(resolution|process)\b",
            r"\brepresent\w+\b.*\bchargeback\b",
        ],
        "flag": "Chargeback handling / rebuttal absent",
        "recommendation": "Implement chargeback intake, evidence and rebuttal workflow.",
    },
    {
        "rule_id": "R_FRAUD_003_NO_VELOCITY_CONTROL",
        "name": "No Velocity / Amount Limits",
        "risk_level": "HIGH",
        "categories": _FRAUD,
        "patterns": [
            r"\b(no|without)\s+velocity\s+(check|limit|control)\b",
            r"\bunlimited\s+transactions\b",
            r"\bno\s+daily\s+limit\b.*\b(new\s+account|first\s+day)\b",
        ],
        "requires_any": [
            r"\bvelocity\s+(check|limit|control|rules)\b",
            r"\btxn\s+limits?\b",
            r"\bamount\s+(cap|threshold)\b",
            r"\brisk\s+based\s+limits\b",
        ],
        "flag": "Velocity and per-account limits not enforced",
        "recommendation": "Apply risk-based velocity, amount and frequency limits.",
    },
    {
        "rule_id": "R_FRAUD_004_NO_MULE_DETECTION",
        "name": "Mule Account Controls Missing",
        "risk_level": "MEDIUM",
        "categories": _FRAUD,
        "patterns": [
            r"\b(no|without)\s+mule\s+(detection|screening|controls)\b",
            r"\bmule\s+account\b",
            r"\bshell\s+accounts?\b",
        ],
        "requires_any": [
            r"\bmule\s+(detection|screening|controls)\b",
            r"\bsanctions?\s+list\b.*\bmule\b",
            r"\brisk\s+scoring\b.*\baccount\b",
        ],
        "flag": "Mule / shell account detection not described",
        "recommendation": "Screen incoming credits and flag mule-account behavioural patterns.",
    },
    {
        "rule_id": "R_FRAUD_005_COI_BLOCKING",
        "name": "No Complaint-Based Blocking",
        "risk_level": "MEDIUM",
        "categories": _FRAUD,
        "patterns": [
            r"\b(no|without)\s+(complaint|scam)[- ]?based\s+blocking\b",
            r"\bscam\b.*\b(not|no)\s+(block|countermeasures?)\b",
            r"\bno\s+auto\s+(block|hold)\s+on\s+(complaint|dispute)\b",
        ],
        "requires_any": [
            r"\bcomplaint\s+intimation\b.*\b(block|freeze|hold)\b",
            r"\bbeneficiary\s+list\b.*\bfraud\b",
            r"\bcollection\s+(hold|block)\b",
        ],
        "flag": "Complaint-based beneficiary blocking not in place",
        "recommendation": "Freeze flagged beneficiaries and maps per scheme fraud rules.",
    },
    {
        "rule_id": "R_FRAUD_006_NO_FRAUD_REGISTRY",
        "name": "No NPCI / Industry Fraud Sharing",
        "risk_level": "LOW",
        "categories": _FRAUD,
        "patterns": [
            r"\b(no|without)\s+(fraud\s+data|fraud\s+report)\s+sharing\b",
            r"\bnot\s+shared\s+with\s+(npci|fraud\s+registry)\b",
        ],
        "requires_any": [
            r"\b(npci|fraud\s+registry)\b",
            r"\bfraud\s+reporting\b",
            r"\bsuspicious\s+pattern\s+sharing\b",
        ],
        "flag": "Fraud intel not shared with industry registry",
        "recommendation": "Report fraud patterns and share indicators per scheme requirements.",
    },
]