"""
CLI for the Finace ML validation layer.

  extract-bank → validate-bank → generate-dataset → qc-dataset
  → split-dataset → train → evaluate → compare
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loguru import logger

from ml_validation.paths import (
    BANK_JSONL,
    BANK_SUMMARY,
    DATASET_DIR,
    REPORTS_DIR,
    SPLITS_DIR,
    VALIDATE_REPORT,
    ensure_dirs,
)
from ml_validation.requirement_bank.eligibility import filter_eligible
from ml_validation.requirement_bank.extract import extract_requirements, summarize_bank
from ml_validation.requirement_bank.review import (
    apply_decisions,
    export_review_sample,
    record_decision,
)
from ml_validation.requirement_bank.store import (
    load_bank,
    save_bank,
    save_review_queue,
)
from ml_validation.requirement_bank.validate import validate_bank
from ml_validation.schema import ReviewStatus


def cmd_extract_bank(args: argparse.Namespace) -> int:
    ensure_dirs()
    logger.info(
        f"Extracting requirements from Mongo corpus "
        f"(limit={args.limit}, regulator={args.regulator}, status={args.status})"
    )
    reqs = extract_requirements(
        limit=args.limit,
        regulator=args.regulator,
        status=args.status,
        min_confidence=args.min_confidence,
        auto_approve_threshold=args.auto_approve,
    )
    path = save_bank(
        reqs,
        meta_extra={
            "extract_limit": args.limit,
            "regulator_filter": args.regulator,
            "status_filter": args.status,
            "min_confidence": args.min_confidence,
            "auto_approve_threshold": args.auto_approve,
        },
    )
    queue_path = save_review_queue(reqs)
    summary = summarize_bank(reqs)
    eligible_n = len(filter_eligible(reqs))
    print(json.dumps({**summary, "eligible_for_dataset": eligible_n}, indent=2))
    print(f"\nBank written -> {path}")
    print(f"Review queue -> {queue_path}")
    print(f"Eligible for dataset generation: {eligible_n}")
    return 0


def cmd_validate_bank(args: argparse.Namespace) -> int:
    ensure_dirs()
    reqs = load_bank(Path(args.path) if args.path else None)
    if not reqs:
        logger.error(f"No bank found at {args.path or BANK_JSONL}. Run extract-bank first.")
        return 1
    report = validate_bank(reqs, verify_mongo=not args.skip_mongo)
    save_bank(reqs, meta_extra={"last_validation": report})
    save_review_queue(reqs)
    VALIDATE_REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "issues_sample"}, indent=2, default=str))
    print(f"\nFull validation report -> {VALIDATE_REPORT}")
    print(f"Eligible for dataset: {len(filter_eligible(reqs))}")
    return 0


def cmd_show_bank(args: argparse.Namespace) -> int:
    reqs = load_bank()
    if args.approved_only:
        reqs = [r for r in reqs if r.review_status == ReviewStatus.APPROVED.value]
    if args.eligible_only:
        reqs = filter_eligible(reqs)
    if args.domain:
        reqs = [r for r in reqs if r.domain == args.domain]
    print(f"Showing {min(args.n, len(reqs))} of {len(reqs)} requirements\n")
    for r in reqs[: args.n]:
        print("=" * 72)
        print(f"ID:       {r.requirement_id}")
        print(f"Domain:   {r.domain} | Regulator: {r.regulator} | Status: {r.review_status}")
        print(f"Document: {r.document}")
        print(f"Section:  {r.section}")
        print(f"Chunk:    {r.source_chunk_id}")
        print(f"Conf:     {r.confidence} | flags: {r.quality_flags}")
        print(f"Requirement:\n  {r.requirement}")
    if BANK_SUMMARY.exists():
        print("\n--- bank_summary.json ---")
        print(BANK_SUMMARY.read_text(encoding="utf-8"))
    return 0


def cmd_review_sample(args: argparse.Namespace) -> int:
    reqs = load_bank()
    sample = export_review_sample(reqs, n=args.n, only_needs_review=not args.all)
    print(json.dumps(sample, indent=2, ensure_ascii=False))
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    decision = record_decision(
        args.id,
        args.action,
        reviewer=args.reviewer,
        notes=args.notes or "",
    )
    print(json.dumps(decision, indent=2))
    print("Run `python -m ml_validation.cli apply-review` to merge into the bank.")
    return 0


def cmd_apply_review(args: argparse.Namespace) -> int:
    reqs = load_bank()
    if not reqs:
        logger.error("No bank loaded.")
        return 1
    apply_decisions(reqs)
    save_bank(reqs, meta_extra={"review_applied": True})
    save_review_queue(reqs)
    print(json.dumps(summarize_bank(reqs), indent=2))
    return 0


def cmd_generate_dataset(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import generate_cases, save_cases, summarize_cases
    from ml_validation.dataset.generate_v2 import generate_cases_v2

    reqs = load_bank()
    eligible = filter_eligible(reqs)
    if len(eligible) < 10:
        logger.error(
            f"Only {len(eligible)} eligible requirements. "
            "Run full extract-bank / approve more rows first."
        )
        return 1
    version = getattr(args, "version", "v1")
    if version == "v2":
        cases = generate_cases_v2(
            reqs,
            paraphrases_per_template=args.paraphrases,
            max_requirements=args.max_requirements,
            seed_tag="v2",
        )
    else:
        cases = generate_cases(
            reqs,
            paraphrases_per_template=args.paraphrases,
            max_requirements=args.max_requirements,
            seed_tag=args.stem,
        )
    path = save_cases(cases, stem=args.stem)
    print(json.dumps(summarize_cases(cases), indent=2))
    print(f"\nDataset written -> {path}")
    return 0


def cmd_qc_dataset(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import load_cases
    from ml_validation.dataset.qc import run_dataset_qc
    from ml_validation.dataset.shortcut_qc import run_shortcut_qc, save_shortcut_report

    path = Path(args.path) if args.path else DATASET_DIR / f"{args.stem}.jsonl"
    cases = load_cases(path)
    chunk_texts = None
    if not args.skip_mongo:
        from db.mongo import chunks

        ids = list({c.source_chunk_id for c in cases})
        chunk_texts = {}
        for i in range(0, len(ids), 500):
            for doc in chunks().find(
                {"chunk_id": {"$in": ids[i : i + 500]}}, {"chunk_id": 1, "text": 1}
            ):
                chunk_texts[doc["chunk_id"]] = doc.get("text") or ""
    report = run_dataset_qc(cases, chunk_texts=chunk_texts)
    out = REPORTS_DIR / f"dataset_qc_{args.stem}.json"
    ensure_dirs()
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    shortcut = run_shortcut_qc(cases)
    spath = save_shortcut_report(shortcut, args.stem)
    print(json.dumps({k: report[k] for k in report if k != "issues_sample"}, indent=2))
    print(
        json.dumps(
            {
                "shortcut_suspicious_phrases": shortcut.get("suspicious_phrase_count"),
                "hard_benchmark_ready": shortcut.get("hard_benchmark_ready"),
                "regulatory_wording_copied_count": shortcut.get(
                    "regulatory_wording_copied_count"
                ),
            },
            indent=2,
        )
    )
    print(f"\nQC report -> {out}")
    print(f"Shortcut QC -> {spath}")
    return 0


def cmd_split_dataset(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import load_cases, save_cases
    from ml_validation.dataset.split import leakage_report, save_splits, split_cases

    path = DATASET_DIR / f"{args.stem}.jsonl"
    cases = load_cases(path)
    splits = split_cases(
        cases,
        seed=args.seed,
        unseen_requirement_ratio=args.unseen_ratio,
    )
    split_path = save_splits(splits, stem=args.stem)
    # Persist split field back into main dataset
    by_id = {c.case_id: c for rows in splits.values() for c in rows}
    for c in cases:
        if c.case_id in by_id:
            c.split = by_id[c.case_id].split
    save_cases(cases, stem=args.stem)
    leak = leakage_report(splits)
    (REPORTS_DIR / f"split_leakage_{args.stem}.json").write_text(
        json.dumps(leak, indent=2), encoding="utf-8"
    )
    print(json.dumps({"counts": {k: len(v) for k, v in splits.items()}, "leakage": leak}, indent=2))
    print(f"\nSplits -> {split_path}")
    return 0 if leak.get("ok") else 1


def cmd_train(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import load_cases
    from ml_validation.model.train import train_models
    from ml_validation.paths import SPLITS_DIR as SD

    train_path = SD / f"{args.stem}_train.jsonl"
    val_path = SD / f"{args.stem}_val.jsonl"
    if not train_path.exists():
        logger.error("Split files missing. Run split-dataset first.")
        return 1
    train = load_cases(train_path)
    val = load_cases(val_path)
    # Drop ambiguous from supervised training labels if requested
    if args.drop_ambiguous:
        train = [c for c in train if c.expected_status != "AMBIGUOUS"]
        val = [c for c in val if c.expected_status != "AMBIGUOUS"]
    meta = train_models(train, val, seed=args.seed, tag=getattr(args, "tag", args.stem))
    print(json.dumps(meta, indent=2))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import load_cases
    from ml_validation.dataset.gold import approved_gold
    from ml_validation.model.evaluate import evaluate_split, save_evaluation
    from ml_validation.model.train import latest_model_dir
    from ml_validation.paths import SPLITS_DIR

    if getattr(args, "path", None):
        path = Path(args.path)
        split_name = args.split or "custom"
    else:
        split_name = args.split
        path = SPLITS_DIR / f"{args.stem}_{split_name}.jsonl"
        if not path.exists():
            alt = DATASET_DIR / f"{args.stem}.jsonl"
            if alt.exists() and split_name in {"all", "full", "dataset", "approved"}:
                path = alt

    cases = load_cases(path)
    if split_name == "approved":
        cases = approved_gold(cases)
        if not cases:
            print(
                json.dumps(
                    {
                        "status": "pending",
                        "reason": "No human-approved gold cases. Complete review CSV first.",
                        "n": 0,
                    },
                    indent=2,
                )
            )
            ensure_dirs()
            stub = {
                "split": "approved",
                "n": 0,
                "status": {"accuracy": None},
                "risk": {},
                "pending": True,
            }
            (REPORTS_DIR / f"evaluation_{args.stem}_approved.json").write_text(
                json.dumps(stub, indent=2), encoding="utf-8"
            )
            return 0

    if args.drop_ambiguous:
        cases = [c for c in cases if c.expected_status != "AMBIGUOUS"]
    model_dir = Path(args.model_dir) if getattr(args, "model_dir", None) else latest_model_dir()
    report = evaluate_split(cases, model_dir=model_dir, split_name=split_name)
    out = save_evaluation(report, stem=f"evaluation_{args.stem}")
    compact = {
        "split": report["split"],
        "n": report["n"],
        "model_dir": report.get("model_dir"),
        "status_accuracy": report["status"]["accuracy"],
        "status_macro_f1": report["status"]["macro_f1"],
        "status_ece": report["status"]["ece"],
        "status_roc_auc": report["status"]["roc_auc_macro_ovr"],
        "risk_accuracy": report["risk"]["accuracy"],
        "risk_macro_f1": report["risk"]["macro_f1"],
        "risk_ece": report["risk"]["ece"],
        "per_domain_status_accuracy": report["per_domain_status_accuracy"],
        "per_difficulty_status_accuracy": report["per_difficulty_status_accuracy"],
    }
    print(json.dumps(compact, indent=2))
    print(f"\nFull evaluation -> {out}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import load_cases
    from ml_validation.compare import compare_cases, save_comparison
    from ml_validation.paths import SPLITS_DIR

    path = SPLITS_DIR / f"{args.stem}_{args.split}.jsonl"
    if not path.exists():
        path = DATASET_DIR / f"{args.stem}.jsonl"
    cases = load_cases(path)
    report = compare_cases(cases, limit=args.limit)
    out = save_comparison(report, stem=f"ml_vs_finace_{args.stem}_{args.split}")
    print(
        json.dumps(
            {
                k: report[k]
                for k in report
                if k
                not in {
                    "details_sample",
                    "difficult_or_disagree_sample",
                    "risk_disagreement",
                }
            },
            indent=2,
        )
    )
    print(json.dumps({"risk_disagreement": report.get("risk_disagreement")}, indent=2, default=str)[:4000])
    print(f"\nComparison report -> {out}")
    return 0


def cmd_build_adversarial(args: argparse.Namespace) -> int:
    from ml_validation.dataset.adversarial import build_adversarial_cases, save_adversarial
    from ml_validation.dataset.generate import summarize_cases

    reqs = load_bank()
    cases = build_adversarial_cases(
        reqs,
        max_requirements=args.max_requirements,
        variants_per_req=args.variants,
    )
    save_adversarial(cases, stem=args.stem)
    print(json.dumps(summarize_cases(cases), indent=2))
    return 0


def cmd_export_gold(args: argparse.Namespace) -> int:
    from ml_validation.dataset.generate import load_cases
    from ml_validation.dataset.gold import export_gold_review_pack, sample_gold_candidates

    pools = []
    for stem in args.pool_stems:
        p = DATASET_DIR / f"{stem}.jsonl"
        if p.exists():
            pools.append(load_cases(p))
    if not pools:
        logger.error("No pool datasets found. Generate V2 / adversarial first.")
        return 1
    cases = sample_gold_candidates(pools, n=args.n, seed=args.seed)
    paths = export_gold_review_pack(cases, stem=args.stem)
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    print("Gold labels are provisional until human review. NOT for training.")
    return 0


def cmd_import_gold_review(args: argparse.Namespace) -> int:
    from ml_validation.dataset.gold import import_gold_review
    from ml_validation.dataset.generate import summarize_cases

    decisions = Path(getattr(args, "decisions", None) or getattr(args, "csv", ""))
    cases = import_gold_review(decisions, stem=args.stem)
    print(json.dumps(summarize_cases(cases), indent=2))
    return 0


def cmd_feature_importance(args: argparse.Namespace) -> int:
    from ml_validation.model.importance import feature_importance_report, save_importance_report
    from ml_validation.model.train import latest_model_dir

    model_dir = Path(args.model_dir) if args.model_dir else latest_model_dir()
    report = feature_importance_report(model_dir)
    out = save_importance_report(report, stem=args.stem)
    print(json.dumps(report, indent=2))
    print(f"\nImportance report -> {out}")
    return 0


def cmd_final_report(args: argparse.Namespace) -> int:
    from ml_validation.report.final_report import build_final_report, save_final_report

    report = build_final_report(
        v1_stem=args.v1_stem,
        v2_stem=args.v2_stem,
        adv_stem=args.adv_stem,
        gold_stem=args.gold_stem,
    )
    path = save_final_report(report)
    print(json.dumps(report["answers"], indent=2, default=str)[:6000])
    print(f"\nFinal report -> {path}")
    print(f"Markdown -> {REPORTS_DIR / 'FINAL_REPORT_V2.md'}")
    return 0


def cmd_pipeline_v2(args: argparse.Namespace) -> int:
    """
    Hard benchmark pipeline:
    shortcut-QC V1 → generate V2 → QC/shortcut → split → train on V2
    → eval V1/V2/unseen/adversarial → gold export → compare → importance → final report
    """
    v1 = args.v1_stem
    v2 = args.v2_stem
    adv = args.adv_stem
    gold = args.gold_stem

    # Shortcut baseline + preserve V1 metrics with the V1 model (before V2 train)
    logger.info("=== V2 PIPELINE: shortcut QC on V1 ===")
    code = cmd_qc_dataset(argparse.Namespace(path=None, stem=v1, skip_mongo=True))
    if code != 0:
        return code
    for split_name in ("test", "unseen_wording"):
        logger.info(f"=== V2 PIPELINE: baseline eval V1/{split_name} (V1 model) ===")
        code = cmd_evaluate(
            argparse.Namespace(
                stem=v1,
                split=split_name,
                drop_ambiguous=True,
                path=None,
                model_dir=None,
            )
        )
        if code != 0:
            return code

    steps = [
        (
            "generate-v2",
            lambda: cmd_generate_dataset(
                argparse.Namespace(
                    paraphrases=args.paraphrases,
                    max_requirements=args.max_requirements,
                    stem=v2,
                    version="v2",
                )
            ),
        ),
        (
            "qc-v2",
            lambda: cmd_qc_dataset(argparse.Namespace(path=None, stem=v2, skip_mongo=True)),
        ),
        (
            "split-v2",
            lambda: cmd_split_dataset(
                argparse.Namespace(stem=v2, seed=args.seed, unseen_ratio=0.10)
            ),
        ),
        (
            "train-v2",
            lambda: cmd_train(
                argparse.Namespace(stem=v2, seed=args.seed, drop_ambiguous=True, tag=v2)
            ),
        ),
        (
            "eval-v2-test",
            lambda: cmd_evaluate(
                argparse.Namespace(
                    stem=v2, split="test", drop_ambiguous=True, path=None, model_dir=None
                )
            ),
        ),
        (
            "eval-v2-unseen",
            lambda: cmd_evaluate(
                argparse.Namespace(
                    stem=v2,
                    split="unseen_wording",
                    drop_ambiguous=True,
                    path=None,
                    model_dir=None,
                )
            ),
        ),
        (
            "eval-v1-transfer-under-v2-model",
            lambda: cmd_evaluate(
                argparse.Namespace(
                    stem="v1_transfer_under_v2_model",
                    split="test",
                    drop_ambiguous=True,
                    path=str(SPLITS_DIR / f"{v1}_test.jsonl"),
                    model_dir=None,
                )
            ),
        ),
        (
            "build-adversarial",
            lambda: cmd_build_adversarial(
                argparse.Namespace(
                    stem=adv, max_requirements=args.adv_max_requirements, variants=1
                )
            ),
        ),
        (
            "eval-adversarial",
            lambda: cmd_evaluate(
                argparse.Namespace(
                    stem=adv, split="all", drop_ambiguous=True, path=None, model_dir=None
                )
            ),
        ),
        (
            "export-gold",
            lambda: cmd_export_gold(
                argparse.Namespace(
                    stem=gold, n=args.gold_n, seed=args.seed, pool_stems=[v2, adv]
                )
            ),
        ),
        (
            "eval-gold-pending",
            lambda: cmd_evaluate(
                argparse.Namespace(
                    stem=gold, split="approved", drop_ambiguous=False, path=None, model_dir=None
                )
            ),
        ),
        (
            "compare-v2",
            lambda: cmd_compare(argparse.Namespace(stem=v2, split="test", limit=400)),
        ),
        (
            "feature-importance",
            lambda: cmd_feature_importance(
                argparse.Namespace(stem="feature_importance_v2", model_dir=None)
            ),
        ),
        (
            "final-report",
            lambda: cmd_final_report(
                argparse.Namespace(v1_stem=v1, v2_stem=v2, adv_stem=adv, gold_stem=gold)
            ),
        ),
    ]
    for name, fn in steps:
        logger.info(f"=== V2 PIPELINE STEP: {name} ===")
        code = fn()
        if code != 0:
            logger.error(f"V2 pipeline stopped at {name} with code {code}")
            return code
    logger.info("V2 pipeline complete.")
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run extract (optional) → generate → qc → split → train → evaluate → compare."""
    steps = []
    if args.extract:
        steps.append(
            (
                "extract-bank",
                lambda: cmd_extract_bank(
                    argparse.Namespace(
                        limit=args.limit,
                        regulator=None,
                        status="active",
                        min_confidence=0.35,
                        auto_approve=0.85,
                    )
                ),
            )
        )
        steps.append(("validate-bank", lambda: cmd_validate_bank(argparse.Namespace(path=None, skip_mongo=False))))

    steps.extend(
        [
            (
                "generate-dataset",
                lambda: cmd_generate_dataset(
                    argparse.Namespace(
                        paraphrases=args.paraphrases,
                        max_requirements=args.max_requirements,
                        stem=args.stem,
                        version="v1",
                    )
                ),
            ),
            (
                "qc-dataset",
                lambda: cmd_qc_dataset(
                    argparse.Namespace(path=None, stem=args.stem, skip_mongo=False)
                ),
            ),
            (
                "split-dataset",
                lambda: cmd_split_dataset(
                    argparse.Namespace(stem=args.stem, seed=args.seed, unseen_ratio=0.10)
                ),
            ),
            (
                "train",
                lambda: cmd_train(
                    argparse.Namespace(
                        stem=args.stem, seed=args.seed, drop_ambiguous=True, tag=args.stem
                    )
                ),
            ),
            (
                "evaluate-test",
                lambda: cmd_evaluate(
                    argparse.Namespace(
                        stem=args.stem,
                        split="test",
                        drop_ambiguous=True,
                        path=None,
                        model_dir=None,
                    )
                ),
            ),
            (
                "evaluate-unseen",
                lambda: cmd_evaluate(
                    argparse.Namespace(
                        stem=args.stem,
                        split="unseen_wording",
                        drop_ambiguous=True,
                        path=None,
                        model_dir=None,
                    )
                ),
            ),
            (
                "compare",
                lambda: cmd_compare(
                    argparse.Namespace(stem=args.stem, split="test", limit=300)
                ),
            ),
        ]
    )
    for name, fn in steps:
        logger.info(f"=== PIPELINE STEP: {name} ===")
        code = fn()
        if code != 0:
            logger.error(f"Pipeline stopped at {name} with code {code}")
            return code
    logger.info("Pipeline complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Finace ML validation layer CLI")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("extract-bank", help="Extract grounded requirements from Mongo corpus")
    e.add_argument("--limit", type=int, default=None)
    e.add_argument("--regulator", type=str, default=None)
    e.add_argument("--status", type=str, default="active")
    e.add_argument("--min-confidence", type=float, default=0.35)
    e.add_argument("--auto-approve", type=float, default=0.85)
    e.set_defaults(func=cmd_extract_bank)

    v = sub.add_parser("validate-bank", help="QC + source-grounding verification")
    v.add_argument("--path", type=str, default=None)
    v.add_argument("--skip-mongo", action="store_true")
    v.set_defaults(func=cmd_validate_bank)

    s = sub.add_parser("show-bank", help="Pretty-print sample requirements")
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--domain", type=str, default=None)
    s.add_argument("--approved-only", action="store_true")
    s.add_argument("--eligible-only", action="store_true")
    s.set_defaults(func=cmd_show_bank)

    r = sub.add_parser("review-sample", help="Export uncertain requirements for human review")
    r.add_argument("--n", type=int, default=20)
    r.add_argument("--all", action="store_true")
    r.set_defaults(func=cmd_review_sample)

    d = sub.add_parser("decide", help="Record approve/reject decision")
    d.add_argument("--id", required=True)
    d.add_argument("--action", required=True, choices=["approve", "reject", "needs_review"])
    d.add_argument("--reviewer", default="human")
    d.add_argument("--notes", default="")
    d.set_defaults(func=cmd_decide)

    a = sub.add_parser("apply-review", help="Apply recorded decisions to the bank")
    a.set_defaults(func=cmd_apply_review)

    g = sub.add_parser("generate-dataset", help="Generate cases FROM eligible bank rows")
    g.add_argument("--paraphrases", type=int, default=2)
    g.add_argument("--max-requirements", type=int, default=None)
    g.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    g.add_argument("--version", type=str, default="v1", choices=["v1", "v2"])
    g.set_defaults(func=cmd_generate_dataset)

    q = sub.add_parser("qc-dataset", help="Dataset quality checks (+ shortcut leakage)")
    q.add_argument("--path", type=str, default=None)
    q.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    q.add_argument("--skip-mongo", action="store_true")
    q.set_defaults(func=cmd_qc_dataset)

    sp = sub.add_parser("split-dataset", help="Leakage-safe family-aware splits")
    sp.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    sp.add_argument("--seed", type=int, default=20261007)
    sp.add_argument("--unseen-ratio", type=float, default=0.10)
    sp.set_defaults(func=cmd_split_dataset)

    t = sub.add_parser("train", help="Train status + risk models")
    t.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    t.add_argument("--seed", type=int, default=20261007)
    t.add_argument("--drop-ambiguous", action="store_true", default=True)
    t.add_argument("--tag", type=str, default=None, help="Artifact tag (defaults to stem)")
    t.set_defaults(func=cmd_train)

    ev = sub.add_parser("evaluate", help="Evaluate on a split or external set")
    ev.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    ev.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "val", "test", "unseen_wording", "all", "approved"],
    )
    ev.add_argument("--drop-ambiguous", action="store_true", default=True)
    ev.add_argument("--path", type=str, default=None, help="Override dataset path")
    ev.add_argument("--model-dir", type=str, default=None, help="Override model directory")
    ev.set_defaults(func=cmd_evaluate)

    c = sub.add_parser("compare", help="ML vs rules vs ground-truth comparison")
    c.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    c.add_argument("--split", type=str, default="test")
    c.add_argument("--limit", type=int, default=300)
    c.set_defaults(func=cmd_compare)

    adv = sub.add_parser("build-adversarial", help="Build adversarial / hard-negative challenge set")
    adv.add_argument("--stem", type=str, default="adversarial_challenge_v1")
    adv.add_argument("--max-requirements", type=int, default=200)
    adv.add_argument("--variants", type=int, default=1)
    adv.set_defaults(func=cmd_build_adversarial)

    eg = sub.add_parser("export-gold", help="Export human-review gold set (provisional labels)")
    eg.add_argument("--stem", type=str, default="gold_human_v1")
    eg.add_argument("--n", type=int, default=150)
    eg.add_argument("--seed", type=int, default=20261007)
    eg.add_argument(
        "--pool-stems",
        nargs="+",
        default=["compliance_benchmark_v2", "adversarial_challenge_v1"],
    )
    eg.set_defaults(func=cmd_export_gold)

    ig = sub.add_parser("import-gold-review", help="Merge human review decisions into gold set")
    ig.add_argument("--stem", type=str, default="gold_human_v1")
    ig.add_argument("--decisions", type=str, required=True, help="Path to decisions JSONL")
    ig.set_defaults(func=cmd_import_gold_review)

    fi = sub.add_parser("feature-importance", help="Shortcut-sensitive feature importance report")
    fi.add_argument("--stem", type=str, default="feature_importance_v2")
    fi.add_argument("--model-dir", type=str, default=None)
    fi.set_defaults(func=cmd_feature_importance)

    fr = sub.add_parser("final-report", help="Write FINAL_REPORT_V2 answering A–H")
    fr.add_argument("--v1-stem", type=str, default="compliance_benchmark_v1")
    fr.add_argument("--v2-stem", type=str, default="compliance_benchmark_v2")
    fr.add_argument("--adv-stem", type=str, default="adversarial_challenge_v1")
    fr.add_argument("--gold-stem", type=str, default="gold_human_v1")
    fr.set_defaults(func=cmd_final_report)

    pipe = sub.add_parser("pipeline", help="Run V1 ML validation pipeline")
    pipe.add_argument("--extract", action="store_true", help="Also re-extract bank from Mongo")
    pipe.add_argument("--limit", type=int, default=None, help="Chunk limit when --extract")
    pipe.add_argument("--paraphrases", type=int, default=2)
    pipe.add_argument("--max-requirements", type=int, default=None)
    pipe.add_argument("--stem", type=str, default="compliance_benchmark_v1")
    pipe.add_argument("--seed", type=int, default=20261007)
    pipe.set_defaults(func=cmd_pipeline)

    p2 = sub.add_parser(
        "pipeline-v2",
        help="Hard benchmark V2 + adversarial + gold + multi-set eval + final report",
    )
    p2.add_argument("--paraphrases", type=int, default=2)
    p2.add_argument("--max-requirements", type=int, default=None)
    p2.add_argument("--v1-stem", type=str, default="compliance_benchmark_v1")
    p2.add_argument("--v2-stem", type=str, default="compliance_benchmark_v2")
    p2.add_argument("--adv-stem", type=str, default="adversarial_challenge_v1")
    p2.add_argument("--gold-stem", type=str, default="gold_human_v1")
    p2.add_argument("--gold-n", type=int, default=150)
    p2.add_argument("--adv-max-requirements", type=int, default=200)
    p2.add_argument("--seed", type=int, default=20261007)
    p2.set_defaults(func=cmd_pipeline_v2)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
