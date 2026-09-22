"""
Run this once to set up MongoDB indexes.
Usage: python -m db.schema
"""
from pymongo import ASCENDING, DESCENDING, IndexModel
from loguru import logger
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.mongo import documents, chunks, users, reports


def setup_indexes():
    # --- documents collection ---
    docs = documents()
    docs.create_indexes([
        IndexModel([("regulation_id", ASCENDING)], unique=True),
        IndexModel([("regulator", ASCENDING)]),
        IndexModel([("category", ASCENDING)]),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("issue_date", DESCENDING)]),
        IndexModel([("topics", ASCENDING)]),
    ])
    logger.info("documents: indexes created")

    # --- chunks collection ---
    cks = chunks()
    cks.create_indexes([
        IndexModel([("chunk_id", ASCENDING)], unique=True),
        IndexModel([("document_id", ASCENDING)]),
        IndexModel([("embedded", ASCENDING)]),  # track embedding status
        IndexModel([("created_at", DESCENDING)]),  # recent-first candidate scan
        IndexModel([("metadata.regulator", ASCENDING)]),
        IndexModel([("metadata.category", ASCENDING)]),
        IndexModel([("metadata.status", ASCENDING)]),
    ])
    logger.info("chunks: indexes created")

    # --- users collection ---
    us = users()
    us.create_indexes([
        IndexModel([("email", ASCENDING)], unique=True),
        IndexModel([("role", ASCENDING)]),
    ])
    logger.info("users: indexes created")

    # --- reports collection ---
    rpts = reports()
    rpts.create_indexes([
        IndexModel([("report_id", ASCENDING)], unique=True),
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
    ])
    logger.info("reports: indexes created")

    logger.success("All MongoDB indexes set up successfully.")


# Document schema examples (for reference — MongoDB is schemaless)
DOCUMENT_SCHEMA = {
    "regulation_id": str,       # unique slug e.g. "RBI-KYC-2024-01"
    "title": str,
    "source": str,              # original filename
    "regulator": str,           # "RBI" | "NPCI"
    "category": str,            # "KYC" | "AEPS" | "NFS" | ...
    "status": str,              # "active" | "superseded" | "partially_modified"
    "issue_date": str,          # ISO date string or empty
    "supersedes": list,         # list of regulation_ids this replaces
    "topics": list,             # inferred topic tags
    "pdf_path": str,            # absolute path to source PDF
    "parsed_text_path": str,    # path to data/parsed/<id>.json
    "page_count": int,
    "ingested_at": str,         # ISO datetime
}

CHUNK_SCHEMA = {
    "chunk_id": str,            # uuid
    "document_id": str,         # regulation_id of parent
    "chunk_index": int,         # position within document
    "section": str,             # section heading if detected
    "text": str,                # chunk text
    "token_count": int,
    "char_offset": int,         # start char in original text
    "embedding": list,          # float32 list, length = embedding_dim
    "embedded": bool,           # whether embedding has been generated
    "metadata": {
        "regulator": str,
        "category": str,
        "status": str,
        "issue_date": str,
        "title": str,
    }
}

REPORT_SCHEMA = {
    "report_id": str,           # uuid
    "user_id": str,
    "workflow_input": dict,     # what the user submitted
    "risk_level": str,          # HIGH | MEDIUM | LOW
    "risk_flags": list,
    "applicable_clauses": list,
    "explanation": str,
    "recommendations": list,
    "compliance_score": int,    # 0-100
    "pdf_path": str,            # local path to generated PDF
    "ipfs_cid": str,
    "tx_hash": str,             # blockchain tx
    "status": str,              # pending | verified | rejected
    "evaluator_remarks": str,
    "created_at": str,
    "updated_at": str,
}


if __name__ == "__main__":
    setup_indexes()
