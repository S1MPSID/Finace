"""
Service layer for the FastAPI wrapper.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from loguru import logger

from config import settings
from db.mongo import chunks, documents, get_client
from embeddings.embedder import Embedder
from ingestion.chunker import chunk_text
from ingestion.parser import parse_pdf
from ml.predict import get_predictor
from rag.rag_pipeline import RAGPipeline
from reports.report_generator import generate_report_pdf
from reports.pdf_signer import sign_report_pdf
from reports.pdf_hash import sha256_file
from storage.ipfs_uploader import upload_file_to_ipfs
from blockchain.proof_writer import store_proof
from retrieval.retriever import LocalRetriever


class DocumentCatalog:
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir

    def list_pdf_files(self) -> list[Path]:
        if not self.docs_dir.exists():
            return []
        return sorted(path for path in self.docs_dir.rglob("*.pdf") if path.is_file())

    def summary(self) -> dict[str, str | int]:
        files = self.list_pdf_files()
        return {
            "docs_dir": str(self.docs_dir),
            "pdf_count": len(files),
        }


class RAGApiService:
    def __init__(self):
        self.catalog = DocumentCatalog(settings.rbi_docs_dir)
        self._pipeline: RAGPipeline | None = None
        self._retriever: LocalRetriever | None = None

    @property
    def pipeline(self) -> RAGPipeline:
        if self._pipeline is None:
            logger.info("Initializing RAG pipeline for FastAPI wrapper")
            self._pipeline = RAGPipeline(retriever=self.retriever)
        return self._pipeline

    @property
    def retriever(self) -> LocalRetriever:
        if self._retriever is None:
            logger.info("Initializing LocalRetriever for FastAPI wrapper")
            self._retriever = LocalRetriever()
        return self._retriever

    # ── Existing: general query ──

    def query(
        self,
        prompt: str,
        top_k: int = 5,
        regulator: str | None = None,
        category: str | None = None,
        call_type: str = "general_query",
        active_categories: list[str] | None = None,
        enable_xai: bool = False,
        enable_semantic_ml: bool = False,
        calibration_frozen: dict[str, Any] | None = None,
        chat_id: str | None = None,
    ) -> dict:
        return self.pipeline.analyze(
            call_type=call_type,
            workflow_text=prompt,
            top_k=top_k,
            regulator=regulator,
            category=category,
            status="active",
            enable_xai=enable_xai,
            enable_semantic_ml=enable_semantic_ml,
            active_categories=active_categories or [],
            calibration_frozen=calibration_frozen,
            chat_id=chat_id,
        )

    # ── New: full analysis with any call_type ──

    def analyze(
        self,
        call_type: str = "general_query",
        workflow_text: str = "",
        existing_report_text: str = "",
        top_k: int = 5,
        regulator: str | None = None,
        category: str | None = None,
        active_categories: list[str] | None = None,
        enable_xai: bool | None = None,
        enable_semantic_ml: bool | None = None,
        calibration_frozen: dict[str, Any] | None = None,
        chat_id: str | None = None,
    ) -> dict:
        return self.pipeline.analyze(
            call_type=call_type,
            workflow_text=workflow_text,
            existing_report_text=existing_report_text,
            top_k=top_k,
            regulator=regulator,
            category=category,
            active_categories=active_categories or [],
            enable_xai=enable_xai,
            enable_semantic_ml=enable_semantic_ml,
            calibration_frozen=calibration_frozen,
            chat_id=chat_id,
        )

    # ── New: generate PDF report ──

    def generate_report(
        self,
        report_id: str,
        org_name: str,
        analysis: dict[str, Any],
    ) -> dict:
        pdf_path = generate_report_pdf(
            analysis=analysis,
            report_id=report_id,
            org_name=org_name,
        )

        return {
            "ok": True,
            "pdf_path": str(pdf_path),
            "report_id": report_id,
        }

    def sign_report(
        self,
        pdf_path: str,
        report_id: str,
        signer_name: str = "Authorized Evaluator",
        signer_role: str = "Compliance Evaluator",
        remarks: str = "",
    ) -> dict:
        result = sign_report_pdf(
            pdf_path,
            report_id=report_id,
            signer_name=signer_name,
            signer_role=signer_role,
            remarks=remarks,
        )
        return {"ok": True, **result}

    def hash_file(self, file_path: str) -> dict:
        return {"document_hash": sha256_file(file_path)}

    # ── New: upload to IPFS ──

    def upload_to_ipfs(self, file_path: str) -> dict:
        path = Path(file_path)
        result = upload_file_to_ipfs(path)
        return {
            "ipfs_cid": result["ipfs_cid"],
            "pin_size": result.get("pin_size", 0),
            "timestamp": result.get("timestamp", ""),
        }

    # ── New: write blockchain proof ──

    def write_blockchain_proof(
        self,
        report_id: str,
        ipfs_cid: str,
        document_hash: str,
        org_name: str,
        risk_level: str = "MEDIUM",
        contract_address: str = "",
    ) -> dict:
        addr = contract_address or settings.compliance_contract_address
        if not addr:
            raise RuntimeError("No contract address configured")

        result = store_proof(
            report_id=report_id,
            ipfs_cid=ipfs_cid,
            document_hash=document_hash,
            org_name=org_name,
            risk_level=risk_level,
            contract_address=addr,
        )
        return {"ok": True, "stdout": result.get("stdout", "")}

    # ── New: search regulations ──

    def search(
        self,
        query: str,
        top_k: int = 10,
        regulator: str | None = None,
    ) -> dict:
        hits = self.retriever.search(
            query_text=query,
            top_k=top_k,
            regulator=regulator,
            use_reranker=True,
        )
        
        # Format hits for the UI
        results = []
        for hit in hits:
            results.append({
                "title": hit.get("section", "Untitled"),
                "authority": hit.get("metadata", {}).get("regulator", "RBI"),
                "version": hit.get("metadata", {}).get("status", "active"),
                "summary": hit.get("text", "")[:500] + "...",
                "id": hit.get("chunk_id"),
                "metadata": hit.get("metadata", {})
            })
            
        return {"results": results}

    # ── What-if counterfactual re-score ──

    def what_if(
        self,
        baseline_score: float,
        score_breakdown: list[dict[str, Any]],
        flips: dict[str, Any] | None = None,
    ) -> dict:
        from xai.what_if import what_if_score

        return what_if_score(
            baseline=float(baseline_score),
            breakdown=score_breakdown,
            flips=flips,
        )

    # ── User-uploaded PDF: extract text (with OCR fallback) ──

    def upload_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        ingest: bool = False,
    ) -> dict:
        safe_name = Path(filename or "document.pdf").name
        if not safe_name.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported")

        upload_dir = settings.data_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = upload_dir / safe_name
        stored_path.write_bytes(file_bytes or b"")

        parsed = parse_pdf(stored_path)

        result = {
            "ok": parsed.method != "ocr_failed",
            "filename": safe_name,
            "stored_path": str(stored_path),
            "method": parsed.method,
            "page_count": parsed.page_count,
            "char_count": len(parsed.text),
            "text": parsed.text,
            "warnings": parsed.warnings or [],
            "extraction_status": "success" if parsed.text.strip() else "failed",
        }

        if ingest and parsed.text.strip():
            result["ingest"] = self._ingest_uploaded_document(
                filename=safe_name,
                stored_path=str(stored_path),
                page_count=parsed.page_count,
                parse_method=parsed.method,
                pages=parsed.pages,
                full_text=parsed.text,
                warnings=parsed.warnings,
            )

        return result

    def _ingest_uploaded_document(
        self,
        filename: str,
        stored_path: str,
        page_count: int,
        parse_method: str,
        pages: list[str],
        full_text: str,
        warnings: list[str],
    ) -> dict:
        """Chunk + embed the uploaded document and register it in MongoDB so the RAG
        retriever can match questions against it."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        base = re.sub(r"[^a-zA-Z0-9._-]+", "-", Path(filename).stem).strip("-")[:48]
        regulation_id = f"UPLOAD-{(base or 'doc')}-{stamp}"
        title = Path(filename).stem
        now = datetime.now(timezone.utc).isoformat()

        # Keep a servable copy in the same corpus directory the document-serving
        # API (backend /docs) reads from, so RAG citations open the same PDF.
        rel_dir = settings.rbi_docs_dir / "uploads"
        rel_dir.mkdir(parents=True, exist_ok=True)
        relative_path = f"uploads/{regulation_id}.pdf"
        shutil.copyfile(Path(stored_path), rel_dir / f"{regulation_id}.pdf")

        parsed_dir = settings.data_dir / "parsed"
        parsed_dir.mkdir(parents=True, exist_ok=True)
        parsed_path = parsed_dir / f"{regulation_id}.json"
        parsed_path.write_text(
            json.dumps(
                {
                    "regulation_id": regulation_id,
                    "pdf_path": stored_path,
                    "page_count": page_count,
                    "method": parse_method,
                    "pages": pages or [],
                    "full_text": full_text,
                    "warnings": warnings or [],
                    "parsed_at": now,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        docs_col = documents()
        docs_col.update_one(
            {"regulation_id": regulation_id},
            {"$set": {
                "regulation_id": regulation_id,
                "title": title,
                "source": filename,
                "relative_path": relative_path,
                "source_type": "user_upload",
                "regulator": "CUSTOM",
                "category": "UPLOAD",
                "status": "active",
                "issue_date": "",
                "supersedes": [],
                "topics": [],
                "pdf_path": stored_path,
                "parsed_text_path": str(parsed_path),
                "page_count": page_count,
                "parse_method": parse_method,
                "char_count": len(full_text),
                "extraction_status": "success" if full_text else "failed",
                "extraction_warnings": warnings or [],
                "ingested_at": now,
            }},
            upsert=True,
        )

        chunk_items = chunk_text(full_text)
        if not chunk_items:
            return {"regulation_id": regulation_id, "chunks_created": 0, "embedded": 0}

        embedder = Embedder()
        text_batch = [c.text for c in chunk_items]
        try:
            vectors = embedder.embed_texts(text_batch, batch_size=16)
        except Exception as exc:
            logger.warning(f"Embedding failed for uploaded doc {filename}: {exc}")
            vectors = [None] * len(chunk_items)

        rows: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunk_items):
            vector = vectors[index] if index < len(vectors) else None
            rows.append({
                "chunk_id": str(uuid4()),
                "document_id": regulation_id,
                "chunk_index": chunk.chunk_index,
                "section": chunk.section,
                "text": chunk.text,
                "token_count": chunk.token_count,
                "char_offset": chunk.char_offset,
                "embedding": vector or [],
                "embedded": vector is not None,
                "metadata": {
                    "regulator": "CUSTOM",
                    "category": "UPLOAD",
                    "status": "active",
                    "issue_date": "",
                    "title": title,
                    "source": filename,
                    "relative_path": relative_path,
                    "source_type": "user_upload",
                },
                "created_at": now,
            })

        chunks_col = chunks()
        if rows:
            chunks_col.insert_many(rows, ordered=True)

        docs_col.update_one(
            {"regulation_id": regulation_id},
            {"$set": {"chunked": True, "chunk_count": len(rows), "chunked_at": now}},
        )

        return {
            "regulation_id": regulation_id,
            "chunks_created": len(rows),
            "embedded": sum(1 for r in rows if r.get("embedded")),
        }

    # ── Health check ──

    def health(self) -> dict:
        docs_summary = self.catalog.summary()
        mongo_ready = True
        indexed_documents = 0
        indexed_chunks = 0

        try:
            get_client().admin.command("ping")
            indexed_documents = documents().count_documents({})
            indexed_chunks = chunks().count_documents({})
        except Exception as exc:
            logger.warning(f"Mongo health check failed: {exc}")
            mongo_ready = False

        return {
            "ok": True,
            "service": "python-rag-fastapi",
            "timestamp": datetime.now(timezone.utc),
            "embedding_backend": settings.embedding_backend,
            "embedding_model": settings.embedding_model,
            "rag_light_xai": settings.rag_light_xai,
            "rag_ready": docs_summary["pdf_count"] > 0,
            "mongo_ready": mongo_ready,
            "docs_dir": docs_summary["docs_dir"],
            "pdf_count": docs_summary["pdf_count"],
            "indexed_documents": indexed_documents,
            "indexed_chunks": indexed_chunks,
            "llm_provider": settings.llm_provider,
            "llm_model": (
                settings.gemini_model
                if settings.llm_provider in {"gemini", "google"}
                else settings.nvidia_model
                if settings.llm_provider == "nvidia"
                else settings.groq_model
                if settings.llm_provider == "groq"
                else settings.xai_model
            ),
            "llm_enabled": os.getenv("RAG_ENABLE_LLM", "1") == "1"
            and bool(
                settings.gemini_api_key
                or settings.nvidia_api_key
                or settings.groq_api_key
                or settings.xai_api_key
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("NVIDIA_API_KEY")
                or os.getenv("GROQ_API_KEY")
                or os.getenv("GROK_API_KEY")
            ),
            "ml_risk_ready": get_predictor().available,
            "ml_risk_model": get_predictor().model_name,
        }
