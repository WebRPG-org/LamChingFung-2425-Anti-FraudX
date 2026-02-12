"""
Gemini LLM Adapter for Google ADK
支持 Google Gemini API (包括 fine-tuned 模型)
"""

import os
import asyncio
from typing import AsyncGenerator, List, Optional

from google import genai
from google.genai import types
from utils.logger import log
from pydantic import PrivateAttr

from google.adk.models import BaseLlm, LlmRequest, LlmResponse


def _extract_text_from_contents(contents: List[types.Content]) -> str:
    """提取 Content 列表中的文本，支持多輪對話格式"""
    if not contents:
        return ""
    
    lines: List[str] = []
    
    # 處理多輪對話
    if len(contents) > 1:
        total_length = sum(
            len(getattr(p, "text", ""))
            for c in contents
            if getattr(c, "parts", None)
            for p in c.parts
        )
        
        if total_length > 6000:
            log.warning(
                f"[GEMINI_LLM] ⚠️ Prompt 長度過長 ({total_length} 字元)，"
                f"可能影響性能。"
            )
        
        # 構建清晰的對話格式
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
                    lines.append(txt)
                else:
                    role_label = "AI" if role == "assistant" else "輸入"
                    if i == len(contents):
                        lines.append(f"【當前輸入】\n{txt}")
                    else:
                        lines.append(f"【對話 {i}】{role_label}: {txt}")
        
        result = "\n\n".join(lines).strip()
        log.info(
            f"[GEMINI_LLM] ✅ 構建多輪對話 prompt: "
            f"{len(contents)} 輪, {total_length} 字元"
        )
        return result
    
    # 單輪對話
    for c in contents:
        if not getattr(c, "parts", None):
            continue
        for p in c.parts:
            txt = getattr(p, "text", None)
            if txt:
                lines.append(txt)
    
    return "\n".join(lines).strip()


class GeminiLlm(BaseLlm):
    """
    Gemini API LLM adapter for ADK
    
    支持:
    - Fine-tuned 模型
    - 異步生成
    - 錯誤處理和重試
    - Token 統計
    - 安全設置
    - 文件上傳（Long Context）
    """

    model: str  # Gemini 模型 ID (例如: "gemini-2.5-flash" 或 "tunedModels/xxx")
    api_key: Optional[str] = None
    system_instruction: str = ""  # System Instruction
    uploaded_files: List = []  # 已上傳的文件列表
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048
    timeout: float = 60.0
    max_retries: int = 3
    
    # 私有屬性（不會被 Pydantic 驗證）
    _client: Optional[genai.Client] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        
        # 配置 API Key
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 未設置。請在環境變量或初始化時提供。")
        
        self._client = genai.Client(api_key=api_key)
        
        log.info(
            f"[GEMINI_LLM] 初始化 - "
            f"模型: {self.model}, "
            f"文件數: {len(self.uploaded_files)}, "
            f"System Instruction: {len(self.system_instruction)} 字"
        )

    @classmethod
    def supported_models(cls) -> list[str]:
        """返回支持的模型列表"""
        return [
            "gemini-2.5-flash",  # 推薦：免費版，性能優秀
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "tunedModels/*"  # 支持所有 fine-tuned 模型
        ]

    def _get_generation_config(self) -> types.GenerateContentConfig:
        """獲取生成配置"""
        return types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_output_tokens,
            system_instruction=self.system_instruction if self.system_instruction else None
        )

    def _get_safety_settings(self) -> list:
        """獲取安全設置（寬鬆設置，適合詐騙模擬場景）"""
        return [
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE"
            ),
        ]

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """帶指數退避的重試機制"""
        retry_delay = 1.0
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # 檢查是否為可重試錯誤
                if any(keyword in error_msg for keyword in ["timeout", "503", "429", "connection"]):
                    if attempt < self.max_retries - 1:
                        log.warning(
                            f"[GEMINI_LLM] 請求失敗 (嘗試 {attempt+1}/{self.max_retries}): {e}. "
                            f"將在 {retry_delay}s 後重試..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指數退避
                        continue
                
                # 不可重試錯誤，直接拋出
                raise
        
        # 所有重試都失敗
        raise Exception(f"Gemini API 請求失敗（已重試 {self.max_retries} 次）: {last_error}")

    async def _generate_content_internal(self, prompt: str) -> str:
        """內部生成方法（用於重試）"""
        try:
            # 構建請求內容（包含文件）
            contents = []
            
            # 添加上傳的文件
            for uploaded_file in self.uploaded_files:
                contents.append(types.Part(file_data=types.FileData(file_uri=uploaded_file.uri)))
                log.info(f"[GEMINI_LLM] 使用已上傳文件: {uploaded_file.display_name}")
            
            # 添加 prompt
            contents.append(types.Part(text=prompt))
            
            # 確保模型名稱格式正確（添加 models/ 前綴，如果需要）
            model_name = self.model
            if not model_name.startswith("models/") and not model_name.startswith("tunedModels/"):
                model_name = f"models/{model_name}"
            
            log.info(f"[GEMINI_LLM] 使用模型: {model_name}")
            
            # 生成內容
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=model_name,
                    contents=types.Content(parts=contents, role="user"),
                    config=self._get_generation_config()
                ),
                timeout=self.timeout
            )
            
            # 提取文本
            if not response.candidates:
                raise Exception("Gemini API 返回空響應")
            
            text = response.text
            
            # 記錄 Token 使用情況
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                log.info(
                    f"[GEMINI_LLM] Token 使用 - "
                    f"輸入: {usage.prompt_token_count}, "
                    f"輸出: {usage.candidates_token_count}, "
                    f"總計: {usage.total_token_count}"
                )
            
            return text
            
        except asyncio.TimeoutError:
            raise Exception(f"Gemini API 請求超時（{self.timeout}s）")
        except Exception as e:
            log.error(f"[GEMINI_LLM] 生成失敗: {e}")
            raise

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        生成內容（ADK 接口）
        
        Args:
            llm_request: ADK LLM 請求
            stream: 是否使用流式生成（目前不支持）
        
        Yields:
            LlmResponse: ADK LLM 響應
        """
        # 提取 prompt
        prompt = _extract_text_from_contents(getattr(llm_request, "contents", []))
        
        log.info(
            f"[GEMINI_LLM] 生成請求 - "
            f"模型: {self.model}, "
            f"文件數: {len(self.uploaded_files)}, "
            f"Prompt 長度: {len(prompt)}, "
            f"System 長度: {len(self.system_instruction)}"
        )
        
        # 使用重試機制生成內容
        text = await self._retry_with_backoff(
            self._generate_content_internal,
            prompt
        )
        
        # 檢查響應長度
        response_len = len(text)
        max_reasonable_length = 5000
        
        if response_len > max_reasonable_length:
            log.warning(
                f"[GEMINI_LLM] ⚠️ 響應過長 ({response_len} 字元 > {max_reasonable_length})，"
                f"已截斷。"
            )
            text = text[:max_reasonable_length]
            # 在句號處截斷
            last_sentence_end = max(
                text.rfind('。'), text.rfind('！'), text.rfind('？'),
                text.rfind('.'), text.rfind('!'), text.rfind('?')
            )
            if last_sentence_end > max_reasonable_length * 0.8:
                text = text[:last_sentence_end + 1]
        
        log.info(f"[GEMINI_LLM] 生成完成 - 響應長度: {response_len}")
        
        # 構建 ADK 響應
        content = types.Content(
            role="model",
            parts=[types.Part(text=text)]
        )
        
        yield LlmResponse(content=content)
