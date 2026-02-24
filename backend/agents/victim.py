import os
from typing import ClassVar
from dotenv import load_dotenv

from agents.prompts.prompt_builder import PromptBuilder
from llms.llm_factory import LlmFactory

load_dotenv()

# 嘗試導入 ADK Agent（如果使用 Ollama 模式）
try:
    from google.adk.agents import Agent as ADKAgent
    BaseAgent = ADKAgent
except ImportError:
    BaseAgent = object

class VictimAgent(BaseAgent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    # 保留 PERSONAS 字典以便向後兼容（如果其他代碼引用）
    PERSONAS: ClassVar[dict[str, str]] = {
        "elderly": "長者 - 陳婆婆",
        "average": "普通市民 - 張文軒",
        "overconfident": "過度自信 - 李俊傑",
        "student": "學生 - 王小明"
    }

    def __init__(self, persona_type: str = "average", simple_mode: bool = False):
        if persona_type not in self.PERSONAS:
            raise ValueError(f"Unknown persona_type: {persona_type}")
        
        from utils.logger import log
        
        # 檢查是否使用簡化模式（環境變量或參數）
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        log.info(f"🎭 VictimAgent 初始化 - Persona: {persona_type}, 簡化模式: {use_simple}")
        
        # 使用 LLM Factory 創建 LLM 實例
        llm = LlmFactory.create_llm("victim")

        # --- 使用 PromptBuilder 建構 Prompt ---
        instruction = PromptBuilder.build_victim_prompt(
            persona_type=persona_type,
            include_examples=not use_simple,  # 簡化模式不包含示例
            simple_mode=use_simple
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
        
        # 根據基類決定初始化方式
        if BaseAgent != object:
            super().__init__(
                name=name_mapping.get(persona_type, "受騙者"),
                model=llm,
                instruction=instruction,
                app_name="agents"
            )
        else:
            self.name = name_mapping.get(persona_type, "受騙者")
            self.model = llm
            self.instruction = instruction
            self.app_name = "agents"
