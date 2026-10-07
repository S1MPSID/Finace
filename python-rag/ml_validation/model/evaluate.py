"""Evaluation metrics for ML validation models — no fabricated numbers."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)

from ml_validation.model.features import vectorize_cases
from ml_validation.model.train import latest_model_dir
from ml_validation.paths import REPORTS_DIR, ensure_dirs
from ml_validation.schema import ComplianceCase


def _ece(proba: np.ndarray, y_true: np.ndarray, classes: np.ndarray, n_bins: int = 10) -> float:
    """Expected calibration error on max-class confidence."""
    conf = proba.max(axis=1)
    pred = classes[proba.argmax(axis=1)]
    correct = (pred == y_true).astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (conf >= bins[i]) & (conf < bins[i + 1] if i < n_bins - 1 else conf <= bins[i + 1])
        if not np.any(mask):
            continue
        ece += abs(correct[mask].mean() - conf[mask].mean()) * (mask.sum() / len(conf))
    return float(ece)


def _safe_roc_auc(y_true: np.ndarray, proba: np.ndarray, classes: np.ndarray) -> float | None:
    try:
        if len(classes) == 2:
            val = float(roc_auc_score(y_true, proba[:, list(classes).index(classes[1])]))
        else:
            val = float(
                roc_auc_score(y_true, proba, multi_class="ovr", average="macro", labels=classes)
            )
        if val != val:  # NaN
            return None
        return val
    except Exception:
        return None


def evaluate_split(
    cases: list[ComplianceCase],
    *,
    model_dir: Path | None = None,
    split_name: str = "test",
) -> dict[str, Any]:
    model_dir = model_dir or latest_model_dir()
    if model_dir is None:
        raise FileNotFoundError("No trained model found. Run train first.")

    status_model = joblib.load(model_dir / "status_model.joblib")
    risk_model = joblib.load(model_dir / "risk_model.joblib")
    X, y_status, y_risk = vectorize_cases(cases)

    status_pred = status_model.predict(X)
    risk_pred = risk_model.predict(X)
    status_proba = status_model.predict_proba(X)
    risk_proba = risk_model.predict_proba(X)

    def pack(y_true, y_pred, proba, model, label: str) -> dict[str, Any]:
        labels = list(model.classes_)
        p, r, f, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, average=None, zero_division=0
        )
        per_class = {
            str(labels[i]): {
                "precision": round(float(p[i]), 4),
                "recall": round(float(r[i]), 4),
                "f1": round(float(f[i]), 4),
            }
            for i in range(len(labels))
        }
        cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "weighted_f1": round(
                float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4
            ),
            "per_class": per_class,
            "confusion_matrix": {"labels": [str(x) for x in labels], "matrix": cm},
            "roc_auc_macro_ovr": _safe_roc_auc(y_true, proba, model.classes_),
            "ece": round(_ece(proba, y_true, model.classes_), 4),
            "classification_report": classification_report(
                y_true, y_pred, zero_division=0, output_dict=True
            ),
            "target": label,
        }

    # Per-domain / difficulty
    by_domain: dict[str, list[int]] = defaultdict(list)
    by_diff: dict[str, list[int]] = defaultdict(list)
    by_risk_true: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(cases):
        by_domain[c.domain].append(i)
        by_diff[c.difficulty].append(i)
        by_risk_true[c.expected_risk].append(i)

    def subset_acc(indices: list[int], y_true, y_pred) -> float | None:
        if not indices:
            return None
        return round(float(accuracy_score(y_true[indices], y_pred[indices])), 4)

    report = {
        "split": split_name,
        "n": len(cases),
        "model_dir": str(model_dir),
        "status": pack(y_status, status_pred, status_proba, status_model, "expected_status"),
        "risk": pack(y_risk, risk_pred, risk_proba, risk_model, "expected_risk"),
        "per_domain_status_accuracy": {
            d: subset_acc(ix, y_status, status_pred) for d, ix in sorted(by_domain.items())
        },
        "per_difficulty_status_accuracy": {
            d: subset_acc(ix, y_status, status_pred) for d, ix in sorted(by_diff.items())
        },
        "per_risk_status_accuracy": {
            d: subset_acc(ix, y_status, status_pred) for d, ix in sorted(by_risk_true.items())
        },
    }
    return report


def save_evaluation(report: dict[str, Any], stem: str = "evaluation") -> Path:
    ensure_dirs()
    path = REPORTS_DIR / f"{stem}_{report.get('split', 'test')}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path
