"""
Pinata IPFS uploader for generated report files.

Usage:
    cd python-rag
    python -m storage.ipfs_uploader --file .\\..\\data\\reports\\rep-001.pdf
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


PINATA_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS"


def upload_file_to_ipfs(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    headers = {}
    if settings.pinata_jwt:
        headers["Authorization"] = f"Bearer {settings.pinata_jwt}"
    elif settings.pinata_api_key and settings.pinata_secret_key:
        headers["pinata_api_key"] = settings.pinata_api_key
        headers["pinata_secret_api_key"] = settings.pinata_secret_key
    else:
        raise RuntimeError("Pinata credentials missing. Set PINATA_JWT or API key/secret in .env")

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        response = requests.post(PINATA_ENDPOINT, files=files, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()
    return {
        "ipfs_cid": data.get("IpfsHash", ""),
        "pin_size": data.get("PinSize", 0),
        "timestamp": data.get("Timestamp", ""),
        "raw": data,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload report PDF to IPFS via Pinata")
    parser.add_argument("--file", required=True, help="Path to PDF report")
    args = parser.parse_args()

    out = upload_file_to_ipfs(Path(args.file))
    print(out)


if __name__ == "__main__":
    main()
