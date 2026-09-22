_REPORTING = ["REPORTING", "GENERAL"]

REPORTING_RULES: list[dict] = [
    {
        "rule_id": "R_REPORT_001_NO_REGULATORY_RETURNS",
        "name": "Regulatory Returns Not Filed",
        "risk_level": "HIGH",
        "categories": _REPORTING,
        "patterns": [
            r"\bno\s+(rbi\s+)?returns?\s+(filed|submitted)\b",
            r"\bnot\s+filing\s+(rbi\s+)?returns?\b",
            r"\b(no|not|without)\s+(filed|submitting)\s+(rbi|regulatory)\s+returns?\b",
            r"\brbi\s+reporting\b.*\b(absent|missing|pending)\b",
            r"\b(no|without)\s+regulatory\s+(reporting|filing|returns)\b",
        ],
        "requires_any": [
            r"\brbi\s+returns\b",
            r"\bmonthly\s+(report|filing)\b",
            r"\bregulatory\s+(reporting|filing|returns)\b",
            r"\bannual\s+statement\b",
        ],
        "flag": "Regulatory / RBI returns not being filed",
        "recommendation": "File scheduled RBI and scheme returns on time with a tracker.",
    },
    {
        "rule_id": "R_REPORT_002_NO_MIS_RECON",
        "name": "No MIS / Reconciliation",
        "risk_level": "MEDIUM",
        "categories": _REPORTING,
        "patterns": [
            r"\b(no|without)\s+(mis|reconciliation)\s+report(ing)?\b",
            r"\breconciliation\b.*\bnot\s+(done|performed|automated)\b",
            r"\b(no|without)\s+auto\s+reconciliation\b",
        ],
        "requires_any": [
            r"\breconciliation\s+(process|report|job|tool)\b",
            r"\bautomated\s+reconciliation\b",
            r"\bdaily\s+settlement\s+recon\b",
        ],
        "flag": "System-generated MIS / reconciliation missing",
        "recommendation": "Automate end-of-day reconciliation and MIS generation.",
    },
    {
        "rule_id": "R_REPORT_003_NO_INTERNAL_AUDIT",
        "name": "Internal Audit / Certification Gap",
        "risk_level": "MEDIUM",
        "categories": _REPORTING,
        "patterns": [
            r"\b(no|without)\s+internal\s+audit\b",
            r"\b(no|without)\s+annual\s+(certification|audit)\b",
            r"\baudit\b.*\bnot\s+(scheduled|conducted|planned)\b",
        ],
        "requires_any": [
            r"\binternal\s+audit\b",
            r"\bannual\s+(certification|audit|review)\b",
            r"\bindependent\s+assurance\b",
        ],
        "flag": "Internal audit / annual certification absent",
        "recommendation": "Schedule periodic internal audits and IS compliance certification.",
    },
    {
        "rule_id": "R_REPORT_004_NO_DATA_DICTIONARY",
        "name": "No Data Dictionary / Submission",
        "risk_level": "MEDIUM",
        "categories": _REPORTING,
        "patterns": [
            r"\b(no|without)\s+data\s+dictionary\b",
            r"\bdata\s+submission\b.*\b(not|pending)\b",
            r"\b(no|without)\s+iis\b.*\bdictionary\b",
        ],
        "requires_any": [
            r"\bdata\s+dictionary\b",
            r"\bdigital\s+data\s+submission\b",
            r"\bnpci\s+data\s+(dictionary|submission)\b",
        ],
        "flag": "Regulatory data dictionary / submission not maintained",
        "recommendation": "Maintain the data dictionary and submit required datasets.",
    },
    {
        "rule_id": "R_REPORT_005_NO_STRESS_TEST",
        "name": "No Stress / Scenario Testing",
        "risk_level": "LOW",
        "categories": _REPORTING,
        "patterns": [
            r"\b(no|without)\s+stress\s+test\w*\b",
            r"\bscenario\s+test\w*\b.*\b(not|absent)\b",
            r"\bno\s+contingency\s+test\b",
        ],
        "requires_any": [
            r"\bstress\s+test\w*\b",
            r"\bscenario\s+analys\w*\b",
            r"\bcontingency\s+(test|drill)\b",
        ],
        "flag": "Stress / scenario testing not documented",
        "recommendation": "Run periodic stress tests and document management actions.",
    },
]