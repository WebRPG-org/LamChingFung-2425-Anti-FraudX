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
    
    # 🔥 情緒狀態定義
    EMOTIONAL_STATES = {
        "neutral": {
            "keywords": ["係咪", "點解", "可能"],
            "trust_change": 0,
            "description": "中立狀態"
        },
        "anxious": {
            "keywords": ["驚", "擔心", "點算", "嚴重"],
            "trust_change": 5,
            "description": "焦慮狀態 - 容易相信騙徒"
        },
        "calm": {
            "keywords": ["冷靜", "慢慢嚟", "等等", "唔急"],
            "trust_change": -5,
            "description": "平靜狀態 - 不容易相信騙徒"
        },
        "suspicious": {
            "keywords": ["騙人", "唔信", "呃人", "假嘅"],
            "trust_change": -10,
            "description": "懷疑狀態 - 高度警覺"
        },
        "panicked": {
            "keywords": ["點算好", "我好驚", "救命", "快啲"],
            "trust_change": 10,
            "description": "恐慌狀態 - 極度容易相信騙徒"
        }
    }
    
    # 🔥 初始信任度（根據人格）
    INITIAL_TRUST = {
        "elderly": {"scammer": 70, "expert": 50, "alertness": 30},
        "average": {"scammer": 50, "expert": 60, "alertness": 50},
        "overconfident": {"scammer": 30, "expert": 40, "alertness": 70},
        "student": {"scammer": 55, "expert": 45, "alertness": 45}
    }

    def __init__(self, persona_type: str = "average", simple_mode: bool = False):
        if persona_type not in self.PERSONAS:
            raise ValueError(f"Unknown persona_type: {persona_type}")
        
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        # 🔥 初始化情緒狀態
        self.emotional_state = "neutral"
        self.persona_type = persona_type
        self.initial_trust = self.INITIAL_TRUST.get(persona_type, self.INITIAL_TRUST["average"])
        
        log.info(f"🎭 VictimAgent 初始化 - Persona: {persona_type}, 簡化模式: {use_simple}")
        log.info(f"   初始信任度: 騙徒={self.initial_trust['scammer']}, 專家={self.initial_trust['expert']}, 警覺={self.initial_trust['alertness']}")
        
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
    
    def _update_emotional_state(self, scammer_message: str, expert_message: str = None) -> str:
        """根據騙徒和專家的消息更新情緒狀態"""
        old_state = self.emotional_state
        
        # 分析騙徒消息
        if scammer_message:
            if any(word in scammer_message for word in ["凍結", "損失", "危險", "後果", "嚴重"]):
                self.emotional_state = "panicked"
            elif any(word in scammer_message for word in ["立即", "馬上", "緊急"]):
                self.emotional_state = "anxious"
        
        # 分析專家消息
        if expert_message:
            if any(word in expert_message for word in ["唔使驚", "冷靜", "慢慢嚟"]):
                self.emotional_state = "calm"
            elif any(word in expert_message for word in ["騙", "詐", "假", "唔信"]):
                self.emotional_state = "suspicious"
        
        if old_state != self.emotional_state:
            log.info(f"😊 情緒狀態變化: {old_state} → {self.emotional_state}")
        
        return self.emotional_state
    
    def _generate_response_based_on_emotion(self) -> str:
        """根據情緒狀態生成自然的受害者反應"""
        state_info = self.EMOTIONAL_STATES.get(self.emotional_state, self.EMOTIONAL_STATES["neutral"])
        
        log.info(f"💭 根據 {self.emotional_state} 狀態生成回應")
        log.info(f"   信任度變化: {state_info['trust_change']:+d}")
        
        return self.emotional_state
