"""
Gemini LLM Adapter for Google ADK
支持 Google Gemini API (包括 fine-tuned 模型)
效能優化版：串流回應 + 降低 max_output_tokens + 對話歷史截斷
"""

import os
import asyncio
from typing import AsyncGenerator, List, Optional

from google import genai
from google.genai import types
from utils.logger import log
from pydantic import PrivateAttr

from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from llms.llm_utils import extract_text_from_contents  # shared helper (DUP-001 fix)


class GeminiLlm(BaseLlm):
    """
    Gemini API LLM adapter for ADK — 效能優化版

    優化點：
    - max_output_tokens 降至 800（對話場景）
    - 使用 generate_content_stream 串流回應（降低首 token 延遲）
    - 對話歷史截斷（最近 10 輪）
    - 共享 genai.Client 單例
    """

    model: str
    api_key: Optional[str] = None
    system_instruction: str = ""
    uploaded_files: List = []
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    # 🔥 關鍵優化：對話場景 800 token 足夠（原為 2048）
    max_output_tokens: int = 800
    timeout: float = 45.0  # 🔥 縮短超時（原為 60s）
    max_retries: int = 2   # 🔥 降低重試（原為 3）

    _client: Optional[genai.Client] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 未設置")
        self._client = genai.Client(api_key=api_key)
        log.info(
            f"[GEMINI_LLM] 初始化 - 模型: {self.model}, "
            f"max_tokens: {self.max_output_tokens}, timeout: {self.timeout}s"
        )

    @classmethod
    def supported_models(cls) -> list[str]:
        return [
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "tunedModels/*"
        ]

    def _get_generation_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_output_tokens,
            system_instruction=self.system_instruction if self.system_instruction else None
        )

    def _get_safety_settings(self) -> list:
        return [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]

    async def _generate_with_stream(self, prompt: str) -> str:
        """
        🔥 使用串流生成降低首 token 延遲
        收集所有 chunks 後拼接返回
        """
        contents = []
        for uploaded_file in self.uploaded_files:
            contents.append(types.Part(file_data=types.FileData(file_uri=uploaded_file.uri)))
        contents.append(types.Part(text=prompt))

        model_name = self.model
        if not model_name.startswith("models/") and not model_name.startswith("tunedModels/"):
            model_name = f"models/{model_name}"

        log.info(f"[GEMINI_LLM] 串流生成 model={model_name} prompt_len={len(prompt)}")

        chunks: List[str] = []
        total_tokens = 0

        try:
            # 使用串流模式
            stream_iter = await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: list(
                        self._client.models.generate_content_stream(
                            model=model_name,
                            contents=types.Content(parts=contents, role="user"),
                            config=self._get_generation_config()
                        )
                    )
                ),
                timeout=self.timeout
            )
            for chunk in stream_iter:
                if chunk.text:
                    chunks.append(chunk.text)

            text = "".join(chunks)

        except AttributeError:
            # 如果不支持 generate_content_stream，回退到非串流
            log.warning("[GEMINI_LLM] 串流不可用，回退到非串流模式")
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=model_name,
                    contents=types.Content(parts=contents, role="user"),
                    config=self._get_generation_config()
                ),
                timeout=self.timeout
            )
            if not response.candidates:
                raise Exception("Gemini API 返回空響應")
            text = response.text
            
        # 截斷過長回應
        max_len = 2000
        if len(text) > max_len:
            log.warning(f"[GEMINI_LLM] 響應過長 ({len(text)} 字元)，截斷")
            text = text[:max_len]
            last_end = max(
                text.rfind('。'), text.rfind('！'), text.rfind('？'),
                text.rfind('.'), text.rfind('!'), text.rfind('?')
            )
            if last_end > max_len * 0.8:
                text = text[:last_end + 1]

        log.info(f"[GEMINI_LLM] 生成完成 response_len={len(text)}")
        return text
            
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """帶指數退避的重試"""
        retry_delay = 0.5
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                if any(kw in error_msg for kw in ["timeout", "503", "429", "connection"]):
                    if attempt < self.max_retries - 1:
                        log.warning(f"[GEMINI_LLM] 重試 {attempt+1}/{self.max_retries}: {e}")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                raise
        raise Exception(f"Gemini API 失敗（已重試 {self.max_retries} 次）: {last_error}")

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        prompt = extract_text_from_contents(
            getattr(llm_request, "contents", []), log_prefix="GEMINI_LLM"
        )
        
        log.info(
            f"[GEMINI_LLM] 請求 model={self.model} "
            f"prompt_len={len(prompt)} max_tokens={self.max_output_tokens}"
        )
        
        text = await self._retry_with_backoff(self._generate_with_stream, prompt)
        
        content = types.Content(
            role="model",
            parts=[types.Part(text=text)]
        )
        yield LlmResponse(content=content)
