"""
Local cosine-similarity retriever over MongoDB chunk embeddings.

Usage:
    cd python-rag
    python -m retrieval.retriever --query "What are AePS chargeback rules?" --top-k 5
    python -m retrieval.retriever --query "KYC requirements" --regulator RBI --status active
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import numpy as np
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import settings
from db.mongo import chunks as chunks_col
from embeddings.embedder import Embedder
from retrieval.reranker import rerank_hits


class LocalRetriever:
    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or Embedder()

    def _build_filter(
        self,
        regulator: str | None = None,
        category: str | None = None,
        status: str = "active",
    ) -> dict[str, Any]:
        query: dict[str, Any] = {"embedded": True}
        if status:
            query["metadata.status"] = status
        if regulator:
            query["metadata.regulator"] = regulator
        if category:
            query["metadata.category"] = category
        return query

    def _load_candidates(self, mongo_filter: dict[str, Any]) -> tuple[list[dict], np.ndarray]:
        limit = max(50, int(settings.retrieval_max_candidates))
        rows = list(
            chunks_col().find(
                mongo_filter,
                {
                    "_id": 0,
                    "chunk_id": 1,
                    "document_id": 1,
                    "chunk_index": 1,
                    "section": 1,
                    "text": 1,
                    "metadata": 1,
                    "embedding": 1,
                },
            ).limit(limit)
        )
        if not rows:
            return [], np.empty((0, 0), dtype=np.float32)

        vectors: list[list[float]] = []
        filtered_rows: list[dict] = []
        for row in rows:
            emb = row.get("embedding") or []
            if not emb:
                continue
            vectors.append(emb)
            filtered_rows.append(row)

        if not vectors:
            return [], np.empty((0, 0), dtype=np.float32)
        matrix = np.asarray(vectors, dtype=np.float32)
        return filtered_rows, matrix

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        regulator: str | None = None,
        category: str | None = None,
        status: str = "active",
        use_reranker: bool = True,
    ) -> list[dict]:
        if not query_text.strip():
            return []

        mongo_filter = self._build_filter(regulator=regulator, category=category, status=status)
        candidates, matrix = self._load_candidates(mongo_filter)
        if not candidates:
            logger.warning("No embedded chunks found for given filters")
            return []

        q_vec = np.asarray(self.embedder.embed_query(query_text), dtype=np.float32)
        if q_vec.size == 0:
            logger.warning("Query embedding failed")
            return []

        # For normalized embeddings this is cosine similarity.
        if q_vec.ndim == 1:
            q_vec = q_vec.reshape(1, -1)
        if matrix.shape[1] != q_vec.shape[1]:
            raise ValueError(
                f"Embedding dimension mismatch: chunks={matrix.shape[1]} query={q_vec.shape[1]}"
            )

        scores = (matrix @ q_vec.T).reshape(-1)
        k = max(1, min(top_k, len(candidates)))
        top_idx = np.argpartition(-scores, k - 1)[:k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]

        hits: list[dict] = []
        for idx in top_idx:
            row = candidates[int(idx)]
            hits.append(
                {
                    "chunk_id": row.get("chunk_id"),
                    "document_id": row.get("document_id"),
                    "chunk_index": row.get("chunk_index"),
                    "section": row.get("section"),
                    "text": row.get("text", ""),
                    "metadata": row.get("metadata", {}),
                    "score": float(scores[int(idx)]),
                }
            )

        if use_reranker:
            hits = rerank_hits(query_text, hits)
        return hits


def _print_hits(hits: list[dict]) -> None:
    if not hits:
        logger.info("No results")
        return
    for i, hit in enumerate(hits, start=1):
        snippet = " ".join((hit.get("text") or "").split())[:220]
        logger.info(
            f"[{i}] score={hit['score']:.4f} doc={hit['document_id']} "
            f"section={hit.get('section', 'GENERAL')}"
        )
        logger.info(f"    {snippet}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local retrieval over MongoDB chunk embeddings")
    parser.add_argument("--query", required=True, help="Query string")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--regulator", default=None, help="Optional filter: RBI/NPCI")
    parser.add_argument("--category", default=None, help="Optional filter: AEPS/NFS/KYC etc.")
    parser.add_argument("--status", default="active", help="Optional filter: active/superseded")
    parser.add_argument("--no-rerank", action="store_true", help="Disable lexical reranking")
    args = parser.parse_args()

    retriever = LocalRetriever()
    hits = retriever.search(
        query_text=args.query,
        top_k=args.top_k,
        regulator=args.regulator,
        category=args.category,
        status=args.status,
        use_reranker=not args.no_rerank,
    )
    _print_hits(hits)


if __name__ == "__main__":
    main()
