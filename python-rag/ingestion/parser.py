"""
PDF text extractor with 3-tier fallback:
  1. pymupdf  — fast, works on searchable PDFs
  2. pdfplumber — better table/layout handling
  3. pytesseract OCR — for scanned/image-only PDFs
"""
from __future__ import annotations
import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from loguru import logger


@dataclass
class ParsedDocument:
    text: str               # full concatenated text
    pages: list[str]        # per-page text list
    page_count: int
    method: str             # "pymupdf" | "pdfplumber" | "ocr"
    warnings: list[str]


_MIN_TEXT_CHARS_PER_PAGE = 50   # below this threshold → suspect scan/image PDF
_MIN_TOTAL_TEXT_CHARS = 200     # very short extraction across full file is likely sparse/failed


def _parse_with_pymupdf(pdf_path: Path) -> ParsedDocument | None:
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)

        def _collect_text(sort_text: bool) -> tuple[str, list[str]]:
            page_texts = []
            for page_index in range(page_count):
                page = doc[page_index]
                page_texts.append(page.get_text("text", sort=sort_text))
            joined = "\n\n".join(page_texts).strip()
            return joined, page_texts

        # First pass: default extraction
        full_text, pages = _collect_text(sort_text=False)
        avg_chars = len(full_text) / max(page_count, 1)
        is_sparse = avg_chars < _MIN_TEXT_CHARS_PER_PAGE or len(full_text) < _MIN_TOTAL_TEXT_CHARS

        # Second pass: sorted extraction can recover more coherent text in some PDFs
        if is_sparse:
            sorted_text, sorted_pages = _collect_text(sort_text=True)
            sorted_avg_chars = len(sorted_text) / max(page_count, 1)
            sorted_sparse = (
                sorted_avg_chars < _MIN_TEXT_CHARS_PER_PAGE
                or len(sorted_text) < _MIN_TOTAL_TEXT_CHARS
            )
            if not sorted_sparse:
                full_text, pages = sorted_text, sorted_pages
                is_sparse = False

        doc.close()
        if is_sparse:
            return None   # likely scanned or extraction failed — fallback needed

        return ParsedDocument(
            text=full_text,
            pages=pages,
            page_count=page_count,
            method="pymupdf",
            warnings=[],
        )
    except Exception as exc:
        logger.debug(f"pymupdf failed on {pdf_path.name}: {exc}")
        return None


def _parse_with_pdfplumber(pdf_path: Path) -> ParsedDocument | None:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                # Also extract tables and append as text
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        cells = [str(c or "").strip() for c in row]
                        text += "\n" + " | ".join(cells)
                pages.append(text.strip())
        full_text = "\n\n".join(pages).strip()
        avg_chars = len(full_text) / max(len(pages), 1)
        if avg_chars < _MIN_TEXT_CHARS_PER_PAGE:
            return None
        return ParsedDocument(
            text=full_text,
            pages=pages,
            page_count=len(pages),
            method="pdfplumber",
            warnings=[],
        )
    except Exception as exc:
        logger.debug(f"pdfplumber failed on {pdf_path.name}: {exc}")
        return None


def _parse_with_ocr(pdf_path: Path) -> ParsedDocument:
    """Last resort: convert PDF pages to images, run Tesseract OCR."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
        import io

        if not shutil.which("tesseract"):
            for candidate in (
                os.getenv("TESSERACT_CMD", ""),
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ):
                if candidate and Path(candidate).exists():
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    break

        doc = fitz.open(str(pdf_path))
        pages = []
        warnings = []
        for i, page in enumerate(doc):
            # Render page at 200 DPI for decent OCR quality
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                text = pytesseract.image_to_string(img, lang="eng")
                pages.append(text.strip())
            except Exception as e:
                warnings.append(f"OCR failed on page {i + 1}: {e}")
                pages.append("")
        doc.close()
        return ParsedDocument(
            text="\n\n".join(pages).strip(),
            pages=pages,
            page_count=len(pages),
            method="ocr",
            warnings=warnings,
        )
    except ImportError as exc:
        message = (
            f"OCR dependency missing for {pdf_path.name}: {exc}. "
            "Install Tesseract OCR and ensure it is available on PATH."
        )
        logger.error(message)
        return ParsedDocument(
            text="",
            pages=[],
            page_count=0,
            method="ocr_failed",
            warnings=[message],
        )
    except Exception as exc:
        message = f"OCR failed for {pdf_path.name}: {exc}"
        logger.error(message)
        return ParsedDocument(
            text="",
            pages=[],
            page_count=0,
            method="ocr_failed",
            warnings=[message],
        )


def parse_pdf(pdf_path: Path) -> ParsedDocument:
    """
    Parse a PDF and return a ParsedDocument.
    Tries pymupdf → pdfplumber → OCR in order.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    # Tier 1 — pymupdf
    result = _parse_with_pymupdf(path)
    if result:
        return result

    # Tier 2 — pdfplumber
    logger.debug(f"pymupdf returned sparse text for {path.name}, trying pdfplumber")
    result = _parse_with_pdfplumber(path)
    if result:
        return result

    # Tier 3 — OCR
    logger.warning(f"PDF appears to be scanned, running OCR on {path.name}")
    return _parse_with_ocr(path)
