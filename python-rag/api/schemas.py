"""
Pydantic request/response models for the FastAPI wrapper.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Existing models ──

class QueryRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=32000)
    top_k: int = Field(default=5, ge=1, le=20)
    regulator: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)


class QueryResponse(BaseModel):
    analysis: dict[str, Any]
    rules: dict[str, Any]
    retrieval_hits: list[dict[str, Any]]
    xai: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    ok: bool
    service: str
    timestamp: datetime
    rag_ready: bool
    mongo_ready: bool
    docs_dir: str
    pdf_count: int
    indexed_documents: int
    indexed_chunks: int
    llm_provider: str
    llm_model: str
    llm_enabled: bool


# ── New: /analyze ──

class AnalyzeRequest(BaseModel):
    call_type: Literal["general_query", "new_report", "update_report"] = "general_query"
    workflow_text: str = Field(min_length=3, max_length=10000)
    existing_report_text: str = Field(default="", max_length=20000)
    top_k: int = Field(default=5, ge=1, le=20)
    regulator: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)


class AnalyzeResponse(BaseModel):
    analysis: dict[str, Any]
    rules: dict[str, Any]
    retrieval_hits: list[dict[str, Any]]
    xai: dict[str, Any] = Field(default_factory=dict)


# ── New: /report ──

class ReportRequest(BaseModel):
    report_id: str = Field(min_length=1, max_length=100)
    org_name: str = Field(min_length=1, max_length=200)
    analysis: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    ok: bool = True
    pdf_path: str
    report_id: str


class ReportSignRequest(BaseModel):
    pdf_path: str = Field(min_length=1)
    report_id: str = Field(min_length=1, max_length=100)
    signer_name: str = Field(default="Authorized Evaluator", max_length=200)
    signer_role: str = Field(default="Compliance Evaluator", max_length=200)
    remarks: str = Field(default="", max_length=2000)


class ReportSignResponse(BaseModel):
    ok: bool = True
    signed_pdf_path: str
    document_hash: str
    pdf_signature: dict[str, Any] = Field(default_factory=dict)


class ReportHashRequest(BaseModel):
    file_path: str = Field(min_length=1)


class ReportHashResponse(BaseModel):
    document_hash: str


# ── New: /ipfs ──

class IpfsRequest(BaseModel):
    file_path: str = Field(min_length=1)


class IpfsResponse(BaseModel):
    ipfs_cid: str
    pin_size: int = 0
    timestamp: str = ""


# ── New: /proof ──

class ProofRequest(BaseModel):
    report_id: str = Field(min_length=1)
    ipfs_cid: str = Field(min_length=1)
    document_hash: str = Field(min_length=1)
    org_name: str = Field(min_length=1)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    contract_address: str = Field(default="")


class ProofResponse(BaseModel):
    ok: bool = True
    stdout: str = ""


# ── New: /search ──

class SearchRequest(BaseModel):
    query: str = Field(min_length=0)
    top_k: int = Field(default=10, ge=1, le=50)
    regulator: str | None = Field(default=None)


class SearchResponse(BaseModel):
    results: list[dict[str, Any]]
