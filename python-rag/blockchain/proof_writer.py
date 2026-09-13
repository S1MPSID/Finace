"""
Write compliance proof on-chain via Hardhat script.

Usage:
    cd python-rag
    python -m blockchain.proof_writer --report-id rep-001 --ipfs-cid <cid> --document-hash <0x...> --org-name "Acme" --risk-level MEDIUM --contract-address <0x...>
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


def sha256_hex(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "0x" + h.hexdigest()


def store_proof(
    report_id: str,
    ipfs_cid: str,
    document_hash: str,
    org_name: str,
    risk_level: str,
    contract_address: str,
) -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    blockchain_dir = repo_root / "Blockchain"
    cmd = [
        "npm",
        "run",
        "store-proof:base-sepolia",
        "--",
        "--report-id",
        report_id,
        "--ipfs-cid",
        ipfs_cid,
        "--document-hash",
        document_hash,
        "--org-name",
        org_name,
        "--risk-level",
        risk_level,
        "--contract",
        contract_address,
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(blockchain_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "Failed to store proof on chain")
    return {"stdout": proc.stdout.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Write compliance proof to Base Sepolia")
    parser.add_argument("--report-id", required=True)
    parser.add_argument("--ipfs-cid", required=True)
    parser.add_argument("--document-hash", required=False, default="")
    parser.add_argument("--document-file", required=False, default="")
    parser.add_argument("--org-name", required=True)
    parser.add_argument("--risk-level", required=True)
    parser.add_argument("--contract-address", default=settings.compliance_contract_address)
    args = parser.parse_args()

    if not args.contract_address:
        raise RuntimeError("Contract address missing. Pass --contract-address or set COMPLIANCE_CONTRACT_ADDRESS")

    doc_hash = args.document_hash.strip()
    if not doc_hash and args.document_file:
        doc_hash = sha256_hex(Path(args.document_file))
    if not doc_hash:
        raise RuntimeError("Provide --document-hash or --document-file")

    out = store_proof(
        report_id=args.report_id,
        ipfs_cid=args.ipfs_cid,
        document_hash=doc_hash,
        org_name=args.org_name,
        risk_level=args.risk_level,
        contract_address=args.contract_address,
    )
    print(out["stdout"])


if __name__ == "__main__":
    main()
