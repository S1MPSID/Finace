"""
Service layer for the FastAPI wrapper.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import settings
from db.mongo import chunks, documents, get_client
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
    ) -> dict:
        return self.pipeline.analyze(
            call_type="general_query",
            workflow_text=prompt,
            top_k=top_k,
            regulator=regulator,
            category=category,
            status="active",
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
    ) -> dict:
        return self.pipeline.analyze(
            call_type=call_type,
            workflow_text=workflow_text,
            existing_report_text=existing_report_text,
            top_k=top_k,
            regulator=regulator,
            category=category,
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
        }
