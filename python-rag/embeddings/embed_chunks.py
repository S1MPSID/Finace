"""
Generate embeddings for chunk records in MongoDB.

Usage:
    cd python-rag
    python -m embeddings.embed_chunks
    python -m embeddings.embed_chunks --limit 500
    python -m embeddings.embed_chunks --batch-size 32
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from loguru import logger
from pymongo import UpdateOne
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.mongo import chunks as chunks_col
from embeddings.embedder import Embedder


_UNEMBEDDED_FILTER = {
    "$or": [
        {"embedded": {"$ne": True}},
        {"embedding": {"$exists": False}},
        {"embedding": []},
    ]
}


def _count_unembedded() -> int:
    return int(chunks_col().count_documents(_UNEMBEDDED_FILTER))


def _fetch_unembedded_page(page_size: int) -> list[dict]:
    """Fetch a small page of unembedded chunks (never load the full corpus)."""
    cursor = (
        chunks_col()
        .find(
            _UNEMBEDDED_FILTER,
            {"_id": 1, "chunk_id": 1, "text": 1},
            sort=[("chunk_id", 1)],
        )
        .limit(page_size)
        .max_time_ms(120000)
    )
    return list(cursor)


def embed_all(limit: int | None = None, batch_size: int = 32) -> dict:
    remaining = _count_unembedded()
    if limit is not None:
        remaining = min(remaining, limit)

    logger.info(f"Found {remaining} unembedded chunks to process")
    if remaining <= 0:
        return {"total": 0, "embedded": 0, "failed": 0}

    embedder = Embedder()
    stats = {"total": remaining, "embedded": 0, "failed": 0}
    processed = 0

    with tqdm(total=remaining, desc="Embedding chunks", unit="chunk") as bar:
        while processed < remaining:
            page_size = min(batch_size, remaining - processed)
            batch = _fetch_unembedded_page(page_size)
            if not batch:
                logger.warning("No more unembedded chunks returned; stopping early")
                break

            texts = [(r.get("text") or "").strip() for r in batch]
            safe_texts = [t if t else " " for t in texts]

            try:
                vectors = embedder.embed_texts(safe_texts, batch_size=len(batch))
            except Exception as exc:
                logger.error(f"Embedding batch failed at processed={processed}: {exc}")
                stats["failed"] += len(batch)
                processed += len(batch)
                bar.update(len(batch))
                continue

            now = datetime.now(timezone.utc).isoformat()
            ops: list[UpdateOne] = []
            for row, vec in zip(batch, vectors):
                ops.append(
                    UpdateOne(
                        {"_id": row["_id"]},
                        {
                            "$set": {
                                "embedding": vec,
                                "embedded": True,
                                "embedded_at": now,
                            }
                        },
                    )
                )

            try:
                chunks_col().bulk_write(ops, ordered=False)
                # Count by batch size; Atlas may report matched without modified.
                stats["embedded"] += len(batch)
            except Exception as exc:
                logger.error(f"Bulk write failed at processed={processed}: {exc}")
                # Fall back to per-doc updates so progress is not lost.
                for row, vec in zip(batch, vectors):
                    try:
                        chunks_col().update_one(
                            {"_id": row["_id"]},
                            {
                                "$set": {
                                    "embedding": vec,
                                    "embedded": True,
                                    "embedded_at": now,
                                }
                            },
                        )
                        stats["embedded"] += 1
                    except Exception as inner:
                        logger.error(
                            f"Failed updating chunk {row.get('chunk_id', str(row['_id']))}: {inner}"
                        )
                        stats["failed"] += 1

            processed += len(batch)
            bar.update(len(batch))

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate embeddings for unembedded chunks in MongoDB")
    parser.add_argument("--limit", type=int, default=None, help="Only embed first N unembedded chunks")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    args = parser.parse_args()

    logger.info("=== Chunk Embedding Pipeline ===")
    stats = embed_all(limit=args.limit, batch_size=args.batch_size)
    logger.success(
        f"Done — total: {stats['total']}, embedded: {stats['embedded']}, failed: {stats['failed']}"
    )


if __name__ == "__main__":
    main()
