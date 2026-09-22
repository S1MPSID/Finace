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


def build_rule_eval_text(workflow_text: str) -> str:
    """
    Only user-authored content should drive deterministic rules.
    Assistant answers often restate risk labels (e.g. 'P2P Crypto Exposure')
    and would otherwise re-trigger the same rules forever.

    Only the latest user message is used: earlier product descriptions would
    re-inject stale risk language (e.g. 'P2P crypto') and re-trigger the same
    rules on entirely unrelated prompts. Remediation turns such as 'we added
    KYC' still work because the rule engine matches required-control patterns
    directly against the current message.
    """
    return extract_current_user_message(workflow_text)


def build_retrieval_query(workflow_text: str) -> str:
    """Latest user message, clipped to the embedding length cap."""
    return extract_current_user_message(workflow_text)[:1200]


def wants_score_improvement(workflow_text: str) -> bool:
    current = extract_current_user_message(workflow_text)
    return bool(_IMPROVE_SCORE_RE.search(current or workflow_text or ""))
