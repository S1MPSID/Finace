"""
Embedding wrapper — fastembed (Render) or sentence-transformers (local).
"""
from __future__ import annotations

import os
from typing import Literal, Sequence

from config import settings

Backend = Literal["fastembed", "sentence_transformers"]


class Embedder:
    def __init__(
        self,
        model_name: str | None = None,
        local_files_only: bool = False,
        backend: str | None = None,
    ):
        self.model_name = model_name or settings.embedding_model
        self.local_files_only = local_files_only
        self.backend = (backend or settings.embedding_backend or "fastembed").lower()
        self._model: object | None = None
        self._backend_type: Backend | None = None

    def _resolve_backend(self) -> Backend:
        if self.backend in {"st", "sentence_transformers", "sentence-transformers"}:
            return "sentence_transformers"
        if self.backend == "fastembed":
            return "fastembed"
        # auto: prefer fastembed on production
        try:
            import fastembed  # noqa: F401

            return "fastembed"
        except ImportError:
            return "sentence_transformers"

    @property
    def model(self):
        if self._model is None:
            self._backend_type = self._resolve_backend()
            if self._backend_type == "fastembed":
                from fastembed import TextEmbedding

                cache_dir = settings.data_dir / "fastembed_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("FASTEMBED_CACHE_PATH", str(cache_dir))
                self._model = TextEmbedding(model_name=self.model_name)
            else:
                from sentence_transformers import SentenceTransformer

                cache_dir = settings.data_dir / "hf_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("HF_HOME", str(cache_dir))
                os.environ.setdefault("TRANSFORMERS_CACHE", str(cache_dir))
                self._model = SentenceTransformer(
                    self.model_name,
                    local_files_only=self.local_files_only,
                )
        return self._model

    def embed_texts(self, texts: Sequence[str], batch_size: int = 16) -> list[list[float]]:
        if not texts:
            return []

        self.model
        assert self._backend_type is not None

        if self._backend_type == "fastembed":
            vectors = list(self._model.embed(list(texts)))
            return [vector.tolist() for vector in vectors]

        vectors = self._model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vectors = self.embed_texts([text], batch_size=1)
        return vectors[0] if vectors else []
