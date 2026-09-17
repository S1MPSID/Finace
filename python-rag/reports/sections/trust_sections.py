"""Trust analytics and conversation snapshot PDF sections."""
from __future__ import annotations

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle


def _safe_str(value, default="—"):
    if value is None:
        return default
    return str(value)


def append_trust_analytics(story, styles, analysis: dict) -> None:
    trust = analysis.get("trust_stats") or {}
    if not trust:
        return

    base, header, body, bullet = styles["base"], styles["header"], styles["body"], styles["bullet"]
    story.append(Paragraph("5. Model Trust & Analytics Dashboard", header))
    story.append(Paragraph(
        "Hybrid compliance evaluation: official score, baseline φ₀, SHAP waterfall, "
        "per-requirement semantic ML status, rule checks, and regulation evidence.",
        body,
    ))
    story.append(Spacer(1, 10))

    # ── Headline: official score + baseline ──
    official = trust.get("official_score") or trust.get("latest_score")
    baseline = trust.get("baseline_score")
    delta_b = trust.get("delta_from_baseline", 0)
    headline_rows = [
        ["Official Score", f"{_safe_str(official)}/100"],
        ["Baseline (φ₀)", _safe_str(baseline)],
        ["Change from Baseline", f"{delta_b:+g}" if delta_b else "0"],
        ["AI Turns Analyzed", _safe_str(trust.get("turns"))],
        ["Latest Risk", _safe_str(trust.get("latest_risk", analysis.get("risk_level", "—")))],
        ["Computed At", _safe_str(trust.get("computed_at"))],
    ]
    table = Table(headline_rows, colWidths=[2.2 * inch, 3.8 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # ── SHAP waterfall ──
    waterfall = trust.get("waterfall") or []
    if waterfall:
        story.append(Paragraph("SHAP Waterfall (score breakdown)", base["Heading3"]))
        wf_rows = [["Factor", "Contribution"]]
        for row in waterfall:
            contrib = row.get("contribution", 0)
            wf_rows.append([
                str(row.get("label", row.get("feature", "?")))[:60],
                f"{contrib:+.2f}",
            ])
        wf_table = Table(wf_rows, colWidths=[4.0 * inch, 1.5 * inch])
        wf_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(wf_table)
        story.append(Spacer(1, 12))

    # ── Requirements breakdown ──
    requirements = trust.get("requirements") or []
    if requirements:
        story.append(Paragraph("Compliance Requirements Breakdown", base["Heading3"]))
        req_rows = [["Requirement", "Status", "Confidence", "Impact"]]
        for req in requirements:
            conf = req.get("confidence", 0)
            req_rows.append([
                str(req.get("requirement", req.get("id", "?")))[:50],
                str(req.get("status", "?")),
                f"{conf * 100:.0f}%" if conf else "—",
                f"{req.get('contribution', 0):+.1f}",
            ])
        req_table = Table(req_rows, colWidths=[2.5 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch])
        req_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(req_table)
        story.append(Spacer(1, 12))

    # ── Rule engine results ──
    rule_checks = trust.get("rule_checks") or []
    if rule_checks:
        story.append(Paragraph("Rule Engine Results", base["Heading3"]))
        for rule in rule_checks:
            rid = rule.get("id", "?")
            label = rule.get("label", rid)
            risk = rule.get("risk_level", "?")
            contrib = rule.get("contribution", 0)
            story.append(Paragraph(
                f"• {label} [{risk}] {contrib:+.1f}",
                bullet,
            ))
        story.append(Spacer(1, 12))

    # ── Semantic ML ──
    semantic_items = trust.get("semantic_items") or []
    if semantic_items:
        story.append(Paragraph("Semantic ML Evaluation", base["Heading3"]))
        for item in semantic_items:
            conf = item.get("confidence", 0)
            story.append(Paragraph(
                f"• {item.get('display_name') or item.get('requirement_id', '?')}: "
                f"{item.get('status', '?')} ({conf * 100:.0f}%) "
                f"[{item.get('model_source', 'ml')}]",
                bullet,
            ))
        story.append(Spacer(1, 12))

    # ── RAG evidence ──
    rag_evidence = trust.get("rag_evidence") or []
    if rag_evidence:
        story.append(Paragraph("RAG Evidence (retrieved regulation chunks)", base["Heading3"]))
        for ev in rag_evidence[:5]:
            doc_id = ev.get("document_id", "—")
            section = ev.get("section", "—")
            text = str(ev.get("text", ""))[:200]
            story.append(Paragraph(
                f"• [{doc_id}] {section}: {text}{'…' if len(str(ev.get('text', ''))) > 200 else ''}",
                bullet,
            ))
        story.append(Spacer(1, 12))

    # ── Legacy fields (backward compat) ──
    story.append(Paragraph("Legacy Trust Metrics", base["Heading3"]))
    story.append(Paragraph(
        f"Trust Index (legacy): {_safe_str(trust.get('trust_index'))} | "
        f"Score Δ (session): {trust.get('delta', 0):+g}",
        body,
    ))

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
