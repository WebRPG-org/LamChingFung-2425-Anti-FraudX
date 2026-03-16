import os
import asyncio
from typing import AsyncGenerator, List

import httpx
from utils.logger import log

from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types as genai_types
from llms.llm_utils import extract_text_from_contents  # shared helper (DUP-001 fix)

# NOTE: 不再使用模組級別共享客戶端。
# 原因：ADK 會在獨立子執行緒建立並銷毀自己的 event loop，
# 跨 loop 共享 AsyncClient 會在 loop 關閉時丟出
# RuntimeError: Event loop is closed。
# 改為每次請求建立短期客戶端（warm_up_model 同樣做法），
# 效能影響可忽略不計，因瓶頸在 Ollama 推理本身。


def _build_client(base_url: str) -> httpx.AsyncClient:
    """建立短期 AsyncClient（每次請求使用，避免跨 event-loop 共享問題）"""
    limits = httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
        keepalive_expiry=30.0,
        )
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(180.0, connect=10.0),
        limits=limits,
    )


class OllamaLlm(BaseLlm):
    """Minimal Ollama-backed LLM for ADK.

    使用 POST /api/generate with stream=false.
    效能優化版：
    - 每次請求使用獨立 AsyncClient（避免跨 event-loop 崩潰）
    - 移除 auto-pull 阻塞（改為啟動時預熱）
    - 降低 num_ctx 和 num_predict 至對話場景合理值
    - 對話歷史截斷（最近 10 輪）
    """

    model: str
    base_url: str | None = None

    @classmethod
    def supported_models(cls) -> list[str]:
        return []

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        base_url = (self.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        prompt = extract_text_from_contents(
            getattr(llm_request, "contents", []), log_prefix="OLLAMA"
        )

        system_instruction = (
            getattr(llm_request, "system_instruction", None)
            or getattr(llm_request, "instruction", None)
            or ""
        )
        if isinstance(system_instruction, str):
            system_text = system_instruction
        else:
            system_text = str(system_instruction) if system_instruction else ""

        # ── 生成參數（對話場景優化值）──────────────────────────────────────
        try:
            temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        except Exception:
            temperature = 0.7
        try:
            top_p = float(os.getenv("OLLAMA_TOP_P", "0.9"))
        except Exception:
            top_p = 0.9
        try:
            repeat_penalty = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))
        except Exception:
            repeat_penalty = 1.1

        # 🔥 關鍵優化：大幅降低 num_ctx（2048 足夠對話場景，原為 4096）
        try:
            num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
        except Exception:
            num_ctx = 2048

        # 🔥 關鍵優化：大幅降低 num_predict（400 tokens ≈ 300字，足夠對話回應）
        # Recorder 需要更多 token 以輸出完整 JSON（預設 1200）
        try:
            num_predict_env = (
                os.getenv("OLLAMA_NUM_PREDICT_RECORDER")
                or os.getenv("OLLAMA_NUM_PREDICT_SCAMMER")
                or os.getenv("OLLAMA_NUM_PREDICT")
            )
            num_predict = int(num_predict_env) if num_predict_env else 400
        except Exception:
            num_predict = 400

        options: dict = {
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
            "num_ctx": num_ctx,
            "num_predict": num_predict,
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "system": system_text,
            "options": options
        }

        # 🔥 移除 auto-pull（改由啟動腳本或 warm-up API 處理）
        # auto_pull 每次都嘗試 pull 會阻塞 3-10 秒，嚴重影響回應速度

        max_retries = 2  # 降低重試次數（從 3 改為 2）
        retry_delay = 0.5  # 縮短初始重試延遲（從 1.0 改為 0.5）

        text = ""
        for attempt in range(max_retries):
            try:
                log.info(
                    f"[OLLAMA] POST /api/generate model={self.model} "
                    f"prompt_len={len(prompt)} num_ctx={num_ctx} "
                    f"num_predict={num_predict} attempt={attempt+1}/{max_retries}"
                )
                async with _build_client(base_url) as client:
                    resp = await client.post("/api/generate", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    text = data.get("response", "")

                # 截斷過長回應
                response_len = len(text)
                max_reasonable_length = 2000  # 降低上限（對話場景）

                if response_len > max_reasonable_length:
                    log.warning(
                        f"[OLLAMA] ⚠️ 響應過長 ({response_len} 字元)，截斷至 {max_reasonable_length}"
                    )
                    text = text[:max_reasonable_length]
                    last_end = max(
                        text.rfind('。'), text.rfind('！'), text.rfind('？'),
                        text.rfind('.'), text.rfind('!'), text.rfind('?')
                    )
                    if last_end > max_reasonable_length * 0.8:
                        text = text[:last_end + 1]
                    
                log.info(f"[OLLAMA] 完成 response_len={len(text)}")
                break

            except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as e:
                if attempt < max_retries - 1:
                    log.warning(f"[OLLAMA] 連接失敗 (attempt {attempt+1}/{max_retries}): {e}. 重試中...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    log.error(f"[OLLAMA] 所有重試失敗: {e}")
                    raise Exception(
                        f"無法連接到 Ollama 服務 ({base_url}): {e}. "
                        f"請確保 Ollama 正在運行並已載入模型 {self.model}"
                    ) from e
            except Exception as e:
                log.error(f"[OLLAMA] 非預期錯誤: {e}")
                raise

        content = genai_types.Content(
            role="model",
            parts=[genai_types.Part(text=text)]
        )

        yield LlmResponse(content=content)


async def warm_up_model(model: str, base_url: str = "http://localhost:11434") -> bool:
    """預熱 Ollama 模型（在服務啟動時調用，避免首次請求延遲）"""
    try:
        payload = {
            "model": model,
            "prompt": "你好",
            "stream": False,
            "options": {"num_predict": 1, "num_ctx": 512}
        }
        async with _build_client(base_url) as client:
            log.info(f"[OLLAMA] 預熱模型 {model}...")
            resp = await client.post("/api/generate", json=payload)
            resp.raise_for_status()
            log.info(f"[OLLAMA] ✅ 模型 {model} 已預熱")
            return True
    except Exception as e:
        log.warning(f"[OLLAMA] ⚠️ 預熱失敗 {model}: {e}")
        return False
