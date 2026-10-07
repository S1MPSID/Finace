"""
Feature extraction for ML validation models.

Features are derived from the *scenario workflow text* only at inference time.
Regulatory text is NEVER a prediction target feature that could let the model
copy labels from the requirement string alone in a trivial way for production
serving — but for the benchmark we include light lexical overlap with the
requirement as an explicit, documented feature (requirement_overlap), because
online Finace also compares workflow text to retrieved clauses.

Important: these features do not modify regulatory evidence.
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np

from ml_validation.schema import ComplianceCase

FEATURE_NAMES: list[str] = [
    "scenario_len_norm",
    "has_shall_must",
    "has_negation",
    "has_kyc",
    "has_aml",
    "has_grievance",
    "has_monitoring",
    "has_audit",
    "has_partial_language",
    "has_out_of_scope",
    "has_pilot_language",
    "has_multi_gap",
    "requirement_token_overlap",
    "domain_mentioned",
    "exclamation_density",
]


_NEG = re.compile(
    r"\b(no|not|without|skip|do not|don't|absent|fail(?:s|ed)? to|never)\b", re.I
)
_PARTIAL = re.compile(r"\b(partial|pilot|incomplete|inconsistent|unclear|roadmap)\b", re.I)
_OOS = re.compile(r"\b(out of scope|does not apply|unrelated|offline-only)\b", re.I)
_MULTI = re.compile(r"\b(multiple gaps|besides missing|also fail)\b", re.I)


def _tokset(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))


def extract_feature_dict(
    scenario: str,
    *,
    domain: str = "",
    requirement: str = "",
) -> dict[str, float]:
    t = scenario or ""
    tl = t.lower()
    req_toks = _tokset(requirement)
    scen_toks = _tokset(t)
    overlap = (len(req_toks & scen_toks) / len(req_toks)) if req_toks else 0.0
    return {
        "scenario_len_norm": min(len(t) / 800.0, 1.0),
        "has_shall_must": 1.0 if re.search(r"\b(shall|must|mandatory)\b", tl) else 0.0,
        "has_negation": 1.0 if _NEG.search(tl) else 0.0,
        "has_kyc": 1.0 if re.search(r"\bkyc\b|\be-?kyc\b", tl) else 0.0,
        "has_aml": 1.0 if re.search(r"\baml\b|anti-?money", tl) else 0.0,
        "has_grievance": 1.0 if re.search(r"\bgrievance\b|\bcomplaint\b", tl) else 0.0,
        "has_monitoring": 1.0 if re.search(r"\bmonitor", tl) else 0.0,
        "has_audit": 1.0 if re.search(r"\baudit\b|\battestation\b", tl) else 0.0,
        "has_partial_language": 1.0 if _PARTIAL.search(tl) else 0.0,
        "has_out_of_scope": 1.0 if _OOS.search(tl) else 0.0,
        "has_pilot_language": 1.0 if re.search(r"\bpilot\b|\bbeta\b", tl) else 0.0,
        "has_multi_gap": 1.0 if _MULTI.search(tl) else 0.0,
        "requirement_token_overlap": float(overlap),
        "domain_mentioned": 1.0
        if domain
        and (
            domain.replace("_", " ").lower() in tl
            or domain.lower() in tl
        )
        else 0.0,
        "exclamation_density": min(t.count("!") / 5.0, 1.0),
    }


def vectorize_cases(cases: list[ComplianceCase]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return X, y_status, y_risk."""
    rows = [
        extract_feature_dict(c.scenario, domain=c.domain, requirement=c.compliance_requirement)
        for c in cases
    ]
    X = np.array([[r[n] for n in FEATURE_NAMES] for r in rows], dtype=np.float64)
    y_status = np.array([c.expected_status for c in cases])
    y_risk = np.array([c.expected_risk for c in cases])
    return X, y_status, y_risk


def vectorize_text(scenario: str, *, domain: str = "", requirement: str = "") -> np.ndarray:
    d = extract_feature_dict(scenario, domain=domain, requirement=requirement)
    return np.array([[d[n] for n in FEATURE_NAMES]], dtype=np.float64)
