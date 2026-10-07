"""
Obligation-language detectors for requirement extraction.

These patterns identify *candidates* inside existing chunk text.
They do NOT invent requirements — they only select sentences that already
appear in the regulatory corpus.
"""
from __future__ import annotations

import re

# Strong deontic / obligation cues common in RBI/NPCI circulars.
OBLIGATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshall\b", re.I),
    re.compile(r"\bmust\b", re.I),
    re.compile(r"\bis\s+required\s+to\b", re.I),
    re.compile(r"\bare\s+required\s+to\b", re.I),
    re.compile(r"\brequired\s+to\b", re.I),
    re.compile(r"\bobligat(?:ed|ion)\b", re.I),
    re.compile(r"\bshould\s+(?:ensure|implement|maintain|provide|conduct|verify|report)\b", re.I),
    re.compile(r"\bit\s+is\s+(?:mandatory|essential|necessary)\b", re.I),
    re.compile(r"\bmandatory\b", re.I),
    re.compile(r"\bmembers?\s+(?:are|shall|must)\b", re.I),
    re.compile(r"\bparticipants?\s+(?:are|shall|must)\b", re.I),
    re.compile(r"\banks?\s+(?:are|shall|must)\b", re.I),
    re.compile(r"\bPSPs?\s+(?:are|shall|must)\b", re.I),
    re.compile(r"\bTPAP\b.+\bshall\b", re.I),
    re.compile(r"\bensur(?:e|es|ing)\s+that\b", re.I),
    re.compile(r"\bcomply\s+with\b", re.I),
    re.compile(r"\bin\s+accordance\s+with\b", re.I),
    re.compile(r"\bas\s+per\s+(?:this|the)\s+(?:circular|guideline|direction|master)\b", re.I),
]

# Soft cues — lower confidence, usually needs_review.
SOFT_OBLIGATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshould\b", re.I),
    re.compile(r"\bmay\s+(?:not|only)\b", re.I),
    re.compile(r"\bexpected\s+to\b", re.I),
    re.compile(r"\badvised\s+to\b", re.I),
    re.compile(r"\brecommended\s+to\b", re.I),
]

# Boilerplate / non-requirement noise.
NOISE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*dear\s+(sir|madam)", re.I),
    re.compile(r"^\s*yours\s+faithfully", re.I),
    re.compile(r"^\s*page\s+\d+", re.I),
    re.compile(r"cin\s*:\s*u\d+", re.I),
    re.compile(r"^\s*subject\s*:", re.I),
    re.compile(r"all\s+rights\s+reserved", re.I),
    re.compile(r"copyright", re.I),
    re.compile(r"disseminate\s+the\s+information", re.I),
    re.compile(r"members\s+are\s+requested\s+to\s+note", re.I),
    re.compile(r"for\s+information\s+and\s+necessary\s+action", re.I),
    re.compile(r"this\s+circular\s+is\s+issued", re.I),
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return []
    parts = _SENTENCE_SPLIT.split(cleaned)
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Also split long semicolon clauses that look like obligations.
        if len(part) > 320 and ";" in part and re.search(r"\bshall\b|\bmust\b", part, re.I):
            for sub in part.split(";"):
                sub = sub.strip(" ;")
                if sub:
                    out.append(sub if sub.endswith((".", "!", "?")) else sub + ".")
        else:
            out.append(part)
    return out


def obligation_score(sentence: str) -> tuple[float, list[str]]:
    """Return (confidence, matched_pattern_names)."""
    if not sentence or len(sentence) < 40:
        return 0.0, []
    flags: list[str] = []
    score = 0.0
    for p in OBLIGATION_PATTERNS:
        if p.search(sentence):
            score += 0.35
            flags.append(f"strong:{p.pattern[:40]}")
    for p in SOFT_OBLIGATION_PATTERNS:
        if p.search(sentence):
            score += 0.12
            flags.append(f"soft:{p.pattern[:40]}")
    for p in NOISE_PATTERNS:
        if p.search(sentence):
            score -= 0.5
            flags.append("noise")
    return max(0.0, min(1.0, score)), flags


def is_obligation_candidate(sentence: str, min_confidence: float = 0.35) -> bool:
    score, _ = obligation_score(sentence)
    return score >= min_confidence
