"""
Quick environment/config debug for python-rag.

Usage:
    cd python-rag
    python -m api.debug_env
"""
from __future__ import annotations

import os
from pathlib import Path

from config import settings


def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    key_present = bool(
        settings.xai_api_key or os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY")
    )
    model_name = settings.xai_model or os.getenv("GROK_MODEL") or os.getenv("GROQ_MODEL") or ""
    print(f"ENV_FILE_PATH={env_path}")
    print(f"ENV_FILE_EXISTS={env_path.exists()}")
    print(f"HAS_XAI_KEY={key_present}")
    print(f"XAI_MODEL={model_name}")
    print(f"XAI_BASE_URL={settings.xai_base_url}")
    print(f"RAG_ENABLE_LLM={os.getenv('RAG_ENABLE_LLM', '1')}")


if __name__ == "__main__":
    main()
