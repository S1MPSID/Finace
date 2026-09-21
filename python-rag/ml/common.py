"""
Shared constants + dataset/split helpers for the ML risk layer.

Kept import-light so both ``ml.train`` and ``ml.evaluate`` can import it without
creating a circular dependency.
"""
from __future__ import annotations

import csv
import os

import numpy as np

from ml.feature_schema import FEATURE_ORDER

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARTIFACTS_DIR = os.path.join(ROOT, "ml", "artifacts")
DATASETS_DIR = os.path.join(ROOT, "ml", "datasets")
REPORTS_DIR = os.path.join(ROOT, "ml", "reports")

DEFAULT_N = 2400
DEFAULT_SEED = 20260919

TRAIN_SIZE = 0.7
VAL_SIZE = 0.5  # of the post-train remainder -> 70/15/15 overall


def default_dataset_csv() -> str:
    return os.path.join(DATASETS_DIR, f"risk_benchmark_v1-{DEFAULT_SEED}-{DEFAULT_N}.csv")


def load_dataset(csv_path: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Load the benchmark CSV -> (X, y, workflow_descriptions)."""
    X_rows: list[list[float]] = []
    y_rows: list[str] = []
    texts: list[str] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            X_rows.append([float(row[f]) for f in FEATURE_ORDER])
            y_rows.append(str(row["label"]))
            texts.append(str(row["workflow_description"]))
    return np.asarray(X_rows, dtype=float), np.asarray(y_rows, dtype=object), texts


def make_splits(
    X: np.ndarray, y: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stratified 70/15/15 train/val/test split (deterministic, reproducible)."""
    from sklearn.model_selection import train_test_split

    idx_all = np.arange(len(y))
    idx_train, idx_remain = train_test_split(
        idx_all, test_size=1 - TRAIN_SIZE, stratify=y, random_state=seed
    )
    idx_val, idx_test = train_test_split(
        idx_remain, test_size=VAL_SIZE, stratify=y[idx_remain], random_state=seed + 1
    )
    return idx_train, idx_val, idx_test