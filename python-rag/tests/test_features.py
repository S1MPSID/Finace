"""Stance-aware feature extraction tests (train/serve parity of the online extractor)."""
import numpy as np
import pytest

from rules.rule_engine import evaluate_rules
from ml.features import extract_workflow_features, feature_vector_from_array
from ml.feature_schema import (
    FEATURE_ORDER,
    PROTECTIVE_CONTROLS,
    EXPOSURE_FEATURES,
)
from ml.dataset import hits_from_features

RETRIEVAL_OK = {
    "regulatory_evidence_count": 1.0,
    "relevant_regulation_count": 0.8,
    "retrieval_strength": 0.78,
    "active_regulation_ratio": 1.0,
}


def _extract(text: str, retrieval: dict = RETRIEVAL_OK) -> dict:
    rules_out = evaluate_rules(text)
    hits = hits_from_features(retrieval, top_k=5)
    fv = extract_workflow_features(text, rules_out, hits, top_k=5)
    return fv.values


def test_feature_order_is_complete():
    assert len(FEATURE_ORDER) == len(set(FEATURE_ORDER))
    assert any(n.startswith("rule:") for n in FEATURE_ORDER)
    for c in PROTECTIVE_CONTROLS:
        assert c in FEATURE_ORDER
    for e in EXPOSURE_FEATURES:
        assert e in FEATURE_ORDER


def test_positive_control_detected():
    text = (
        "Full KYC is implemented for all new customers. An AML program covers "
        "all customer activity. Transaction monitoring flags unusual activity. "
        "We maintain a grievance redressal portal. FEMA compliance checks run on "
        "every cross-border payment. Two-factor authentication is mandatory. "
        "Our board reviews the compliance policy quarterly."
    )
    values = _extract(text)
    for c in PROTECTIVE_CONTROLS:
        assert values[c] >= 1.0, f"{c} should be present"

    assert values["kyc_present"] == 1.0
    assert values["aml_present"] == 1.0
    assert values["grievance_mechanism"] == 1.0


def test_negation_window_suppresses_control():
    text = "We do not have transaction monitoring and we lack KYC verification."
    values = _extract(text)
    assert values["transaction_monitoring"] == 0.0
    assert values["kyc_present"] == 0.0


def test_rule_feature_reflects_rule_engine():
    text = "We onboard customers without KYC verification."
    values = _extract(text)
    assert values["rule:R001_NO_KYC"] == 1.0


def test_negated_controls_trigger_relevant_rules():
    text = (
        "Customers open accounts without KYC verification. We do not run AML "
        "screening or transaction monitoring. There is no grievance channel, "
        "and we do not use FEMA or foreign-exchange compliance checks. The "
        "platform supports P2P crypto transfers and international remittances."
    )
    rules = evaluate_rules(text)
    triggered = {item["rule_id"] for item in rules["triggered_rules"]}
    assert {"R001_NO_KYC", "R002_P2P_CRYPTO", "R003_CROSS_BORDER_NO_FEMA", "R004_NO_GRIEVANCE"} <= triggered

    values = _extract(text)
    assert values["kyc_present"] == 0.0
    assert values["aml_present"] == 0.0
    assert values["transaction_monitoring"] == 0.0
    assert values["fema_controls"] == 0.0
    assert values["grievance_mechanism"] == 0.0


def test_retrieval_metrics_mapped():
    values = _extract("A plain compliant workflow.")
    assert 0.0 <= values["regulatory_evidence_count"] <= 1.0
    assert 0.0 <= values["retrieval_strength"] <= 1.0
    assert 0.0 <= values["active_regulation_ratio"] <= 1.0


def test_feature_vector_from_array_reconstructs():
    values = _extract("KYC is implemented.")
    arr = [values[f] for f in FEATURE_ORDER]
    fv = feature_vector_from_array(np.array(arr))
    for name, val in zip(FEATURE_ORDER, arr):
        assert fv.values[name] == pytest.approx(val)

    assert fv.array().shape == (len(FEATURE_ORDER),)
