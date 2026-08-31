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
    ) -> dict:
        if call_type not in {"general_query", "new_report", "update_report"}:
            raise ValueError("call_type must be one of: general_query, new_report, update_report")

        # Update flow should see active + superseded context, not only active.
        if call_type == "update_report":
            status = None

        rule_text = build_rule_eval_text(workflow_text)
        retrieval_query = build_retrieval_query(workflow_text)
        improve = wants_score_improvement(workflow_text)

        # Step 1: deterministic rules on USER text only
        rule_out = evaluate_rules(rule_text)

        # Step 2: retrieval on focused query (better matching)
        hits = self.retriever.search(
            query_text=retrieval_query,
            top_k=top_k,
            regulator=regulator,
            category=category,
            status=status or "",
            use_reranker=True,
        )

        # Step 3: LLM reasoning
        prompt = build_compliance_prompt(
            call_type=call_type,
            workflow_text=workflow_text,
            retrieved_chunks=hits,
            existing_report_text=existing_report_text,
            top_k=top_k,
            triggered_rules=rule_out.get("triggered_rules") or [],
            score_improvement_requested=improve,
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

        # Step 4: soft merge (no hard 40/60 caps)
        score = _merge_compliance_score(
            llm_struct.compliance_score,
            rule_out.get("triggered_rules") or [],
            score_improvement_requested=improve,
        )
        score_risk = _risk_from_score(score)
        rule_llm_risk = _pick_higher_risk(rule_out["risk_level"], llm_struct.risk_level)
        # When score is strong, prefer the score-aligned band so UI is not stuck on HIGH·40.
        if score >= 85:
            final_risk = "LOW"
        elif score >= 65:
            final_risk = _pick_lower_risk(rule_llm_risk, "MEDIUM")
            if final_risk == "HIGH" and not (rule_out.get("triggered_rules") or []):
                final_risk = "MEDIUM"
        else:
            final_risk = rule_llm_risk
            # Keep risk coherent with score band when rules are clear.
            if not (rule_out.get("triggered_rules") or []):
                final_risk = _pick_higher_risk(final_risk, score_risk)

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
            compliance_score=score,
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

        return {
            "analysis": final.model_dump(),
            "rules": rule_out,
            "retrieval_hits": hits,
            "xai": explain_decision(
                workflow_text=rule_text,
                rules_out=rule_out,
                retrieval_hits=hits,
                final_score=final.compliance_score,
                final_risk=final.risk_level,
            ),
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
