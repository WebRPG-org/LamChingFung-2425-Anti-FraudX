"""
Unified LLM Factory for multi-cloud AI providers.
Supports Vertex AI, Amazon Bedrock, and Azure OpenAI.
"""

import os
from typing import Optional
from utils.logger import log


class LlmFactory:
    """Create provider-specific LLM clients based on AI_PROVIDER."""

    @staticmethod
    def get_current_provider() -> str:
        provider = os.getenv("AI_PROVIDER", "vertex").strip().lower()
        provider_aliases = {
            "vertex_ai": "vertex",
            "google_vertex": "vertex",
            "amazon_bedrock": "bedrock",
            "azure": "azure_openai",
            "azure_openai": "azure_openai",
        }
        normalized = provider_aliases.get(provider, provider)
        if normalized not in {"vertex", "bedrock", "azure_openai"}:
            log.warning(f"[LLM_FACTORY] Unknown AI_PROVIDER={provider}, fallback to vertex")
            return "vertex"
        return normalized

    @staticmethod
    def create_llm(agent_type: str, use_gemini: Optional[bool] = None, scam_type: str = "", context: str = ""):
        valid_types = ["scammer", "victim", "expert", "recorder"]
        if agent_type not in valid_types:
            raise ValueError(f"無效的 agent_type: {agent_type}. 必須是 {valid_types} 之一")

        provider = LlmFactory.get_current_provider()
        log.info(f"[LLM_FACTORY] 使用 AI provider: {provider}")

        if provider == "vertex":
            return LlmFactory._create_vertex_ai_llm(agent_type, scam_type, context)
        if provider == "bedrock":
            return LlmFactory._create_bedrock_llm(agent_type)
        if provider == "azure_openai":
            return LlmFactory._create_azure_openai_llm(agent_type)

        raise ValueError(f"不支持的 AI provider: {provider}")

    @staticmethod
    def _create_vertex_ai_llm(agent_type: str, scam_type: str = "", context: str = ""):
        from llms.vertex_ai_llm import VertexAILLM

        return VertexAILLM(
            model_name=os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash-lite"),
            project_id=os.getenv("GCP_PROJECT_ID", "anti-fraudx"),
            location=os.getenv("GCP_LOCATION", "asia-east2"),
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
            timeout=60.0,
            max_retries=3,
        )

    @staticmethod
    def _create_bedrock_llm(agent_type: str):
        from llms.bedrock_llm import BedrockLLM

        return BedrockLLM(
            model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
            region=os.getenv("AWS_REGION", "ap-east-1"),
            temperature=0.7,
            max_output_tokens=2048,
        )

    @staticmethod
    def _create_azure_openai_llm(agent_type: str):
        from llms.azure_openai_llm import AzureOpenAILLM

        return AzureOpenAILLM(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            temperature=0.7,
            max_output_tokens=2048,
        )

    @staticmethod
    def get_provider_info() -> dict:
        provider = LlmFactory.get_current_provider()
        if provider == "vertex":
            return {
                "provider": "vertex",
                "model": os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash-lite"),
                "project_id": os.getenv("GCP_PROJECT_ID", "anti-fraudx"),
                "location": os.getenv("GCP_LOCATION", "asia-east2"),
            }
        if provider == "bedrock":
            return {
                "provider": "bedrock",
                "model": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                "region": os.getenv("AWS_REGION", "ap-east-1"),
            }
        return {
            "provider": "azure_openai",
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        }
