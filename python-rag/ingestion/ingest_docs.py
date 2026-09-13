"""
Entry point: walks RBI DOCS/, parses every PDF, stores in MongoDB documents collection
and saves raw parsed text to data/parsed/<regulation_id>.json

Usage:
    cd python-rag
    python -m ingestion.ingest_docs
    python -m ingestion.ingest_docs --limit 20       # test with first 20 files
    python -m ingestion.ingest_docs --reparse        # force re-parse already ingested docs
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import settings
from db.mongo import documents as docs_col
from ingestion.parser import parse_pdf
from ingestion.metadata_extractor import extract_metadata


def _find_all_pdfs(root: Path) -> list[Path]:
    # De-duplicate by normalized absolute path (Windows filesystems are case-insensitive).
    unique_paths: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        key = str(path.resolve()).lower()
        unique_paths[key] = path
    return sorted(unique_paths.values())


def _already_ingested(regulation_id: str) -> bool:
    return docs_col().find_one({"regulation_id": regulation_id}, {"_id": 1}) is not None


def _parsed_out_path(regulation_id: str) -> Path:
    out_dir = settings.data_dir / "parsed"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize regulation_id for use as filename
    safe_name = regulation_id.replace("/", "-").replace("\\", "-")
    digest = hashlib.sha1(regulation_id.encode("utf-8")).hexdigest()[:12]
    safe_prefix = safe_name[:48].rstrip("-_")
    safe_name = f"{safe_prefix}-{digest}" if safe_prefix else digest
    return out_dir / f"{safe_name}.json"


def _build_parsed_index() -> dict[str, Path]:
    """Map regulation_id -> existing parsed JSON path for fast reseeding."""
    out_dir = settings.data_dir / "parsed"
    index: dict[str, Path] = {}
    if not out_dir.exists():
        return index
    for path in out_dir.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            rid = payload.get("regulation_id")
            if isinstance(rid, str) and rid and rid not in index:
                index[rid] = path
        except Exception:
            continue
    logger.info(f"Loaded {len(index)} existing parsed JSON files from {out_dir}")
    return index


def _save_parsed_json(regulation_id: str, parsed_data: dict) -> Path:
    out_path = _parsed_out_path(regulation_id)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    return out_path


def ingest_all(limit: int | None = None, reparse: bool = False) -> dict:
    root = settings.rbi_docs_dir
    if not root.exists():
        logger.error(f"RBI DOCS directory not found: {root}")
        sys.exit(1)

    all_pdfs = _find_all_pdfs(root)
    logger.info(f"Found {len(all_pdfs)} PDF files under {root}")
    logger.info(f"Using data_dir={settings.data_dir}")

    if limit:
        all_pdfs = all_pdfs[:limit]
        logger.info(f"Limiting to first {limit} files")

    parsed_index = {} if reparse else _build_parsed_index()

    stats = {
        "total": len(all_pdfs),
        "ingested": 0,
        "skipped": 0,
        "failed": 0,
        "ocr": 0,
        "reused_parsed": 0,
    }

    for pdf_path in tqdm(all_pdfs, desc="Ingesting PDFs", unit="file"):
        try:
            meta = extract_metadata(pdf_path, root)
            regulation_id = meta["regulation_id"]

            if not reparse and _already_ingested(regulation_id):
                stats["skipped"] += 1
                continue

            parsed_data = None
            parsed_json_path: Path | None = None
            existing = parsed_index.get(regulation_id)
            if existing is not None and existing.exists():
                with open(existing, "r", encoding="utf-8") as f:
                    parsed_data = json.load(f)
                parsed_json_path = existing
                stats["reused_parsed"] += 1

            if parsed_data is None:
                # Parse PDF
                parsed = parse_pdf(pdf_path)

                if parsed.method == "ocr":
                    stats["ocr"] += 1

                # Save parsed JSON even if text extraction failed, so document record is preserved.
                parsed_data = {
                    "regulation_id": regulation_id,
                    "pdf_path": str(pdf_path),
                    "page_count": parsed.page_count,
                    "method": parsed.method,
                    "pages": parsed.pages,
                    "full_text": parsed.text,
                    "warnings": parsed.warnings,
                    "parsed_at": datetime.now(timezone.utc).isoformat(),
                }
                parsed_json_path = _save_parsed_json(regulation_id, parsed_data)

            assert parsed_json_path is not None
            full_text = (parsed_data.get("full_text") or "").strip()
            warnings = parsed_data.get("warnings") or []
            page_count = int(parsed_data.get("page_count") or 0)
            parse_method = parsed_data.get("method") or "unknown"

            # Update metadata with parse results
            meta.update({
                "page_count": page_count,
                "parse_method": parse_method,
                "parsed_text_path": str(parsed_json_path),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "char_count": len(full_text),
                "extraction_status": "success" if full_text else "failed",
                "extraction_warnings": warnings,
            })

            # Upsert into MongoDB
            docs_col().update_one(
                {"regulation_id": regulation_id},
                {"$set": meta},
                upsert=True,
            )

            if warnings:
                for w in warnings:
                    logger.warning(f"[{regulation_id}] {w}")

            if not full_text:
                logger.warning(f"No text extracted from {pdf_path.name} — stored metadata with failed status")
                stats["failed"] += 1
                continue

            stats["ingested"] += 1

        except Exception as exc:
            logger.error(f"Failed to ingest {pdf_path.name}: {exc}")
            stats["failed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Ingest RBI/NPCI PDFs into MongoDB")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N files")
    parser.add_argument("--reparse", action="store_true", help="Re-parse already ingested docs")
    args = parser.parse_args()

    logger.info("=== PDF Ingestion Pipeline ===")
    stats = ingest_all(limit=args.limit, reparse=args.reparse)
    logger.success(
        f"Done — ingested: {stats['ingested']}, skipped: {stats['skipped']}, "
        f"failed: {stats['failed']}, OCR used: {stats['ocr']}, "
        f"reused_parsed: {stats.get('reused_parsed', 0)}"
    )


if __name__ == "__main__":
    main()
