"""
Controlled scenario templates.

Each template produces a workflow description whose *label* is fixed by the
template type relative to a grounded regulatory requirement — not by an LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

from ml_validation.schema import ExpectedRisk, ExpectedStatus, ScenarioType


@dataclass(frozen=True)
class ScenarioTemplate:
    scenario_type: str
    expected_status: str
    expected_risk: str
    severity: str
    difficulty: str
    builder_key: str


TEMPLATES: list[ScenarioTemplate] = [
    ScenarioTemplate(
        ScenarioType.COMPLIANT.value,
        ExpectedStatus.COMPLIANT.value,
        ExpectedRisk.LOW.value,
        "LOW",
        "easy",
        "compliant",
    ),
    ScenarioTemplate(
        ScenarioType.NON_COMPLIANT.value,
        ExpectedStatus.NON_COMPLIANT.value,
        ExpectedRisk.HIGH.value,
        "HIGH",
        "easy",
        "non_compliant",
    ),
    ScenarioTemplate(
        ScenarioType.PARTIAL.value,
        ExpectedStatus.PARTIAL.value,
        ExpectedRisk.MEDIUM.value,
        "MEDIUM",
        "medium",
        "partial",
    ),
    ScenarioTemplate(
        ScenarioType.EDGE.value,
        ExpectedStatus.PARTIAL.value,
        ExpectedRisk.MEDIUM.value,
        "MEDIUM",
        "hard",
        "edge",
    ),
    ScenarioTemplate(
        ScenarioType.AMBIGUOUS.value,
        ExpectedStatus.AMBIGUOUS.value,
        ExpectedRisk.MEDIUM.value,
        "MEDIUM",
        "hard",
        "ambiguous",
    ),
    ScenarioTemplate(
        ScenarioType.MULTI_VIOLATION.value,
        ExpectedStatus.NON_COMPLIANT.value,
        ExpectedRisk.HIGH.value,
        "HIGH",
        "hard",
        "multi_violation",
    ),
    ScenarioTemplate(
        ScenarioType.HARD_NEGATIVE.value,
        ExpectedStatus.COMPLIANT.value,
        ExpectedRisk.LOW.value,
        "LOW",
        "hard",
        "hard_negative",
    ),
]


def _short_req(requirement: str, max_len: int = 180) -> str:
    t = " ".join((requirement or "").split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def build_scenario(
    *,
    domain: str,
    requirement: str,
    builder_key: str,
    paraphrase_idx: int = 0,
) -> str:
    """Deterministic workflow text templates (paraphrase variants by index)."""
    req = _short_req(requirement)
    domain_label = domain.replace("_", " ")

    compliant = [
        (
            f"We operate a {domain_label} fintech service. Our compliance program explicitly "
            f"implements the following regulatory obligation and we maintain audit evidence for it: {req} "
            f"Controls are mandatory, monitored, and reviewed quarterly."
        ),
        (
            f"Our {domain_label} product workflow is designed to satisfy this circular requirement in full: {req} "
            f"We have written policies, maker-checker controls, and periodic DR/compliance attestations."
        ),
        (
            f"As a regulated {domain_label} participant, we confirm adherence to: {req} "
            f"Implementation is complete with logging, escalation, and management oversight."
        ),
    ]
    non_compliant = [
        (
            f"We run a {domain_label} platform focused on rapid onboarding. We do not currently "
            f"implement this regulatory obligation and have no compensating control: {req}"
        ),
        (
            f"Our {domain_label} operations intentionally skip the process described here to reduce cost: {req} "
            f"There is no remediation plan or audit trail for this gap."
        ),
        (
            f"Customers can use our {domain_label} service without the control required by: {req} "
            f"Compliance review has not been started."
        ),
    ]
    partial = [
        (
            f"For our {domain_label} workflow we have started work on: {req} "
            f"However rollout is incomplete — only a pilot segment is covered and monitoring is not yet live."
        ),
        (
            f"We partially address this {domain_label} requirement: {req} "
            f"Policy exists on paper but operational enforcement and reporting are still inconsistent."
        ),
    ]
    edge = [
        (
            f"We are a {domain_label} intermediary relying on a partner bank. The partner claims to handle "
            f"this obligation, but our own contract and SOPs do not explicitly cover: {req} "
            f"Accountability between parties is unclear."
        ),
    ]
    ambiguous = [
        (
            f"Our {domain_label} product may touch related processes. Documentation mentions related themes "
            f"but it is unclear whether we are in scope for: {req} "
            f"No formal legal opinion has been obtained."
        ),
    ]
    multi = [
        (
            f"Our {domain_label} stack has multiple gaps. Besides missing KYC/AML hygiene in places, "
            f"we also fail to implement: {req} "
            f"There is no grievance escalation and no FEMA/reporting desk where relevant."
        ),
    ]
    hard_neg = [
        (
            f"We operate an unrelated SaaS billing tool with no {domain_label} rails. Marketing mentions "
            f"payments generally, but we do not offer the regulated product features addressed by: {req} "
            f"Therefore this obligation does not apply to our current workflow."
        ),
        (
            f"Although our blog discusses {domain_label} regulations, the live product is offline-only "
            f"loyalty points with no settlement. The following circular requirement is out of scope: {req}"
        ),
    ]

    buckets = {
        "compliant": compliant,
        "non_compliant": non_compliant,
        "partial": partial,
        "edge": edge,
        "ambiguous": ambiguous,
        "multi_violation": multi,
        "hard_negative": hard_neg,
    }
    options = buckets[builder_key]
    return options[paraphrase_idx % len(options)]
