"""
FastAPI wrapper for the existing Python RAG pipeline.

Run:
    uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    ReportRequest,
    ReportResponse,
    ReportSignRequest,
    ReportSignResponse,
    ReportHashRequest,
    ReportHashResponse,
    IpfsRequest,
    IpfsResponse,
    ProofRequest,
    ProofResponse,
    SearchRequest,
    SearchResponse,
)
from api.services import RAGApiService


service = RAGApiService()


def _warmup_models() -> None:
    logger.info("Warming embedder (first load can take ~30s on t2.micro)...")
    service.retriever.embedder.embed_query("RBI KYC compliance warmup")
    logger.info("Embedder ready")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting python-rag FastAPI wrapper")
    warmup_task = None
    if os.getenv("WARM_EMBEDDER", "1") == "1":
        loop = asyncio.get_running_loop()
        # Do not block startup — PDF/report routes work without the embedder.
        warmup_task = loop.run_in_executor(None, _warmup_models)
        logger.info("Embedder warmup running in background (first run downloads ~1.3GB model)")
    yield
    if warmup_task is not None:
        try:
            await warmup_task
        except Exception:
            logger.exception("Embedder warmup failed")
    logger.info("Stopping python-rag FastAPI wrapper")


app = FastAPI(
    title="Finace Python RAG Wrapper",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(**service.health())


@app.post("/query", response_model=QueryResponse)
async def query_rag(payload: QueryRequest) -> QueryResponse:
    try:
        result = service.query(
            prompt=payload.prompt,
            top_k=payload.top_k,
            regulator=payload.regulator,
            category=payload.category,
        )
        return QueryResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail="RAG query failed") from exc


# ──────────────────────────────────────────────
# POST /analyze  — Full analysis with any call_type
# ──────────────────────────────────────────────
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = service.analyze(
            call_type=payload.call_type,
            workflow_text=payload.workflow_text,
            existing_report_text=payload.existing_report_text,
            top_k=payload.top_k,
            regulator=payload.regulator,
            category=payload.category,
        )
        return AnalyzeResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed") from exc


# ──────────────────────────────────────────────
# POST /report  — Generate a compliance report PDF
# ──────────────────────────────────────────────
@app.post("/report", response_model=ReportResponse)
async def generate_report(payload: ReportRequest) -> ReportResponse:
    try:
        result = service.generate_report(
            report_id=payload.report_id,
            org_name=payload.org_name,
            analysis=payload.analysis,
        )
        return ReportResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=500, detail="Report generation failed") from exc


@app.post("/report/sign", response_model=ReportSignResponse)
async def sign_report(payload: ReportSignRequest) -> ReportSignResponse:
    try:
        result = service.sign_report(
            pdf_path=payload.pdf_path,
            report_id=payload.report_id,
            signer_name=payload.signer_name,
            signer_role=payload.signer_role,
            remarks=payload.remarks,
        )
        return ReportSignResponse(
            ok=True,
            signed_pdf_path=result["signed_pdf_path"],
            document_hash=result["document_hash"],
            pdf_signature=result.get("pdf_signature", {}),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report signing failed")
        raise HTTPException(status_code=500, detail="Report signing failed") from exc


@app.post("/report/hash", response_model=ReportHashResponse)
async def hash_report_file(payload: ReportHashRequest) -> ReportHashResponse:
    try:
        result = service.hash_file(payload.file_path)
        return ReportHashResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report hash failed")
        raise HTTPException(status_code=500, detail="Report hash failed") from exc


# ──────────────────────────────────────────────
# POST /ipfs  — Upload report PDF to IPFS via Pinata
# ──────────────────────────────────────────────
@app.post("/ipfs", response_model=IpfsResponse)
async def upload_ipfs(payload: IpfsRequest) -> IpfsResponse:
    try:
        result = service.upload_to_ipfs(file_path=payload.file_path)
        return IpfsResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("IPFS upload failed")
        raise HTTPException(status_code=500, detail="IPFS upload failed") from exc


# ──────────────────────────────────────────────
# POST /proof  — Write compliance proof to blockchain
# ──────────────────────────────────────────────
@app.post("/proof", response_model=ProofResponse)
async def write_proof(payload: ProofRequest) -> ProofResponse:
    try:
        result = service.write_blockchain_proof(
            report_id=payload.report_id,
            ipfs_cid=payload.ipfs_cid,
            document_hash=payload.document_hash,
            org_name=payload.org_name,
            risk_level=payload.risk_level,
            contract_address=payload.contract_address,
        )
        return ProofResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Blockchain proof write failed")
        raise HTTPException(status_code=500, detail="Proof write failed") from exc


# ──────────────────────────────────────────────
# POST /search  — Search indexed regulations
# ──────────────────────────────────────────────
@app.post("/search", response_model=SearchResponse)
async def search_regulations(payload: SearchRequest) -> SearchResponse:
    try:
        result = service.search(
            query=payload.query,
            top_k=payload.top_k,
            regulator=payload.regulator,
        )
        return SearchResponse(**result)
    except Exception as exc:
        logger.exception("Regulation search failed")
        raise HTTPException(status_code=500, detail="Search failed") from exc
