"""ReportLab table helpers with wrapping Paragraph cells."""
from __future__ import annotations

import re
from xml.sax.saxutils import escape

from reportlab.platypus import Paragraph


def plain_cell_text(raw: str) -> str:
    """Strip HTML / markdown noise for compact table cells."""
    text = str(raw or "").strip()
    if not text:
        return "—"
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text or "—"


def truncate_middle(text: str, max_len: int = 48) -> str:
    if len(text) <= max_len:
        return text
    half = (max_len - 3) // 2
    return f"{text[:half]}…{text[-half:]}"


def table_cell(text, styles, header: bool = False) -> Paragraph:
    style_key = "table_head" if header else "table_cell"
    content = escape(plain_cell_text(text))
    return Paragraph(content, styles[style_key])


def wrap_table_rows(rows: list[list], styles, header_row: bool = True) -> list[list]:
    wrapped: list[list] = []
    for row_idx, row in enumerate(rows):
        is_header = header_row and row_idx == 0
        wrapped.append([table_cell(cell, styles, header=is_header) for cell in row])
    return wrapped
