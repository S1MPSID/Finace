"""Page headers, footers, and numbering for compliance PDFs."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def _draw_header_footer(c: canvas.Canvas, doc, report_id: str, report_kind: str) -> None:
    c.saveState()
    w, h = doc.pagesize

    c.setStrokeColor(colors.HexColor("#1e3a5f"))
    c.setLineWidth(0.75)
    c.line(0.75 * inch, h - 0.55 * inch, w - 0.75 * inch, h - 0.55 * inch)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#1e3a5f"))
    c.drawString(0.75 * inch, h - 0.45 * inch, "FINACE REGULATORY COMPLIANCE REPORT")
    c.setFont("Helvetica", 8)
    c.drawRightString(w - 0.75 * inch, h - 0.45 * inch, report_kind.upper())

    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.line(0.75 * inch, 0.65 * inch, w - 0.75 * inch, 0.65 * inch)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(0.75 * inch, 0.45 * inch, f"Report ID: {report_id}")
    c.drawCentredString(w / 2, 0.45 * inch, "CONFIDENTIAL — FOR REGULATORY & INTERNAL USE")
    c.drawRightString(w - 0.75 * inch, 0.45 * inch, f"Page {c.getPageNumber()}")
    c.restoreState()


def make_page_callbacks(report_id: str, report_kind: str):
    def on_page(c: canvas.Canvas, doc) -> None:
        _draw_header_footer(c, doc, report_id, report_kind)

    return on_page, on_page
