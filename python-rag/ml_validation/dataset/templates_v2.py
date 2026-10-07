"""
Hard / realistic V2 scenario templates.

Design goals vs V1:
- Do NOT paste the regulatory requirement sentence into the scenario.
- Avoid label-correlated shortcut phrases ("without KYC", "out of scope", "pilot").
- Prefer implicit/indirect business language, long workflows, and shared vocabulary
  across compliant and non-compliant classes.
- Labels still come from the template type tied to a grounded requirement_id —
  not from an LLM.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from ml_validation.schema import ExpectedRisk, ExpectedStatus, ScenarioType


@dataclass(frozen=True)
class ScenarioTemplateV2:
    scenario_type: str
    expected_status: str
    expected_risk: str
    severity: str
    difficulty: str
    builder_key: str


TEMPLATES_V2: list[ScenarioTemplateV2] = [
    ScenarioTemplateV2(
        ScenarioType.COMPLIANT.value,
        ExpectedStatus.COMPLIANT.value,
        ExpectedRisk.LOW.value,
        "LOW",
        "hard",
        "compliant_natural",
    ),
    ScenarioTemplateV2(
        "compliant_with_risk_vocab",
        ExpectedStatus.COMPLIANT.value,
        ExpectedRisk.LOW.value,
        "LOW",
        "hard",
        "compliant_with_risk_vocab",
    ),
    ScenarioTemplateV2(
        ScenarioType.NON_COMPLIANT.value,
        ExpectedStatus.NON_COMPLIANT.value,
        ExpectedRisk.HIGH.value,
        "HIGH",
        "hard",
        "noncompliant_implicit",
    ),
    ScenarioTemplateV2(
        "noncompliant_no_trigger_words",
        ExpectedStatus.NON_COMPLIANT.value,
        ExpectedRisk.HIGH.value,
        "HIGH",
        "hard",
        "noncompliant_no_trigger_words",
    ),
    ScenarioTemplateV2(
        ScenarioType.PARTIAL.value,
        ExpectedStatus.PARTIAL.value,
        ExpectedRisk.MEDIUM.value,
        "MEDIUM",
        "hard",
        "partial_borderline",
    ),
    ScenarioTemplateV2(
        "implicit_violation",
        ExpectedStatus.NON_COMPLIANT.value,
        ExpectedRisk.HIGH.value,
        "HIGH",
        "hard",
        "implicit_violation",
    ),
    ScenarioTemplateV2(
        "noisy_long_workflow",
        ExpectedStatus.PARTIAL.value,
        ExpectedRisk.MEDIUM.value,
        "MEDIUM",
        "hard",
        "noisy_long_workflow",
    ),
    ScenarioTemplateV2(
        ScenarioType.MULTI_VIOLATION.value,
        ExpectedStatus.NON_COMPLIANT.value,
        ExpectedRisk.HIGH.value,
        "HIGH",
        "hard",
        "multi_issue_natural",
    ),
    ScenarioTemplateV2(
        ScenarioType.HARD_NEGATIVE.value,
        ExpectedStatus.COMPLIANT.value,
        ExpectedRisk.LOW.value,
        "LOW",
        "hard",
        "hard_negative_distractors",
    ),
    ScenarioTemplateV2(
        ScenarioType.EDGE.value,
        ExpectedStatus.PARTIAL.value,
        ExpectedRisk.MEDIUM.value,
        "MEDIUM",
        "hard",
        "borderline_accountability",
    ),
]


_THEME_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("identity_verification", re.compile(r"\bkyc\b|\be-?kyc\b|\baadhaar\b|\bidentity\b|\bverification\b", re.I)),
    ("aml_monitoring", re.compile(r"\baml\b|\bmonitor|\bsuspicious|\bstr\b|\bscreening\b", re.I)),
    ("grievance", re.compile(r"\bgrievance\b|\bcomplaint\b|\bdispute\b|\bredress", re.I)),
    ("credentials_access", re.compile(r"\bcredential|\bmaker|\bchecker|\bpassword|\buser\s*id\b|\bauth", re.I)),
    ("reporting_attestation", re.compile(r"\battest|\breport|\bself.?attest|\bcompliance\s+portal|\bpcomp", re.I)),
    ("dr_continuity", re.compile(r"\bdr\b|\bdisaster|\bdrill|\bcontinuity|\bbcp\b", re.I)),
    ("settlement_adjustments", re.compile(r"\bchargeback|\badjustment|\barcs\b|\bsettlement\b", re.I)),
    ("data_retention", re.compile(r"\bretention\b|\blog\b|\baudit\s+trail\b|\brecord", re.I)),
]


def infer_control_theme(requirement: str) -> str:
    for name, pat in _THEME_RULES:
        if pat.search(requirement or ""):
            return name
    # Stable fallback from hash so generation is reproducible per requirement.
    digest = hashlib.sha1((requirement or "").encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_THEME_RULES)
    return _THEME_RULES[idx][0]


def _noise_block(variant: int) -> str:
    noises = [
        "Office hours are 9–6 IST. The cafeteria menu rotates weekly. Parking validation is available for visitors.",
        "We use Slack for internal chat and Notion for product specs. Brand guidelines were updated last quarter.",
        "The mobile app supports dark mode. Push notifications can be muted. Release notes are published on Fridays.",
        "Recruiting is open for two backend roles. The annual offsite is planned in Goa. Travel policy allows economy flights.",
    ]
    return noises[variant % len(noises)]


def _theme_fact(theme: str, mode: str, variant: int) -> str:
    """
    mode: implemented | delayed | missing_implicit | shared_vocab | partner_unclear
    Facts avoid classic shortcut phrases while encoding compliance stance.
    """
    table: dict[str, dict[str, list[str]]] = {
        "identity_verification": {
            "implemented": [
                "Before any account is activated, customers complete video-based identity capture and document matching; activation is blocked until the check clears.",
                "Onboarding queues hold new profiles until an analyst confirms PAN/Aadhaar match results from the verification vendor.",
            ],
            "delayed": [
                "Customers receive a live account after mobile OTP; document collection is scheduled only if they later request higher limits.",
                "Product opens a limited wallet immediately and schedules identity checks as a backlog ticket for the ops team.",
            ],
            "missing_implicit": [
                "Growth wants same-day activation, so the launch checklist only includes phone OTP and email confirmation.",
                "The onboarding PRD lists OTP, device fingerprint, and welcome SMS — identity document steps were deferred to a later phase.",
            ],
            "shared_vocab": [
                "During design reviews we discussed KYC risk, AML exposure, incomplete filings, and violation scenarios in tabletop exercises.",
                "Training decks mention KYC, AML, risk, incomplete controls, and historical violation case studies for awareness.",
            ],
            "partner_unclear": [
                "A partner bank handles customer setup; our contract mentions ‘regulatory diligence’ but does not assign who performs identity checks before go-live.",
            ],
        },
        "aml_monitoring": {
            "implemented": [
                "Transfers above internal thresholds pause for secondary review; analysts file escalations through the monitoring console before release.",
                "Nightly batch jobs score accounts for unusual velocity and route exceptions to the financial crime desk.",
            ],
            "delayed": [
                "Monitoring rules exist in a spreadsheet; engineering has not wired them into the live payment path yet.",
                "We rely on monthly manual spot checks of a sample of ledgers rather than continuous screening.",
            ],
            "missing_implicit": [
                "The payment path posts settlements straight to the ledger after authorization with no secondary review queue.",
                "Ops capacity focuses on uptime; unusual patterns are investigated only when a partner bank emails us.",
            ],
            "shared_vocab": [
                "Workshops covered AML typology, risk scoring, incomplete alerts, and violation walkthroughs using synthetic datasets.",
            ],
            "partner_unclear": [
                "An outsourced processor advertises ‘compliance tooling’; our runbooks do not show who owns alert closure for our MIDs.",
            ],
        },
        "grievance": {
            "implemented": [
                "Customers open tickets in a tracked portal with SLA clocks; unresolved items escalate to a nodal officer with an audit trail.",
                "Every failed transfer creates a case ID customers can query; status updates are logged for regulators on request.",
            ],
            "delayed": [
                "Support answers Instagram DMs and a shared inbox; ticket IDs and SLA clocks are planned for next quarter.",
                "Complaints are noted in a Google Sheet by interns; there is no customer-visible tracking ID yet.",
            ],
            "missing_implicit": [
                "Users are told to email founders@ for issues; there is no structured intake or escalation path in production.",
                "The app FAQ says ‘contact your bank’ and does not expose an in-product dispute channel.",
            ],
            "shared_vocab": [
                "All-hands slides referenced grievance frameworks, KYC failures, AML fines, incomplete remediation, and violation headlines from peers.",
            ],
            "partner_unclear": [
                "Disputes may be handled by a BPO; RACI between our app and the BPO for complaint closure is still draft.",
            ],
        },
        "credentials_access": {
            "implemented": [
                "Privileged actions require dual approval; each operator has an individual SSO identity with MFA and session logging.",
                "Production changes need maker and approver steps bound to named corporate IDs, not shared mailboxes.",
            ],
            "delayed": [
                "The back-office still uses one shared console login for the night shift while IAM rollout continues.",
                "SSO is live for email, but the settlement console remains on a common password rotated quarterly.",
            ],
            "missing_implicit": [
                "Ops prefers a single shared admin account taped on the NOC board so handovers are faster.",
                "Contractors access the production portal through a vendor laptop using the same named ‘ops’ profile.",
            ],
            "shared_vocab": [
                "Security training covered credential stuffing, KYC fraud, AML typologies, incomplete access reviews, and violation postmortems.",
            ],
            "partner_unclear": [
                "A systems integrator retains production access ‘for support’; we have not finished inventorying those identities.",
            ],
        },
        "reporting_attestation": {
            "implemented": [
                "Compliance files the periodic portal attestation with evidence packs attached; deadlines are tracked on a calendar with dual sign-off.",
                "Each quarter the control owners upload self-attestation artefacts and the CCO countersigns before submission.",
            ],
            "delayed": [
                "Attestation reminders sit in a backlog; last cycle’s packet was assembled after the portal deadline as a catch-up exercise.",
                "Evidence collection is informal — teams email screenshots when asked rather than following a fixed calendar.",
            ],
            "missing_implicit": [
                "Product roadmap has no owner for regulatory portal submissions; engineering assumes legal will ‘handle filings somehow’.",
                "We have never submitted a self-attestation packet; leadership prioritizes feature launches over portal calendars.",
            ],
            "shared_vocab": [
                "Town halls mentioned reporting risk, KYC audits, AML examinations, incomplete submissions, and peer violation stories.",
            ],
            "partner_unclear": [
                "A consultant offered to ‘take care of attestations’; no signed SOW defines who presses submit in the portal.",
            ],
        },
        "dr_continuity": {
            "implemented": [
                "We run scheduled failover exercises twice a year; results and remediation tickets are stored with timestamps.",
                "Secondary site cutovers are rehearsed with payment traffic and signed off by technology and compliance.",
            ],
            "delayed": [
                "A DR runbook exists as a slide deck; the last live failover rehearsal was cancelled and not rescheduled.",
                "Backups are taken, but application-level failover has not been demonstrated to the steering committee.",
            ],
            "missing_implicit": [
                "Production runs in a single region; capacity planning assumes the primary zone is always available.",
                "The architecture wiki describes HA as aspirational; no rehearsal calendar is maintained.",
            ],
            "shared_vocab": [
                "Tabletops discussed outage risk, KYC freeze scenarios, AML halt procedures, incomplete runbooks, and violation liabilities.",
            ],
            "partner_unclear": [
                "Cloud DR is ‘included’ in the vendor brochure; our acceptance tests never exercised a regional failure for payments.",
            ],
        },
        "settlement_adjustments": {
            "implemented": [
                "Chargeback and adjustment queues show acceptance source flags; exceptions require dual review before funds move.",
                "Issuers and acquirers reconcile ARCS-style reports daily with clear ownership for auto-accepted items.",
            ],
            "delayed": [
                "Adjustments are reconciled in Excel after month-end; real-time flags in the back office are still a wishlist item.",
                "Auto-acceptance behaviour is poorly understood by the ops team that inherited the console.",
            ],
            "missing_implicit": [
                "Settlement differences are written off to a suspense GL without a documented dispute workflow.",
                "The product posts net settlement figures and does not expose adjustment provenance to member ops.",
            ],
            "shared_vocab": [
                "Ops training referenced chargeback risk, KYC holds, AML freezes, incomplete reconciliations, and violation case studies.",
            ],
            "partner_unclear": [
                "A processor owns the dispute UI; we cannot see whether acceptances are manual or automatic for our portfolio.",
            ],
        },
        "data_retention": {
            "implemented": [
                "Transaction and access logs are retained on WORM storage with a documented purge calendar aligned to policy.",
                "Audit trails for privileged actions are immutable for the mandated period and searchable for exams.",
            ],
            "delayed": [
                "Logs rotate on the default cloud retention; legal is still defining how long payment audit trails must stay online.",
                "We keep dumps on a laptop share ‘for now’ while evaluating an archival product.",
            ],
            "missing_implicit": [
                "Debug logs are wiped weekly to save cost; there is no long-lived audit store for settlement decisions.",
                "Engineering treats observability as ephemeral; historical reconstructions rely on memory.",
            ],
            "shared_vocab": [
                "Privacy workshops covered retention risk, KYC data, AML dossiers, incomplete inventories, and violation headlines.",
            ],
            "partner_unclear": [
                "A SaaS SIEM holds some events; no RFP clarifies retention length for our payment audit use case.",
            ],
        },
    }
    options = table.get(theme, table["identity_verification"]).get(mode) or table["identity_verification"]["implemented"]
    return options[variant % len(options)]


def build_scenario_v2(
    *,
    domain: str,
    requirement: str,
    builder_key: str,
    paraphrase_idx: int = 0,
) -> str:
    """Build a hard scenario that does not embed the requirement text."""
    theme = infer_control_theme(requirement)
    domain_label = domain.replace("_", " ")
    v = paraphrase_idx
    noise = _noise_block(v)

    intros = [
        f"We operate a {domain_label} fintech stack serving retail and small-merchant flows in India.",
        f"Our company processes {domain_label}-related payments for marketplace sellers and consumers.",
        f"The product organisation ships a {domain_label} channel alongside cards and wallets.",
    ]
    intro = intros[v % len(intros)]

    if builder_key == "compliant_natural":
        body = _theme_fact(theme, "implemented", v)
        return (
            f"{intro} {body} Control owners meet monthly; evidence packs are available for exams. "
            f"Incidental notes: {noise}"
        )

    if builder_key == "compliant_with_risk_vocab":
        vocab = _theme_fact(theme, "shared_vocab", v)
        body = _theme_fact(theme, "implemented", v + 1)
        return (
            f"{intro} {vocab} Despite that vocabulary appearing in training materials, live operations "
            f"actually follow this practice: {body} {noise}"
        )

    if builder_key == "noncompliant_implicit":
        body = _theme_fact(theme, "missing_implicit", v)
        return (
            f"{intro} Leadership prioritises conversion metrics. {body} "
            f"Roadmaps list growth experiments and partnership deals ahead of control hardening. {noise}"
        )

    if builder_key == "noncompliant_no_trigger_words":
        # Avoid words: without, no KYC, skip, out of scope, pilot, missing, violation
        body = _theme_fact(theme, "delayed", v)
        return (
            f"{intro} Launch sequencing puts revenue features first. {body} "
            f"Customer success measures time-to-first-transaction as the north-star metric. {noise}"
        )

    if builder_key == "partial_borderline":
        a = _theme_fact(theme, "implemented", v)
        b = _theme_fact(theme, "delayed", v + 1)
        return (
            f"{intro} For enterprise clients, {a} For the self-serve SMB segment, {b} "
            f"Coverage therefore differs by cohort. {noise}"
        )

    if builder_key == "implicit_violation":
        body = _theme_fact(theme, "missing_implicit", v + 2)
        return (
            f"{intro} The architecture review board signed off on the current path. {body} "
            f"No compensating control was recorded in the decision log. {noise}"
        )

    if builder_key == "noisy_long_workflow":
        body = _theme_fact(theme, "delayed", v)
        return (
            f"{intro} Week-one journey: marketing acquisition → device bind → first credit. "
            f"{_noise_block(v + 1)} Meanwhile on controls: {body} "
            f"Finance closes books on T+2; legal reviews vendor MSAs annually. {_noise_block(v + 2)}"
        )

    if builder_key == "multi_issue_natural":
        a = _theme_fact(theme, "missing_implicit", v)
        b = _theme_fact("grievance", "delayed", v)
        c = _theme_fact("credentials_access", "delayed", v + 1)
        return (
            f"{intro} Several operational gaps coexist. First, {a} Second, {b} Third, {c} "
            f"Program management tracks these as separate epics with no shared deadline. {noise}"
        )

    if builder_key == "hard_negative_distractors":
        vocab = _theme_fact(theme, "shared_vocab", v)
        # Truly out of regulated rails but using scary words — still COMPLIANT for this requirement
        # because the live product does not offer the regulated activity.
        return (
            f"We sell offline event ticketing software with QR check-in at venues. "
            f"{vocab} Those topics appear only in awareness training. "
            f"The live product never settles funds, never opens payment accounts, and never performs "
            f"{domain_label} switching; merchants invoice customers outside our platform. {noise}"
        )

    if builder_key == "borderline_accountability":
        body = _theme_fact(theme, "partner_unclear", v)
        return (
            f"{intro} Distribution relies on a partner bank and a processor. {body} "
            f"Internal counsel has asked for a clearer RACI before the next exam cycle. {noise}"
        )

    # Fallback
    return f"{intro} {_theme_fact(theme, 'delayed', v)} {noise}"
