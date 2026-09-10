"""
LLM client wrapper for RAG reasoning.
Primary provider: Google Gemini 2.5 Flash.
"""
from __future__ import annotations

import json
import os
import re
import time

import httpx
from loguru import logger

from config import settings


def _extract_json_object(text: str) -> dict:
    """Extract and parse the best JSON object from model output."""
    cleaned = (text or "").strip()

    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"^Here's a thinking process:.*?(?=\{)", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if "```" in cleaned:
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fence:
            cleaned = fence.group(1)

    try:
        return json.loads(cleaned.strip())
    except Exception:
        pass

    candidates = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", cleaned, flags=re.DOTALL)
    if not candidates:
        match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
        candidates = [match.group(1)] if match else []

    for candidate in reversed(candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue

    raise ValueError(f"Could not parse JSON from model response. Raw text: {cleaned[:500]}...")


class LLMClient:
    def __init__(self):
        self.provider = (settings.llm_provider or "gemini").strip().lower()
        self.api_key = (
            settings.gemini_api_key
            or os.getenv("GEMINI_API_KEY", "")
            or settings.nvidia_api_key
            or settings.groq_api_key
            or settings.xai_api_key
            or os.getenv("NVIDIA_API_KEY", "")
            or os.getenv("GROQ_API_KEY", "")
            or os.getenv("XAI_API_KEY", "")
        )

        if self.provider in {"gemini", "google"}:
            self.provider = "gemini"
            self.base_url = settings.gemini_base_url.rstrip("/")
            self.model = settings.gemini_model or "gemini-2.5-flash"
            self.models = [self.model]
        elif self.provider == "nvidia":
            self.base_url = settings.nvidia_base_url.rstrip("/")
            primary = settings.nvidia_model or "nvidia/nemotron-3.5-lightning-30b-a3b"
            fallbacks = [
                "nvidia/nemotron-3.5-lightning-30b-a3b",
                "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            ]
            ordered = [primary] + [m for m in fallbacks if m != primary]
            self.models = ordered
            self.model = ordered[0]
        elif self.provider == "groq" or str(self.api_key).startswith("gsk_"):
            self.base_url = "https://api.groq.com/openai/v1"
            self.model = settings.groq_model
            self.models = [self.model]
        else:
            self.base_url = (settings.xai_base_url or "https://api.x.ai/v1").rstrip("/")
            self.model = settings.xai_model
            self.models = [self.model]

        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.top_p = settings.llm_top_p
        self.reasoning_budget = settings.llm_reasoning_budget

    def _mock_response(self, reason: str) -> dict:
        return {
            "risk_level": "MEDIUM",
            "risk_flags": [f"LLM fallback used: {reason}"],
            "applicable_clauses": [],
            "explanation": f"Fallback mode used. Reason: {reason}",
            "recommendations": [
                "Set RAG_ENABLE_LLM=1 to enable live LLM calls.",
                "Set GEMINI_API_KEY in python-rag/.env.",
            ],
            "compliance_score": 55,
            "reasoning_steps": [f"Fallback: {reason}"],
        }

    def _call_gemini(self, prompt: str, model: str) -> dict:
        url = f"{self.base_url}/models/{model}:generateContent"
        # Gemini 2.5 uses "thinking" tokens that count against maxOutputTokens.
        # Keep thinking low so the JSON answer is not truncated.
        thinking_budget = 0
        if "2.5" in model:
            thinking_budget = min(256, max(0, self.max_tokens // 8))

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a compliance analysis engine. "
                            "Return a single valid JSON object only. "
                            "No markdown. No thinking. No prose outside JSON. "
                            "Always include a non-empty 'explanation' string. "
                            "compliance_score is 0-100 (higher = more compliant). "
                            "Use 90-100 with risk_level LOW when controls address prior gaps / XAI drivers. "
                            "When the user remediates findings or asks to raise the score, increase compliance_score accordingly."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "topP": self.top_p,
                "maxOutputTokens": max(self.max_tokens, 4096),
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": thinking_budget},
            },
        }

        response = httpx.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            json=payload,
            timeout=90.0,
        )
        if response.status_code >= 400:
            logger.error(f"Gemini HTTP {response.status_code} model={model}: {response.text[:600]}")
            response.raise_for_status()

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {str(data)[:400]}")

        candidate = candidates[0] or {}
        finish_reason = candidate.get("finishReason")
        usage = data.get("usageMetadata") or {}
        logger.info(
            f"Gemini finishReason={finish_reason} usage={usage}"
        )

        parts = ((candidate.get("content") or {}).get("parts") or [])
        text = "".join(str(p.get("text") or "") for p in parts).strip()
        if not text:
            raise RuntimeError(f"Gemini returned empty content: {str(data)[:400]}")

        try:
            parsed = _extract_json_object(text)
        except Exception as exc:
            if finish_reason == "MAX_TOKENS":
                raise RuntimeError(
                    f"Gemini truncated JSON (MAX_TOKENS). usage={usage}. partial={text[:200]}"
                ) from exc
            raise

        if not str(parsed.get("explanation") or "").strip():
            # Recover a usable explanation if the model omitted it.
            flags = parsed.get("risk_flags") or []
            recs = parsed.get("recommendations") or []
            parsed["explanation"] = (
                "Compliance analysis completed. "
                + (f"Key risks: {', '.join(map(str, flags[:5]))}. " if flags else "")
                + (f"Recommendations: {', '.join(map(str, recs[:5]))}." if recs else "")
            ).strip()
        return parsed

    def _build_openai_payload(self, prompt: str, model: str) -> dict:
        payload: dict = {
            "model": model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a compliance analysis engine. "
                        "Return a single valid JSON object only. "
                        "No markdown. No thinking. No prose outside JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        if (
            self.provider == "nvidia"
            and self.reasoning_budget > 0
            and "reasoning" in model.lower()
        ):
            payload["reasoning_budget"] = min(self.reasoning_budget, 2048)
        if self.provider in {"groq", "xai"}:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _call_openai_compatible(self, prompt: str, model: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=self._build_openai_payload(prompt, model),
            timeout=120.0,
        )
        if response.status_code >= 400:
            logger.error(f"LLM HTTP {response.status_code} model={model}: {response.text[:500]}")
            response.raise_for_status()

        data = response.json()
        message = (data.get("choices") or [{}])[0].get("message") or {}
        text = (message.get("content") or "").strip()
        if not text:
            text = (
                message.get("reasoning_content")
                or message.get("reasoning")
                or ""
            ).strip()
        return _extract_json_object(text)

    def _call_model(self, prompt: str, model: str) -> dict:
        if self.provider == "gemini":
            return self._call_gemini(prompt, model)
        return self._call_openai_compatible(prompt, model)

    def _generate(self, prompt: str) -> dict:
        last_error: Exception | None = None

        for model in self.models:
            for attempt in range(1, 3):
                try:
                    logger.info(f"LLM call provider={self.provider} model={model} attempt={attempt}")
                    result = self._call_model(prompt, model)
                    self.model = model
                    return result
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    code = exc.response.status_code if exc.response is not None else 0
                    if code in {429, 503} and attempt < 2:
                        time.sleep(attempt * 2)
                        continue
                    if code in {404, 410, 429, 503}:
                        break
                    if attempt < 2:
                        time.sleep(attempt * 2)
                        continue
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(attempt * 2)
                        continue
                    break

        raise RuntimeError(f"LLM failed across models {self.models}: {last_error}")

    def generate_json(self, prompt: str) -> dict:
        if os.getenv("RAG_ENABLE_LLM", "1") != "1":
            reason = "RAG_ENABLE_LLM is not set to 1"
            logger.warning(f"{reason}; using fallback response")
            return self._mock_response(reason)

        try:
            if not self.api_key:
                reason = "GEMINI_API_KEY not set"
                logger.warning(f"{reason}; using fallback response")
                return self._mock_response(reason)

            return self._generate(prompt)
        except Exception as exc:
            logger.error(f"LLM generation failed; using fallback response: {exc}")
            return self._mock_response(f"LLM generation failed: {exc}")
