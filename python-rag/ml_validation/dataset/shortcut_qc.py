"""
Detect lexical / template shortcuts that inflate ML accuracy.

Produces a dataset-quality report with keyword↔label correlations.
Does not invent fixes — flags problems for review.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ml_validation.paths import REPORTS_DIR, ensure_dirs
from ml_validation.requirement_bank.quality import normalize_for_id
from ml_validation.schema import ComplianceCase

# Phrases historically correlated with V1 labels
SHORTCUT_PHRASES: list[tuple[str, str]] = [
    (r"\bwithout\s+kyc\b", "without_kyc"),
    (r"\bno\s+kyc\b", "no_kyc"),
    (r"\bskip\s+kyc\b", "skip_kyc"),
    (r"\bout\s+of\s+scope\b", "out_of_scope"),
    (r"\bdoes\s+not\s+apply\b", "does_not_apply"),
    (r"\bpilot\b", "pilot"),
    (r"\bwithout\b", "without"),
    (r"\bdo\s+not\s+(?:currently\s+)?implement\b", "do_not_implement"),
    (r"\bno\s+grievance\b", "no_grievance"),
    (r"\bno\s+compensating\s+control\b", "no_compensating"),
    (r"\bunrelated\b", "unrelated"),
    (r"\bintentionally\s+skip\b", "intentionally_skip"),
]

RISK_VOCAB = [
    "kyc",
    "aml",
    "violation",
    "risk",
    "incomplete",
    "grievance",
    "non-compliant",
    "non compliant",
    "missing",
]


def _phi_correlation(present: list[bool], positive: list[bool]) -> float:
    """Matthews-like binary association in [-1, 1] via phi coefficient."""
    n = len(present)
    if n == 0:
        return 0.0
    tp = sum(1 for p, y in zip(present, positive) if p and y)
    fp = sum(1 for p, y in zip(present, positive) if p and not y)
    fn = sum(1 for p, y in zip(present, positive) if (not p) and y)
    tn = sum(1 for p, y in zip(present, positive) if (not p) and not y)
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denom == 0:
        return 0.0
    return (tp * tn - fp * fn) / denom


def _token_jaccard(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z0-9]{3,}", (a or "").lower()))
    tb = set(re.findall(r"[a-z0-9]{3,}", (b or "").lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def run_shortcut_qc(cases: list[ComplianceCase]) -> dict[str, Any]:
    n = len(cases)
    phrase_hits: dict[str, Counter[str]] = defaultdict(Counter)
    phrase_rates: dict[str, dict[str, float]] = {}
    flagged: list[dict[str, Any]] = []
    flag_counts: Counter[str] = Counter()

    # 1) Shortcut phrase presence by label
    for name_pat, name in SHORTCUT_PHRASES:
        pat = re.compile(name_pat, re.I)
        present = []
        labels_nc = []
        for c in cases:
            hit = bool(pat.search(c.scenario or ""))
            present.append(hit)
            labels_nc.append(c.expected_status == "NON_COMPLIANT")
            if hit:
                phrase_hits[name][c.expected_status] += 1
        phi = _phi_correlation(present, labels_nc)
        rate = sum(present) / max(n, 1)
        phrase_rates[name] = {
            "presence_rate": round(rate, 4),
            "phi_vs_non_compliant": round(phi, 4),
            "by_status": dict(phrase_hits[name]),
            "suspicious": abs(phi) >= 0.35 and rate >= 0.05,
        }
        if phrase_rates[name]["suspicious"]:
            flag_counts["suspicious_phrase_label_correlation"] += 1

    # 2) Regulatory wording copied into scenario
    copied = 0
    for c in cases:
        req = " ".join((c.compliance_requirement or "").split())
        if len(req) >= 60 and req[:60].lower() in (c.scenario or "").lower():
            copied += 1
            flag_counts["regulatory_wording_copied"] += 1
            flagged.append(
                {
                    "case_id": c.case_id,
                    "flag": "regulatory_wording_copied",
                    "requirement_id": c.requirement_id,
                }
            )
        elif _token_jaccard(req, c.scenario or "") >= 0.55 and len(req) > 80:
            flag_counts["high_requirement_overlap"] += 1
            c.quality_flags = list(
                dict.fromkeys((c.quality_flags or []) + ["high_requirement_overlap"])
            )

    # 3) Risk vocabulary balanced across classes?
    vocab_balance: dict[str, dict[str, float]] = {}
    for term in RISK_VOCAB:
        pat = re.compile(rf"\b{re.escape(term)}\b", re.I)
        by_status: Counter[str] = Counter()
        for c in cases:
            if pat.search(c.scenario or ""):
                by_status[c.expected_status] += 1
        total_hits = sum(by_status.values()) or 1
        vocab_balance[term] = {
            "hits": int(sum(by_status.values())),
            "share_by_status": {k: round(v / total_hits, 4) for k, v in by_status.items()},
        }

    # 4) Near-identical scenarios (normalized)
    buckets: dict[str, list[str]] = defaultdict(list)
    for c in cases:
        buckets[normalize_for_id(c.scenario)[:48]].append(c.case_id)
    near_groups = {k: v for k, v in buckets.items() if len(v) > 1}

    # 5) Template skeletons differing only by label (same normalized without status words)
    skeleton_map: dict[str, set[str]] = defaultdict(set)
    for c in cases:
        sk = normalize_for_id(
            re.sub(
                r"\b(compliant|non.?compliant|partial|missing|implement|gap)\b",
                "",
                c.scenario or "",
                flags=re.I,
            )
        )[:64]
        skeleton_map[sk].add(c.expected_status)
    label_only_templates = sum(1 for statuses in skeleton_map.values() if len(statuses) > 1)

    suspicious_phrases = {
        k: v for k, v in phrase_rates.items() if v.get("suspicious")
    }

    report = {
        "n": n,
        "shortcut_phrase_rates": phrase_rates,
        "suspicious_phrase_count": len(suspicious_phrases),
        "suspicious_phrases": suspicious_phrases,
        "regulatory_wording_copied_count": copied,
        "high_requirement_overlap_count": flag_counts.get("high_requirement_overlap", 0),
        "risk_vocab_class_balance": vocab_balance,
        "near_identical_scenario_groups": len(near_groups),
        "near_identical_examples": list(near_groups.items())[:15],
        "skeletons_spanning_multiple_labels": label_only_templates,
        "flag_counts": dict(flag_counts),
        "flagged_sample": flagged[:40],
        "hard_benchmark_ready": (
            len(suspicious_phrases) <= 2
            and copied == 0
            and flag_counts.get("high_requirement_overlap", 0) < max(20, n * 0.02)
        ),
        "notes": [
            "suspicious = |phi(phrase, NON_COMPLIANT)| >= 0.35 with presence_rate >= 5%.",
            "V2 aims to minimize suspicious phrases and zero regulatory copy into scenarios.",
            "Near-identical groups may include intentional paraphrases within a family.",
        ],
    }
    return report


def save_shortcut_report(report: dict[str, Any], stem: str) -> Path:
    ensure_dirs()
    path = REPORTS_DIR / f"shortcut_qc_{stem}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
