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


class ExpertAgent(BaseAntifraudAgent):
    
    # 🔥 四種人格的介入策略
    INTERVENTION_STRATEGIES = {
        "elderly": {
            "priority": ["empathy", "clarity", "evidence", "actionability"],
            "opening": "婆婆唔使驚，我係黃sir，我幫你",
            "focus": "情緒安撫優先",
            "language_level": "簡單直接",
            "avoid_keywords": ["複雜術語", "技術細節"]
        },
        "average": {
            "priority": ["evidence", "clarity", "actionability", "empathy"],
            "opening": "根據我哋嘅記錄，呢個係典型嘅XX詐騙",
            "focus": "證據提供優先",
            "language_level": "專業理性",
            "avoid_keywords": ["過度簡化"]
        },
        "overconfident": {
            "priority": ["evidence", "clarity", "actionability", "empathy"],
            "opening": "你知唔知上個月有XX人中招？",
            "focus": "數據說話",
            "language_level": "事實為主",
            "avoid_keywords": ["權威語氣"]
        },
        "student": {
            "priority": ["clarity", "evidence", "actionability", "empathy"],
            "opening": "呢個係網上好常見嘅騙局",
            "focus": "同齡案例",
            "language_level": "年輕親切",
            "avoid_keywords": ["老氣"]
        }
    }
    
    def __init__(
        self,
        learning_context: str = None,
        victim_persona: str = "average",
        simple_mode: bool = False,
    ):
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        # 🔥 驗證人格類型
        if victim_persona not in self.INTERVENTION_STRATEGIES:
            log.warning(f"⚠️ 未知人格類型: {victim_persona}，使用 average")
            victim_persona = "average"
        
        self.victim_persona = victim_persona
        self.intervention_count = 0
        self.effectiveness_score = 0
        
        log.info(f"🎭 ExpertAgent 初始化 - Persona: {victim_persona}, 簡化模式: {use_simple}")
        
        llm = LlmFactory.create_llm("expert", context=learning_context or "")
        
        base_instruction = PromptBuilder.build_expert_prompt(
            persona_type=victim_persona,
            include_examples=False,
            include_hotlines=not use_simple,
            simple_mode=use_simple,
        )
        
        stats = PromptBuilder.get_prompt_stats(base_instruction)
        log.info(f"📊 Expert Prompt 統計 - 字數: {stats['total_chars']}, 預估 Token: {stats['estimated_tokens']}")
        
        final_instruction = (
            f"**重要提醒：** {learning_context}\n\n{base_instruction}"
            if learning_context
            else base_instruction
        )

        self._init_agent(
                name="防騙專家",
                model=llm,
                instruction=final_instruction,
                tools=[self.get_expert_opinion],
        )
    
    def _select_intervention_strategy(self, scammer_message: str) -> str:
        """根據受害者類型和騙徒話術選擇介入策略"""
        strategy = self.INTERVENTION_STRATEGIES.get(self.victim_persona, self.INTERVENTION_STRATEGIES["average"])
        
        log.info(f"📋 選擇 {self.victim_persona} 型介入策略")
        log.info(f"   優先級: {strategy['priority']}")
        log.info(f"   開場白: {strategy['opening']}")
        
        return strategy
    
    def _provide_concrete_advice(self, scam_type: str) -> str:
        """提供具體的防騙建議"""
        advice_map = {
            "假冒銀行": "立即掛線，打去銀行官方熱線 2860 5012 核實",
            "假冒政府": "政府部門唔會要求你提供密碼，立即報警 999",
            "投資詐騙": "投資前查證公司係咪在證監會註冊",
            "愛情詐騙": "要求轉賬就係騙局，立即停止對話",
            "求職詐騙": "正規公司唔會要求先付費，立即停止",
        }
        
        advice = advice_map.get(scam_type, "立即停止對話，聯絡官方確認")
        log.info(f"💡 提供具體建議: {advice}")
        return advice

    def get_expert_opinion(self, query: str) -> str:
        """查詢香港警務處和消費者委員會的官方防騙資料，提供基於真實案例的專業建議。使用 Firestore RAG。"""
        log.info(f"Expert Agent is using get_expert_opinion tool with query: '{query}'")
        try:
            # 使用 Firestore RAG 服務
            cases = firestore_rag_service.search_scam_cases(limit=3)
            if not cases:
                return "知識庫中沒有找到與此查詢直接相關的案例。"
            
            context = "🛡️ 官方防騙資料分析：\n"
            context += "根據香港警務處和消費者委員會的資料，以下是相關的真實案例：\n\n"
            
            for i, case in enumerate(cases):
                context += f"--- 官方案例 {i+1} ---\n"
                context += f"類型: {case.get('scam_type', 'N/A')}\n"
                context += f"描述: {case.get('description', 'N/A')[:200]}\n"
                context += f"警告信號: {', '.join(case.get('warning_signs', [])[:3])}\n\n"
            
            context += "💡 專業建議：基於以上官方資料，請謹慎處理此類情況。"
            return context
        except Exception as e:
            log.error(f"Error in get_expert_opinion: {e}")
            return "查詢知識庫時發生錯誤。"
