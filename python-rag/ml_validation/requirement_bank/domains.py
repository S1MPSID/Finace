"""Map corpus document metadata / paths onto canonical Finace domains."""
from __future__ import annotations

import re

from ml_validation.schema import CANONICAL_DOMAINS

# Corpus category strings → canonical domain
_CATEGORY_MAP: dict[str, str] = {
    "UPI": "UPI",
    "E-UPI": "UPI",
    "BHIM_AADHAR": "BHIM_AADHAR",
    "BHIM AADHAR": "BHIM_AADHAR",
    "IMPS": "IMPS",
    "NEFT": "NEFT_RTGS",
    "RTGS": "NEFT_RTGS",
    "NEFT_RTGS": "NEFT_RTGS",
    "CTS": "CTS",
    "AEPS": "AEPS",
    "EKYC": "EKYC",
    "E-KYC": "EKYC",
    "KYC": "KYC",
    "NFS": "NFS",
    "NACH": "NACH",
    "RUPAY": "RUPAY",
    "FASTAG": "FASTAG",
    "NIPC": "NPCI",
    "NPCI": "NPCI",
    "RBI": "RBI_MD",
    "RBI_CIRCULAR": "RBI_MD",
    "RBI (1)": "RBI_MD",
    "RBI_MD": "RBI_MD",
    "CRYPTO": "CRYPTO_VA",
    "VDA": "CRYPTO_VA",
    "CRYPTO_VA": "CRYPTO_VA",
    "FEMA": "FX_FEMA",
    "FX": "FX_FEMA",
    "FX_FEMA": "FX_FEMA",
    "PPI": "PPI",
    "BBPS": "BBPS",
}

_PATH_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bupi\b|/e-upi/|/bhim", re.I), "UPI"),
    (re.compile(r"\bimps\b", re.I), "IMPS"),
    (re.compile(r"\bneft\b|\brtgs\b", re.I), "NEFT_RTGS"),
    (re.compile(r"\bcts\b|cheque", re.I), "CTS"),
    (re.compile(r"\baeps\b", re.I), "AEPS"),
    (re.compile(r"\bekyc\b|e-kyc|aadhaar", re.I), "EKYC"),
    (re.compile(r"\bnfs\b|\batm\b", re.I), "NFS"),
    (re.compile(r"\bnach\b", re.I), "NACH"),
    (re.compile(r"\brupay\b", re.I), "RUPAY"),
    (re.compile(r"\bfastag\b", re.I), "FASTAG"),
    (re.compile(r"\bfema\b|\bforex\b|foreign.?exchange", re.I), "FX_FEMA"),
    (re.compile(r"\bcrypto\b|\bvda\b|virtual.?digital", re.I), "CRYPTO_VA"),
    (re.compile(r"\bppi\b|prepaid", re.I), "PPI"),
    (re.compile(r"\bbbps\b", re.I), "BBPS"),
    (re.compile(r"\bkyc\b", re.I), "KYC"),
    (re.compile(r"/rbi/|rbi[_-]", re.I), "RBI_MD"),
    (re.compile(r"\bnpci\b", re.I), "NPCI"),
]


def map_domain(
    *,
    category: str | None = None,
    document_id: str | None = None,
    title: str | None = None,
    relative_path: str | None = None,
) -> str:
    cat = (category or "").strip()
    if cat in _CATEGORY_MAP:
        return _CATEGORY_MAP[cat]
    upper = cat.upper().replace(" ", "_")
    if upper in _CATEGORY_MAP:
        return _CATEGORY_MAP[upper]
    if upper in CANONICAL_DOMAINS:
        return upper

    blob = " ".join(x for x in (document_id, title, relative_path, cat) if x)
    for pattern, domain in _PATH_HINTS:
        if pattern.search(blob):
            return domain
    return "GENERAL"
