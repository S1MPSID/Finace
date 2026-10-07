"""Text quality gates for corpus chunks and extracted requirements."""
from __future__ import annotations

import re
import string

_PRINTABLE = set(string.printable)
_WORD = re.compile(r"[A-Za-z]{3,}")


def ascii_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for c in text if c in _PRINTABLE)
    return printable / max(len(text), 1)


def alpha_word_ratio(text: str) -> float:
    tokens = re.findall(r"\S+", text or "")
    if not tokens:
        return 0.0
    words = [t for t in tokens if _WORD.search(t)]
    return len(words) / len(tokens)


def looks_like_ocr_garbage(text: str) -> bool:
    """Heuristic for badly OCR'd or binary-tainted chunk text."""
    t = text or ""
    if len(t.strip()) < 40:
        return True
    if ascii_ratio(t) < 0.75:
        return True
    if alpha_word_ratio(t) < 0.45:
        return True
    # High density of replacement chars / control junk
    if t.count("�") >= 2:
        return True
    weird = sum(1 for c in t if ord(c) > 127 and c not in "₹–—‘’“”…")
    if weird / max(len(t), 1) > 0.08:
        return True
    return False


def normalize_for_id(text: str) -> str:
    t = re.sub(r"\s+", " ", (text or "").lower().strip())
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return t[:240]


def evidence_is_grounded(evidence: str, chunk_text: str, min_ratio: float = 0.85) -> bool:
    """
    True if evidence is a substring of chunk_text (preferred) or
    has very high token overlap (handles minor whitespace normalization).
    """
    ev = re.sub(r"\s+", " ", (evidence or "").strip())
    ch = re.sub(r"\s+", " ", (chunk_text or "").strip())
    if not ev or not ch:
        return False
    if ev in ch:
        return True
    # Fallback: token Jaccard on lowercased alnum tokens
    ev_toks = set(re.findall(r"[a-z0-9]{2,}", ev.lower()))
    ch_toks = set(re.findall(r"[a-z0-9]{2,}", ch.lower()))
    if not ev_toks:
        return False
    overlap = len(ev_toks & ch_toks) / len(ev_toks)
    return overlap >= min_ratio
