import os
import sys
from typing import ClassVar
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from agents.prompts.prompt_builder import PromptBuilder
from llms.llm_factory import LlmFactory
from agents.base_agent import BaseAntifraudAgent  # DUP-002 fix

load_dotenv()


class VictimAgent(BaseAntifraudAgent):

    PERSONAS: ClassVar[dict] = {
        "elderly":        "長者 - 陳婆婆",
        "average":        "普通市民 - 張文軒",
        "overconfident":  "過度自信 - 李俊傑",
        "student":        "學生 - 王小明",
    }

    _NAME_MAP: ClassVar[dict] = {
        "elderly":       "受騙者",
        "average":       "受騙者",
        "overconfident": "用戶",
        "student":       "大學生",
    }

    def __init__(self, persona_type: str = "average", simple_mode: bool = False):
        if persona_type not in self.PERSONAS:
            raise ValueError(f"Unknown persona_type: {persona_type}")
        
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        log.info(f"🎭 VictimAgent 初始化 - Persona: {persona_type}, 簡化模式: {use_simple}")
        
        llm = LlmFactory.create_llm("victim")

        instruction = PromptBuilder.build_victim_prompt(
            persona_type=persona_type,
            include_examples=not use_simple,
            simple_mode=use_simple,
        )
        
        stats = PromptBuilder.get_prompt_stats(instruction)
        log.info(f"📊 Victim Prompt 統計 - 字數: {stats['total_chars']}, 預估 Token: {stats['estimated_tokens']}")

        self._init_agent(
            name=self._NAME_MAP.get(persona_type, "受騙者"),
                model=llm,
                instruction=instruction,
            )
