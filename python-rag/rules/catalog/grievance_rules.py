_GRIEVANCE = ["GRIEVANCE", "GENERAL"]

GRIEVANCE_RULES: list[dict] = [
    {
        "rule_id": "R_GRIE_001_NO_COMPLAINT_SLA",
        "name": "Complaint SLA Not Defined",
        "risk_level": "MEDIUM",
        "categories": _GRIEVANCE,
        "patterns": [
            r"\bcomplaint\b.*\b(no|without)\s+sla\b",
            r"\bgrievance\b.*\bno\s+time[- ]?frame\b",
            r"\bno\s+complaint\s+(redressal|resolution)\s+sla\b",
        ],
        "requires_any": [
            r"\bcomplaint\s*(resolution)?\s*sla\b",
            r"\btat\b.*\bcomplaint\b",
            r"\bwithin\s+\d+\s+(days|working\s+days)\b",
        ],
        "flag": "Grievance redressal SLA / TAT not defined",
        "recommendation": "Publish complaint resolution SLAs aligned to RBI/refund timelines.",
    },
    {
        "rule_id": "R_GRIE_002_NO_GRIEVANCE_PORTAL",
        "name": "No Grievance Portal / Escalation",
        "risk_level": "MEDIUM",
        "categories": _GRIEVANCE,
        "patterns": [
            r"\b(no|without)\s+(grievance|complaint)\s+(portal|officer|customer\s+care)\b",
            r"\bno\s+escalation\s+matrix\b",
        ],
        "requires_any": [
            r"\bgrievance\s+(portal|officer|cell|redressal\s+officer)\b",
            r"\bescalation\s+matrix\b",
            r"\bcustomer\s+care\s+(team|portal)\b",
        ],
        "flag": "Dedicated grievance channel or escalation matrix missing",
        "recommendation": "Provide a grievance portal, redressal officer, and escalation path.",
    },
    {
        "rule_id": "R_GRIE_003_NO_OMBUDSMAN_REFERENCE",
        "name": "Ombudsman / Nodal Officer Not Referenced",
        "risk_level": "LOW",
        "categories": _GRIEVANCE,
        "patterns": [
            r"\b(no|without)\s+(ombudsman|nodal\s+officer|principal\s+nodal\s+officer)\b",
            r"\bombudsman\b.*\bnot\s+(published|mentioned|referenced)\b",
        ],
        "requires_any": [
            r"\bombudsman\b",
            r"\bnodal\s+officer\b",
            r"\bprincipal\s+nodal\s+officer\b",
        ],
        "flag": "RB-I payment ombudsman / nodal officer not disclosed",
        "recommendation": "Publish nodal officer and RBI ombudsman escalation on customer channels.",
    },
    {
        "rule_id": "R_GRIE_004_COMPLAINTS_NOT_REPORTED",
        "name": "Complaint Data Not Reported",
        "risk_level": "MEDIUM",
        "categories": _GRIEVANCE,
        "patterns": [
            r"\bcomplaints?\b.*\bnot\s+(reported|shared|submitted)\b",
            r"\b(no|without)\s+complaint\s+reporting\s+to\s+(rbi|npci|npc)\b",
        ],
        "requires_any": [
            r"\bcomplaint\s+reporting\b",
            r"\breport\w*\s+complaint",
            r"\bmonthly\s+report\b.*\bcomplaint",
        ],
        "flag": "Complaint statistics are not furnished to regulator/scheme",
        "recommendation": "File complaint volumes and disposition reports as required.",
    },
    {
        "rule_id": "R_GRIE_005_NO_CUSTOMER_OUTREACH",
        "name": "No Customer Awareness / Outreach",
        "risk_level": "LOW",
        "categories": _GRIEVANCE,
        "patterns": [
            r"\bno\s+customer\s+(awareness|education|outreach)\b",
            r"\bcustomers?\b.*\bnot\s+informed\b",
            r"\bno\s+communication\s+on\s+(fees|limits|complaint)\b",
        ],
        "requires_any": [
            r"\bcustomer\s+(awareness|education|outreach|communication)\b",
            r"\bintimation\b",
            r"\bapp\/sms\s+notification\b",
        ],
        "flag": "Customer awareness / disclosure outreach not described",
        "recommendation": "Run periodic customer education and transparent disclosures.",
    },
]