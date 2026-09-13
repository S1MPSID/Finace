"""ReportLab style helpers for formal compliance PDFs."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


NAVY = colors.HexColor("#1e3a5f")
SLATE = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748b")
LIGHT_BG = colors.HexColor("#f8fafc")
ACCENT = colors.HexColor("#0f766e")


def build_pdf_styles():
    base = getSampleStyleSheet()
    return {
        "base": base,
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontSize=26,
            leading=30,
            spaceAfter=8,
            textColor=NAVY,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Heading2"],
            fontSize=13,
            leading=16,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=24,
        ),
        "cover_kind": ParagraphStyle(
            "CoverKind",
            parent=base["Heading1"],
            fontSize=15,
            leading=18,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=20,
            fontName="Helvetica-Bold",
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading1"],
            fontSize=14,
            leading=18,
            spaceBefore=18,
            spaceAfter=10,
            textColor=NAVY,
            fontName="Helvetica-Bold",
            borderPadding=4,
        ),
        "subsection": ParagraphStyle(
            "Subsection",
            parent=base["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=SLATE,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            textColor=SLATE,
        ),
        "body_left": ParagraphStyle(
            "BodyLeft",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=6,
            textColor=SLATE,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            leftIndent=14,
            bulletIndent=0,
            spaceAfter=5,
            textColor=SLATE,
        ),
        "mono": ParagraphStyle(
            "Mono",
            parent=base["BodyText"],
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            textColor=SLATE,
            leftIndent=8,
            rightIndent=8,
            backColor=LIGHT_BG,
            borderColor=colors.HexColor("#e2e8f0"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "toc": ParagraphStyle(
            "TOC",
            parent=base["BodyText"],
            fontSize=10,
            leading=16,
            leftIndent=12,
            textColor=SLATE,
        ),
        "legal_notice": ParagraphStyle(
            "LegalNotice",
            parent=base["BodyText"],
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "cert": ParagraphStyle(
            "Cert",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            textColor=SLATE,
            spaceAfter=10,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontSize=8,
            leading=10,
            textColor=SLATE,
            alignment=TA_LEFT,
            wordWrap="LTR",
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
            wordWrap="LTR",
        ),
    }


def as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []
