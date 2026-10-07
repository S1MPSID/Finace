"""
Train status + risk classifiers on the grounded compliance benchmark.

Compares LogisticRegression vs RandomForest; selects by validation macro-F1.
Does not use deep learning by default — data scale suits classical models.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from ml_validation.model.features import FEATURE_NAMES, vectorize_cases
from ml_validation.paths import MODELS_DIR, ensure_dirs
from ml_validation.schema import ComplianceCase


def _candidates(seed: int = 42) -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=4000,
            solver="lbfgs",
            C=1.0,
            class_weight="balanced",
            random_state=seed,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=250,
            max_depth=16,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=seed,
            n_jobs=-1,
        ),
    }


def _pick(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_va: np.ndarray,
    y_va: np.ndarray,
    seed: int,
) -> tuple[str, Any, dict[str, dict]]:
    results: dict[str, dict] = {}
    best_name = ""
    best_model = None
    best_f1 = -1.0
    for name, model in _candidates(seed).items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_va)
        macro = float(f1_score(y_va, pred, average="macro", zero_division=0))
        results[name] = {
            "val_accuracy": round(float(accuracy_score(y_va, pred)), 4),
            "val_macro_f1": round(macro, 4),
        }
        if macro > best_f1:
            best_f1 = macro
            best_name = name
            best_model = model
    assert best_model is not None
    # Refit on train only (caller may refit on train+val later)
    return best_name, best_model, results


def train_models(
    train: list[ComplianceCase],
    val: list[ComplianceCase],
    *,
    seed: int = 20261007,
    tag: str = "default",
) -> dict[str, Any]:
    ensure_dirs()
    X_tr, y_status_tr, y_risk_tr = vectorize_cases(train)
    X_va, y_status_va, y_risk_va = vectorize_cases(val)

    status_name, status_model, status_cmp = _pick(X_tr, y_status_tr, X_va, y_status_va, seed)
    risk_name, risk_model, risk_cmp = _pick(X_tr, y_risk_tr, X_va, y_risk_va, seed)

    # Refit winners on train
    status_model.fit(X_tr, y_status_tr)
    risk_model.fit(X_tr, y_risk_tr)

    # Background sample for explanations
    bg_idx = np.linspace(0, max(len(X_tr) - 1, 0), num=min(100, len(X_tr)), dtype=int)
    background = X_tr[bg_idx]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    safe_tag = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in tag)[:48]
    model_dir = MODELS_DIR / f"validation_{safe_tag}_{stamp}"
    model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(status_model, model_dir / "status_model.joblib")
    joblib.dump(risk_model, model_dir / "risk_model.joblib")
    np.save(model_dir / "background_X.npy", background)

    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_names": FEATURE_NAMES,
        "status_model": status_name,
        "risk_model": risk_name,
        "status_model_compare": status_cmp,
        "risk_model_compare": risk_cmp,
        "train_size": len(train),
        "val_size": len(val),
        "seed": seed,
        "tag": tag,
        "notes": [
            "ML predicts compliance status and risk from workflow text features.",
            "Does not override regulatory documents, rules, RAG evidence, or Gemini.",
            "Explanations from this model are distinct from Finace surrogate SHAP/LIME.",
        ],
        "model_dir": str(model_dir),
    }
    (model_dir / "pipeline.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # Pointer to latest
    (MODELS_DIR / "latest.json").write_text(
        json.dumps({"model_dir": str(model_dir), **{k: meta[k] for k in ("status_model", "risk_model", "created_at")}}, indent=2),
        encoding="utf-8",
    )
    logger.info(f"Models saved -> {model_dir} (status={status_name}, risk={risk_name})")
    return meta


def latest_model_dir() -> Path | None:
    pointer = MODELS_DIR / "latest.json"
    if not pointer.exists():
        return None
    data = json.loads(pointer.read_text(encoding="utf-8"))
    p = Path(data["model_dir"])
    return p if p.exists() else None
