"""
Feature extraction for the ML risk layer.

Mirrors the offline synthetic-dataset generation so that online serving uses the
exact same mapping (train/serve parity):

- rule features     : deterministic output of ``evaluate_rules``
- control/exposure  : stance-aware mention detection on the rule-eval text
- retrieval metrics : computed from ``retrieval_hits``

Control/exposure mentions are suppressed when a negation token appears within a
small token window (see ``NEGATION_WINDOW``), so "no transaction monitoring"
does not produce ``transaction_monitoring = 1``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np

from ml.feature_schema import (
    FEATURE_ORDER,
    FeatureDefinition,
    NEGATION_TOKENS,
    NEGATION_WINDOW,
    PROTECTIVE_CONTROLS,
    build_feature_definitions,
)

_TOKEN_RE = re.compile(r"\S+")
_NEG_RE_BLACKLIST = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in NEGATION_TOKENS) + r")\b",
    re.IGNORECASE,
)


@dataclass
class FeatureVector:
    values: dict[str, float]
    definitions: list[FeatureDefinition]

    def array(self) -> np.ndarray:
        return np.array([self.values[n] for n in FEATURE_ORDER], dtype=float)

    @property
    def control_coverage(self) -> float:
        present = sum(self.values.get(c, 0.0) >= 0.5 for c in PROTECTIVE_CONTROLS)
        return present / len(PROTECTIVE_CONTROLS)

    def triggered_counts(self) -> dict[str, int]:
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        from rules.rules_config import RULES

        rule_by_id = {r["rule_id"]: r for r in RULES}
        for d in self.definitions:
            if d.ftype != "rule":
                continue
            if self.values.get(d.name, 0.0) < 0.5:
                continue
            rid = d.name.replace("rule:", "")
            rule = rule_by_id.get(rid)
            if not rule:
                continue
            level = rule.get("risk_level", "MEDIUM")
            counts[level] = counts.get(level, 0) + 1
        return counts


def _is_negated(text: str, start: int, end: int) -> bool:
    left = _TOKEN_RE.findall(text[:start])[-NEGATION_WINDOW:] if start else []
    right = _TOKEN_RE.findall(text[end:])[:NEGATION_WINDOW]
    window = " ".join(left + right)
    return bool(_NEG_RE_BLACKLIST.search(window))


def _mention_is_present(text: str, patterns: tuple[str, ...]) -> bool:
    """Stance-aware: a positive mention counts only if it is not negated nearby."""
    if not patterns:
        return False
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            if not _is_negated(text, m.start(), m.end()):
                return True
    return False


def _retrieval_value(name: str, hits: list[dict[str, Any]], top_k: int) -> float:
    if name == "regulatory_evidence_count":
        return min(len(hits or []) / max(top_k, 1), 1.0)

    if name == "relevant_regulation_count":
        docs = {
            h.get("document_id")
            or h.get("metadata", {}).get("source")
            or h.get("metadata", {}).get("relative_path")
            for h in (hits or [])
        }
        docs.discard(None)
        return min(len(docs) / max(top_k, 1), 1.0)

    if name == "retrieval_strength":
        scores: list[float] = []
        for hit in hits or []:
            raw = hit.get("score", hit.get("rerank_score", hit.get("similarity", 0.0)))
            try:
                scores.append(float(raw))
            except (TypeError, ValueError):
                continue
        return float(np.clip(np.mean(scores), 0.0, 1.0)) if scores else 0.0

    if name == "active_regulation_ratio":
        hits = hits or []
        if not hits:
            return 0.0
        active = 0
        for h in hits:
            status = (h.get("metadata") or {}).get("status")
            if status in (None, "", "active"):
                active += 1
        return active / len(hits)

    return 0.0


def extract_workflow_features(
    workflow_text: str,
    rules_out: dict[str, Any],
    retrieval_hits: list[dict[str, Any]],
    top_k: int = 5,
    definitions: list[FeatureDefinition] | None = None,
) -> FeatureVector:
    """Build the canonical ML feature vector from existing pipeline outputs."""
    defs = definitions or build_feature_definitions()
    text = workflow_text or ""

    triggered = {
        item.get("rule_id")
        for item in (rules_out or {}).get("triggered_rules", [])
        if item.get("rule_id")
    }

    values: dict[str, float] = {}
    for d in defs:
        if d.ftype == "rule":
            rid = d.name.replace("rule:", "")
            values[d.name] = 1.0 if rid in triggered else 0.0
        elif d.ftype in ("control", "exposure"):
            values[d.name] = 1.0 if _mention_is_present(text, d.mention_patterns) else 0.0
        elif d.ftype == "retrieval":
            values[d.name] = _retrieval_value(d.name, retrieval_hits or [], top_k)
        else:
            values[d.name] = d.prototype

    return FeatureVector(values=values, definitions=defs)


def feature_vector_from_array(
    x: np.ndarray,
    definitions: list[FeatureDefinition] | None = None,
) -> FeatureVector:
    defs = definitions or build_feature_definitions()
    return FeatureVector(
        values={d.name: float(v) for d, v in zip(defs, x)},
        definitions=defs,
    )