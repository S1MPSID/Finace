"""
Relevance router for the deterministic rule catalog.

The rule catalog is data-driven and large (one dict per rule, grouped by
category). Running *every* rule on *every* prompt is what causes the same stale
rules to come back each turn. This module decides, from the current prompt and
optional category hint, which rule categories are actually relevant, so the rule
engine only assesses the matching packs plus the always-on core controls.

Relevance is intentionally deterministic and explainable:

- ``detect_relevant_categories`` : keyword routing on the current user message.
- ``enrich_relevance_from_hits``  : evidence-informed widening, so a vague prompt
  is still routed to categories proven present in the indexed corpus.
"""
from __future__ import annotations

import re
from typing import Any

# Canonical category tag -> human label shown in the UI / response block.
CATEGORY_LABELS: dict[str, str] = {
    "UPI": "UPI / BHIM",
    "IMPS": "IMPS",
    "AEPS": "AEPS / BC banking",
    "NEFT_RTGS": "NEFT / RTGS",
    "CTS": "Cheque Truncation (CTS)",
    "NFS": "ATM / NFS",
    "NPCI": "NPCI schemes (NACH / RuPay / FASTag)",
    "CRYPTO_VA": "Virtual Digital Assets (VDA)",
    "FX_FEMA": "Cross-border / FEMA",
    "EKYC": "e-KYC / onboarding",
    "RBI_MD": "Master Directions / governance",
    "GRIEVANCE": "Grievance redressal",
    "MERCHANT_PG": "Merchant acquiring / payment gateway",
    "DATA_SECURITY": "Data & security",
    "FRAUD_OPS": "Fraud / scam operations",
    "REPORTING": "Regulatory reporting",
}

# Category tag -> discriminating keywords. Routing based on these lets a prompt
# like "AEPS cash withdrawal limits" evaluate only AEPS (+ core) rules.
CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
    "UPI": (
        r"\bupi\b",
        r"\bbhim\b",
        r"\bvpa\b",
        r"\bcollect\s+request\b",
        r"\bupi\s+mandate\b",
        r"\bvoice\s+payment\b",
        r"\bsound\s*box\b",
        r"\bupi\s+(lite|pin|credit|id)\b",
        r"\bdelegated\s+payment\b",
    ),
    "IMPS": (r"\bimps\b", r"\bmmid\b"),
    "AEPS": (r"\baeps\b", r"\bbhim\s+aadhaar\b", r"\bmicro\s*atm\b", r"\bbanking\s+correspondent\b"),
    "NEFT_RTGS": (r"\bneft\b", r"\brtgs\b", r"\bifsc\b", r"\bamb\b", r"\bbusiness\s+correspondent\b"),
    "CTS": (r"\bcheque\b", r"\bcts\b", r"\bpositive\s+pay\b", r"\btrunc\w*\b"),
    "NFS": (r"\batm\b", r"\bcdm\b", r"\bcash\s+recycler\b", r"\bswitch\s+nfs\b", r"\bcrash\s+withdraw\b"),
    "NPCI": (r"\bnpci\b", r"\bnach\b", r"\brupay\b", r"\bfastag\b", r"\bnetc\b", r"\be[- ]?mandate\b"),
    "CRYPTO_VA": (
        r"\bvirtual\s+(digital\s+)?asset\b",
        r"\bvda\b",
        r"\bcrypto\w*\b",
        r"\bbitcoin\b",
        r"\bethereum\b",
        r"\bstablecoin\b",
        r"\bblockchain\b",
        r"\bdefi\b",
        r"\btokeni[sz]ed\s+asset\b",
    ),
    "FX_FEMA": (
        r"\bfema\b",
        r"\bforeign\s+exchange\b",
        r"\bforex\b",
        r"\bcross[- ]border\b",
        r"\bremit\w*\b",
        r"\boutward\s+remittance\b",
        r"\bauthori[sz]ed\s+dealer\b",
        r"\bliberalised\s+remittance\b",
        r"\bforex\s+card\b",
    ),
    "EKYC": (r"\be-?kyc\b", r"\bvideo\s+kyc\b", r"\bckyc\b", r"\bre-?kyc\b", r"\baadhaar\s+eb?kych\b"),
    "RBI_MD": (
        r"\boutsourc\w*\b",
        r"\bvendor\b",
        r"\bthird[- ]party\b",
        r"\bincident\s+(reporting|management)\b",
        r"\bboard\s+oversight\b",
        r"\baudit\s+committee\b",
        r"\bgovernance\s+framework\b",
        r"\bmaster\s+direction\b",
    ),
    "GRIEVANCE": (
        r"\bgrievance\b",
        r"\bcomplaint\w*\b",
        r"\bredressal\b",
        r"\bombud\w*\b",
        r"\bcustomer\s+care\b",
        r"\bresolution\s+(of\s+)?complaints?\b",
    ),
    "MERCHANT_PG": (
        r"\bmerchant\b",
        r"\bpayment\s+gateway\b",
        r"\bacquiring\b",
        r"\bnodal\s+account\b",
        r"\bescrow\b",
        r"\bsettlement\s+(cycle|pool|account|payout)\b",
        r"\bsub[- ]merchant\b",
        r"\bmdr\b",
        r"\binterchange\b",
        r"\bpay-in\s+date\b",
    ),
    "DATA_SECURITY": (
        r"\bdata\s+(privacy|protection|security|locali[sz]ation)\b",
        r"\bpersonal\s+(data|information)\b",
        r"\bprivacy\b",
        r"\bconsent\b",
        r"\bencrypt\w*\b",
        r"\bpci[- ]dss\b",
        r"\biso\s*27001\b",
        r"\bcyber\s+security\b",
        r"\bdata\s+breach\b",
        r"\btokeni[sz]ation\b",
        r"\bcvv\b",
        r"\bcard\s+(data|details|number|pan)\b",
        r"\bpan\s+number\b",
    ),
    "FRAUD_OPS": (
        r"\bfraud\b",
        r"\bscam\w*\b",
        r"\bchargeback\b",
        r"\bsuspicious\s+transaction\b",
        r"\bmule\b",
        r"\bphishing\b",
        r"\bunauthorized\s+transaction\b",
        r"\bstr\s+filing\b",
        r"\bfraud\s+monitoring\b",
    ),
    "REPORTING": (
        r"\brbi\s+(reporting|returns|reports)\b",
        r"\bregulatory\s+(report|filing|return)",
        r"\bdata\s+dictionary\b",
        r"\bsupervisory\s+(report|submission)\b",
        r"\bstress\s+test\b",
        r"\breporting\s+to\s+npc(i)?\b",
        r"\bfil(e|ing|ed)\s+(returns?|reports?)\b",
    ),
}

# Report/document category hints -> canonical tags. Kept lossy by design: a hint
# seeds routing, it does not force every related pack.
_HINT_ALIASES: dict[str, set[str]] = {
    "UPI": {"UPI"},
    "BHIM": {"UPI"},
    "PPI": {"UPI", "MERCHANT_PG"},
    "PPI WALLET": {"UPI", "MERCHANT_PG"},
    "WALLET": {"UPI"},
    "AEPS": {"AEPS"},
    "IMPS": {"IMPS"},
    "NEFT": {"NEFT_RTGS"},
    "RTGS": {"NEFT_RTGS"},
    "NEFT/RTGS": {"NEFT_RTGS"},
    "CTS": {"CTS", "NPCI"},
    "CHEQUE": {"CTS"},
    "ATM": {"NFS"},
    "NFS": {"NFS"},
    "CRYPTO": {"CRYPTO_VA", "FX_FEMA"},
    "VDA": {"CRYPTO_VA"},
    "CROSS-BORDER": {"FX_FEMA"},
    "CROSS BORDER": {"FX_FEMA"},
    "FEMA": {"FX_FEMA"},
    "FOREX": {"FX_FEMA"},
    "MERCHANT": {"MERCHANT_PG"},
    "PAYMENT GATEWAY": {"MERCHANT_PG", "RBI_MD"},
    "CISO": {"DATA_SECURITY", "RBI_MD", "REPORTING"},
    "EKYC": {"EKYC"},
    "KYC": {"EKYC"},
    "GRIEVANCE": {"GRIEVANCE"},
    "DATA": {"DATA_SECURITY"},
    "FRAUD": {"FRAUD_OPS"},
    "REPORTING": {"REPORTING"},
}

_memo = {tag: [re.compile(p, re.IGNORECASE) for p in pats] for tag, pats in CATEGORY_TERMS.items()}


def _matches_any(tag: str, text: str) -> list[str]:
    return [p.pattern for p in _memo[tag] if re.search(p, text)]


def _hint_to_tags(category_hint: str | None) -> set[str]:
    if not category_hint:
        return set()
    hint = str(category_hint).strip()
    if not hint:
        return set()
    upper = hint.upper()
    if upper in _HINT_ALIASES:
        return set(_HINT_ALIASES[upper])
    tags: set[str] = set()
    for alias, mapped in _HINT_ALIASES.items():
        if alias in upper:
            tags |= mapped
    if not tags:
        for tag, patterns in CATEGORY_TERMS.items():
            if _matches_any(tag, hint):
                tags.add(tag)
    return tags


def detect_relevant_categories(
    text: str,
    category_hint: str | None = None,
) -> dict[str, Any]:
    """
    Return the rule categories relevant to the current prompt.

    ``categories`` is the ordered routing result; core rules are always added by
    the rule engine itself and are therefore not listed here. Empty output is
    legitimate - it means "no domain pack relevant to this prompt", so the
    engine falls back to core-only evaluation instead of re-triggering stale
    domain rules.
    """
    haystack = text or ""
    matched_terms: dict[str, list[str]] = {}
    tags: list[str] = []
    for tag in CATEGORY_TERMS:
        terms = _matches_any(tag, haystack)
        if terms:
            matched_terms[tag] = terms
            tags.append(tag)

    hint_tags = sorted(_hint_to_tags(category_hint))
    for tag in hint_tags:
        if tag not in tags:
            tags.append(tag)

    return {
        "categories": tags,
        "matched_terms": matched_terms,
        "hint_categories": hint_tags,
        "labels": {tag: CATEGORY_LABELS.get(tag, tag) for tag in tags},
        "method": "keyword-routing on current user message" + (" + category hint" if hint_tags else ""),
    }


def enrich_relevance_from_hits(
    relevance: dict[str, Any],
    hits: list[dict[str, Any]] | None,
    max_hits: int = 5,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """
    Widen relevance from what is actually present in the retrieved evidence.

    A short or vague prompt may not contain domain keywords even though the
    underlying documents do. When a retrieved chunk's metadata (category,
    regulation, title) matches a pack's keywords above ``min_score``, that pack
    is added with an ``evidence`` origin so the rule engine assesses it too.
    """
    if not hits:
        return relevance
    tags = list(relevance.get("categories") or [])
    categories: dict[str, Any] = {(c or "").upper(): {"origin": "prompt"} for c in tags}
    for hit in (hits or [])[:max_hits]:
        meta = hit.get("metadata") or {}
        try:
            score = max(
                float(hit.get("score") or 0.0),
                float(hit.get("rerank_score") or 0.0),
                float(hit.get("similarity") or 0.0),
            )
        except (TypeError, ValueError):
            score = 1.0
        if score < min_score:
            continue
        evidence_text = " ".join(
            str(value or "")
            for value in (
                meta.get("category"),
                meta.get("regulator"),
                meta.get("regulation"),
                meta.get("title"),
                meta.get("source"),
                meta.get("relative_path"),
                hit.get("document_id"),
            )
        )
        for tag in CATEGORY_TERMS:
            if not _matches_any(tag, evidence_text):
                continue
            entry = categories.setdefault(tag, {"origin": "retrieval_evidence"})
            if entry.get("origin") != "prompt":
                entry["origin"] = "retrieval_evidence"
            entry.setdefault("supporting_hits", 0)
            entry["supporting_hits"] += 1

    ordered = [
        tag
        for tag, info in sorted(categories.items(), key=lambda kv: (-(kv[1].get("supporting_hits") or 0), kv[0]))
    ]
    return {
        "categories": ordered,
        "matched_terms": relevance.get("matched_terms") or {},
        "hint_categories": relevance.get("hint_categories") or [],
        "labels": {tag: CATEGORY_LABELS.get(tag, tag) for tag in ordered},
        "category_origins": categories,
        "method": relevance.get("method", "") + ("; widened by retrieved evidence" if ordered else ""),
    }