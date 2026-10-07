"""
Assemble the V2 final evaluation report answering A–H.

Does not fabricate metrics — reads JSON artifacts produced by the pipeline.
Marks missing / unreviewed sections as pending.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml_validation.paths import REPORTS_DIR, ensure_dirs


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _metric_block(ev: dict[str, Any] | None) -> dict[str, Any]:
    if not ev:
        return {"status": "pending", "reason": "evaluation artifact missing"}
    return {
        "status": "measured",
        "n": ev.get("n"),
        "status_accuracy": ev.get("status", {}).get("accuracy"),
        "status_macro_f1": ev.get("status", {}).get("macro_f1"),
        "status_ece": ev.get("status", {}).get("ece"),
        "status_roc_auc": ev.get("status", {}).get("roc_auc_macro_ovr"),
        "risk_accuracy": ev.get("risk", {}).get("accuracy"),
        "risk_macro_f1": ev.get("risk", {}).get("macro_f1"),
        "risk_ece": ev.get("risk", {}).get("ece"),
        "per_domain_status_accuracy": ev.get("per_domain_status_accuracy"),
        "per_difficulty_status_accuracy": ev.get("per_difficulty_status_accuracy"),
        "per_risk_status_accuracy": ev.get("per_risk_status_accuracy"),
    }


def build_final_report(
    *,
    v1_stem: str = "compliance_benchmark_v1",
    v2_stem: str = "compliance_benchmark_v2",
    adv_stem: str = "adversarial_challenge_v1",
    gold_stem: str = "gold_human_v1",
) -> dict[str, Any]:
    v1_test = _load(REPORTS_DIR / f"evaluation_{v1_stem}_test.json")
    v1_unseen = _load(REPORTS_DIR / f"evaluation_{v1_stem}_unseen_wording.json")
    v2_test = _load(REPORTS_DIR / f"evaluation_{v2_stem}_test.json")
    v2_unseen = _load(REPORTS_DIR / f"evaluation_{v2_stem}_unseen_wording.json")
    adv_ev = _load(REPORTS_DIR / f"evaluation_{adv_stem}_all.json")
    gold_ev = _load(REPORTS_DIR / f"evaluation_{gold_stem}_approved.json")
    gold_meta = _load(
        Path(__file__).resolve().parents[1] / "data" / "datasets" / f"{gold_stem}_meta.json"
    )
    shortcut_v1 = _load(REPORTS_DIR / f"shortcut_qc_{v1_stem}.json")
    shortcut_v2 = _load(REPORTS_DIR / f"shortcut_qc_{v2_stem}.json")
    importance = _load(REPORTS_DIR / "feature_importance_v2.json")
    compare_v2 = _load(REPORTS_DIR / f"ml_vs_finace_{v2_stem}_test.json")

    v1_acc = (v1_test or {}).get("status", {}).get("accuracy")
    v2_acc = (v2_test or {}).get("status", {}).get("accuracy")
    drop = None
    if isinstance(v1_acc, (int, float)) and isinstance(v2_acc, (int, float)):
        drop = round(float(v1_acc) - float(v2_acc), 4)

    gold_review_status = "pending"
    if gold_meta:
        gold_review_status = gold_meta.get("review_status", "pending")
    if gold_ev and gold_ev.get("n", 0) > 0:
        gold_review_status = "measured_on_approved_subset"
    else:
        gold_ev_block: dict[str, Any] = {
            "status": "pending",
            "reason": "No human-approved gold cases yet. Export review CSV and import decisions.",
        }

    if gold_ev and gold_ev.get("n", 0) > 0:
        gold_ev_block = _metric_block(gold_ev)

    answers = {
        "A_still_strong_after_removing_shortcuts": {
            "answer": (
                "measured"
                if v2_acc is not None
                else "pending"
            ),
            "v2_status_accuracy": v2_acc,
            "v2_shortcut_hard_benchmark_ready": (shortcut_v2 or {}).get("hard_benchmark_ready"),
            "v2_suspicious_phrases": (shortcut_v2 or {}).get("suspicious_phrase_count"),
            "interpretation": (
                "Compare V2 accuracy to V1; if V2 remains near-perfect, inspect feature importance "
                "for residual shortcuts. If V2 drops, that is expected for a harder set."
            ),
        },
        "B_drop_v1_to_v2": {
            "v1_status_accuracy": v1_acc,
            "v2_status_accuracy": v2_acc,
            "absolute_drop": drop,
            "status": "measured" if drop is not None else "pending",
        },
        "C_unseen_requirements": {
            "v1_unseen": _metric_block(v1_unseen),
            "v2_unseen": _metric_block(v2_unseen),
        },
        "D_adversarial": _metric_block(adv_ev),
        "E_human_validated_gold": {
            "review_status": gold_review_status,
            "metrics": gold_ev_block,
        },
        "F_feature_drivers": importance
        if importance
        else {"status": "pending", "reason": "Run feature-importance"},
        "G_ml_vs_rules_disagreement": (compare_v2 or {}).get("risk_disagreement")
        or {"status": "pending"},
        "H_limitations": [
            "Template labels are not legal ground truth.",
            "Gold set remains pending until human/mentor approval.",
            "Gemini Finace assessment not invoked in compare (cost); rules used as Finace deterministic baseline.",
            "V2 reduces lexical shortcuts but residual structural cues remain (e.g. scenario_len_norm dominance).",
            "High V1 scores were development-benchmark artefacts from shortcut-prone templates.",
            "Adversarial set shows larger drops — treat V2 test accuracy as still partly template-separable.",
            "ML vs rules disagreement is expected; categories are heuristic, not correctness verdicts.",
            "ML never overrides RAG evidence, rules, Gemini, citations, or compliance score.",
        ],
    }

    report = {
        "title": "Finace ML Validation — Hard Benchmark V2 Final Report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture": {
            "regulations": "SOURCE OF TRUTH",
            "rag": "REGULATORY EVIDENCE",
            "rules": "DETERMINISTIC CONTROLS",
            "ml": "INDEPENDENT LEARNED PREDICTION",
            "gemini": "CONTEXTUAL REASONING",
            "xai": "MODEL/SURROGATE EXPLANATION",
        },
        "sets": {
            "v1": _metric_block(v1_test),
            "v2": _metric_block(v2_test),
            "v2_unseen_requirements": _metric_block(v2_unseen),
            "adversarial": _metric_block(adv_ev),
            "gold": gold_ev_block,
        },
        "shortcut_qc": {"v1": shortcut_v1, "v2": shortcut_v2},
        "answers": answers,
        "artifacts_dir": str(REPORTS_DIR),
    }
    return report


def save_final_report(report: dict[str, Any], name: str = "FINAL_REPORT_V2.json") -> Path:
    ensure_dirs()
    path = REPORTS_DIR / name
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    md = REPORTS_DIR / "FINAL_REPORT_V2.md"
    a = report["answers"]
    lines = [
        "# Finace ML Validation — Hard Benchmark V2 Final Report",
        "",
        f"Generated: {report['created_at']}",
        "",
        "## Architecture (unchanged)",
        "",
        "- Regulatory Documents = SOURCE OF TRUTH",
        "- RAG = REGULATORY EVIDENCE",
        "- Rules = DETERMINISTIC CONTROLS",
        "- ML = INDEPENDENT LEARNED PREDICTION",
        "- Gemini = CONTEXTUAL REASONING",
        "- XAI = MODEL/SURROGATE EXPLANATION",
        "",
        "## A. Performance after removing lexical shortcuts?",
        "",
        f"- V2 status accuracy: `{a['A_still_strong_after_removing_shortcuts'].get('v2_status_accuracy')}`",
        f"- V2 hard_benchmark_ready (shortcut QC): `{a['A_still_strong_after_removing_shortcuts'].get('v2_shortcut_hard_benchmark_ready')}`",
        f"- Suspicious phrase count: `{a['A_still_strong_after_removing_shortcuts'].get('v2_suspicious_phrases')}`",
        "",
        "## B. Drop V1 → V2",
        "",
        f"- V1: `{a['B_drop_v1_to_v2'].get('v1_status_accuracy')}`",
        f"- V2: `{a['B_drop_v1_to_v2'].get('v2_status_accuracy')}`",
        f"- Absolute drop: `{a['B_drop_v1_to_v2'].get('absolute_drop')}`",
        "",
        "## C. Unseen requirements",
        "",
        f"- V1 unseen: `{a['C_unseen_requirements']['v1_unseen']}`",
        f"- V2 unseen: `{a['C_unseen_requirements']['v2_unseen']}`",
        "",
        "## D. Adversarial",
        "",
        f"`{a['D_adversarial']}`",
        "",
        "## E. Human-validated gold",
        "",
        f"- Review status: `{a['E_human_validated_gold'].get('review_status')}`",
        f"- Metrics: `{a['E_human_validated_gold'].get('metrics')}`",
        "",
        "## F. Feature drivers",
        "",
        "See `feature_importance_v2.json`.",
        "",
        "## G. ML vs Rules disagreement",
        "",
        "See comparison artifact `risk_disagreement` section. Disagreement ≠ either side wrong.",
        "",
        "## H. Limitations",
        "",
    ]
    for lim in a["H_limitations"]:
        lines.append(f"- {lim}")
    lines.append("")
    lines.append(f"Full JSON: `{path}`")
    md.write_text("\n".join(lines), encoding="utf-8")
    return path
