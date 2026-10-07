"""Filesystem layout for ML validation artifacts."""
from __future__ import annotations

from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent.parent
MLV_ROOT = Path(__file__).resolve().parent

DATA_DIR = MLV_ROOT / "data"
BANK_DIR = DATA_DIR / "requirement_bank"
DATASET_DIR = DATA_DIR / "datasets"
SPLITS_DIR = DATA_DIR / "splits"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = DATA_DIR / "reports"
REVIEW_DIR = DATA_DIR / "review"

BANK_JSONL = BANK_DIR / "requirements.jsonl"
BANK_META = BANK_DIR / "bank_meta.json"
BANK_SUMMARY = BANK_DIR / "bank_summary.json"
REVIEW_QUEUE = REVIEW_DIR / "needs_review.jsonl"
REVIEW_DECISIONS = REVIEW_DIR / "decisions.jsonl"
VALIDATE_REPORT = REPORTS_DIR / "requirement_bank_validation.json"


def ensure_dirs() -> None:
    for d in (BANK_DIR, DATASET_DIR, SPLITS_DIR, MODELS_DIR, REPORTS_DIR, REVIEW_DIR):
        d.mkdir(parents=True, exist_ok=True)
