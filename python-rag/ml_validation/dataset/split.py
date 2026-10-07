"""
Leakage-aware dataset splits.

- Related paraphrase families stay in the same split.
- An additional unseen-wording set holds out entire requirements (not just paraphrases).
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from ml_validation.paths import SPLITS_DIR, ensure_dirs
from ml_validation.schema import ComplianceCase


def _stable_bucket(key: str, mod: int = 100) -> int:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % mod


def split_cases(
    cases: list[ComplianceCase],
    *,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 20261007,
    unseen_requirement_ratio: float = 0.10,
) -> dict[str, list[ComplianceCase]]:
    """
    Returns dict with keys: train, val, test, unseen_wording.

    1) Hold out a fraction of *requirement_ids* entirely → unseen_wording (generalization).
    2) Remaining cases split by *family_id* into train/val/test (no family leakage).
    """
    by_req: dict[str, list[ComplianceCase]] = defaultdict(list)
    for c in cases:
        by_req[c.requirement_id].append(c)

    req_ids = sorted(by_req.keys())
    rng = random.Random(seed)
    rng.shuffle(req_ids)

    n_unseen = max(1, int(len(req_ids) * unseen_requirement_ratio)) if req_ids else 0
    unseen_reqs = set(req_ids[:n_unseen])
    remain_reqs = req_ids[n_unseen:]

    unseen_wording = [c for rid in unseen_reqs for c in by_req[rid]]

    # Family split on remaining
    families: dict[str, list[ComplianceCase]] = defaultdict(list)
    for rid in remain_reqs:
        for c in by_req[rid]:
            families[c.family_id or c.case_id].append(c)

    fam_ids = sorted(families.keys())
    rng.shuffle(fam_ids)

    n = len(fam_ids)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train_f = set(fam_ids[:n_train])
    val_f = set(fam_ids[n_train : n_train + n_val])
    test_f = set(fam_ids[n_train + n_val :])

    out: dict[str, list[ComplianceCase]] = {
        "train": [],
        "val": [],
        "test": [],
        "unseen_wording": unseen_wording,
    }
    for fid, rows in families.items():
        if fid in train_f:
            split = "train"
        elif fid in val_f:
            split = "val"
        else:
            split = "test"
        for c in rows:
            c.split = split
            out[split].append(c)
    for c in unseen_wording:
        c.split = "unseen_wording"

    return out


def save_splits(splits: dict[str, list[ComplianceCase]], stem: str = "compliance_benchmark") -> Path:
    ensure_dirs()
    path = SPLITS_DIR / f"{stem}_splits.json"
    payload: dict[str, Any] = {
        "counts": {k: len(v) for k, v in splits.items()},
        "ids": {k: [c.case_id for c in v] for k, v in splits.items()},
        "method": "family_aware + held_out_requirements_for_unseen_wording",
        "leakage_prevention": [
            "paraphrase families never cross splits",
            "unseen_wording holds out entire requirement_ids",
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Also write per-split JSONL for convenience
    for name, rows in splits.items():
        p = SPLITS_DIR / f"{stem}_{name}.jsonl"
        with p.open("w", encoding="utf-8") as f:
            for c in rows:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
    return path


def leakage_report(splits: dict[str, list[ComplianceCase]]) -> dict[str, Any]:
    fam: dict[str, set[str]] = defaultdict(set)
    req: dict[str, set[str]] = defaultdict(set)
    for name, rows in splits.items():
        for c in rows:
            fam[c.family_id].add(name)
            req[c.requirement_id].add(name)

    family_leaks = {k: sorted(v) for k, v in fam.items() if len(v) > 1}
    # requirement may appear in train/val/test (different families) — that is OK.
    # requirement must NOT appear in both unseen_wording and another split.
    req_unseen_leaks = {
        k: sorted(v)
        for k, v in req.items()
        if "unseen_wording" in v and len(v) > 1
    }
    return {
        "family_cross_split_count": len(family_leaks),
        "requirement_unseen_leak_count": len(req_unseen_leaks),
        "family_leak_examples": list(family_leaks.items())[:10],
        "requirement_unseen_leak_examples": list(req_unseen_leaks.items())[:10],
        "ok": len(family_leaks) == 0 and len(req_unseen_leaks) == 0,
    }
