"""
Generate highly detailed, multi-page compliance report PDF from analysis payload.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak, Table, TableStyle

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings

def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []

def generate_report_pdf(
    analysis: dict,
    report_id: str,
    org_name: str,
    output_dir: Path | None = None,
) -> Path:
    out_dir = output_dir or (settings.data_dir / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report_id}.pdf"

    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Title'],
        fontSize=28,
        spaceAfter=30,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER
    )
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=15,
        textColor=colors.HexColor("#1e293b"),
        borderPadding=10,
    )
    body_style = ParagraphStyle(
        'BodyJustify',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    bullet_style = ParagraphStyle(
        'BulletItem',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        leftIndent=20,
        spaceAfter=8
    )
    mono_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['BodyText'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
        leftIndent=10,
        rightIndent=10,
        backColor=colors.HexColor("#f1f5f9"),
        spaceBefore=10,
        spaceAfter=10
    )

    story = []

    # ────────────────────────────────────────────
    # PAGE 1: COVER PAGE
    # ────────────────────────────────────────────
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("REGULATORY COMPLIANCE", subtitle_style))
    story.append(Paragraph("AUDIT REPORT", title_style))
    story.append(Spacer(1, 1 * inch))
    
    # Info Table
    data = [
        ["Organization:", org_name],
        ["Report ID:", report_id],
        ["Date Generated:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["Risk Level:", analysis.get("risk_level", "UNKNOWN")],
        ["Compliance Score:", f"{analysis.get('compliance_score', 0)} / 100"]
    ]
    t = Table(data, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#334155")),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ────────────────────────────────────────────
    # PAGE 2: AUDIT SCOPE & METHODOLOGY
    # ────────────────────────────────────────────
    story.append(Paragraph("1. Audit Scope & Methodology", header_style))
    story.append(Paragraph("This compliance audit report was generated autonomously using the Finace Autonomous Compliance Engine. The engine utilizes Retrieval-Augmented Generation (RAG) to cross-reference the organization's declared business workflows against active regulatory circulars, including guidelines from the Reserve Bank of India (RBI) and National Payments Corporation of India (NPCI).", body_style))
    story.append(Paragraph("The scope of this audit covers the specific operational processes disclosed by the organization. The engine evaluates these processes for adherence to data security, transaction processing, fraud management, and dispute resolution mandates as explicitly stated in the retrieved regulatory clauses.", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Key Evaluation Metrics:", styles["Heading3"]))
    story.append(Paragraph("• <b>Risk Level:</b> Determines the severity of identified compliance gaps.", bullet_style))
    story.append(Paragraph("• <b>Compliance Score:</b> A quantitative measure (0-100) reflecting overall adherence.", bullet_style))
    story.append(Paragraph("• <b>Risk Flags:</b> Specific areas of concern requiring immediate remediation.", bullet_style))
    story.append(PageBreak())

    # ────────────────────────────────────────────
    # PAGE 3: EXECUTIVE SUMMARY & ANALYSIS
    # ────────────────────────────────────────────
    story.append(Paragraph("2. Executive Summary & Deep Analysis", header_style))
    
    # Explanation from LLM (Now expected to be massive)
    explanation = analysis.get("explanation", "No detailed explanation provided.")
    # Split explanation by newlines to handle paragraphs
    for para in explanation.split('\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    story.append(PageBreak())

    # ────────────────────────────────────────────
    # PAGE 4: RISK ASSESSMENT & RECOMMENDATIONS
    # ────────────────────────────────────────────
    story.append(Paragraph("3. Risk Assessment & Recommendations", header_style))
    
    story.append(Paragraph("Identified Risk Flags", styles["Heading2"]))
    flags = _as_list(analysis.get("risk_flags"))
    if not flags:
        story.append(Paragraph("No immediate risk flags identified.", body_style))
    else:
        for flag in flags:
            story.append(Paragraph(f"• {flag}", bullet_style))
            
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Remediation Recommendations", styles["Heading2"]))
    recs = _as_list(analysis.get("recommendations"))
    if not recs:
        story.append(Paragraph("No recommendations provided.", body_style))
    else:
        for rec in recs:
            story.append(Paragraph(f"• {rec}", bullet_style))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Reasoning Steps Taken by Audit Engine", styles["Heading2"]))
    steps = _as_list(analysis.get("reasoning_steps"))
    for step in steps:
        story.append(Paragraph(f"- {step}", bullet_style))
        
    story.append(PageBreak())

    # ────────────────────────────────────────────
    # PAGE 5: REGULATORY CITATIONS
    # ────────────────────────────────────────────
    story.append(Paragraph("4. Regulatory Citations (Evidence)", header_style))
    story.append(Paragraph("The following clauses were directly retrieved from official regulatory documents to formulate this report's findings.", body_style))
    story.append(Spacer(1, 10))
    
    clauses = analysis.get("applicable_clauses", [])
    if isinstance(clauses, list) and len(clauses) > 0:
        for c in clauses[:20]:
            title = str(c.get("title", "Clause"))
            source = str(c.get("source", ""))
            text = str(c.get("text", ""))[:1200]
            story.append(Paragraph(f"<b>Document / Source:</b> {source}", styles["Heading3"]))
            story.append(Paragraph(f"<b>Section:</b> {title}", styles["Normal"]))
            story.append(Paragraph(f'"{text}"', mono_style))
            story.append(Spacer(1, 15))
    else:
        story.append(Paragraph("No specific clauses were cited for this workflow.", body_style))
        
    # Superseded notes
    if analysis.get("superseded_references") or analysis.get("superseded_change_notes"):
        story.append(Spacer(1, 20))
        story.append(Paragraph("Superseded / Legacy Change Notes", styles["Heading2"]))
        for ref in _as_list(analysis.get("superseded_references")):
            story.append(Paragraph(f"• Reference: {ref}", bullet_style))
        for note in _as_list(analysis.get("superseded_change_notes")):
            story.append(Paragraph(f"• Note: {note}", bullet_style))

    story.append(PageBreak())

    # ────────────────────────────────────────────
    # PAGE 6+: WORKFLOW INTERACTION LOG (APPENDIX)
    # ────────────────────────────────────────────
    story.append(Paragraph("Appendix: Full Workflow Interaction Log", header_style))
    story.append(Paragraph("Below is the complete, immutable transcript of the workflow submitted for analysis. This context was used to generate the findings in this report.", body_style))
    story.append(Spacer(1, 10))

    workflow_input = analysis.get("workflow_input", {})
    workflow_text = ""
    if isinstance(workflow_input, dict):
        workflow_text = workflow_input.get("text", "")
    elif isinstance(workflow_input, str):
        workflow_text = workflow_input

    if workflow_text:
        # Split interaction log by common delimiters like "User Query:" or "AI Response:"
        # To make it readable in the PDF
        lines = workflow_text.split('\n')
        for line in lines:
            if line.strip():
                if line.startswith("User Query:") or line.startswith("AI Response:"):
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(f"<b>{line.strip()}</b>", styles["BodyText"]))
                else:
                    story.append(Paragraph(line.strip(), body_style))
    else:
        story.append(Paragraph("No interaction log provided.", body_style))

    # Build PDF
    doc = SimpleDocTemplate(
        str(out_path), 
        pagesize=A4,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=18
    )
    doc.build(story)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate extensive compliance PDF report")
    parser.add_argument("--input-json", required=True, help="Path to analysis json file")
    parser.add_argument("--report-id", required=True, help="Unique report id")
    parser.add_argument("--org-name", required=True, help="Organization name")
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Sometimes the analysis object is nested
    analysis = payload.get("analysis", payload)
    
    # Inject workflow text if passed at root
    if "workflow_input" not in analysis and "workflow_input" in payload:
        analysis["workflow_input"] = payload["workflow_input"]

    out = generate_report_pdf(analysis, report_id=args.report_id, org_name=args.org_name)
    print(str(out))


if __name__ == "__main__":
    main()
