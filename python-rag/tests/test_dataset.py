"""Dataset integrity + train/serve parity checks."""
import csv
import json
import os

import numpy as np

from ml.common import load_dataset
from ml.dataset import parity_check
from ml.feature_schema import FEATURE_ORDER


def test_meta_marked_synthetic(benchmark_csv):
    meta_path = benchmark_csv.replace(".csv", "_meta.json")
    assert os.path.exists(meta_path)
    with open(meta_path, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    assert meta["purpose"].startswith("SYNTHETIC")
    assert "NOT regulatory ground truth" in meta["purpose"]
    assert meta["n_rows"] > 0
    assert meta["features"] == FEATURE_ORDER


def test_rows_readable_and_bounded(benchmark_csv):
    X, y, texts = load_dataset(benchmark_csv)
    assert len(X) == len(y) == len(texts) > 0
    assert not np.isnan(X).any()
    assert X.min() >= 0.0 and X.max() <= 1.0 + 1e-9
    assert set(np.unique(y)) <= {"LOW", "MEDIUM", "HIGH"}
    assert len(np.unique(y)) == 3


def test_row_features_match_schema(benchmark_csv):
    with open(benchmark_csv, "r", encoding="utf-8") as fh:
        row = next(csv.DictReader(fh))
    for feature in FEATURE_ORDER:
        assert feature in row, f"missing column {feature}"
    for feature in row:
        if feature in (
            "label",
            "workflow_description",
            "triggered_rule_ids",
            "latent_risk_score",
            "intended_controls",
            "intended_exposures",
        ):
            continue
        assert feature in FEATURE_ORDER, f"unexpected column {feature}"


def test_train_serve_parity(benchmark_csv):
    mismatches = parity_check(benchmark_csv)
    assert mismatches == [], f"parity mismatches: {mismatches[:5]}"


def test_label_rulebook_thresholds_sane():
    from ml.labeling import label_from_risk_score

    assert label_from_risk_score(0.0) == "LOW"
    assert label_from_risk_score(0.37) == "LOW"
    assert label_from_risk_score(0.38) == "MEDIUM"
    assert label_from_risk_score(0.61) == "MEDIUM"
    assert label_from_risk_score(0.62) == "HIGH"
    assert label_from_risk_score(1.0) == "HIGH"