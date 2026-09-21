"""
Train and select the compliance ML risk model on the synthetic benchmark.

Pipeline
--------
1. load the risk benchmark CSV (see ml/dataset.py)
2. stratified 70/15/15 train / validation / test split (deterministic seed)
3. fit candidate models on train:
     - LogisticRegression (multinomial logit; direct, linear SHAP-explainable)
     - RandomForestClassifier (non-linear; Tree SHAP-explainable)
4. select the best base model by macro-F1 on the held-out validation set
5. refit the selected model on the full train set and export artifacts:
     - model.joblib                (scikit-learn estimator)
     - pipeline.json               (model + dataset + schema metadata)
     - background_X.npy            (SHAP baseline sample from training data)
     - splits.json                 (train/val/test row indices -> reproducibility)
6. probabilities are the model's predicted class probabilities and are NOT framed
   as calibrated confidence; evaluation reports ECE alongside accuracy.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.common import (
    ARTIFACTS_DIR,
    DEFAULT_N,
    DEFAULT_SEED,
    default_dataset_csv,
    load_dataset,
    make_splits,
)
from ml.evaluate import ece
from ml.feature_schema import FEATURE_ORDER, RISK_LEVELS, SCHEMA_VERSION

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score


def candidate_models() -> dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=3000,
            solver="lbfgs",
            C=1.0,
            random_state=42,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
    }


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def select_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> tuple[str, dict[str, object], dict[str, dict]]:
    models = candidate_models()
    results: dict[str, dict] = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred_val = model.predict(X_val)
        proba_val = model.predict_proba(X_val)
        pred_train = model.predict(X_train)
        results[name] = {
            "model": name,
            "val_accuracy": round(float(accuracy_score(y_val, pred_val)), 4),
            "val_macro_f1": round(float(f1_score(y_val, pred_val, average="macro")), 4),
            "val_weighted_f1": round(float(f1_score(y_val, pred_val, average="weighted")), 4),
            "val_ece": round(ece(proba_val, y_val, model.classes_), 4),
            "train_accuracy": round(float(accuracy_score(y_train, pred_train)), 4),
            "train_macro_f1": round(float(f1_score(y_train, pred_train, average="macro")), 4),
        }

    best_name = max(results, key=lambda n: results[n]["val_macro_f1"])
    return best_name, models, results


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/select the ML risk model")
    parser.add_argument("--csv", default=default_dataset_csv())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out-dir", default=ARTIFACTS_DIR)
    parser.add_argument("--no-refit", action="store_true", help="Use the on-train fit as final artifact (tests)")
    args = parser.parse_args()

    X, y, _ = load_dataset(args.csv)
    idx_train, idx_val, idx_test = make_splits(X, y, args.seed)

    best_name, models, results = select_model(
        X[idx_train], y[idx_train], X[idx_val], y[idx_val]
    )
    print("candidate results (validation):")
    for name, m in results.items():
        print(
            f"  {name:24s} macro_f1={m['val_macro_f1']} acc={m['val_accuracy']} "
            f"ece={m['val_ece']}"
        )
    print(f"selected model: {best_name}")

    if not args.no_refit:
        final_model = models[best_name]
        final_model.fit(X[idx_train], y[idx_train])
    else:
        final_model = models[best_name]

    import joblib

    os.makedirs(args.out_dir, exist_ok=True)
    joblib.dump(final_model, os.path.join(args.out_dir, "model.joblib"))
    np.save(os.path.join(args.out_dir, "background_X.npy"), X[idx_train][:200])
    with open(os.path.join(args.out_dir, "splits.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "train": idx_train.tolist(),
                "val": idx_val.tolist(),
                "test": idx_test.tolist(),
                "seed": args.seed,
            },
            fh,
            indent=2,
        )

    y_val_pred = final_model.predict(X[idx_val])
    pipeline_meta: dict = {
        "schema_version": SCHEMA_VERSION,
        "features": FEATURE_ORDER,
        "classes": [str(c) for c in final_model.classes_],
        "target": "compliance_risk_class (synthetic benchmark labels)",
        "selected_model": best_name,
        "model_hyperparameters": models[best_name].get_params(),
        "candidate_results": results,
        "model_version": "1.0.0",
        "dataset_version": f"v1-{args.seed}-{len(y)}",
        "training_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_versions": {
            "python": sys.version.split()[0],
            "numpy": _package_version("numpy"),
            "scikit_learn": _package_version("scikit-learn"),
            "shap": _package_version("shap"),
        },
        "seed": args.seed,
        "split": {
            "train_size": 0.7,
            "n_train": int(len(idx_train)),
            "n_val": int(len(idx_val)),
            "n_test": int(len(idx_test)),
        },
        "final_validation_macro_f1": round(
            float(f1_score(y[idx_val], y_val_pred, average="macro")), 4
        ),
        "final_validation_accuracy": round(
            float(accuracy_score(y[idx_val], y_val_pred)), 4
        ),
        "probability_notes": [
            "probabilities are model predicted class probabilities.",
            "NOT calibrated confidence; ECE is reported in evaluation.",
            "SHAP explains the selected base ML model (ml/explain.py).",
            "Benchmark/synthetic: retrain on real labelled workflows before production use.",
        ],
    }
    with open(os.path.join(args.out_dir, "pipeline.json"), "w", encoding="utf-8") as fh:
        json.dump(pipeline_meta, fh, indent=2)

    print("artifacts written to", args.out_dir)

    # Held-out test evaluation (once, no tuning).
    from ml.evaluate import simple_metrics

    test_report = simple_metrics(final_model, X[idx_test], y[idx_test], RISK_LEVELS, "test")
    print("test metrics:")
    for k, v in test_report.items():
        if not isinstance(v, (dict, list)):
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
