import os
import asyncio
from typing import AsyncGenerator, List

import httpx
from utils.logger import log

from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types as genai_types


def _extract_text_from_contents(contents: List[genai_types.Content]) -> str:
    """提取 Content 列表中的文本，支持多輪對話格式
    
    增強版：優化對話歷史格式化，提升上下文理解能力
    """
    if not contents:
        return ""
    
    lines: List[str] = []
    
    # 🔥 增強：處理多輪對話（優化格式）
    if len(contents) > 1:
        # 檢測是否超過建議長度（用於日誌警告）
        total_length = sum(
            len(getattr(p, "text", ""))
            for c in contents
            if getattr(c, "parts", None)
            for p in c.parts
        )
        
        if total_length > 6000:
            log.warning(
                f"[OLLAMA_LLM] ⚠️ Prompt 長度過長 ({total_length} 字元)，"
                f"可能影響性能。建議使用 ContextManager 進行摘要。"
            )
        
        # 多輪對話：構建清晰的對話格式
        for i, c in enumerate(contents, 1):
            if not getattr(c, "parts", None):
                continue
            
            role = getattr(c, "role", "user")
            
            for p in c.parts:
                txt = getattr(p, "text", None)
                if not txt:
                    continue
                
                # 智能處理角色標籤
                if any(prefix in txt for prefix in ["騙徒:", "受騙者:", "專家:", "記錄人:", "你（", "第"]):
                    # 已經包含角色標籤或格式化內容，直接使用
                    lines.append(txt)
                else:
                    # 添加清晰的角色標籤
                    role_label = "AI" if role == "assistant" else "輸入"
                    
                    # 如果是最後一條消息，標記為 "當前"
                    if i == len(contents):
                        lines.append(f"【當前輸入】\n{txt}")
                    else:
                        lines.append(f"【對話 {i}】{role_label}: {txt}")
        
        result = "\n\n".join(lines).strip()
        log.info(
            f"[OLLAMA_LLM] ✅ 構建多輪對話 prompt: "
            f"{len(contents)} 輪, {total_length} 字元"
        )
        return result
    
    # 單輪對話：直接拼接文本
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
            # 🔥 優先檢查特定 Agent 的生成長度設置（例如騙徒專用）
            num_predict_env = os.getenv("OLLAMA_NUM_PREDICT_SCAMMER") or os.getenv("OLLAMA_NUM_PREDICT")
            # 🔥 設置默認最大生成長度：2000 tokens (約 1500-2000 字)
            # 對於對話場景，這個長度足夠，避免生成過長響應
            num_predict = int(num_predict_env) if num_predict_env else 2000
        except Exception:
            num_predict = 2000  # 默認值

        options: dict = {
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
            "num_ctx": num_ctx,
            "num_predict": num_predict,  # 🔥 始終設置，避免無限生成
        }
        if top_k is not None:
            options["top_k"] = top_k

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
        
        # Retry logic for connection issues
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Use connection limits to prevent pool exhaustion
                limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
                async with httpx.AsyncClient(base_url=base_url, timeout=gen_timeout, limits=limits) as client:
                    log.info(f"[OLLAMA] POST /api/generate base={base_url} model={self.model} prompt_len={len(prompt)} system_len={len(system_text)} attempt={attempt+1}/{max_retries}")
                    resp = await client.post("/api/generate", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    text = data.get("response", "")
                    
                    # 🔥 檢查響應長度，避免過長響應
                    response_len = len(text)
                    max_reasonable_length = 5000  # 約 5000 字元（對話場景的合理上限）
                    
                    if response_len > max_reasonable_length:
                        log.warning(
                            f"[OLLAMA] ⚠️ 響應過長 ({response_len} 字元 > {max_reasonable_length})，"
                            f"可能包含重複內容。已截斷至 {max_reasonable_length} 字元。"
                        )
                        # 截斷到合理長度，保留前 N 字元
                        text = text[:max_reasonable_length]
                        # 嘗試在句號、問號或感嘆號處截斷
                        last_sentence_end = max(
                            text.rfind('。'), text.rfind('！'), text.rfind('？'),
                            text.rfind('.'), text.rfind('!'), text.rfind('?')
                        )
                        if last_sentence_end > max_reasonable_length * 0.8:  # 如果最後一句話在 80% 之後
                            text = text[:last_sentence_end + 1]
                    
                    log.info(
                        f"[OLLAMA] response_len={response_len} status={resp.status_code} "
                        f"(num_predict={num_predict})"
                    )
                    break  # Success, exit retry loop
            except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as e:
                if attempt < max_retries - 1:
                    log.warning(f"[OLLAMA] Connection failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    log.error(f"[OLLAMA] All {max_retries} connection attempts failed: {e}")
                    raise Exception(f"無法連接到 Ollama 服務 ({base_url}): {e}. 請確保 Ollama 正在運行。") from e
            except Exception as e:
                log.error(f"[OLLAMA] Unexpected error: {e}")
                raise

        content = genai_types.Content(
            role="model",
            parts=[genai_types.Part(text=text)]
        )

        # Wrap in LlmResponse for ADK (it aliases google.genai types internally)
        yield LlmResponse(content=content)


