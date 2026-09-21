"""Scenario-level behavioral tests mirroring the stability scenarios."""
import numpy as np

from ml.features import feature_vector_from_array
from ml.feature_schema import FEATURE_ORDER
from ml.stability import scenario_features, SCENARIOS


def test_every_scenario_feature_extractable():
    seen = set()
    for s in SCENARIOS:
        rules_out, values = scenario_features(s)
        assert isinstance(values, dict)
        assert set(values.keys()) == set(FEATURE_ORDER)
        seen.add(s["id"])
    assert seen == {s["id"] for s in SCENARIOS}


def test_scenario_rule_triggers():
    for s in SCENARIOS:
        rules_out, _ = scenario_features(s)
        triggered = {t.get("rule_id") for t in rules_out.get("triggered_rules", [])}
        if "expect_rule" in s:
            assert s["expect_rule"] in triggered, f"{s['id']}: {s['expect_rule']} not triggered"
        if "expect_no_rule" in s:
            assert s["expect_no_rule"] not in triggered, f"{s['id']}: {s['expect_no_rule']} still triggered"


def test_compliant_scenario_all_controls():
    s = next(x for x in SCENARIOS if x["id"] == "compliant_low")
    _, values = scenario_features(s)
    from ml.feature_schema import PROTECTIVE_CONTROLS

    present = sum(values[c] >= 0.5 for c in PROTECTIVE_CONTROLS)
    assert present == len(PROTECTIVE_CONTROLS)


def test_remediated_low_probability(predictor):
    s = next(x for x in SCENARIOS if x["id"] == "remdiated")
    _, values = scenario_features(s)
    fv = feature_vector_from_array(np.array([values[f] for f in FEATURE_ORDER]))
    pred = predictor.predict(fv)
    assert pred["risk_class"] == "LOW"
    assert pred["probabilities"]["LOW"] > 0.5


def test_high_risk_scenarios_raise_probability(predictor):
    _, values_lo = scenario_features(next(x for x in SCENARIOS if x["id"] == "compliant_low"))
    base = predictor.predict(feature_vector_from_array(np.array([values_lo[f] for f in FEATURE_ORDER])))["probabilities"]["HIGH"]

    for s in SCENARIOS:
        if s["id"] in ("compliant_low", "remdiated", "irrelevant_nonfinancial"):
            continue
        _, values = scenario_features(s)
        fv = feature_vector_from_array(np.array([values[f] for f in FEATURE_ORDER]))
        p_high = predictor.predict(fv)["probabilities"]["HIGH"]
        assert p_high > base, f"{s['id']}: P(HIGH) {p_high:.3f} not above benign baseline {base:.3f}"
