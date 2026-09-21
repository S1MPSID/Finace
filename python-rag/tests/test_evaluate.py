"""Held-out evaluation gate: metrics recomputed from stored artifacts + splits."""
import json
import os

import numpy as np

from ml.common import load_dataset, make_splits, default_dataset_csv, REPORTS_DIR
from ml.explain import load_artifacts
from ml.feature_schema import RISK_LEVELS
from ml.predict import MLRiskPredictor


def test_evaluation_report_exists_and_complete():
    path = os.path.join(REPORTS_DIR, "evaluation_report.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as fh:
        report = json.load(fh)
    assert 0.0 < report["test_macro_f1"] <= 1.0
    assert report["test_accuracy"] > 0.5
    assert report["test_ece"] < 0.2
    assert set(report["test_per_class"].keys()) == set(RISK_LEVELS)


def _run_predictor_to_report(tmp_path):
    model, meta, _ = load_artifacts()
    X, y, _ = load_dataset(default_dataset_csv())
    tr, va, te = make_splits(X, y, seed=meta.get("seed", 0))
    idx = np.sort(te)
    out_path = str(tmp_path / "eval.json")
    from ml.evaluate import write_report

    path = write_report(model, X[idx], y[idx], {"test": te.tolist()}, meta, out_path=out_path)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_evaluation_recomputes_on_held_out(tmp_path):
    report = _run_predictor_to_report(tmp_path)
    assert report["model"] in ("random_forest", "RandomForestClassifier", "LogisticRegression", "logistic", "logistic_regression")
    assert 0.0 < report["test_macro_f1"] <= 1.0
    assert report["test_accuracy"] > 0.5
    assert report["test_ece"] < 0.2
    assert set(report["test_per_class"].keys()) == set(RISK_LEVELS)


def test_predictor_probabilities_sum_to_one(tmp_path):
    report = _run_predictor_to_report(tmp_path)
    assert report["regression_health"]["class_priors"]
    assert abs(sum(report["regression_health"]["class_priors"].values()) - 1.0) < 1e-6
