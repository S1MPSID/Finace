"""
Helpers to separate conversation history from the text used for
rule evaluation and retrieval (so assistant prose does not re-trigger rules).
"""
from __future__ import annotations

import re


_CURRENT_USER_RE = re.compile(
    r"###\s*CURRENT USER MESSAGE\s*\n(?P<body>.*)\Z",
    re.IGNORECASE | re.DOTALL,
)
_USER_TURN_RE = re.compile(
    r"###\s*USER TURN\s+\d+\s*\n(?P<body>.*?)(?=\n###|\n=====|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_IMPROVE_SCORE_RE = re.compile(
    r"\b("
    r"increase\s+(the\s+)?score|raise\s+(the\s+)?score|score\s+to\s+\d+"
    r"|make\s+(it\s+)?(90|higher|better)|improve\s+(the\s+)?(score|compliance)"
    r"|fix\s+(the\s+)?(issues|gaps|findings)|we\s+(now\s+)?(have|added|implemented)"
    r"|remediat|mitigat|address(ed|ing)?\s+(the\s+)?(drivers|xai|gaps)"
    r")\b",
    re.IGNORECASE,
)


def extract_current_user_message(workflow_text: str) -> str:
    text = workflow_text or ""
    m = _CURRENT_USER_RE.search(text)
    if m:
        return m.group("body").strip()
    return text.strip()


def extract_user_turns(workflow_text: str) -> list[str]:
    text = workflow_text or ""
    turns = [m.group("body").strip() for m in _USER_TURN_RE.finditer(text) if m.group("body").strip()]
    current = extract_current_user_message(text)
    # First prompt alone has no USER TURN markers.
    if not turns and current:
        return [current]
    if current and (not turns or turns[-1] != current):
        turns.append(current)
    return turns


def build_rule_eval_text(workflow_text: str) -> str:
    """
    Only user-authored content should drive deterministic rules.
    Assistant answers often restate risk labels (e.g. 'P2P Crypto Exposure')
    and would otherwise re-trigger the same rules forever.
    """
    turns = extract_user_turns(workflow_text)
    if not turns:
        return (workflow_text or "").strip()
    # Prefer earliest product description + latest message (covers remediations).
    if len(turns) == 1:
        return turns[0]
    return f"{turns[0]}\n\n{turns[-1]}"


def build_retrieval_query(workflow_text: str) -> str:
    """Shorter, higher-signal query for embedding search."""
    turns = extract_user_turns(workflow_text)
    if not turns:
        return (workflow_text or "").strip()[:1200]
    if len(turns) == 1:
        return turns[0][:1200]
    # First description + latest ask keeps retrieval on-product.
    return f"{turns[0]}\n\n{turns[-1]}"[:1200]


def wants_score_improvement(workflow_text: str) -> bool:
    current = extract_current_user_message(workflow_text)
    return bool(_IMPROVE_SCORE_RE.search(current or workflow_text or ""))
