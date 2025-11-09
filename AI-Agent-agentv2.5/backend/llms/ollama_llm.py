import os
import asyncio
from typing import AsyncGenerator, List

import httpx
from utils.logger import log

from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types as genai_types


def _extract_text_from_contents(contents: List[genai_types.Content]) -> str:
    lines: List[str] = []
    if not contents:
        return ""
    for c in contents:
        if not getattr(c, "parts", None):
            continue
        for p in c.parts:
            txt = getattr(p, "text", None)
            if txt:
                lines.append(txt)
    return "\n".join(lines).strip()


class OllamaLlm(BaseLlm):
    """Minimal Ollama-backed LLM for ADK.

    Uses POST /api/generate with stream=false.
    Returns google.genai.types.Content for compatibility with ADK Runner.
    """

    # Ensure pydantic knows about the required field coming from BaseLlm
    model: str
    # Optional per-instance base URL override
    base_url: str | None = None

    @classmethod
    def supported_models(cls) -> list[str]:
        # Accept any model string; routing handled by Ollama server.
        return []

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        base_url = (self.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        prompt = _extract_text_from_contents(getattr(llm_request, "contents", []))

        # Try to include system instruction (if provided by ADK)
        system_instruction = (
            getattr(llm_request, "system_instruction", None)
            or getattr(llm_request, "instruction", None)
            or ""
        )
        if isinstance(system_instruction, str):
            system_text = system_instruction
        else:
            system_text = str(system_instruction) if system_instruction else ""

        # Generation options (overridable via environment variables)
        try:
            temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.5"))
        except Exception:
            temperature = 0.5
        try:
            top_p = float(os.getenv("OLLAMA_TOP_P", "0.85"))
        except Exception:
            top_p = 0.85
        try:
            repeat_penalty = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))
        except Exception:
            repeat_penalty = 1.1
        try:
            num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        except Exception:
            num_ctx = 4096
        # Optional knobs
        try:
            top_k_env = os.getenv("OLLAMA_TOP_K")
            top_k = int(top_k_env) if top_k_env else None
        except Exception:
            top_k = None
        try:
            num_predict_env = os.getenv("OLLAMA_NUM_PREDICT")
            num_predict = int(num_predict_env) if num_predict_env else None
        except Exception:
            num_predict = None

        options: dict = {
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
            "num_ctx": num_ctx,
        }
        if top_k is not None:
            options["top_k"] = top_k
        if num_predict is not None:
            options["num_predict"] = num_predict

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # 將 system 指令傳入 Ollama（若空則由模型忽略）
            "system": system_text,
            # 生成選項可依需要微調（支援環境變數覆寫）
            "options": options
        }

        # Ensure model availability (auto-pull on first use to avoid 404/long wait)
        auto_pull = os.getenv("OLLAMA_AUTO_PULL", "1") != "0"
        if auto_pull:
            try:
                pull_timeout = httpx.Timeout(900.0, connect=30.0)
                async with httpx.AsyncClient(base_url=base_url, timeout=pull_timeout) as client:
                    log.info(f"[OLLAMA] POST /api/pull base={base_url} name={self.model}")
                    pr = await client.post("/api/pull", json={"name": self.model, "stream": False})
                    pr.raise_for_status()
            except Exception as e:
                # If exists or endpoint doesn't support pull, ignore
                log.info(f"[OLLAMA] pull skipped or already present: {e}")

        gen_timeout = httpx.Timeout(300.0, connect=30.0)
        async with httpx.AsyncClient(base_url=base_url, timeout=gen_timeout) as client:
            log.info(f"[OLLAMA] POST /api/generate base={base_url} model={self.model} prompt_len={len(prompt)} system_len={len(system_text)}")
            resp = await client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "")
            log.info(f"[OLLAMA] response_len={len(text)} status={resp.status_code}")

        content = genai_types.Content(
            role="model",
            parts=[genai_types.Part(text=text)]
        )

        # Wrap in LlmResponse for ADK (it aliases google.genai types internally)
        yield LlmResponse(content=content)


