"""
Payment / doc-folder categories for chat onboarding + keyword inference.
"""
from __future__ import annotations

import re

PAYMENT_CATEGORIES: list[dict[str, str]] = [
    {"id": "UPI", "label": "UPI / BHIM", "icon": "smartphone"},
    {"id": "IMPS", "label": "IMPS", "icon": "zap"},
    {"id": "NEFT_RTGS", "label": "NEFT / RTGS", "icon": "landmark"},
    {"id": "CTS", "label": "CTS / Cheques", "icon": "file-text"},
    {"id": "AEPS", "label": "AEPS", "icon": "fingerprint"},
    {"id": "EKYC", "label": "e-KYC", "icon": "id-card"},
    {"id": "NFS", "label": "NFS / ATM", "icon": "credit-card"},
    {"id": "NPCI", "label": "RuPay / NACH / FASTag", "icon": "layers"},
    {"id": "RBI_MD", "label": "RBI master directions", "icon": "book"},
    {"id": "CRYPTO_VA", "label": "Crypto / VDA", "icon": "coins"},
    {"id": "FX_FEMA", "label": "FX / FEMA", "icon": "globe"},
    {"id": "GENERAL", "label": "General payments", "icon": "help-circle"},
]

DOC_FOLDER_BY_CATEGORY: dict[str, list[str]] = {
    "UPI": ["E-UPI", "BHIM AADHAR"],
    "IMPS": ["IMPS"],
    "CTS": ["CTS"],
    "AEPS": ["AEPS"],
    "EKYC": ["E-KYC"],
    "NFS": ["NFS"],
    "NPCI": ["NIPC"],
    "RBI_MD": ["RBI", "RBI (1)"],
    "CRYPTO_VA": ["CRYPTO", "VDA"],
    "FX_FEMA": ["FEMA", "FX"],
    "NEFT_RTGS": ["NEFT", "RTGS"],
    "GENERAL": [],
}

_KEYWORD_PATTERNS: list[tuple[str, list[str]]] = [
    ("CRYPTO_VA", [
        r"\bcrypto", r"\bvda\b", r"\bvirtual\s+digital", r"\bbitcoin",
        r"\bethereum", r"\bstablecoin", r"\bp2p\s+crypto", r"\bweb3",
        r"\bdefi\b", r"\btoken\b", r"\blockchain\b",
    ]),
    ("EKYC", [
        r"\bekyc\b", r"\be-?kyc\b", r"\baadhaar\s+otp", r"\bpan\s+verification",
        r"\bvideo\s+kyc", r"\bidentity\s+verif", r"\bdoc\s+verif",
    ]),
    ("FX_FEMA", [
        r"\bfema\b", r"\bforex\b", r"\bforeign\s+exchange", r"\bremittance",
        r"\bcross.?border", r"\bfc\s*qr", r"\binward\s+remit",
    ]),
    ("AEPS", [
        r"\baeps\b", r"\baadhaar\s+enabled", r"\bbiometric\s+auth",
        r"\bcash\s+withdrawal\s+aadhaar",
    ]),
    ("IMPS", [r"\bimps\b", r"\bimmediate\s+payment"]),
    ("NEFT_RTGS", [r"\bneft\b", r"\brtgs\b", r"\breal\s+time\s+gross"]),
    ("NFS", [r"\bnfs\b", r"\batm\s+network", r"\batm\b"]),
    ("NPCI", [r"\bnpci\b", r"\brupay\b", r"\bnach\b", r"\bfastag\b", r"\bembourg"]),
    ("UPI", [
        r"\bupi\b", r"\bbhim\b", r"\bupi\s+merchant", r"\bupi\s+collect",
        r"\bupi\s+id\b", r"\bvpa\b", r"\bqr\s+code\s+payment",
    ]),
]


def infer_categories_from_text(text: str) -> list[str]:
    """Infer payment categories from prompt/workflow text using keyword patterns.

    Returns categories in priority order (most specific first).
    GENERAL is never inferred — it is the fallback when nothing matches.
    """
    t = (text or "").lower()
    found: list[str] = []
    for cat_id, patterns in _KEYWORD_PATTERNS:
        if any(re.search(p, t) for p in patterns):
            found.append(cat_id)
    return found


def category_ids() -> list[str]:
    return [c["id"] for c in PAYMENT_CATEGORIES]


def resolve_retrieval_category(active: list[str] | None) -> str | None:
    """Pick first folder-friendly category for retriever filter."""
    if not active:
        return None
    for cid in active:
        if cid in DOC_FOLDER_BY_CATEGORY and DOC_FOLDER_BY_CATEGORY[cid]:
            return DOC_FOLDER_BY_CATEGORY[cid][0]
    return None
