import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.firestore_rag_service import firestore_rag_service
from utils.logger import log
from agents.prompts.prompt_builder import PromptBuilder
from llms.llm_factory import LlmFactory
from agents.base_agent import BaseAntifraudAgent  # DUP-002 fix

load_dotenv()


class ScammerAgent(BaseAntifraudAgent):
    
    # 🔥 策略階段定義
    STRATEGY_PHASES = {
        "trust_building": {
            "description": "建立信任階段",
            "tactics": ["authority", "empathy", "evidence"],
            "duration": 2
        },
        "panic_creation": {
            "description": "製造恐慌階段",
            "tactics": ["fear", "urgency", "threat"],
            "duration": 2
        },
        "action_urging": {
            "description": "催促行動階段",
            "tactics": ["urgency", "pressure", "deadline"],
            "duration": 2
        }
    }
    
    # 🔥 人格適應配置
    PERSONA_ADAPTATIONS = {
        "elderly": {
            "tone": "溫柔、耐心、像對自己父母",
            "keywords": ["婆婆", "安全", "保護"],
            "avoid": ["複雜術語", "快速變化"]
        },
        "average": {
            "tone": "專業、理性、帶關心",
            "keywords": ["根據", "數據", "案例"],
            "avoid": ["過度簡化"]
        },
        "overconfident": {
            "tone": "挑戰、激將、製造對立",
            "keywords": ["你以為", "證明", "能力"],
            "avoid": ["權威語氣"]
        },
        "student": {
            "tone": "年輕、親切、同齡感",
            "keywords": ["機會", "賺錢", "簡單"],
            "avoid": ["老氣"]
        }
    }
    
    def __init__(self, scam_tactic: str = "假冒銀行", simple_mode: bool = False, victim_persona: str = "average"):
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        # 🔥 Limit scammer output length (~100 chars)
        os.environ["OLLAMA_NUM_PREDICT_SCAMMER"] = "200"
        
        # 🔥 初始化策略階段
        self.strategy_phase = "trust_building"
        self.phase_round_count = 0
        self.tactics_used = []
        self.victim_persona = victim_persona
        
        log.info(f"🎭 ScammerAgent 初始化 - 手法: {scam_tactic}, 人格: {victim_persona}, 簡化模式: {use_simple}")
        
        llm = LlmFactory.create_llm("scammer", scam_type=scam_tactic)
        
        instruction = PromptBuilder.build_scammer_prompt(
            scam_tactic=scam_tactic,
            include_examples=not use_simple,
            simple_mode=use_simple,
        )
        
        stats = PromptBuilder.get_prompt_stats(instruction)
        log.info(f"📊 Scammer Prompt 統計 - 字數: {stats['total_chars']}, 預估 Token: {stats['estimated_tokens']}")

        self._init_agent(
                name="專業騙徒",
                model=llm,
                instruction=instruction,
                tools=[self.get_tactic_context],
        )
    
    def _get_next_strategy_phase(self):
        """根據回合數自動進入下一個策略階段"""
        phases = list(self.STRATEGY_PHASES.keys())
        current_idx = phases.index(self.strategy_phase)
        if self.phase_round_count >= self.STRATEGY_PHASES[self.strategy_phase]["duration"]:
            if current_idx < len(phases) - 1:
                self.strategy_phase = phases[current_idx + 1]
                self.phase_round_count = 0
                log.info(f"🔄 策略階段轉換: {phases[current_idx]} → {self.strategy_phase}")
    
    def _apply_persona_adaptation(self, base_prompt: str) -> str:
        """根據受害者人格調整話術"""
        if self.victim_persona not in self.PERSONA_ADAPTATIONS:
            return base_prompt
        
        adaptation = self.PERSONA_ADAPTATIONS[self.victim_persona]
        adapted_prompt = f"{base_prompt}\n\n【人格適應】\n"
        adapted_prompt += f"語氣: {adaptation['tone']}\n"
        adapted_prompt += f"關鍵詞: {', '.join(adaptation['keywords'])}\n"
        
        log.info(f"📝 已應用 {self.victim_persona} 型人格適應")
        return adapted_prompt

    def get_tactic_context(self, query: str) -> str:
        """查詢真實騙案範例作為「話術靈感」，避免離題。使用 Firestore RAG。"""
        try:
            # 使用 Firestore RAG 服務
            cases = firestore_rag_service.search_scam_cases(limit=2)
            if not cases:
                return "（暫時搵唔到相似案例）"
            
            out = []
            for case in cases:
                title = case.get('scam_type', 'N/A')
                description = case.get('description', '')[:100]
                out.append(f"《{title}》: {description}")
            
            return "\n".join(out[:2])
        except Exception as e:
            log.warning(f"scammer RAG error: {e}")
            return "（RAG 發生錯誤）"
