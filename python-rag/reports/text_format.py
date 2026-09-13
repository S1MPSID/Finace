"""Convert Markdown / HTML chat content into ReportLab-safe rich text."""
from __future__ import annotations

import re
from xml.sax.saxutils import escape


def _md_inline(text: str) -> str:
    """Escape XML and apply inline markdown (bold/italic)."""
    out = escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", out)
    return out


def _expand_inline_markdown(text: str) -> str:
    """Break inline ### / ## markers onto their own lines."""
    text = re.sub(r"(?<!\n)(#{1,3}\s+)", r"\n\1", text)
    text = re.sub(r"(?<!\n)(\*\*[^*]+\*\*)", r"\n\1", text)
    # Remove lines that are only stray hash marks (e.g. lone "#" after ===== END =====)
    text = re.sub(r"(?m)^#+\s*$\n?", "", text)
    return text


def _is_decorative_line(stripped: str) -> bool:
    if not stripped:
        return True
    if re.fullmatch(r"#+\s*", stripped):
        return True
    if re.fullmatch(r"[=\-]{3,}", stripped):
        return True
    if re.fullmatch(r"[=#\-\s]+", stripped):
        return True
    upper = stripped.upper()
    return upper in {"END", "===== END =====", "===== CONVERSATION ====="}


def _normalize_html_breaks(text: str) -> str:
    for level in range(6, 0, -1):
        text = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            lambda m, lvl=level: f"\n\n{'#' * min(lvl, 3)} {m.group(1).strip()}\n",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>\s*", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?o[lu][^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    return _expand_inline_markdown(text)


def _strip_unsupported_tags(text: str) -> str:
    """Keep only b, i, u tags for ReportLab Paragraph."""
    allowed = {"b", "i", "u", "/b", "/i", "/u"}

    def repl(match: re.Match) -> str:
        closing = match.group(1) or ""
        tag = (match.group(2) or "").lower()
        key = f"{closing}{tag}"
        if key in allowed:
            return f"<{key}>"
        return ""

    return re.sub(r"</?([\w]+)[^>]*>", repl, text, flags=re.IGNORECASE)


def html_or_markdown_to_reportlab(raw: str) -> str:
    """Single paragraph markup safe for ReportLab."""
    if not raw:
        return ""
    text = _normalize_html_breaks(str(raw))
    text = _strip_unsupported_tags(text)
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _is_decorative_line(stripped):
            continue
        if stripped.startswith("### "):
            lines.append(f"<b><font size=11>{_md_inline(stripped[4:])}</font></b>")
        elif stripped.startswith("## "):
            lines.append(f"<b><font size=12>{_md_inline(stripped[3:])}</font></b>")
        elif stripped.startswith("# "):
            lines.append(f"<b><font size=13>{_md_inline(stripped[2:])}</font></b>")
        elif stripped.startswith("• ") or stripped.startswith("- "):
            lines.append(f"• {_md_inline(stripped.lstrip('•- ').strip())}")
        else:
            lines.append(_md_inline(stripped))
    return "<br/>".join(lines)


def iter_reportlab_blocks(raw: str) -> list[tuple[str, str]]:
    """
    Yield (style_key, markup) blocks for PDF story assembly.
    style_key: section | subsection | body | bullet | spacer
    """
    if not raw:
        return []

    text = _normalize_html_breaks(str(raw))
    blocks: list[tuple[str, str]] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if _is_decorative_line(stripped):
            if re.fullmatch(r"[=\-]{3,}", stripped) or re.fullmatch(r"=+", stripped):
                blocks.append(("spacer", ""))
            continue
        upper = stripped.upper()
        if stripped.startswith("### "):
            blocks.append(("subsection", f"<b>{_md_inline(stripped[4:])}</b>"))
        elif stripped.startswith("## "):
            blocks.append(("subsection", f"<b>{_md_inline(stripped[3:])}</b>"))
        elif stripped.startswith("# "):
            blocks.append(("subsection", f"<b>{_md_inline(stripped[2:])}</b>"))
        elif (
            upper.startswith("USER TURN")
            or upper.startswith("ASSISTANT TURN")
            or upper.startswith("CURRENT USER MESSAGE")
        ):
            blocks.append(("subsection", f"<b>{_md_inline(stripped)}</b>"))
        elif stripped.startswith("• ") or stripped.startswith("- "):
            blocks.append(("bullet", _md_inline(stripped.lstrip("•- ").strip())))
        else:
            blocks.append(("body", _md_inline(stripped)))

    return blocks


def append_rich_text(story, styles, raw: str, default_style: str = "body") -> None:
    """Append formatted blocks to a ReportLab story."""
    from reportlab.platypus import Paragraph, Spacer

    style_map = {
        "section": styles.get("section"),
        "subsection": styles.get("subsection"),
        "body": styles.get("body") or styles.get("body_left"),
        "bullet": styles.get("bullet"),
    }

    blocks = iter_reportlab_blocks(raw)
    if not blocks and raw:
        markup = html_or_markdown_to_reportlab(raw)
        if markup:
            story.append(Paragraph(markup, style_map.get(default_style) or styles["body"]))
        return

    for kind, markup in blocks:
        if kind == "spacer":
            story.append(Spacer(1, 8))
            continue
        if not markup:
            continue
        para_style = style_map.get(kind) or style_map.get(default_style) or styles["body"]
        story.append(Paragraph(markup[:4000], para_style))
