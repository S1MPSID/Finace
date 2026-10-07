"""
Human-validated gold evaluation set (100–200 cases).

- Sampled from V2 / adversarial pools with provenance retained.
- Labels are provisional until a human reviewer approves.
- NEVER used for training or hyperparameter tuning.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from ml_validation.paths import DATASET_DIR, REVIEW_DIR, ensure_dirs
from ml_validation.schema import ComplianceCase, ReviewStatus


def sample_gold_candidates(
    pools: list[list[ComplianceCase]],
    *,
    n: int = 150,
    seed: int = 20261007,
) -> list[ComplianceCase]:
    """Stratified-ish sample across domains and statuses; dedupe by family."""
    rng = random.Random(seed)
    flat: list[ComplianceCase] = []
    seen_fam: set[str] = set()
    for pool in pools:
        for c in pool:
            if c.family_id in seen_fam:
                continue
            seen_fam.add(c.family_id)
            flat.append(c)
    rng.shuffle(flat)

    by_key: dict[tuple[str, str], list[ComplianceCase]] = defaultdict(list)
    for c in flat:
        by_key[(c.domain, c.expected_status)].append(c)

    picked: list[ComplianceCase] = []
    keys = sorted(by_key.keys())
    # Round-robin until n
    while len(picked) < n and any(by_key[k] for k in keys):
        for k in keys:
            if len(picked) >= n:
                break
            if by_key[k]:
                picked.append(by_key[k].pop())

    created = datetime.now(timezone.utc).isoformat()
    out: list[ComplianceCase] = []
    for c in picked:
        # New case ids under gold namespace; keep provenance
        digest = hashlib.sha1(f"gold|{c.case_id}".encode()).hexdigest()[:16]
        payload = c.to_dict()
        payload.update(
            {
                "case_id": f"GOLD-{digest}",
                "family_id": f"GOLDFAM-{c.family_id}",
                "split": "gold",
                "review_status": ReviewStatus.NEEDS_REVIEW.value,
                "review_notes": (
                    "Pending independent human/mentor verification. "
                    "Template label is provisional — not automatic ground truth."
                ),
                "quality_flags": list(
                    dict.fromkeys((c.quality_flags or []) + ["gold_candidate", "not_for_training"])
                ),
                "created_at": created,
            }
        )
        out.append(ComplianceCase.from_dict(payload))

    logger.info(f"Gold candidates sampled: {len(out)}")
    return out


def export_gold_review_pack(
    cases: list[ComplianceCase],
    *,
    stem: str = "gold_set_v1",
) -> dict[str, Path]:
    """
    Export JSONL + CSV for human review.

    Reviewer fills: reviewer_status (approve/reject/needs_review), reviewer_notes,
    and may override expected_status / expected_risk if they disagree (override columns).
    """
    ensure_dirs()
    gold_dir = REVIEW_DIR / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = DATASET_DIR / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

    csv_path = gold_dir / f"{stem}_review.csv"
    fields = [
        "case_id",
        "requirement_id",
        "domain",
        "regulatory_document",
        "regulatory_section",
        "source_chunk_id",
        "compliance_requirement",
        "scenario",
        "expected_status",
        "expected_risk",
        "severity",
        "scenario_type",
        "reviewer_status",
        "reviewer_notes",
        "override_expected_status",
        "override_expected_risk",
        "reviewer_name",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in cases:
            w.writerow(
                {
                    "case_id": c.case_id,
                    "requirement_id": c.requirement_id,
                    "domain": c.domain,
                    "regulatory_document": c.regulatory_document,
                    "regulatory_section": c.regulatory_section,
                    "source_chunk_id": c.source_chunk_id,
                    "compliance_requirement": c.compliance_requirement,
                    "scenario": c.scenario,
                    "expected_status": c.expected_status,
                    "expected_risk": c.expected_risk,
                    "severity": c.severity,
                    "scenario_type": c.scenario_type,
                    "reviewer_status": "needs_review",
                    "reviewer_notes": "",
                    "override_expected_status": "",
                    "override_expected_risk": "",
                    "reviewer_name": "",
                }
            )

    guide = gold_dir / f"{stem}_REVIEW_GUIDE.md"
    guide.write_text(
        f"""# Gold set review guide (`{stem}`)

## Purpose
Independent human/mentor/compliance verification of provisional template labels.
This set must **never** be used for training or hyperparameter tuning.

## Files
- Cases: `{jsonl_path}`
- Review spreadsheet: `{csv_path}`

## How to review
1. Read `scenario` and `compliance_requirement` (plus document/section/chunk id).
2. Decide if the expected status/risk is reasonable for the scenario relative to that requirement.
3. Set `reviewer_status` to `approve`, `reject`, or `needs_review`.
4. Optionally set `override_expected_status` / `override_expected_risk` if you disagree.
5. Add `reviewer_notes` and `reviewer_name`.
6. Import with:
   `python -m ml_validation.cli import-gold-review --decisions <path> --stem {stem}`

## Rules
- Do not invent regulatory text.
- If the scenario is ambiguous relative to the cited requirement, use `needs_review`.
- Reject cases with broken provenance (wrong chunk / hallucinated obligation).
""",
        encoding="utf-8",
    )

    meta = {
        "stem": stem,
        "n": len(cases),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "not_for_training": True,
        "review_status": "pending_human_review",
        "jsonl": str(jsonl_path),
        "csv": str(csv_path),
        "guide": str(guide),
    }
    meta_path = DATASET_DIR / f"{stem}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"jsonl": jsonl_path, "csv": csv_path, "guide": guide, "meta": meta_path}


def import_gold_review(
    csv_path: Path,
    *,
    stem: str = "gold_set_v1",
) -> list[ComplianceCase]:
    """Apply reviewer CSV decisions onto the gold JSONL."""
    from ml_validation.dataset.generate import load_cases, save_cases

    jsonl_path = DATASET_DIR / f"{stem}.jsonl"
    cases = {c.case_id: c for c in load_cases(jsonl_path)}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("case_id") or ""
            c = cases.get(cid)
            if not c:
                continue
            status = (row.get("reviewer_status") or "").strip().lower()
            if status in {"approve", "approved"}:
                c.review_status = ReviewStatus.APPROVED.value
            elif status in {"reject", "rejected"}:
                c.review_status = ReviewStatus.REJECTED.value
            else:
                c.review_status = ReviewStatus.NEEDS_REVIEW.value
            c.review_notes = row.get("reviewer_notes") or c.review_notes
            if row.get("override_expected_status"):
                c.expected_status = row["override_expected_status"].strip().upper()
            if row.get("override_expected_risk"):
                c.expected_risk = row["override_expected_risk"].strip().upper()
            if row.get("reviewer_name"):
                c.quality_flags = list(
                    dict.fromkeys(
                        (c.quality_flags or []) + [f"reviewed_by:{row['reviewer_name']}"]
                    )
                )

    updated = list(cases.values())
    save_cases(updated, stem=stem)
    approved = sum(1 for c in updated if c.review_status == ReviewStatus.APPROVED.value)
    logger.info(f"Gold import: {approved}/{len(updated)} approved")
    return updated


def approved_gold(cases: list[ComplianceCase]) -> list[ComplianceCase]:
    return [c for c in cases if c.review_status == ReviewStatus.APPROVED.value]
