"""
Hybrid calibration: φ₀ = SEED_WEIGHT × φ₀_seed + LIVE_WEIGHT × φ₀_live

- φ₀_seed: mean score on seed workflows (refreshed every SEED_REFRESH_DAYS)
- φ₀_live: rolling mean of scored sessions (refreshed daily)
- Per-chat frozen baseline is set at chat start (Node stores on session; passed into pipeline)
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger

from config import settings
from rules.reference_workflows import REFERENCE_WORKFLOWS
from rules.rule_engine import evaluate_rules

META_ID = "global"
COL_META = "calibration_meta"
COL_SNAPSHOTS = "calibration_snapshots"
COL_SEEDS = "calibration_seeds"

LIVE_WINDOW_DAYS = 30


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _blend(seed: float, live: float) -> float:
    w_s = settings.calibration_seed_weight
    w_l = settings.calibration_live_weight
    return round(w_s * seed + w_l * live, 2)


def compute_phi0_seed_from_texts(texts: list[str]) -> float:
    from rules.scoring import score_from_anchor

    if not texts:
        return 70.0
    provisional = 70.0
    scores = [
        score_from_anchor(provisional, evaluate_rules(w).get("triggered_rules") or [], None)[0]
        for w in texts
    ]
    mean = sum(scores) / len(scores)
    refined = [
        score_from_anchor(mean, evaluate_rules(w).get("triggered_rules") or [], None)[0]
        for w in texts
    ]
    return round(sum(refined) / len(refined), 2)


def _coll(name: str):
    try:
        from db.mongo import get_collection

        return get_collection(name)
    except Exception as exc:
        logger.warning(f"Mongo unavailable for calibration ({name}): {exc}")
        return None


def ensure_seed_documents() -> None:
    coll = _coll(COL_SEEDS)
    if coll is None:
        return
    if coll.count_documents({}) >= len(REFERENCE_WORKFLOWS):
        return
    coll.delete_many({})
    for i, text in enumerate(REFERENCE_WORKFLOWS):
        coll.insert_one({"index": i, "text": text, "active": True})


def load_seed_texts() -> list[str]:
    coll = _coll(COL_SEEDS)
    if coll is None or coll.count_documents({}) == 0:
        return list(REFERENCE_WORKFLOWS)
    docs = list(coll.find({"active": True}).sort("index", 1))
    return [d["text"] for d in docs if d.get("text")]


def read_meta() -> dict[str, Any] | None:
    coll = _coll(COL_META)
    if coll is None:
        return None
    return coll.find_one({"_id": META_ID})


def write_meta(doc: dict[str, Any]) -> None:
    coll = _coll(COL_META)
    if coll is None:
        return
    doc["_id"] = META_ID
    doc["updated_at"] = _utcnow()
    coll.replace_one({"_id": META_ID}, doc, upsert=True)


def recompute_phi0_seed() -> float:
    texts = load_seed_texts()
    return compute_phi0_seed_from_texts(texts)


def recompute_phi0_live() -> tuple[float, float, int]:
    coll = _coll(COL_SNAPSHOTS)
    if coll is None:
        seed = recompute_phi0_seed()
        return seed, 0.0, 0
    since = _utcnow() - timedelta(days=LIVE_WINDOW_DAYS)
    cursor = coll.find({"scored_at": {"$gte": since}}, {"official_score": 1})
    scores = [float(d["official_score"]) for d in cursor if d.get("official_score") is not None]
    if not scores:
        seed = recompute_phi0_seed()
        return seed, 0.0, 0
    mean = sum(scores) / len(scores)
    if len(scores) > 1:
        var = sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)
        std = math.sqrt(var)
    else:
        std = 0.0
    return round(mean, 2), round(std, 2), len(scores)


def refresh_calibration_if_due() -> dict[str, Any]:
    """Update global meta when seed/live refresh intervals elapse."""
    ensure_seed_documents()
    meta = read_meta() or {}
    now = _utcnow()

    seed_at = meta.get("seed_updated_at")
    if seed_at and not isinstance(seed_at, datetime):
        seed_at = seed_at.replace(tzinfo=timezone.utc) if hasattr(seed_at, "replace") else None

    live_at = meta.get("live_updated_at")
    if live_at and not isinstance(live_at, datetime):
        live_at = live_at.replace(tzinfo=timezone.utc) if hasattr(live_at, "replace") else None

    phi0_seed = meta.get("phi0_seed")
    phi0_live = meta.get("phi0_live")

    seed_due = (
        phi0_seed is None
        or seed_at is None
        or (now - seed_at).total_seconds() >= settings.calibration_seed_refresh_days * 86400
    )
    if seed_due:
        phi0_seed = recompute_phi0_seed()
        seed_at = now
        logger.info(f"Calibration φ₀_seed refreshed → {phi0_seed}")

    live_due = (
        phi0_live is None
        or live_at is None
        or (now - live_at).total_seconds() >= settings.calibration_live_refresh_hours * 3600
    )
    if live_due:
        phi0_live, std, n = recompute_phi0_live()
        live_at = now
        meta["phi0_live_std"] = std
        meta["phi0_live_sample_count"] = n
        logger.info(f"Calibration φ₀_live refreshed → {phi0_live} (n={n})")

    if phi0_seed is None:
        phi0_seed = recompute_phi0_seed()
    if phi0_live is None:
        phi0_live, std, n = recompute_phi0_live()
        meta.setdefault("phi0_live_std", std)
        meta.setdefault("phi0_live_sample_count", n)

    blended = _blend(float(phi0_seed), float(phi0_live))
    out = {
        "phi0_seed": float(phi0_seed),
        "phi0_live": float(phi0_live),
        "phi0_blended": blended,
        "seed_weight": settings.calibration_seed_weight,
        "live_weight": settings.calibration_live_weight,
        "seed_updated_at": seed_at or now,
        "live_updated_at": live_at or now,
        **{k: meta.get(k) for k in ("phi0_live_std", "phi0_live_sample_count") if k in meta},
    }
    write_meta(out)
    return out


def get_current_calibration() -> dict[str, Any]:
    try:
        return refresh_calibration_if_due()
    except Exception as exc:
        logger.warning(f"Calibration fallback (no mongo): {exc}")
        seed = compute_phi0_seed_from_texts(REFERENCE_WORKFLOWS)
        live = seed
        return {
            "phi0_seed": seed,
            "phi0_live": live,
            "phi0_blended": _blend(seed, live),
            "seed_weight": settings.calibration_seed_weight,
            "live_weight": settings.calibration_live_weight,
        }


def resolve_anchor(
    frozen: dict[str, Any] | None = None,
) -> tuple[float, float, float, float]:
    """
    Returns (anchor_for_scoring, phi0_seed, phi0_live, phi0_blended).
    If frozen is set (per-chat), use frozen blended as anchor.
    """
    if frozen and frozen.get("phi0_blended") is not None:
        b = float(frozen["phi0_blended"])
        s = float(frozen.get("phi0_seed", b))
        l = float(frozen.get("phi0_live", b))
        return b, s, l, b
    cur = get_current_calibration()
    b = float(cur["phi0_blended"])
    return b, float(cur["phi0_seed"]), float(cur["phi0_live"]), b


def record_snapshot(
    *,
    official_score: float,
    chat_id: str | None = None,
    call_type: str | None = None,
    categories: list[str] | None = None,
) -> None:
    coll = _coll(COL_SNAPSHOTS)
    if coll is None:
        return
    try:
        coll.insert_one(
            {
                "scored_at": _utcnow(),
                "official_score": float(official_score),
                "chat_id": chat_id or "",
                "call_type": call_type or "",
                "categories": categories or [],
            }
        )
    except Exception as exc:
        logger.warning(f"Failed to record calibration snapshot: {exc}")
