"""
Prompt builder for compliance RAG reasoning.
"""
from __future__ import annotations

import json


def _serialize_chunks(chunks: list[dict], max_chunks: int = 5) -> str:
    selected = chunks[:max_chunks]
    lines: list[str] = []
    for i, c in enumerate(selected, start=1):
        title = c.get("metadata", {}).get("title", "")
        doc_id = c.get("document_id", "")
        section = c.get("section", "GENERAL")
        text = (c.get("text") or "").strip()
        lines.append(
            f"[Chunk {i}] doc={doc_id} section={section} title={title}\n{text}"
        )
    return "\n\n".join(lines)


def build_compliance_prompt(
    call_type: str,
    workflow_text: str,
    retrieved_chunks: list[dict],
    existing_report_text: str = "",
    top_k: int = 5,
    triggered_rules: list[dict] | None = None,
    score_improvement_requested: bool = False,
) -> str:
    context = _serialize_chunks(retrieved_chunks, max_chunks=top_k)
    output_schema = {
        "call_type": "general_query|new_report|update_report",
        "risk_level": "HIGH|MEDIUM|LOW",
        "risk_flags": ["..."],
        "applicable_clauses": [{"title": "...", "text": "...", "source": "..."}],
        "explanation": "...",
        "recommendations": ["..."],
        "compliance_score": 0,
        "reasoning_steps": ["..."],
        "superseded_references": ["doc_id or circular ref"],
        "superseded_change_notes": ["what changed and why"],
    }
    existing_block = ""
    if existing_report_text.strip():
        existing_block = f"\nExisting Report Content:\n{existing_report_text}\n"

    rules_block = "(none)"
    if triggered_rules:
        rules_block = "\n".join(
            f"- {r.get('name')} [{r.get('risk_level')}] — {r.get('flag')}"
            for r in triggered_rules
        )

    improve_block = ""
    if score_improvement_requested:
        improve_block = (
            "\nSCORE IMPROVEMENT MODE:\n"
            "- The user wants a higher compliance score (target often 90+).\n"
            "- Re-read prior XAI drivers / SHAP stats in the conversation and treat remediations "
            "the user describes as closing those gaps.\n"
            "- If controls for previous drivers are now claimed (KYC, AML/EDD, FEMA/FX, grievance, 2FA), "
            "set compliance_score to 90-98 and risk_level to LOW unless a clear residual gap remains.\n"
            "- Explain what improved vs the prior score and which XAI drivers were addressed.\n"
        )

    return (
        "You are an ELITE fintech compliance legal expert.\n"
        f"Call type: {call_type}\n\n"
        "GOAL: Analyze the workflow and provide PRECISE, actionable legal guidance based ONLY on the provided context.\n\n"
        "SCORING RUBRIC (compliance_score is 0-100, higher = more compliant / safer):\n"
        "- 90-100 + risk_level LOW: controls for KYC/AML/FEMA/grievance (as relevant) are described and residual gaps are minor.\n"
        "- 70-89 + MEDIUM: mostly controlled with a few open gaps.\n"
        "- 40-69 + HIGH/MEDIUM: material gaps remain.\n"
        "- Below 40: critical uncontrolled risks.\n"
        "- Prefer optimistic-but-honest scoring: when the user describes remediations or asks to raise the score "
        "and those remediations address prior XAI drivers, MOVE THE SCORE UP (often into 90+).\n"
        "- Do not keep repeating a low prior score if the latest user message adds missing controls.\n"
        "- If conversation history includes XAI / SHAP statistics, use them to decide what to fix and how much to raise the score.\n\n"
        "STRICT RULES:\n"
        "1. Be detailed and practical, but keep the JSON compact enough to fit in one response.\n"
        "2. Cite specific annexures/clauses from the context when available.\n"
        "3. Put the main narrative in 'explanation' as HTML using <h2> and <p> tags.\n"
        "4. Use 'applicable_clauses' to quote the most relevant legal text.\n"
        "5. NO MARKDOWN fences. Return only valid JSON.\n"
        "6. 'explanation' MUST be a non-empty string.\n\n"
        f"Still-active deterministic rule flags (from USER text only):\n{rules_block}\n"
        f"{improve_block}\n"
        f"Workflow Input:\n{workflow_text}\n\n"
        f"{existing_block}\n"
        f"Regulatory Context (The Evidence):\n{context}\n\n"
        "Expected Explanation Style:\n"
        "Write a clear structured analysis with these sections in HTML:\n"
        "1. Executive Overview\n"
        "2. Detailed Risk Breakdown\n"
        "3. Regulatory Mapping\n"
        "4. Operational Impact\n"
        "5. Remediation Plan\n"
        "Keep each section focused (a few paragraphs), not multi-page.\n\n"
        f"Output JSON schema:\n{json.dumps(output_schema)}"
    )
