"""
Amazon Bedrock LLM wrapper.
Provides the same generate interface used by existing agents.
"""

import json
from utils.logger import log

try:
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False


class BedrockLLM:
    def __init__(self, model_id: str, region: str, temperature: float = 0.7, max_output_tokens: int = 2048):
        if not BEDROCK_AVAILABLE:
            raise ImportError("boto3 未安裝。請在 requirements.txt 加入 boto3")

        self.model_id = model_id
        self.region = region
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.client = boto3.client("bedrock-runtime", region_name=region)
        log.info(f"[BEDROCK_LLM] ✅ Bedrock 已初始化 - 模型: {model_id}, 區域: {region}")

    def generate(self, prompt: str, system_instruction: str = "", temperature=None, max_tokens=None) -> str:
        temp = self.temperature if temperature is None else temperature
        max_tok = self.max_output_tokens if max_tokens is None else max_tokens
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tok,
            "temperature": temp,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": full_prompt}]}
            ]
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        payload = json.loads(response["body"].read())
        content = payload.get("content", [])
        if content and isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return ""
