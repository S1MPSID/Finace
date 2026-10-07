"""
Dedicated adversarial / hard-negative challenge set.

Same keywords appear across classes; non-compliant cases avoid obvious triggers.
Not used for training when running the V2 pipeline evaluation suite.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from loguru import logger

from ml_validation.dataset.generate import save_cases
from ml_validation.dataset.templates_v2 import infer_control_theme
from ml_validation.requirement_bank.eligibility import filter_eligible
from ml_validation.schema import ComplianceCase, ExpectedRisk, ExpectedStatus, RegulatoryRequirement, ReviewStatus


def _cid(req_id: str, kind: str, idx: int) -> str:
    d = hashlib.sha1(f"adv|{req_id}|{kind}|{idx}".encode()).hexdigest()[:16]
    return f"CASE-{d}"


def _fid(req_id: str, kind: str) -> str:
    return f"FAM-{hashlib.sha1(f'adv|{req_id}|{kind}'.encode()).hexdigest()[:12]}"


def _shared_vocab_block() -> str:
    return (
        "Internal workshops mentioned KYC, AML, violation scenarios, risk registers, "
        "incomplete remediation plans, and peer enforcement actions."
    )


def build_adversarial_cases(
    requirements: list[RegulatoryRequirement],
    *,
    max_requirements: int = 200,
    variants_per_req: int = 2,
) -> list[ComplianceCase]:
    eligible = filter_eligible(requirements)
    eligible.sort(key=lambda r: (r.domain, r.requirement_id))
    eligible = eligible[:max_requirements]
    created = datetime.now(timezone.utc).isoformat()
    cases: list[ComplianceCase] = []

    for req in eligible:
        theme = infer_control_theme(req.requirement)
        domain = req.domain.replace("_", " ")
        for idx in range(variants_per_req):
            # A) COMPLIANT with scary keywords
            scen_c = (
                f"{_shared_vocab_block()} "
                f"For our live {domain} channel, every activation waits on completed identity and control checks "
                f"tied to theme '{theme}', with dual review and retained evidence. "
                f"Marketing copy may say 'fast onboarding' but production gates remain enforced. "
                f"Distractor: we also sponsor a cricket jersey and run a podcast about payments innovation."
            )
            cases.append(
                ComplianceCase(
                    case_id=_cid(req.requirement_id, "adv_compliant", idx),
                    requirement_id=req.requirement_id,
                    domain=req.domain,
                    scenario=scen_c,
                    scenario_type="adversarial_compliant_risk_vocab",
                    difficulty="hard",
                    regulatory_document=req.document,
                    regulatory_section=req.section,
                    source_chunk_id=req.source_chunk_id,
                    compliance_requirement=req.requirement,
                    expected_status=ExpectedStatus.COMPLIANT.value,
                    expected_risk=ExpectedRisk.LOW.value,
                    severity="LOW",
                    family_id=_fid(req.requirement_id, "adv_compliant"),
                    bank_version=req.bank_version or "1.0.0",
                    evidence=req.evidence,
                    quality_flags=["adversarial", "shared_risk_vocab"],
                    review_status=ReviewStatus.APPROVED.value,
                    created_at=created,
                )
            )

            # B) NON_COMPLIANT without obvious trigger words (no without/no/skip/missing/pilot)
            scen_n = (
                f"Our {domain} acquisition funnel prioritises time-to-first-transaction. "
                f"Accounts become usable after phone OTP and device bind; deeper control work for theme "
                f"'{theme}' is sequenced behind revenue experiments and partner launches. "
                f"Customer success dashboards highlight conversion, not control coverage. "
                f"Distractor: office snacks include almonds; the design system uses Inter font."
            )
            cases.append(
                ComplianceCase(
                    case_id=_cid(req.requirement_id, "adv_noncompliant", idx),
                    requirement_id=req.requirement_id,
                    domain=req.domain,
                    scenario=scen_n,
                    scenario_type="adversarial_noncompliant_no_triggers",
                    difficulty="hard",
                    regulatory_document=req.document,
                    regulatory_section=req.section,
                    source_chunk_id=req.source_chunk_id,
                    compliance_requirement=req.requirement,
                    expected_status=ExpectedStatus.NON_COMPLIANT.value,
                    expected_risk=ExpectedRisk.HIGH.value,
                    severity="HIGH",
                    family_id=_fid(req.requirement_id, "adv_noncompliant"),
                    bank_version=req.bank_version or "1.0.0",
                    evidence=req.evidence,
                    quality_flags=["adversarial", "no_obvious_triggers"],
                    review_status=ReviewStatus.APPROVED.value,
                    created_at=created,
                )
            )

            # C) COMPLIANT hard-negative: offline product + scary words
            scen_hn = (
                f"{_shared_vocab_block()} "
                f"The shipped product is venue badge printing for conferences. "
                f"No {domain} settlement, account opening, or payment switch participation occurs. "
                f"Payment-rail obligations for theme '{theme}' are therefore not exercised by the live system."
            )
            cases.append(
                ComplianceCase(
                    case_id=_cid(req.requirement_id, "adv_hardneg", idx),
                    requirement_id=req.requirement_id,
                    domain=req.domain,
                    scenario=scen_hn,
                    scenario_type="adversarial_hard_negative",
                    difficulty="hard",
                    regulatory_document=req.document,
                    regulatory_section=req.section,
                    source_chunk_id=req.source_chunk_id,
                    compliance_requirement=req.requirement,
                    expected_status=ExpectedStatus.COMPLIANT.value,
                    expected_risk=ExpectedRisk.LOW.value,
                    severity="LOW",
                    family_id=_fid(req.requirement_id, "adv_hardneg"),
                    bank_version=req.bank_version or "1.0.0",
                    evidence=req.evidence,
                    quality_flags=["adversarial", "hard_negative"],
                    review_status=ReviewStatus.APPROVED.value,
                    created_at=created,
                )
            )

    logger.info(f"Adversarial set: {len(cases)} cases from {len(eligible)} requirements")
    return cases


def save_adversarial(cases: list[ComplianceCase], stem: str = "adversarial_challenge_v1") -> None:
    save_cases(cases, stem=stem)
