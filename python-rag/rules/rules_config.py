"""
Deterministic rule definitions for hybrid compliance scoring.

`RULES` is the single merged catalog used by the rule engine, the ML feature
schema and the XAI explainer. Every rule lives in `rules/catalog/` grouped by
payment / regulatory theme; add a new rule by adding one dict to the relevant
pack (or a new pack) - no other wiring is required.

The multi-category design means a rule only fires when its `categories` overlap
the categories the relevance router selected for the current prompt. Rules with
an empty `categories` list (core controls: R001-R011) are evaluated on every
prompt.
"""
from __future__ import annotations

from rules.catalog import ALL_CATALOG_RULES


RULES: list[dict] = ALL_CATALOG_RULES


def category_index() -> dict[str, list[dict]]:
    """Rules grouped by category tag (excluding the GENERAL marker)."""
    index: dict[str, list[dict]] = {}
    for rule in RULES:
        for category in rule.get("categories") or []:
            if category == "GENERAL":
                continue
            index.setdefault(category, []).append(rule)
    return index