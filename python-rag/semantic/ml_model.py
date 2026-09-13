"""Semantic status classifier trained on regulation corpus chunks (TF-IDF + logistic regression)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

MODEL_PATH = Path(__file__).resolve().parent / "models" / "status_classifier.joblib"
_pipeline: Any = None


def model_available() -> bool:
    return MODEL_PATH.is_file()


def load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if not model_available():
        return None
    try:
        import joblib

        _pipeline = joblib.load(MODEL_PATH)
        return _pipeline
    except Exception as exc:
        logger.warning(f"Failed to load semantic model: {exc}")
        return None


def _top_regulation_snippet(category_id: str, retrieval_hits: list[dict[str, Any]] | None) -> str:
    if not retrieval_hits:
        return ""
    for hit in retrieval_hits:
        meta = hit.get("metadata") or {}
        rel = str(meta.get("relative_path") or "").lower()
        text = (hit.get("text") or "")[:1500]
        if not text:
            continue
        if category_id.lower() in rel or True:
            return text
    return (retrieval_hits[0].get("text") or "")[:1500]


_CONF_TRUST = 0.75


def predict_status(
    category_id: str,
    text: str,
    retrieval_hits: list[dict[str, Any]] | None = None,
) -> tuple[str, float, str]:
    from semantic.evaluator import _heuristic_status

    reg = _top_regulation_snippet(category_id, retrieval_hits)
    wf = (text or "")[:12000]
    sample = f"[{category_id}] REG: {reg} | WF: {wf}" if reg else f"[{category_id}] WF: {wf}"

    pipe = load_pipeline()
    if pipe is None:
        st, conf, _ = _heuristic_status(category_id, wf)
        return st, conf, "heuristic"

    try:
        status = str(pipe.predict([sample])[0])
        proba = pipe.predict_proba([sample])[0]
        confidence = float(max(proba))
        if status not in {"COMPLIANT", "PARTIAL", "MISSING", "UNKNOWN"}:
            status = "PARTIAL"
        # High-confidence ML predictions win outright.
        if confidence >= _CONF_TRUST:
            return status, confidence, "ml"
        # Uncertain model: let strong deterministic keyword evidence arbitrate,
        # but keep the (honest) ML confidence figure.
        heur_status, _, strength = _heuristic_status(category_id, wf)
        if strength >= 2 and heur_status in {"COMPLIANT", "MISSING"} and heur_status != status:
            return heur_status, confidence, "ml+heuristic"
        return status, confidence, "ml"
    except Exception as exc:
        logger.warning(f"Semantic ML predict failed: {exc}")
        st, conf, _ = _heuristic_status(category_id, wf)
        return st, conf, "heuristic"
