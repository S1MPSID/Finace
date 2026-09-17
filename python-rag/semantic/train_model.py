"""Train the bootstrap semantic classifier.

Usage:
    cd python-rag
    python -m semantic.train_model            # train & report (skips if model exists)
    python -m semantic.train_model --force    # always retrain
"""
from __future__ import annotations

import argparse

from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

from semantic.dataset_builder import collect_training_rows
from semantic.ml_model import MODEL_PATH


def _build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=12000, ngram_range=(1, 2), min_df=2)),
            ("clf", LogisticRegression(max_iter=800, class_weight="balanced")),
        ]
    )


def ensure_model_trained(force: bool = False) -> None:
    if MODEL_PATH.is_file() and not force:
        return
    main()


def main(force: bool = False) -> None:
    texts, labels = collect_training_rows()
    if len(texts) < 10:
        raise RuntimeError("Not enough training rows to fit semantic model")

    pipe = _build_pipeline()
    pipe.fit(texts, labels)

    # Hold-out validation report (same dataset split used every run).
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    logger.info(f"Hold-out accuracy: {accuracy_score(y_test, preds):.3f}")
    logger.info(f"\n{classification_report(y_test, preds, zero_division=0)}")

    # Refit on everything for the shipped artifact.
    pipe = _build_pipeline()
    pipe.fit(texts, labels)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(pipe, MODEL_PATH)
    logger.info(f"Semantic model saved ({len(texts)} rows) → {MODEL_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train semantic status classifier")
    parser.add_argument("--force", action="store_true", help="Retrain even if model exists")
    args = parser.parse_args()
    main(force=args.force)