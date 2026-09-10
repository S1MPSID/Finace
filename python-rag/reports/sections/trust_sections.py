"""Trust analytics and conversation snapshot PDF sections."""
from __future__ import annotations

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle


def append_trust_analytics(story, styles, analysis: dict) -> None:
    trust = analysis.get("trust_stats") or {}
    if not trust:
        return

    base, header, body, bullet = styles["base"], styles["header"], styles["body"], styles["bullet"]
    story.append(Paragraph("5. Model Trust & Analytics Dashboard", header))
    story.append(Paragraph(
        "Statistics from the Compliance Studio conversation: scores, SHAP/LIME drivers, "
        "retrieval evidence, and control coverage.",
        body,
    ))
    story.append(Spacer(1, 10))

    rows = [
        ["Trust Index (0-100)", str(trust.get("trust_index", "—"))],
        ["AI Turns Analyzed", str(trust.get("turns", "—"))],
        ["Latest Score", str(trust.get("latest_score", analysis.get("compliance_score", "—")))],
        ["Latest Risk", str(trust.get("latest_risk", analysis.get("risk_level", "—")))],
        ["Score Change (Δ)", str(trust.get("delta", 0))],
        ["Computed At", str(trust.get("computed_at", "—"))],
    ]
    table = Table(rows, colWidths=[2.2 * inch, 3.8 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Trust Factor Breakdown", base["Heading3"]))
    for factor in trust.get("factor_radar") or []:
        story.append(Paragraph(f"• {factor.get('name', 'Factor')}: {factor.get('score', 0)}/100", bullet))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Score Trajectory", base["Heading3"]))
    for row in trust.get("score_series") or []:
        story.append(Paragraph(
            f"• {row.get('turn')}: score={row.get('score')}, risk={row.get('risk')}, sources={row.get('sources', 0)}",
            bullet,
        ))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Top SHAP Drivers", base["Heading3"]))
    for driver in trust.get("top_drivers") or []:
        story.append(Paragraph(f"• {driver}", bullet))

    story.append(PageBreak())


def append_conversation_snapshots(story, styles, analysis: dict) -> None:
    snapshots = analysis.get("conversation_snapshots") or []
    if not snapshots:
        return

    base, header, body, bullet = styles["base"], styles["header"], styles["body"], styles["bullet"]
    story.append(Paragraph("6. Compliance Conversation Snapshots", header))
    story.append(Paragraph("Per-turn snapshots with scores and XAI summaries.", body))

    for snap in snapshots:
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"<b>Turn {snap.get('index')} — {str(snap.get('role', '')).upper()}</b>",
            base["Heading3"],
        ))
        if snap.get("compliance_score") is not None:
            story.append(Paragraph(
                f"Score: {snap.get('compliance_score')} | Risk: {snap.get('risk_level', '—')} | "
                f"Sources: {snap.get('sources_count', 0)}",
                body,
            ))
        content = str(snap.get("content", ""))[:2000]
        if content:
            story.append(Paragraph(content.replace("\n", "<br/>"), body))
        for d in (snap.get("xai_summary") or {}).get("top_drivers") or []:
            story.append(Paragraph(f"• {d}", bullet))

    story.append(PageBreak())
