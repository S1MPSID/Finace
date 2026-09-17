_CRYPTO = ["CRYPTO_VA", "GENERAL"]

CRYPTO_RULES: list[dict] = [
    {
        "rule_id": "R_CRYPTO_001_VDA_NO_FIU",
        "name": "VDA Without FIU / PMLA Alignment",
        "risk_level": "HIGH",
        "categories": _CRYPTO,
        "patterns": [
            r"\b(crypto|virtual\s+digital\s+asset|vda)\b.*\b(no|without)\s+(fiu|pmla)\b",
            r"\bexchange\b.*\bunregistered\b",
        ],
        "requires_any": [r"\bfiu\b", r"\bpmla\b", r"\btravel\s+rule\b", r"\bvda\s+reporting\b"],
        "flag": "VDA activity without FIU/PMLA alignment",
        "recommendation": "Register/report per FIU-IND and PMLA obligations for VDAs.",
    },
    {
        "rule_id": "R_CRYPTO_002_NO_WALLET_SCREENING",
        "name": "Wallet Screening / Sanctions Gap",
        "risk_level": "HIGH",
        "categories": _CRYPTO,
        "patterns": [r"\bwallet\b.*\b(no|without)\s+screening\b", r"\bsanctions\b.*\bnot\s+checked\b"],
        "requires_any": [r"\bsanctions\s+screening\b", r"\bofac\b", r"\bwallet\s+screening\b"],
        "flag": "Crypto wallet sanctions screening not described",
        "recommendation": "Screen wallets and counterparties against sanctions lists.",
    },
    {
        "rule_id": "R_CRYPTO_003_CUSTODY_GAP",
        "name": "VDA Custody / Key Management Gap",
        "risk_level": "MEDIUM",
        "categories": _CRYPTO,
        "patterns": [r"\bhot\s+wallet\b.*\bno\s+multisig\b", r"\bprivate\s+key\b.*\bshared\b"],
        "requires_any": [r"\bcustody\b", r"\bmultisig\b", r"\bhsm\b", r"\bkey\s+management\b"],
        "flag": "VDA custody and key management weak",
        "recommendation": "Use HSM/multisig and segregate customer assets.",
    },
]
