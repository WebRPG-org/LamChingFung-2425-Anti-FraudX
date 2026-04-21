"""
Azure OpenAI LLM wrapper.
Provides the same generate interface used by existing agents.
"""

from utils.logger import log

try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False


class AzureOpenAILLM:
    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str, temperature: float = 0.7, max_output_tokens: int = 2048):
        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError("openai 未安裝。請在 requirements.txt 加入 openai")
        if not endpoint or not api_key:
            raise ValueError("Azure OpenAI endpoint / api key 未配置")

        self.deployment = deployment
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        log.info(f"[AZURE_OPENAI_LLM] ✅ Azure OpenAI 已初始化 - deployment: {deployment}")

    def generate(self, prompt: str, system_instruction: str = "", temperature=None, max_tokens=None) -> str:
        temp = self.temperature if temperature is None else temperature
        max_tok = self.max_output_tokens if max_tokens is None else max_tokens

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok,
        )
        if response.choices:
            return response.choices[0].message.content or ""
        return ""
