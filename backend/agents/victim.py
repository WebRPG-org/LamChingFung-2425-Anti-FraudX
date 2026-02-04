import os
from typing import ClassVar
from dotenv import load_dotenv

from google.adk.agents import Agent
from llms.ollama_llm import OllamaLlm
from agents.prompts.prompt_builder import PromptBuilder

load_dotenv()

class VictimAgent(Agent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    # 保留 PERSONAS 字典以便向後兼容（如果其他代碼引用）
    PERSONAS: ClassVar[dict[str, str]] = {
        "elderly": "長者 - 陳婆婆",
        "average": "普通市民 - 張文軒",
        "overconfident": "過度自信 - 李俊傑",
        "student": "學生 - 王小明"
    }

    def __init__(self, persona_type: str = "average"):
        if persona_type not in self.PERSONAS:
            raise ValueError(f"Unknown persona_type: {persona_type}")
        
        local_model_name = os.getenv("AGENT_MODEL_VICTIM") or os.getenv("AGENT_MODEL", "gemma3:4b")
        base_url = os.getenv("OLLAMA_BASE_URL_VICTIM") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        from utils.logger import log
        log.info(f"🎭 VictimAgent 初始化 - Persona: {persona_type}, 模型: {local_model_name}, URL: {base_url}")
        llm = OllamaLlm(model=local_model_name, base_url=base_url)

        # --- 使用 PromptBuilder 建構 Prompt ---
        instruction = PromptBuilder.build_victim_prompt(
            persona_type=persona_type,
            include_examples=True
        )
        
        # 記錄 Prompt 統計
        stats = PromptBuilder.get_prompt_stats(instruction)
        log.info(f"📊 Victim Prompt 統計 - 字數: {stats['total_chars']}, 預估 Token: {stats['estimated_tokens']}")

        # 根據 persona 設置名稱
        name_mapping = {
            "elderly": "受騙者",
            "average": "受騙者",
            "overconfident": "用戶",
            "student": "大學生"
        }
        
        super().__init__(
            name=name_mapping.get(persona_type, "受騙者"),
            model=llm,
            instruction=instruction,
            app_name="agents"  # 匹配文件夾名稱
        )
