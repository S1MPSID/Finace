"""Formal regulatory compliance report sections."""
from __future__ import annotations

from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from reports.pdf_styles import as_list
from reports.table_utils import plain_cell_text, truncate_middle, wrap_table_rows
from reports.text_format import append_rich_text, html_or_markdown_to_reportlab


REPORT_KIND_LABELS = {
    "initial": "Initial Compliance Assessment Report",
    "upgrade": "Compliance Upgrade & Remediation Report",
    "advisory": "Regulatory Compliance Advisory Memorandum",
}


def infer_report_kind(analysis: dict) -> str:
    call_type = str(analysis.get("call_type") or "").lower()
    if call_type == "update_report":
        return "upgrade"
    if call_type == "new_report":
        return "initial"
    history = analysis.get("evaluation_metadata", {}).get("update_history") or []
    if history:
        return "upgrade"
    workflow = analysis.get("workflow_input") or {}
    text = str(workflow.get("text", "") if isinstance(workflow, dict) else workflow).upper()
    if "AI-IMPROVED" in text or "REMEDIATION" in text:
        return "upgrade"
    if call_type == "general_query":
        return "advisory"
    return "initial"


def _meta_table(rows: list[list[str]]) -> Table:
    table = Table(rows, colWidths=[2.1 * inch, 4.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#334155")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ]
        )
    )
    return table


def append_cover(story, styles, analysis: dict, report_id: str, org_name: str) -> str:
    kind = infer_report_kind(analysis)
    kind_label = REPORT_KIND_LABELS[kind]

    story.append(Spacer(1, 1.4 * inch))
    story.append(Paragraph("FINACE AUTONOMOUS COMPLIANCE ENGINE", styles["cover_subtitle"]))
    story.append(Paragraph(kind_label.upper(), styles["cover_kind"]))
    story.append(Paragraph(org_name, styles["cover_title"]))
    story.append(Spacer(1, 0.35 * inch))

    regulator = "RBI"
    wf = analysis.get("workflow_input") or {}
    if isinstance(wf, dict) and wf.get("regulator"):
        regulator = str(wf.get("regulator"))

    rows = [
        ["Report Reference", report_id],
        ["Subject Entity", org_name],
        ["Regulatory Framework", f"{regulator} / NPCI (as applicable)"],
        ["Report Date (UTC)", datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")],
        ["Compliance Score", f"{analysis.get('compliance_score', 0)} / 100"],
        ["Risk Classification", str(analysis.get("risk_level", "PENDING"))],
        ["Report Status", str(analysis.get("status", "pending")).upper()],
    ]
    story.append(_meta_table(rows))
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        Paragraph(
            "<b>CONFIDENTIAL.</b> This document constitutes a machine-assisted compliance "
            "determination prepared for internal governance, audit readiness, and evaluator review. "
            "It does not constitute legal advice or regulatory certification.",
            styles["legal_notice"],
        )
    )
    story.append(PageBreak())
    return kind


def append_table_of_contents(story, styles, report_kind: str) -> None:
    story.append(Paragraph("TABLE OF CONTENTS", styles["section"]))
    sections = [
        "1. Document Control & Purpose",
        "2. Scope of Assessment",
        "3. Compliance Determination",
        "4. Control Gaps & Required Actions",
        "5. Regulatory Basis Schedule (Annex A)",
    ]
    if report_kind == "upgrade":
        sections.append("6. Compliance Upgrade Record")
    sections.extend(
        [
            "7. Evaluator Certification (if applicable)",
            "Annex B — Submitted Workflow Record",
        ]
    )
    for line in sections:
        story.append(Paragraph(line, styles["toc"]))
    story.append(PageBreak())


def append_document_control(story, styles, analysis: dict, report_id: str, report_kind: str) -> None:
    story.append(Paragraph("1. DOCUMENT CONTROL & PURPOSE", styles["section"]))
    purpose = {
        "initial": (
            "This report documents the <b>initial compliance posture</b> of the submitted product "
            "workflow against indexed RBI/NPCI requirements. It is intended to serve as a "
            "baseline compliance artifact for launch readiness and evaluator sign-off."
        ),
        "upgrade": (
            "This report documents a <b>compliance upgrade cycle</b> — a reassessment after "
            "remediation or product changes. It records score movement, closed gaps, and "
            "remaining obligations relative to a prior assessment."
        ),
        "advisory": (
            "This memorandum records a <b>targeted regulatory advisory</b> output. It supports "
            "compliance planning but does not replace a full workflow assessment report."
        ),
    }
    story.append(Paragraph(purpose.get(report_kind, purpose["initial"]), styles["body"]))
    story.append(Spacer(1, 10))
    rows = [
        ["Document Type", REPORT_KIND_LABELS.get(report_kind, "Compliance Report")],
        ["Reference ID", report_id],
        ["Generation Method", "Finace RAG + Rule Engine + LLM Structured Output"],
        ["Evidence Standard", "Indexed regulatory corpus with cited excerpts (Annex A)"],
    ]
    story.append(_meta_table(rows))
    story.append(PageBreak())


def append_scope(story, styles, analysis: dict) -> None:
    story.append(Paragraph("2. SCOPE OF ASSESSMENT", styles["section"]))
    wf = analysis.get("workflow_input") or {}
    regulator = wf.get("regulator", "RBI") if isinstance(wf, dict) else "RBI"
    story.append(
        Paragraph(
            f"The assessment scope covers the product workflow described in Annex B, evaluated "
            f"against applicable <b>{regulator}</b> circulars, master directions, and NPCI "
            f"operating guidelines present in the Finace regulatory corpus.",
            styles["body"],
        )
    )
    story.append(Paragraph("<b>2.1 In Scope</b>", styles["subsection"]))
    for item in (
        "Customer onboarding, KYC/AML controls referenced in the workflow",
        "Payment, wallet, or lending flows as described by the submitter",
        "Data protection, grievance, and reporting obligations where triggered",
        "Retrieved regulatory clauses supporting each determination",
    ):
        story.append(Paragraph(f"• {item}", styles["bullet"]))
    story.append(Paragraph("<b>2.2 Out of Scope</b>", styles["subsection"]))
    for item in (
        "On-site inspection or manual document verification",
        "Legal opinion or binding regulatory approval",
        "Non-indexed or superseded circulars not present in corpus",
    ):
        story.append(Paragraph(f"• {item}", styles["bullet"]))
    story.append(PageBreak())


def append_compliance_determination(story, styles, analysis: dict) -> None:
    story.append(Paragraph("3. COMPLIANCE DETERMINATION", styles["section"]))
    score = analysis.get("compliance_score", 0)
    risk = str(analysis.get("risk_level", "MEDIUM"))
    story.append(
        Paragraph(
            f"Based on automated rule evaluation, retrieval-grounded analysis, and structured "
            f"reasoning, the engine assigns a <b>compliance score of {score}/100</b> with an "
            f"overall <b>risk classification of {risk}</b>.",
            styles["body"],
        )
    )

    rows = [
        ["Metric", "Value"],
        ["Compliance Score", f"{score} / 100"],
        ["Risk Level", risk],
        ["Risk Flags Identified", str(len(as_list(analysis.get("risk_flags"))))],
        ["Required Actions", str(len(as_list(analysis.get("recommendations"))))],
        ["Regulatory Citations", str(len(analysis.get("applicable_clauses") or []))],
    ]
    table = Table(rows, colWidths=[2.4 * inch, 4.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Spacer(1, 8))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>3.1 Determination Summary</b>", styles["subsection"]))
    explanation = str(analysis.get("explanation", ""))
    if explanation.strip():
        append_rich_text(story, styles, explanation, default_style="body")

    if analysis.get("reasoning_steps"):
        story.append(Paragraph("<b>3.2 Assessment Trail</b>", styles["subsection"]))
        for i, step in enumerate(as_list(analysis.get("reasoning_steps")), start=1):
            story.append(Paragraph(f"{i}. {step}", styles["bullet"]))
    story.append(PageBreak())


def append_gaps_and_actions(story, styles, analysis: dict) -> None:
    story.append(Paragraph("4. CONTROL GAPS & REQUIRED ACTIONS", styles["section"]))
    story.append(
        Paragraph(
            "The following items represent compliance gaps identified by the rule engine and "
            "structured analysis. Required actions must be implemented and re-assessed via a "
            "<b>Compliance Upgrade Report</b> before production launch where risk is HIGH.",
            styles["body"],
        )
    )

    flags = as_list(analysis.get("risk_flags"))
    story.append(Paragraph("<b>4.1 Identified Control Gaps</b>", styles["subsection"]))
    if flags:
        gap_rows = [["#", "Gap / Control Deficiency"]] + [
            [str(i), plain_cell_text(f)] for i, f in enumerate(flags, 1)
        ]
        gap_table = Table(wrap_table_rows(gap_rows, styles), colWidths=[0.45 * inch, 6.05 * inch])
        gap_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7f1d1d")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecaca")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(gap_table)
    else:
        story.append(Paragraph("No material control gaps identified at this assessment.", styles["body"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>4.2 Required Remediation Actions</b>", styles["subsection"]))
    recs = as_list(analysis.get("recommendations"))
    if recs:
        action_rows = [["Priority", "Action Required"]] + [
            [str(i), plain_cell_text(rec)] for i, rec in enumerate(recs, 1)
        ]
        action_table = Table(wrap_table_rows(action_rows, styles), colWidths=[0.65 * inch, 5.85 * inch])
        action_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#99f6e4")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(action_table)
    else:
        story.append(Paragraph("No additional remediation actions specified.", styles["body"]))
    story.append(PageBreak())


def _clause_document_name(clause: dict) -> str:
    for key in ("document_name", "source_file", "source", "relative_path", "document_id"):
        value = str(clause.get(key) or "").strip()
        if not value or value.lower() in {"regulation", "n/a", "legal reference"}:
            continue
        if "/" in value or "\\" in value:
            return value.replace("\\", "/").split("/")[-1]
        return value
    return "Regulatory Document"


def append_regulatory_schedule(story, styles, analysis: dict) -> None:
    story.append(Paragraph("5. REGULATORY BASIS SCHEDULE (ANNEX A)", styles["section"]))
    story.append(
        Paragraph(
            "Supporting statutory and regulatory excerpts retrieved from the indexed corpus. "
            "These citations form the evidential basis for Section 3 determinations.",
            styles["body"],
        )
    )
    clauses = analysis.get("applicable_clauses", [])
    if not isinstance(clauses, list) or not clauses:
        story.append(Paragraph("No indexed regulatory excerpts attached.", styles["body"]))
        story.append(PageBreak())
        return

    sched_rows = [["Ref", "Document", "Section", "Excerpt (abridged)"]]
    for idx, c in enumerate(clauses[:15], start=1):
        if not isinstance(c, dict):
            continue
        doc = truncate_middle(_clause_document_name(c), 52)
        section = plain_cell_text(c.get("title") or c.get("section") or "—")
        raw_excerpt = plain_cell_text(str(c.get("text") or ""))
        excerpt = raw_excerpt[:320] + ("…" if len(raw_excerpt) > 320 else "")
        sched_rows.append([f"A-{idx}", doc, section, excerpt])

    table = Table(
        wrap_table_rows(sched_rows, styles),
        colWidths=[0.45 * inch, 1.35 * inch, 1.35 * inch, 3.35 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(Spacer(1, 8))
    story.append(table)
    story.append(PageBreak())


def append_upgrade_record(story, styles, analysis: dict) -> None:
    story.append(Paragraph("6. COMPLIANCE UPGRADE RECORD", styles["section"]))
    story.append(
        Paragraph(
            "This section records changes applied during a compliance upgrade cycle — "
            "remediation steps, superseded references, and score movement.",
            styles["body"],
        )
    )
    trust = analysis.get("trust_stats") or {}
    if trust.get("delta") is not None:
        story.append(
            Paragraph(
                f"<b>Score change (Δ):</b> {trust.get('delta', 0)} points "
                f"(latest: {trust.get('latest_score', '—')}, prior trajectory documented in engine logs).",
                styles["body"],
            )
        )
    history = (analysis.get("evaluation_metadata") or {}).get("update_history") or []
    for entry in history[-5:]:
        story.append(
            Paragraph(
                f"• {entry.get('updated_at', '—')}: "
                f"{'; '.join(entry.get('change_notes') or []) or 'Re-assessment completed'}",
                styles["bullet"],
            )
        )
    for ref in as_list(analysis.get("superseded_references")):
        story.append(Paragraph(f"• Superseded reference: {ref}", styles["bullet"]))
    for note in as_list(analysis.get("superseded_change_notes")):
        story.append(Paragraph(f"• Change note: {note}", styles["bullet"]))
    story.append(PageBreak())


def append_evaluator_amendments(story, styles, analysis: dict) -> None:
    logs = analysis.get("evaluation_logs") or []
    refs = analysis.get("evaluator_references") or []
    manual_logs = [l for l in logs if isinstance(l, dict) and l.get("action") in ("amendment", "reference_added", "verified", "rejected")]
    if not manual_logs and not refs:
        return

    header, body, bullet = styles["section"], styles["body"], styles["bullet"]
    story.append(Paragraph("EVALUATOR MANUAL REVIEW RECORD", header))
    story.append(
        Paragraph(
            "Human evaluator adjustments, regulatory references supplied during review, and audit trail "
            "of all manual changes applied before certification.",
            body,
        )
    )
    story.append(Spacer(1, 10))

    if refs:
        story.append(Paragraph("<b>Evaluator-Supplied References</b>", styles["subsection"]))
        for idx, ref in enumerate(refs, start=1):
            if not isinstance(ref, dict):
                continue
            story.append(Paragraph(f"<b>Ref E-{idx}:</b> {ref.get('document_name', 'Document')}", styles["subsection"]))
            if ref.get("comment"):
                story.append(Paragraph(f"<i>Evaluator note:</i> {ref.get('comment')}", body))
            story.append(Paragraph(f'"{str(ref.get("reference_text", ""))[:900]}"', styles["mono"]))
            story.append(Spacer(1, 8))

    if manual_logs:
        story.append(Paragraph("<b>Change Audit Log</b>", styles["subsection"]))
        for entry in manual_logs[-20:]:
            ts = str(entry.get("created_at", ""))[:19]
            story.append(
                Paragraph(
                    f"<b>{entry.get('action', 'change').upper()}</b> — {entry.get('actor_name', 'Evaluator')} ({ts})",
                    body,
                )
            )
            if entry.get("comment"):
                story.append(Paragraph(f"Comment: {entry.get('comment')}", bullet))
            for ch in entry.get("changes") or []:
                if not isinstance(ch, dict):
                    continue
                story.append(
                    Paragraph(
                        f"• {ch.get('field')}: {ch.get('old_value')} → {ch.get('new_value')}",
                        bullet,
                    )
                )
            story.append(Spacer(1, 6))
    story.append(PageBreak())


def append_certification(story, styles, analysis: dict) -> None:
    story.append(Paragraph("7. EVALUATOR CERTIFICATION", styles["section"]))
    meta = analysis.get("evaluation_metadata") or {}
    evaluator = meta.get("evaluator_name") or "Pending evaluator review"
    remarks = analysis.get("evaluator_remarks") or ""
    signed = analysis.get("is_digitally_signed")

    story.append(
        Paragraph(
            "The undersigned evaluator has reviewed the machine-assisted determination herein "
            "and confirms that the report is suitable for internal compliance governance "
            "and optional blockchain anchoring.",
            styles["cert"],
        )
    )
    cert_rows = [
        ["Evaluator", evaluator],
        ["Review Status", str(analysis.get("status", "pending")).upper()],
        ["Digital Signature", "APPLIED" if signed else "PENDING"],
        ["Remarks", remarks or "—"],
    ]
    story.append(_meta_table(cert_rows))
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph("_" * 60, styles["body_left"]))
    story.append(Paragraph("Authorized Compliance Evaluator — Signature", styles["legal_notice"]))
    story.append(PageBreak())


def append_workflow_appendix(story, styles, analysis: dict) -> None:
    story.append(Paragraph("ANNEX B — SUBMITTED WORKFLOW RECORD", styles["section"]))
    story.append(
        Paragraph(
            "Primary workflow text submitted for assessment. This annex supports reproducibility "
            "of the compliance determination.",
            styles["body"],
        )
    )
    workflow_input = analysis.get("workflow_input", {})
    workflow_text = workflow_input.get("text", "") if isinstance(workflow_input, dict) else str(workflow_input or "")
    if not workflow_text:
        story.append(Paragraph("No workflow submission attached.", styles["body"]))
        return

    append_rich_text(story, styles, workflow_text, default_style="body_left")
