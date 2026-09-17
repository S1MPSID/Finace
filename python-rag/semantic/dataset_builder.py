"""
Labelled compliance dataset for the semantic status classifier.

Rule we follow (per the hybrid design): regulatory knowledge informs the *requirements*
(REG side), and the model judges whether the *response* (WF side) satisfies them:

    sample = "[CAT] REG: <requirement> | WF: <response>"  →  label

Sources of (requirement → response → label) triples, in priority order:

1. `semantic/manifest.json`       – hand-curated / manually-reviewed examples.
2. Template generator            – deterministic (requirement × response-status) rows
                                   derived from per-category regulatory requirements.
3. Mongo `chunks` (optional)     – the actual RAG-indexed PDF chunks become the REG
                                   requirement; synthetic response variants become WF.

The raw chunk is NEVER the label by itself: it is the requirement the response is
judged against. Labels are fixed by the response template's compliance semantics.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from rules.category_registry import PAYMENT_CATEGORIES
from rules.reference_workflows import REFERENCE_WORKFLOWS

LABELS = ("COMPLIANT", "PARTIAL", "MISSING", "UNKNOWN")

# (id, requirement phrase, control noun used in response language)
_CONTROL_AREAS: list[tuple[str, str, str]] = [
    (
        "kyc",
        "perform customer due diligence (e-KYC) and verify identity",
        "KYC verification",
    ),
    (
        "aml",
        "implement anti-money laundering (AML) monitoring and report suspicious transactions",
        "AML transaction monitoring",
    ),
    (
        "grievance",
        "maintain a grievance redressal mechanism with complaint tracking and resolution timelines",
        "a grievance redressal mechanism",
    ),
    (
        "fema",
        "maintain FEMA / foreign-exchange compliance and lodge periodic returns",
        "FEMA reporting",
    ),
    (
        "2fa",
        "authenticate customers with two-factor authentication (OTP)",
        "two-factor authentication",
    ),
    (
        "consent",
        "capture explicit customer consent before processing or sharing data",
        "explicit customer consent logs",
    ),
    (
        "retention",
        "align data retention with record-keeping norms and purge at expiry",
        "a data retention policy",
    ),
    (
        "reporting",
        "meet regulatory reporting obligations under the master directions",
        "regulatory reporting",
    ),
]

_REQUIREMENT_TEXT: dict[str, str] = {
    "kyc": "The regulator requires {cat} providers to {req} before activating any customer account.",
    "aml": "Under the applicable master directions, {cat} providers must {req}.",
    "grievance": "Every {cat} provider is required to {req}.",
    "fema": "{cat} providers handling foreign exchange must {req}.",
    "2fa": "Regulations mandate that {cat} providers {req} for all transactions.",
    "consent": "{cat} providers must {req}.",
    "retention": "{cat} providers shall {req}.",
    "reporting": "{cat} providers are obligated to {req}.",
}

# Response variants per status. Each embeds the control noun so the classifier
# learns to distinguish "implemented / hedging / missing / off-topic" wording.
_STATUS_RESPONSES: dict[str, list[str]] = {
    "COMPLIANT": [
        "We have implemented {ctrl} across our {cat} operations and it is audited quarterly.",
        "Our {cat} flow now includes {ctrl}; controls are active in production.",
        "We maintain {ctrl} with documented SOPs and a dedicated owner.",
        "Customer-facing {cat} processes cover {ctrl}; no scope exclusions remain.",
        "Implementation of {ctrl} is complete and verified by internal audit.",
        "We verify customer identity (e-KYC) before activating any account.",
        "Every transaction in our {cat} service is protected with {ctrl_lower}.",
        "We operate a compliant program with {ctrl_lower} in place across all segments.",
        "Our {cat} flows run {ctrl_lower} on every account, including legacy ones.",
        "We already meet the {ctrl_lower} obligations for {cat} and document evidence.",
    ],
    "PARTIAL": [
        "We plan to introduce {ctrl} for {cat} next year.",
        "{ctrl} is under review for our {cat} service and will roll out in phases.",
        "Only part of our {cat} flows include {ctrl}; the remainder follows in Q3.",
        "We are evaluating {ctrl}; a pilot for {cat} starts this quarter.",
        "Partial {ctrl} exists for {cat}; full rollout depends on board approval.",
    ],
    "MISSING": [
        "We do not provide {ctrl} for {cat}.",
        "There is no {ctrl} in our current {cat} operations.",
        "{ctrl} is not implemented and not planned for {cat}.",
        "Our {cat} service operates without {ctrl}.",
        "No {ctrl} is available for {cat}; we do not intend to add it.",
    ],
    "UNKNOWN": [
        "Our marketing FAQ covers generic payment questions only.",
        "Sales brochures describe fees and transaction limits only.",
        "Press releases mention growth milestones; nothing on compliance controls.",
        "The onboarding flow asks for basic details; we have no team policy to share.",
    ],
}

_MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.json"


# ────────────────────────────────────────────────────────────────────────
# 1. Hand-curated / manually-reviewed rows (semantic/manifest.json)
# ────────────────────────────────────────────────────────────────────────
def _from_manifest() -> tuple[list[str], list[str]]:
    if not _MANIFEST_PATH.is_file():
        return [], []
    try:
        data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"manifest.json unreadable: {exc}")
        return [], []
    rows = data if isinstance(data, list) else data.get("examples", [])
    texts: list[str] = []
    labels: list[str] = []
    for row in rows:
        cat = str(row.get("category") or "GENERAL").upper()
        reg = str(row.get("requirement") or "").strip()
        wf = str(row.get("response") or "").strip()
        label = str(row.get("label") or "").strip().upper()
        if not reg or not wf or label not in LABELS:
            continue
        texts.append(f"[{cat}] REG: {reg} | WF: {wf}")
        labels.append(label)
    if texts:
        logger.info(f"Manifest rows: {len(texts)} (label dist: {_dist(labels)})")
    return texts, labels


# ────────────────────────────────────────────────────────────────────────
# 2. Deterministic template generator
# ────────────────────────────────────────────────────────────────────────
def _category_pairs() -> list[tuple[str, str]]:
    return [(c["id"], c["label"]) for c in PAYMENT_CATEGORIES]


def _template_rows() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []

    for cat_id, cat_label in _category_pairs():
        for ctrl_id, req_phrase, _ctrl_noun in _CONTROL_AREAS:
            requirement = _REQUIREMENT_TEXT[ctrl_id].format(cat=cat_label, req=req_phrase)
            for status in LABELS:
                variants = _STATUS_RESPONSES[status]
                if status == "UNKNOWN":
                    for variant in variants:
                        texts.append(
                            f"[{cat_id}] REG: {requirement} | WF: {variant.format(cat=cat_label.lower())}"
                        )
                        labels.append(status)
                    continue
                for variant in variants:
                    wf = variant.format(
                        ctrl=_ctrl_noun,
                        ctrl_lower=_ctrl_noun.lower(),
                        cat=cat_label.lower(),
                    )
                    texts.append(f"[{cat_id}] REG: {requirement} | WF: {wf}")
                    labels.append(status)

    if texts:
        logger.info(f"Template rows: {len(texts)} (label dist: {_dist(labels)})")
    return texts, labels


# ────────────────────────────────────────────────────────────────────────
# 3. Optional Mongo corpus augmentation (real indexed PDF chunks)
# ────────────────────────────────────────────────────────────────────────
def _infer_category(meta: dict, text: str) -> str:
    rel = str(meta.get("relative_path") or meta.get("source") or "").lower()
    cat_field = str(meta.get("category") or "").upper()
    ids = {c["id"] for c in PAYMENT_CATEGORIES}
    if cat_field in ids:
        return cat_field
    folder_map = {
        "e-upi": "UPI", "bhim": "UPI", "imps": "IMPS", "cts": "CTS", "aeps": "AEPS",
        "e-kyc": "EKYC", "nfs": "NFS", "nipc": "NPCI", "rbi": "RBI_MD",
    }
    for key, cid in folder_map.items():
        if key in rel:
            return cid
    lower = text.lower()[:400]
    if "fema" in lower or "foreign exchange" in lower:
        return "FX_FEMA"
    return "RBI_MD"


# Response variants for corpus rows are *response language*, not mutated regulation
# text — the classifier must learn "does the response satisfy the requirement".
_CORPUS_WF: dict[str, list[str]] = {
    "COMPLIANT": [
        "We have implemented {topic} across production and it is verified by internal audit.",
        "We maintain {topic} with documented processes and a named control owner.",
        "Our operations fully cover {topic}; evidence is retained and reviews are scheduled.",
        "We complete {topic} before any customer is activated.",
    ],
    "PARTIAL": [
        "We plan to introduce {topic} next year.",
        "Only part of our flows include {topic}; the remainder is planned for Q3.",
        "{topic} is under review and will be rolled out in phases.",
        "We are piloting {topic} this quarter for one segment only.",
    ],
    "MISSING": [
        "We do not provide {topic}.",
        "There is no {topic} in our current operations and none is planned.",
        "We operate without {topic}; adding it is not on our roadmap.",
    ],
}

_TOPIC_PATTERNS: list[tuple[list[str], str]] = [
    (
        ["e-kyc", "kyc", "aadhaar", "identity verification", "customer due diligence"],
        "e-KYC and identity verification",
    ),
    (
        ["anti-money laundering", "aml", "suspicious transaction", "str filing", "transaction monitoring"],
        "AML monitoring and suspicious-transaction reporting",
    ),
    (["grievance", "complaint", "redressal"], "a grievance redressal mechanism"),
    (["fema", "foreign exchange", "forex", "periodic returns"], "FEMA compliance and periodic returns"),
    (["two-factor authentication", "2fa", "otp"], "OTP-based two-factor authentication"),
    (["consent"], "explicit customer consent capture"),
    (["retention", "record-keeping", "purge", "data retention"], "a data retention and purge policy"),
    (["reporting", "report to", "returns to the regulator", "master directions"], "regulatory reporting"),
]


def _detect_topic(text: str) -> str:
    low = (text or "").lower()
    for keys, phrase in _TOPIC_PATTERNS:
        if any(k in low for k in keys):
            return phrase
    return "the controls described above"


def _from_regulation_corpus() -> tuple[list[str], list[str]]:
    env_limit = int(os.getenv("SEMANTIC_TRAIN_CHUNK_LIMIT", "6000") or "0")
    max_chunks = env_limit if env_limit > 0 else 6000
    texts: list[str] = []
    labels: list[str] = []

    try:
        from db.mongo import get_collection

        coll = get_collection("chunks")
        if coll is None:
            logger.warning("chunks collection unavailable — corpus augmentation skipped")
            return texts, labels

        cursor = coll.find({}, {"text": 1, "metadata": 1}).limit(max_chunks)

        idx = 0
        for ch in cursor:
            body = (ch.get("text") or "").strip()
            if len(body) < 80:
                continue
            cat = _infer_category(ch.get("metadata") or {}, body)
            requirement = body[:3000]
            topic = _detect_topic(body)
            for status, variants in _CORPUS_WF.items():
                variant = variants[idx % len(variants)]
                texts.append(f"[{cat}] REG: {requirement} | WF: {variant.format(topic=topic)}")
                labels.append(status)
                idx += 1
        logger.info(f"Corpus augmentation rows: {len(texts)}")
    except Exception as exc:
        logger.warning(f"Regulation corpus augmentation failed: {exc}")
    return texts, labels


# ────────────────────────────────────────────────────────────────────────
# Assembly
# ────────────────────────────────────────────────────────────────────────
def _dist(labels: list[str]) -> str:
    return ", ".join(f"{lbl}={labels.count(lbl)}" for lbl in LABELS)


def collect_training_rows() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []

    for part in (_from_manifest(), _template_rows(), _from_regulation_corpus(), _bootstrap_legacy()):
        t, l = part
        texts.extend(t)
        labels.extend(l)

    logger.info(
        f"Semantic dataset total: {len(texts)} rows"
        f" (label dist: {_dist(labels)})"
    )
    return texts, labels


def _bootstrap_legacy() -> tuple[list[str], list[str]]:
    """Reference workflows with per-category REQ side — small deterministic bootstrap."""
    texts: list[str] = []
    labels: list[str] = []
    for cat_id, _cat_label in _category_pairs():
        for workflow in REFERENCE_WORKFLOWS:
            req = f"{_CATEGORY_BOOTSTRAP_REQ[cat_id]}" if cat_id in _CATEGORY_BOOTSTRAP_REQ else (
                f"Regulated {cat_id} activities must comply with applicable master directions."
            )
            texts.append(f"[{cat_id}] REG: {req} | WF: {workflow}")
            low = (workflow or "").lower()
            if any(k in low for k in ("without", "no ", "skip", "not", "lacking", "only email")) and any(
                k in low for k in ("kyc", "aml", "grievance", "fema", "monitoring", "complaint")
            ):
                labels.append("MISSING")
            elif any(k in low for k in ("grievance officer appointed", "maker-checker", "control", "e-kyc")):
                labels.append("COMPLIANT")
            else:
                labels.append("PARTIAL")
    if texts:
        logger.info(f"Legacy bootstrap rows: {len(texts)}")
    return texts, labels


_CATEGORY_BOOTSTRAP_REQ: dict[str, str] = {
    "UPI": "UPI participants must implement KYC, AML monitoring, grievance redressal and 2FA controls.",
    "IMPS": "IMPS participants must follow settlement, 2FA and complaint-handling requirements.",
    "NEFT_RTGS": "NEFT/RTGS participants must verify customers before activation and reconcile daily.",
    "CTS": "CTS participants must apply maker-checker and maintain an audit trail for cheque clearing.",
    "AEPS": "AEPS participants must authenticate with Aadhaar and meet biometric device standards.",
    "EKYC": "e-KYC must use Aadhaar OTP with customer consent and a data retention policy.",
    "NFS": "NFS/ATM participants must meet pin security, dispute and reconciliation norms.",
    "NPCI": "RuPay/NACH/FASTag participants must meet NPCI programme rules and reporting.",
    "RBI_MD": "All payment systems must follow RBI master directions on KYC, AML and customer protection.",
    "CRYPTO_VA": "VDA service providers must apply AML/CFT screening and transaction monitoring.",
    "FX_FEMA": "Forex participants must maintain FEMA compliance and lodge periodic returns.",
    "GENERAL": "Payment providers must operate with KYC, AML, grievance and reporting controls in place.",
}