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
from rag.evidence_scope import (
    annotate_hits,
    build_evidence_scope,
    qualify_legal_language,
    select_applicable_hits,
)
from rag.llm_client import LLMClient
from rag.output_schema import ApplicableClause, ComplianceOutput
from rag.prompt_builder import build_compliance_prompt
from retrieval.retriever import LocalRetriever
from rules.rule_engine import evaluate_rules
from xai.explainer import explain_decision, extract_features, score_from_features

from ml.features import extract_workflow_features
from ml.predict import get_predictor


_RISK_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
_RULE_FEATURES = {
    "R001_NO_KYC": ("rule:R001_NO_KYC", "kyc_present"),
    "R002_P2P_CRYPTO": ("rule:R002_P2P_CRYPTO", "p2p_crypto_activity", "aml_present", "transaction_monitoring"),
    "R003_CROSS_BORDER_NO_FEMA": ("rule:R003_CROSS_BORDER_NO_FEMA", "cross_border_activity", "fema_controls"),
    "R004_NO_GRIEVANCE": ("rule:R004_NO_GRIEVANCE", "grievance_mechanism"),
}


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


def _final_risk(score: int, rule_out: dict, llm_risk: str) -> str:
    """Combine score/LLM risk without downgrading active deterministic rules."""
    score_risk = _risk_from_score(score)
    triggered = rule_out.get("triggered_rules") or []
    rule_llm_risk = _pick_higher_risk(rule_out.get("risk_level", "LOW"), llm_risk)
    if triggered:
        return rule_llm_risk
    if score >= 85:
        return "LOW"
    if score >= 65:
        return _pick_lower_risk(rule_llm_risk, "MEDIUM")
    return _pick_higher_risk(rule_llm_risk, score_risk)


def _merge_compliance_score(
    llm_score: int,
    deterministic_score: float,
    *,
    score_improvement_requested: bool,
) -> int:
    """
    Unified formula-driven metric system:
    Final Score = (Deterministic Score * 0.7) + (LLM Proposed Score * 0.3)
    """
    merged_score = (deterministic_score * 0.7) + (float(llm_score) * 0.3)
    
    if score_improvement_requested:
        merged_score += 5.0
        
    return int(max(0, min(100, merged_score)))


def _rank_rule_assessments(rule_out: dict, ml_risk: dict) -> list[dict]:
    """Rank only prompt-applicable rules using model-attributed impact.

    ``impact_value`` is the sum of positive SHAP contributions for features
    belonging to the rule. It is in the model's native units (log-odds for the
    selected logistic model, probability for a tree model), never a percent.
    Deterministic severity and trigger status break ties.
    """
    shap_by_feature = {
        item.get("feature"): float(item.get("shap_value") or 0.0)
        for item in ((ml_risk.get("explanation") or {}).get("features") or [])
    }
    rows: list[dict] = []
    for item in rule_out.get("rule_assessments") or []:
        rid = item.get("rule_id")
        relevant = _RULE_FEATURES.get(rid, (f"rule:{rid}",))
        contributions = [shap_by_feature.get(name, 0.0) for name in relevant]
        positive_impact = sum(value for value in contributions if value > 0.0)
        row = dict(item)
        row["impact_value"] = round(positive_impact, 4)
        row["impact_units"] = (ml_risk.get("explanation") or {}).get("units", "deterministic severity")
        row["impact_features"] = [name for name in relevant if name in shap_by_feature]
        rows.append(row)
    rows.sort(
        key=lambda row: (
            float(row.get("impact_value") or 0.0),
            1 if row.get("triggered") else 0,
            _RISK_RANK.get(row.get("risk_level"), 1),
        ),
        reverse=True,
    )
    for index, row in enumerate(rows, start=1):
        row["impact_rank"] = index
    return rows


def _add_evidence_status(rows: list[dict], evidence_scope: dict) -> list[dict]:
    domain_by_rule = {
        "R001_NO_KYC": "kyc_aml_controls",
        "R002_P2P_CRYPTO": "vda_aml",
        "R003_CROSS_BORDER_NO_FEMA": "cross_border_fx",
        "R004_NO_GRIEVANCE": "grievance",
    }
    direct = set(evidence_scope.get("direct_evidence_domains") or [])
    unresolved = set(evidence_scope.get("unresolved_domains") or [])
    for row in rows:
        domain = domain_by_rule.get(row.get("rule_id"))
        row["evidence_status"] = (
            "SUPPORTED_IN_RETRIEVED_CONTEXT" if domain in direct else "INSUFFICIENT_DIRECT_EVIDENCE"
        )
        row["applicability"] = (
            "REQUIRES_ENTITY_SPECIFIC_VALIDATION"
            if domain in direct or domain in unresolved
            else "NOT_ESTABLISHED"
        )
    return rows


class RAGPipeline:
    def __init__(self, retriever: LocalRetriever | None = None):
        self.retriever = retriever or LocalRetriever()
        self.llm = LLMClient()

    def _ml_risk_block(
        self,
        rule_text: str,
        rule_out: dict,
        hits: list,
        top_k: int,
    ) -> dict:
        """
        Backward-compatible ML risk intelligence signal.

        Extracts the canonical ML feature vector from the SAME outputs the rest of
        the engine already produced (rule triggers + retrieval hits + rule-eval
        text), then predicts the risk class with the trained model and attaches
        exact SHAP attributions. The block is additive: when no trained artifact
        exists (or inference fails) the key is still returned with
        ``available=False`` so consumers never assume ML is on.
        """
        try:
            predictor = get_predictor()
            if not predictor.available:
                return {
                    "available": False,
                    "risk_class": None,
                    "probabilities": {"LOW": None, "MEDIUM": None, "HIGH": None},
                    "notes": [
                        "ML risk layer inactive: no trained artifact in ml/artifacts."
                    ],
                }
            fv = extract_workflow_features(rule_text, rule_out, hits, top_k=top_k)
            return predictor.combined(fv)
        except Exception as exc:
            logger.warning(f"ML risk layer failed (continuing without it): {exc}")
            return {
                "available": False,
                "risk_class": None,
                "probabilities": {"LOW": None, "MEDIUM": None, "HIGH": None},
                "notes": ["ML risk layer error; deterministic engine unaffected."],
            }

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
        hits = annotate_hits(hits, rule_text)
        evidence_scope = build_evidence_scope(rule_text, hits)

        # Step 3: LLM reasoning
        prompt = build_compliance_prompt(
            call_type=call_type,
            workflow_text=workflow_text,
            retrieved_chunks=hits,
            existing_report_text=existing_report_text,
            top_k=top_k,
            triggered_rules=rule_out.get("triggered_rules") or [],
            score_improvement_requested=improve,
            evidence_scope=evidence_scope,
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
        llm_struct.explanation = qualify_legal_language(llm_struct.explanation)

        if evidence_scope.get("warnings"):
            evidence_note = (
                "<h2>Evidence Applicability Note</h2>"
                "<p>Some workflow domains do not have directly applicable evidence in the indexed corpus. "
                "The findings below are potential exposure assessments and workflow control observations, "
                "not definitive legal violations. Obtain and review the applicable VDA/FIU/PMLA, "
                "foreign-exchange/remittance, and grievance provisions for the entity's actual facts before relying on them.</p>"
            )
            llm_struct.explanation = evidence_note + (llm_struct.explanation or "")

        # Only direct-domain evidence is presented as an applicable clause.
        # Similarity-only or merchant-sector evidence remains inspectable in
        # retrieval_hits but cannot silently become the legal basis.
        clauses: list[ApplicableClause] = []
        for hit in select_applicable_hits(hits):
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
                basis=(hit.get("evidence_scope") or {}).get("basis", "direct"),
                applicability_note=(hit.get("evidence_scope") or {}).get("applicability_note", ""),
            )
            )

        # Step 4: ML signal and rule-impact ranking
        ml_risk = self._ml_risk_block(rule_text, rule_out, hits, top_k)
        rule_assessments = _add_evidence_status(
            _rank_rule_assessments(rule_out, ml_risk), evidence_scope
        )

        # Step 5: soft merge using deterministic formula
        vector, spec, _ = extract_features(workflow_text, rule_out, hits)
        deterministic_score = score_from_features(vector, spec)

        score = _merge_compliance_score(
            llm_struct.compliance_score,
            deterministic_score,
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

        final_risk = _final_risk(score, rule_out, llm_struct.risk_level)
        merged_flags = list(dict.fromkeys(rule_out["risk_flags"] + llm_struct.risk_flags))
        # Drop stale flags when rules no longer fire and user is remediating.
        if improve and not (rule_out.get("triggered_rules") or []):
            merged_flags = list(llm_struct.risk_flags)
        merged_recs = list(
            dict.fromkeys(rule_out["recommendations"] + llm_struct.recommendations)
        )
        if evidence_scope.get("warnings"):
            merged_recs.append(
                "VALIDATION NEEDED: Confirm the entity's jurisdiction, customer residency, transaction structure, currencies, counterparties, licences and authorised intermediaries, then map the workflow to directly applicable VDA/AML, FEMA/foreign-exchange and grievance provisions."
            )

        final = ComplianceOutput(
            call_type=call_type,
            risk_level=final_risk,
            risk_flags=merged_flags,
            # Never fall back to model-proposed clauses: only retrieved chunks
            # that passed the applicability gate may enter the legal schedule.
            applicable_clauses=clauses,
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
            "evidence_scope": evidence_scope,
            "rule_assessments": rule_assessments,
            "xai": explain_decision(
                workflow_text=rule_text,
                rules_out=rule_out,
                retrieval_hits=hits,
                final_score=final.compliance_score,
                final_risk=final.risk_level,
            ),
            "ml_risk": ml_risk,
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
