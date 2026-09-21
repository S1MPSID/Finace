"""
Canonical ML feature schema for the compliance risk prediction layer.

Every feature below is derivable from *existing* system outputs so the model can
be served online without new instrumentation:

- rule-trigger features  -> ``rules.rule_engine.evaluate_rules`` output
- control / exposure      -> stance-aware keyword detection on the rule-eval text
- retrieval metrics       -> ``retrieval_hits`` returned by ``LocalRetriever.search``

Design rules
------------
1. The final compliance risk *label* never appears as a feature.
2. Control features are stance-aware: a mere mention of a term (e.g. "grievance")
   does *not* mean the control is implemented. Presence requires a positive
   assertion that is not negated within a small token window.
3. Rule-trigger features come from the deterministic rule engine exactly as
   produced offline (same function, same configuration -> train/serve parity).
4. No standard scaler is applied: feature values keep their native, documented
   units so SHAP attributions stay literally traceable (binary 0/1 flags, counts
   normalized to [0,1], mean similarity in [0,1]).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from rules.rules_config import RULES

FeatureType = Literal["rule", "control", "exposure", "retrieval"]

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")

# Features that reduce risk when active (protective controls).
PROTECTIVE_CONTROLS: tuple[str, ...] = (
    "kyc_present",
    "aml_present",
    "transaction_monitoring",
    "grievance_mechanism",
    "fema_controls",
    "authentication_control",
    "compliance_policy_present",
)

# Features that indicate activity exposure (increase risk if unmitigated).
EXPOSURE_FEATURES: tuple[str, ...] = (
    "cross_border_activity",
    "p2p_crypto_activity",
)

RETRIEVAL_FEATURES: tuple[str, ...] = (
    "regulatory_evidence_count",
    "relevant_regulation_count",
    "retrieval_strength",
    "active_regulation_ratio",
)


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    ftype: FeatureType
    description: str
    value_range: tuple[float, float]
    direction: Literal[
        "higher_increases_risk",
        "higher_decreases_risk",
        "contextual",
    ]
    source: str
    mention_patterns: tuple[str, ...] = ()
    prototype: float = 0.0


# Negation tokens used by the stance-aware control/exposure detector.
NEGATION_TOKENS: tuple[str, ...] = (
    "no",
    "none",
    "not",
    "without",
    "skip",
    "skipped",
    "bypass",
    "bypassed",
    "absent",
    "missing",
    "lack",
    "lacks",
    "lacking",
    "isn",
    "aren",
    "don",
    "doesn",
    "didn",
)

# Token window (each side) in which a negation suppresses a mention.
NEGATION_WINDOW = 8


# Stance-aware mention patterns: the text must assert the control exists,
# and any mention inside a negated window is ignored.
# The phrasing mirrors the positive "requires_any" lists of rules_config.py
# so the ML feature set agrees with what the deterministic engine accepts.
_CONTROL_MENTIONS: dict[str, tuple[str, ...]] = {
    "kyc_present": (
        r"\b(full|mandatory|complete|strong)?\s*kyc\b.*\b(in\s+place|enabled|implemented|added|present|done)\b",
        r"\b(have|has|with|using|added|implemented)\s+(full\s+)?kyc\b",
        r"\bkyc\s+(is\s+)?(complete|mandatory|enabled|implemented)\b",
        r"\be-?kyc\b",
        r"\baadhaar\b",
        r"\bkyc\s+verification\b",
        r"\bverify\w*\s+with\s+kyc\b",
    ),
    "aml_present": (
        r"\baml\b",
        r"\banti[- ]money[- ]laundering\b",
        r"\banti[- ]money\b",
        r"\benhanced\s+due\s+diligence\b",
        r"\bedd\b",
    ),
    "transaction_monitoring": (
        r"\btransaction\s+monitoring\b",
        r"\bongoing\s+due\s+diligence\b",
        r"\bsuspicious\s+transaction\b",
        r"\btransaction\s+screening\b",
        r"\bstr\s+filing\b",
    ),
    "grievance_mechanism": (
        r"\bgrievance\s+(redressal|mechanism|process|portal|cell)\b",
        r"\bcomplaint\s+(handling|redressal|mechanism|process)\b",
        r"\bombuds\w*\b",
    ),
    "fema_controls": (
        r"\bfema\b",
        r"\bfx\s+compliance\b",
        r"\bforex\s+(declaration|compliance)\b",
        r"\brbi\s+reporting\b",
        r"\bforeign\s+exchange\s+compliance\b",
    ),
    "authentication_control": (
        r"\b2fa\b",
        r"\bmfa\b",
        r"\botp\b",
        r"\btwo[- ]factor\b",
        r"\bmulti[-\s]factor\b",
        r"\b(otp|passcode|pin)\s+verification\b",
    ),
    "compliance_policy_present": (
        r"\bcompliance\s+(policy|framework|program)\b",
        r"\bboard\s+oversight\b",
        r"\bcompliance\s+officer\b",
        r"\bgovernance\s+(framework|structure|policy)\b",
        r"\binternal\s+audit\b",
        r"\bcompliance\s+training\b",
        r"\bstaff\s+training\b",
        r"\bpolicy\s+document\b",
    ),
}

_EXPOSURE_MENTIONS: dict[str, tuple[str, ...]] = {
    "cross_border_activity": (
        r"\bcross[- ]border\b",
        r"\bforeign\s+transfer\b",
        r"\binternational\s+remittance\b",
        r"\boutward\s+remittance\b",
        r"\binward\s+remittance\b",
        r"\boverseas\s+(transfer|remittance|payment|wire)\b",
        r"\bforeign\s+exchange\b",
    ),
    "p2p_crypto_activity": (
        r"\bp2p\b",
        r"\bcrypto\b",
        r"\bbitcoin\b",
        r"\bethereum\b",
        r"\bvirtual\s+asset\b",
        r"\bvirtual\s+digital\s+asset\b",
        r"\bcrypto[- ]asset\b",
        r"\bvda\b",
        r"\bdigital\s+currency\b",
    ),
}


def _rule_definitions() -> list[FeatureDefinition]:
    defs: list[FeatureDefinition] = []
    for rule in RULES:
        rid = rule["rule_id"]
        risk = rule.get("risk_level", "MEDIUM")
        defs.append(
            FeatureDefinition(
                name=f"rule:{rid}",
                ftype="rule",
                description=f"Deterministic rule '{rule.get('name')}' ({rid}) was triggered by the rule engine.",
                value_range=(0.0, 1.0),
                direction="higher_increases_risk",
                source=f"rules.rules_config.RULES[{rid}].risk_level={risk} + rules.rule_engine.evaluate_rules",
            )
        )
    return defs


def _text_definitions() -> list[FeatureDefinition]:
    defs: list[FeatureDefinition] = []

    for name in PROTECTIVE_CONTROLS:
        patterns = tuple(_CONTROL_MENTIONS.get(name, ()))
        defs.append(
            FeatureDefinition(
                name=name,
                ftype="control",
                description=f"Stance-aware presence of the protective control '{name}' in the workflow text.",
                value_range=(0.0, 1.0),
                direction="higher_decreases_risk",
                source="workflow_text (stance-aware keyword detection)",
                mention_patterns=patterns,
            )
        )

    for name in EXPOSURE_FEATURES:
        patterns = tuple(_EXPOSURE_MENTIONS.get(name, ()))
        defs.append(
            FeatureDefinition(
                name=name,
                ftype="exposure",
                description=f"Workflow text indicates '{name}' activity (exposure domain).",
                value_range=(0.0, 1.0),
                direction="higher_increases_risk",
                source="workflow_text (presence detection)",
                mention_patterns=patterns,
            )
        )

    return defs


def _retrieval_definitions() -> list[FeatureDefinition]:
    return [
        FeatureDefinition(
            name="regulatory_evidence_count",
            ftype="retrieval",
            description="Retrieved regulatory evidence chunks normalized by top_k (evidence coverage).",
            value_range=(0.0, 1.0),
            direction="contextual",
            source="len(retrieval_hits) / top_k",
        ),
        FeatureDefinition(
            name="relevant_regulation_count",
            ftype="retrieval",
            description="Distinct regulation documents retrieved normalized by top_k (regulatory surface).",
            value_range=(0.0, 1.0),
            direction="contextual",
            source="distinct document_id in retrieval_hits / top_k",
        ),
        FeatureDefinition(
            name="retrieval_strength",
            ftype="retrieval",
            description="Mean retrieval similarity score of the hits clipped to [0,1] (grounding strength).",
            value_range=(0.0, 1.0),
            direction="contextual",
            source="mean(retrieval_hits[*].score) clipped to [0,1]",
        ),
        FeatureDefinition(
            name="active_regulation_ratio",
            ftype="retrieval",
            description="Fraction of retrieved hits whose regulatory status is active (or unknown).",
            value_range=(0.0, 1.0),
            direction="contextual",
            source="fraction of retrieval_hits with metadata.status in {None, 'active'}",
        ),
    ]


def build_feature_definitions() -> list[FeatureDefinition]:
    """Deterministic, fixed feature order used by training, serving and SHAP."""
    return _rule_definitions() + _text_definitions() + _retrieval_definitions()


FEATURE_ORDER: list[str] = [d.name for d in build_feature_definitions()]

SCHEMA_VERSION = "1.0.0"


def feature_index(name: str) -> int:
    return FEATURE_ORDER.index(name)


def rule_feature_names() -> list[str]:
    return [d.name for d in _rule_definitions()]


def serializable_schema() -> dict:
    """JSON-friendly schema dump for metadata and documentation checks."""
    return {
        "schema_version": SCHEMA_VERSION,
        "features": [
            {
                "name": d.name,
                "type": d.ftype,
                "description": d.description,
                "range": list(d.value_range),
                "direction": d.direction,
                "source": d.source,
                "patterns": list(d.mention_patterns),
            }
            for d in build_feature_definitions()
        ],
    }