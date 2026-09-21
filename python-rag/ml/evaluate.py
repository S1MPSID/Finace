"""
Held-out evaluation utilities + report writer for the ML risk layer.

Evaluation respects the trained artifact exactly: the held-out test set is scored
once, metrics are written to ``ml/reports/evaluation_report.json`` and the test
partition is never used for model selection.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.common import (
    ARTIFACTS_DIR,
    DATASETS_DIR,
    DEFAULT_SEED,
    REPORTS_DIR,
    default_dataset_csv,
    load_dataset,
    make_splits,
)
from ml.feature_schema import FEATURE_ORDER, RISK_LEVELS, SCHEMA_VERSION

try:
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
        roc_auc_score,
    )
except ImportError:
    accuracy_score = f1_score = precision_recall_fscore_support = confusion_matrix = None
    roc_auc_score = None
    classification_report = None


def ece(probas: np.ndarray, y: np.ndarray, classes: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error over the predicted class argmax (multiclass)."""
    probas = np.asarray(probas, dtype=float)
    y = np.asarray(y)
    argmax = probas.argmax(axis=1)
    conf = probas.max(axis=1)
    correct = argmax == np.asarray([list(classes).index(v) for v in y])

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece_val = 0.0
    n = len(conf)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf >= lo) & (conf < hi) if hi < 1.0 else (conf >= lo) & (conf <= hi)
        if not mask.any():
            continue
        acc = correct[mask].mean()
        ece_val += (mask.sum() / n) * abs(acc - conf[mask].mean())
    return float(ece_val)


def _class_index(y: np.ndarray, classes: np.ndarray) -> np.ndarray:
    mapping = {str(c): i for i, c in enumerate(classes)}
    return np.array([mapping.get(str(v), -1) for v in y], dtype=int)


def _ovr_auc(probas: np.ndarray, y: np.ndarray, classes: np.ndarray) -> dict[str, float]:
    """One-vs-rest ROC-AUC per class (macro + per class)."""
    if roc_auc_score is None:
        return {}
    yi = _class_index(y, classes)
    if (yi < 0).any():
        return {}
    out: dict[str, float] = {}
    try:
        cls_auc = {}
        macro = 0.0
        for i, c in enumerate(classes):
            binary = (yi == i).astype(int)
            auc = float(roc_auc_score(binary, probas[:, i]))
            cls_auc[str(c)] = round(auc, 4)
            macro += auc
        out["ovr_auc"] = {
            "macro": round(macro / max(len(classes), 1), 4),
            "per_class": cls_auc,
        }
    except Exception:
        out["ovr_auc"] = {}
    return out


def simple_metrics(
    model,
    X: np.ndarray,
    y: np.ndarray,
    class_order: tuple[str, ...] = RISK_LEVELS,
    prefix: str = "",
) -> dict:
    """Compute the standard metric block used for validation/test runs."""
    pred = model.predict(X)
    proba = model.predict_proba(X)

    classes = model.classes_
    report = classification_report(y, pred, labels=list(classes), output_dict=True, zero_division=0)
    cm = confusion_matrix(y, pred, labels=list(classes))
    prec, rec, f1, _ = precision_recall_fscore_support(y, pred, labels=list(classes), zero_division=0)

    out: dict = {
        f"{prefix}_accuracy": round(float(accuracy_score(y, pred)), 4),
        f"{prefix}_macro_f1": round(float(f1_score(y, pred, labels=list(classes), average="macro", zero_division=0)), 4),
        f"{prefix}_weighted_f1": round(float(f1_score(y, pred, labels=list(classes), average="weighted", zero_division=0)), 4),
        f"{prefix}_ece": round(ece(proba, y, classes), 4),
    }
    per_class = {}
    for i, c in enumerate(classes):
        per_class[str(c)] = {
            "precision": round(float(prec[i]), 4),
            "recall": round(float(rec[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int((_class_index(y, classes) == i).sum()),
        }
    out[f"{prefix}_per_class"] = per_class
    out[f"{prefix}_confusion_matrix"] = cm.tolist()
    out[f"{prefix}_class_order"] = [str(c) for c in classes]
    auc = _ovr_auc(proba, y, classes)
    if auc:
        out[f"{prefix}_auc"] = auc
    return out


def regression_health(model, X: np.ndarray, y: np.ndarray) -> dict:
    """Diagnostics to catch silent train/serve degeneration (feature smells)."""
    classes = model.classes_
    yi = _class_index(y, classes)
    out: dict = {}
    if (yi < 0).any():
        out["unseen_label"] = True
        return out
    for i, c in enumerate(classes):
        frac = float(((yi == i).sum()) / max(len(yi), 1))
        out[f"prior_{c}"] = round(frac, 4)
    return {"class_priors": out}


def write_report(model, X_test, y_test, splits, pipeline_meta, out_path: str | None = None) -> str:
    report = simple_metrics(model, X_test, y_test, RISK_LEVELS, prefix="test")
    report["regression_health"] = regression_health(model, X_test, y_test)
    report["test_class_order"] = [str(c) for c in model.classes_]
    report["splits"] = {k: len(v) for k, v in splits.items() if isinstance(v, list)}
    report["model"] = pipeline_meta.get("selected_model", "?")
    report["schema_version"] = SCHEMA_VERSION
    out_path = out_path or os.path.join(REPORTS_DIR, "evaluation_report.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the trained ML risk model on held-out test split")
    parser.add_argument("--out-dir", default=ARTIFACTS_DIR)
    parser.add_argument("--csv", default=default_dataset_csv())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    import joblib

    model_path = os.path.join(args.out_dir, "model.joblib")
    if not os.path.exists(model_path):
        print("No artefact found; run ml/train.py first.", file=sys.stderr)
        sys.exit(1)

    model = joblib.load(model_path)
    with open(os.path.join(args.out_dir, "pipeline.json"), "r", encoding="utf-8") as fh:
        pipeline_meta = json.load(fh)
    with open(os.path.join(args.out_dir, "splits.json"), "r", encoding="utf-8") as fh:
        splits = json.load(fh)

    X, y, texts = load_dataset(args.csv)
    report = simple_metrics(model, X[splits["test"]], y[splits["test"]], RISK_LEVELS, prefix="test")
    report["regression_health"] = regression_health(model, X[splits["test"]], y[splits["test"]])
    report["test_class_order"] = [str(c) for c in model.classes_]
    report["splits"] = {k: len(v) for k, v in splits.items() if isinstance(v, list)}

    path = write_report(model, X[splits["test"]], y[splits["test"]], splits, pipeline_meta)
    print("evaluation report written to", path)
    for k, v in report.items():
        if not isinstance(v, (dict, list)):
            print(f"  {k}: {v}")

    from sklearn.metrics import accuracy_score, f1_score
    print("test_accuracy:", round(accuracy_score(y[splits["test"]], model.predict(X[splits["test"]])), 4))
    print("test_macro_f1:", round(f1_score(y[splits["test"]], model.predict(X[splits["test"]]), average="macro"), 4))


if __name__ == "__main__":
    main()