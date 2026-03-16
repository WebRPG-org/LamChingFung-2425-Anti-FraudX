"""
Vertex AI LLM - Google Vertex AI 集成模塊
支持 Vertex AI Express Mode（無需管理端點）
"""

import os
import json
from typing import Optional, List, Dict, Any
from utils.logger import log

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Content, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    log.warning("[VERTEX_AI_LLM] Vertex AI SDK 未安裝")


class VertexAILLM:
    """
    Vertex AI LLM 類
    使用 Google Vertex AI 的 Generative AI 模型
    支持 gemini-3.1-flash-lite-preview 等模型
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash-lite",
        project_id: str = "anti-fraudx",
        location: str = "us-central1",
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 2048,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        初始化 Vertex AI LLM

        Args:
            model_name: 模型名稱（默認：gemini-3.1-flash-lite-preview）
            project_id: GCP 項目 ID
            location: GCP 區域（默認：us-central1）
            temperature: 溫度參數（0-2）
            top_p: Top-p 採樣參數
            top_k: Top-k 採樣參數
            max_output_tokens: 最大輸出 token 數
            timeout: 請求超時時間（秒）
            max_retries: 最大重試次數
        """
        if not VERTEX_AI_AVAILABLE:
            raise ImportError(
                "Vertex AI SDK 未安裝。請運行: pip install google-cloud-aiplatform"
            )

        self.model_name = model_name
        self.project_id = project_id
        self.location = location
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.max_retries = max_retries

        # 初始化 Vertex AI
        try:
            vertexai.init(project=project_id, location=location)
            self.model = GenerativeModel(model_name)
            log.info(
                f"[VERTEX_AI_LLM] ✅ Vertex AI 已初始化 - 模型: {model_name}, 項目: {project_id}"
            )
        except Exception as e:
            log.error(f"[VERTEX_AI_LLM] ❌ Vertex AI 初始化失敗: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用戶提示
            system_instruction: 系統指令
            temperature: 溫度參數（可選，覆蓋默認值）
            max_tokens: 最大 token 數（可選，覆蓋默認值）

        Returns:
            生成的文本
        """
        try:
            # 使用提供的參數或默認值
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_output_tokens

            # 構建完整提示
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            else:
                full_prompt = prompt

            # 調用 Vertex AI API
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temp,
                    "top_p": self.top_p,
                    "top_k": self.top_k,
                    "max_output_tokens": max_tok,
                },
                stream=False,
            )

            # 提取文本
            if response.text:
                log.debug(
                    f"[VERTEX_AI_LLM] ✅ 生成成功 - 長度: {len(response.text)} 字"
                )
                return response.text
            else:
                log.warning("[VERTEX_AI_LLM] ⚠️ 生成結果為空")
                return ""

        except Exception as e:
            log.error(f"[VERTEX_AI_LLM] ❌ 生成失敗: {e}")
            raise

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        流式生成文本

        Args:
            prompt: 用戶提示
            system_instruction: 系統指令
            temperature: 溫度參數（可選）
            max_tokens: 最大 token 數（可選）

        Yields:
            生成的文本片段
        """
        try:
            # 使用提供的參數或默認值
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_output_tokens

            # 構建完整提示
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            else:
                full_prompt = prompt

            # 調用 Vertex AI API（流式）
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temp,
                    "top_p": self.top_p,
                    "top_k": self.top_k,
                    "max_output_tokens": max_tok,
                },
                stream=True,
            )

            # 逐個 yield 文本片段
            for chunk in response:
                if chunk.text:
                    yield chunk.text

            log.debug("[VERTEX_AI_LLM] ✅ 流式生成完成")

        except Exception as e:
            log.error(f"[VERTEX_AI_LLM] ❌ 流式生成失敗: {e}")
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        多輪對話

        Args:
            messages: 消息列表，格式：[{"role": "user/assistant", "content": "..."}]
            system_instruction: 系統指令
            temperature: 溫度參數（可選）
            max_tokens: 最大 token 數（可選）

        Returns:
            助手的回應
        """
        try:
            # 使用提供的參數或默認值
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_output_tokens

            # 構建對話歷史
            chat_history = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    chat_history.append(
                        Content(role="user", parts=[Part.from_text(content)])
                    )
                elif role == "assistant":
                    chat_history.append(
                        Content(role="model", parts=[Part.from_text(content)])
                    )

            # 開始對話
            chat = self.model.start_chat(history=chat_history)

            # 發送最後一條消息
            if messages:
                last_message = messages[-1].get("content", "")
                response = chat.send_message(
                    last_message,
                    generation_config={
                        "temperature": temp,
                        "top_p": self.top_p,
                        "top_k": self.top_k,
                        "max_output_tokens": max_tok,
                    },
                )

                if response.text:
                    log.debug(
                        f"[VERTEX_AI_LLM] ✅ 對話成功 - 長度: {len(response.text)} 字"
                    )
                    return response.text
                else:
                    log.warning("[VERTEX_AI_LLM] ⚠️ 對話結果為空")
                    return ""
            else:
                log.warning("[VERTEX_AI_LLM] ⚠️ 消息列表為空")
                return ""

        except Exception as e:
            log.error(f"[VERTEX_AI_LLM] ❌ 對話失敗: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        計算文本的 token 數

        Args:
            text: 要計算的文本

        Returns:
            token 數
        """
        try:
            response = self.model.count_tokens(text)
            token_count = response.total_tokens
            log.debug(f"[VERTEX_AI_LLM] Token 計數: {token_count}")
            return token_count
        except Exception as e:
            log.error(f"[VERTEX_AI_LLM] ❌ Token 計數失敗: {e}")
            return 0

    def get_model_info(self) -> Dict[str, Any]:
        """
        獲取模型信息

        Returns:
            模型信息字典
        """
        return {
            "model_name": self.model_name,
            "project_id": self.project_id,
            "location": self.location,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }


# 測試函數
if __name__ == "__main__":
    # 初始化 LLM
    llm = VertexAILLM(
        model_name="gemini-2.5-flash-lite",
        project_id=os.getenv("GCP_PROJECT_ID", "anti-fraudx"),
        location="us-central1",
    )

    # 測試生成
    print("=== 測試生成 ===")
    response = llm.generate("你好，請介紹一下自己")
    print(f"回應: {response}\n")

    # 測試對話
    print("=== 測試對話 ===")
    messages = [
        {"role": "user", "content": "你叫什麼名字？"},
        {"role": "assistant", "content": "我是 Claude，一個 AI 助手。"},
        {"role": "user", "content": "你能幫我做什麼？"},
    ]
    response = llm.chat(messages)
    print(f"回應: {response}\n")

    # 獲取模型信息
    print("=== 模型信息 ===")
    info = llm.get_model_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))
