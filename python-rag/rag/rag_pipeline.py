"""
Hybrid RAG pipeline:
1) Deterministic rules (user text only)
2) Retrieval (focused query)
3) Prompt + LLM JSON reasoning
4) Soft merge of rule + LLM score (no hard 40 cap)

Usage:
    cd python-rag
    python -m rag.rag_pipeline --workflow "We support P2P crypto without KYC."
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag.context_utils import (
    build_retrieval_query,
    build_rule_eval_text,
    wants_score_improvement,
)
from rag.llm_client import LLMClient
from rag.output_schema import ApplicableClause, ComplianceOutput
from rag.prompt_builder import build_compliance_prompt
from retrieval.retriever import LocalRetriever
from rules.rule_engine import evaluate_rules
from rules.category_registry import resolve_retrieval_category
from rules.category_registry import infer_categories_from_text
from rules.calibration_store import record_snapshot
from rules.scoring import compute_official_score, risk_from_score_and_rules
from semantic.evaluator import SemanticComplianceEvaluator
from xai.explainer import explain_decision


_RISK_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _pick_higher_risk(a: str, b: str) -> str:
    return a if _RISK_RANK.get(a, 1) >= _RISK_RANK.get(b, 1) else b


def _pick_lower_risk(a: str, b: str) -> str:
    return a if _RISK_RANK.get(a, 1) <= _RISK_RANK.get(b, 1) else b


def _risk_from_score(score: int) -> str:
    if score >= 85:
        return "LOW"
    if score >= 65:
        return "MEDIUM"
    return "HIGH"


def _merge_compliance_score(
    llm_score: int,
    triggered_rules: list[dict],
    *,
    score_improvement_requested: bool,
) -> int:
    """
    Soft merge: trust the LLM score, apply modest penalties for still-open rules.
    Never hard-cap at 40 — remediations / improvement asks can reach 90+.
    """
    score = int(llm_score)

    high_n = sum(1 for r in triggered_rules if r.get("risk_level") == "HIGH")
    med_n = sum(1 for r in triggered_rules if r.get("risk_level") == "MEDIUM")

    if triggered_rules:
        # Softer penalties when the user is actively remediating / raising the score.
        high_pen = 4 if score_improvement_requested else 8
        med_pen = 2 if score_improvement_requested else 4
        score -= high_n * high_pen
        score -= med_n * med_pen
    else:
        if score_improvement_requested:
            score = max(score, 92)
        elif score >= 75:
            score = max(score, 88)

    if score_improvement_requested:
        # Keep follow-up improvements in the high band when the LLM agrees.
        if high_n == 0:
            score = max(score, 90)
        elif llm_score >= 85:
            score = max(score, 88)
        elif llm_score >= 70:
            score = max(score, 80)

    return int(max(0, min(100, score)))


class RAGPipeline:
    def __init__(self, retriever: LocalRetriever | None = None):
        self.retriever = retriever or LocalRetriever()
        self.llm = LLMClient()

    def analyze(
        self,
        call_type: str,
        workflow_text: str,
        existing_report_text: str = "",
        top_k: int = 5,
        regulator: str | None = None,
        category: str | None = None,
        status: str | None = "active",
        enable_xai: bool | None = None,
        enable_semantic_ml: bool | None = None,
        active_categories: list[str] | None = None,
        calibration_frozen: dict[str, Any] | None = None,
        chat_id: str | None = None,
    ) -> dict:
        if call_type not in {"general_query", "new_report", "update_report"}:
            raise ValueError("call_type must be one of: general_query, new_report, update_report")

        # Update flow should see active + superseded context, not only active.
        if call_type == "update_report":
            status = None

        rule_text = build_rule_eval_text(workflow_text)
        retrieval_query = build_retrieval_query(workflow_text)
        improve = wants_score_improvement(workflow_text)
        if enable_xai is None:
            enable_xai = call_type in {"new_report", "update_report"}
        if enable_semantic_ml is None:
            enable_semantic_ml = call_type in {"new_report", "update_report"}

        categories = list(active_categories or [])
        if category and category not in categories:
            categories.append(category)

        # Auto-infer categories from prompt text when none selected
        if not categories:
            inferred = infer_categories_from_text(workflow_text)
            if inferred:
                categories = inferred

        # Step 1: deterministic rules on USER text only
        rule_out = evaluate_rules(rule_text, active_categories=categories)

        # Step 2: retrieval on focused query (better matching)
        retrieval_cat = resolve_retrieval_category(categories) or category

        hits = self.retriever.search(
            query_text=retrieval_query,
            top_k=top_k,
            regulator=regulator,
            category=retrieval_cat,
            status=status or "",
            use_reranker=True,
        )

        triggered = rule_out.get("triggered_rules") or []
        semantic = SemanticComplianceEvaluator()
        run_semantic = bool(enable_semantic_ml) and (
            call_type != "general_query" or enable_xai
        )
        semantic_items = (
            semantic.evaluate(
                rule_text,
                active_categories=categories or None,
                retrieval_hits=hits,
                improvement_requested=improve,
            )
            if run_semantic
            else []
        )
        official_score, score_breakdown, score_anchor, calibration_used = compute_official_score(
            triggered,
            hits,
            semantic_items=semantic_items or None,
            calibration_frozen=calibration_frozen,
        )
        if call_type != "general_query":
            record_snapshot(
                official_score=official_score,
                chat_id=chat_id,
                call_type=call_type,
                categories=categories or None,
            )
        official_risk = risk_from_score_and_rules(official_score, triggered)

        # Step 3: LLM reasoning (narrative only — official score from rule engine)
        prompt = build_compliance_prompt(
            call_type=call_type,
            workflow_text=workflow_text,
            retrieved_chunks=hits,
            existing_report_text=existing_report_text,
            top_k=top_k,
            triggered_rules=triggered,
            score_improvement_requested=improve,
            system_compliance_score=int(round(official_score)) if call_type != "general_query" else None,
            system_risk_level=official_risk if call_type != "general_query" else None,
        )
        llm_raw = self.llm.generate_json(prompt)
        if isinstance(llm_raw, dict):
            risk = str(llm_raw.get("risk_level") or "MEDIUM").strip().upper()
            if risk not in {"HIGH", "MEDIUM", "LOW"}:
                risk = "MEDIUM"
            llm_raw["risk_level"] = risk
            try:
                llm_raw["compliance_score"] = int(llm_raw.get("compliance_score", 70))
            except Exception:
                llm_raw["compliance_score"] = 70
            for key in ("risk_flags", "recommendations", "reasoning_steps", "applicable_clauses"):
                if not isinstance(llm_raw.get(key), list):
                    llm_raw[key] = []
        llm_struct = ComplianceOutput.model_validate(llm_raw)

        # Add retrieved clauses
        clauses: list[ApplicableClause] = []
        for hit in hits:
            meta = hit.get("metadata", {})
            source_path = (
                meta.get("relative_path")
                or meta.get("source")
                or hit.get("document_id")
                or ""
            )
            clauses.append(
                ApplicableClause(
                    title=hit.get("section") or "Clause",
                    text=(hit.get("text") or "")[:1200],
                    source=source_path,
                )
            )

        numeric_score = int(round(official_score))
        score = numeric_score if call_type != "general_query" else None
        final_risk = official_risk if call_type != "general_query" else llm_struct.risk_level

        merged_flags = list(dict.fromkeys(rule_out["risk_flags"] + llm_struct.risk_flags))
        # Drop stale flags when rules no longer fire and user is remediating.
        if improve and not (rule_out.get("triggered_rules") or []):
            merged_flags = list(llm_struct.risk_flags)
        merged_recs = list(
            dict.fromkeys(rule_out["recommendations"] + llm_struct.recommendations)
        )

        final = ComplianceOutput(
            call_type=call_type,
            risk_level=final_risk,
            risk_flags=merged_flags,
            applicable_clauses=clauses if clauses else llm_struct.applicable_clauses,
            explanation=llm_struct.explanation,
            recommendations=merged_recs,
            compliance_score=score if score is not None else llm_struct.compliance_score,
            reasoning_steps=llm_struct.reasoning_steps,
            superseded_references=llm_struct.superseded_references,
            superseded_change_notes=llm_struct.superseded_change_notes,
        )

        if call_type == "update_report":
            superseded_docs = [
                h.get("document_id", "")
                for h in hits
                if h.get("metadata", {}).get("status") == "superseded"
            ]
            if superseded_docs:
                dedup = list(dict.fromkeys([d for d in superseded_docs if d]))
                final.superseded_references = list(
                    dict.fromkeys(final.superseded_references + dedup)
                )
                if not final.superseded_change_notes:
                    final.superseded_change_notes = [
                        "Update includes superseded/legacy references for change comparison."
                    ]

        xai_payload = None
        if enable_xai:
            xai_payload = explain_decision(
                workflow_text=rule_text,
                rules_out=rule_out,
                retrieval_hits=hits,
                final_score=numeric_score,
                final_risk=final_risk,
                score_breakdown=score_breakdown,
                baseline_score=score_anchor,
            )
            xai_payload["semantic_evaluation"] = semantic_items or []
            xai_payload["calibration"] = calibration_used

        analysis_dump = final.model_dump()
        if call_type == "general_query":
            analysis_dump["compliance_score"] = None

        return {
            "analysis": analysis_dump,
            "rules": rule_out,
            "retrieval_hits": hits,
            "score_breakdown": score_breakdown,
            "score_anchor": score_anchor,
            "calibration": calibration_used,
            "semantic_evaluation": semantic_items,
            "active_categories": categories,
            "xai": xai_payload,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run hybrid compliance RAG analysis")
    parser.add_argument(
        "--call-type",
        default="general_query",
        choices=["general_query", "new_report", "update_report"],
        help="Type of AI call",
    )
    parser.add_argument("--workflow", required=True, help="Workflow/business description text")
    parser.add_argument(
        "--existing-report-file",
        default=None,
        help="Path to existing report text file (used for update_report)",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Top-k retrieved chunks")
    parser.add_argument("--regulator", default=None, help="Optional regulator filter")
    parser.add_argument("--category", default=None, help="Optional category filter")
    parser.add_argument("--status", default="active", help="Optional status filter")
    args = parser.parse_args()

    existing_text = ""
    if args.existing_report_file:
        with open(args.existing_report_file, "r", encoding="utf-8") as f:
            existing_text = f.read()

    pipeline = RAGPipeline()
    result = pipeline.analyze(
        call_type=args.call_type,
        workflow_text=args.workflow,
        existing_report_text=existing_text,
        top_k=args.top_k,
        regulator=args.regulator,
        category=args.category,
        status=args.status if args.status else None,
    )
    logger.info(json.dumps(result["analysis"], indent=2))


if __name__ == "__main__":
    main()
