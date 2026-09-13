"""
Deterministic rule definitions for hybrid compliance scoring.

Rules are maintained in `rules/catalog/` by payment / regulatory theme.
`RULES` is the merged list used by the rule engine and XAI feature spec.
"""
from __future__ import annotations

from rules.catalog import ALL_CATALOG_RULES

RULES: list[dict] = ALL_CATALOG_RULES
