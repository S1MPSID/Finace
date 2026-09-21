"""MLRiskPredictor contract + deterministic prediction / SHAP additivity."""
import numpy as np
import pytest

from ml.feature_schema import FEATURE_ORDER, RISK_LEVELS
from ml.stability import scenario_features, SCENARIOS


def _scenario_vector(scenario: dict):
    _, values = scenario_features(scenario)
    from ml.features import feature_vector_from_array

    return feature_vector_from_array(np.array([values[f] for f in FEATURE_ORDER]))


def test_predictor_available(predictor):
    assert predictor.available
    assert predictor.model_name


def test_predict_output_contract(predictor):
    out = predictor.predict(_scenario_vector(SCENARIOS[0]))
    assert out["available"] is True
    assert out["risk_class"] in RISK_LEVELS
    total = sum(out["probabilities"].values())
    assert abs(total - 1.0) < 1e-6
    assert set(out["probabilities"].keys()) == set(RISK_LEVELS)


def test_prediction_deterministic(predictor):
    scenario = SCENARIOS[0]
    fv = _scenario_vector(scenario)
    assert predictor.predict(fv) == predictor.predict(fv)


def test_combined_returns_explanation(predictor):
    out = predictor.combined(_scenario_vector(SCENARIOS[1]))
    assert out["available"] is True
    expl = out["explanation"]
    assert expl.get("method") in ("tree_shap", "exact_linear_logit_shap")
    assert expl.get("target") == "P(risk class = HIGH)"
    assert len(expl.get("features", [])) == len(FEATURE_ORDER)


def test_shap_additivity_exact(predictor):
    scenario = SCENARIOS[4]
    fv = _scenario_vector(scenario)
    pred = predictor.predict(fv)
    expl = predictor.explain(fv)
    p_high = pred["probabilities"]["HIGH"]
    assert expl["predicted_probability"] == pytest.approx(p_high, abs=1e-4)
    shap_sum = sum(f["shap_value"] for f in expl["features"])
    assert abs(expl["baseline"] + shap_sum - expl["predicted_value"]) < 5e-3


def test_rule_drivers_mention_triggered_rules(predictor):
    scenario = next(s for s in SCENARIOS if s.get("expect_rule") == "R001_NO_KYC")
    out = predictor.combined(_scenario_vector(scenario))
    drivers = " ".join(out["explanation"]["top_risk_drivers"])
    assert "R001" in drivers or "KYC" in drivers
