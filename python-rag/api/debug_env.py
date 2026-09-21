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
    provider = (settings.llm_provider or "gemini").strip().lower()
    key_by_provider = {
        "gemini": settings.gemini_api_key or os.getenv("GEMINI_API_KEY", ""),
        "google": settings.gemini_api_key or os.getenv("GEMINI_API_KEY", ""),
        "groq": settings.groq_api_key or os.getenv("GROQ_API_KEY", ""),
        "nvidia": settings.nvidia_api_key or os.getenv("NVIDIA_API_KEY", ""),
        "xai": settings.xai_api_key or os.getenv("XAI_API_KEY", ""),
    }
    model_by_provider = {
        "gemini": settings.gemini_model,
        "google": settings.gemini_model,
        "groq": settings.groq_model,
        "nvidia": settings.nvidia_model,
        "xai": settings.xai_model,
    }
    key_present = bool(key_by_provider.get(provider, ""))
    model_name = model_by_provider.get(provider, "")
    print(f"ENV_FILE_PATH={env_path}")
    print(f"ENV_FILE_EXISTS={env_path.exists()}")
    print(f"LLM_PROVIDER={provider}")
    print(f"HAS_ACTIVE_PROVIDER_KEY={key_present}")
    print(f"LLM_MODEL={model_name}")
    print(f"RAG_ENABLE_LLM={os.getenv('RAG_ENABLE_LLM', '1')}")


if __name__ == "__main__":
    main()
