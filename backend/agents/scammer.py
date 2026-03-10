import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rag_service import query_db
from utils.logger import log
from agents.prompts.prompt_builder import PromptBuilder
from llms.llm_factory import LlmFactory
from agents.base_agent import BaseAntifraudAgent  # DUP-002 fix

load_dotenv()


class ScammerAgent(BaseAntifraudAgent):
    
    def __init__(self, scam_tactic: str = "假冒銀行", simple_mode: bool = False):
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        # 🔥 Limit scammer output length (~100 chars)
        os.environ["OLLAMA_NUM_PREDICT_SCAMMER"] = "200"
        
        log.info(f"🎭 ScammerAgent 初始化 - 手法: {scam_tactic}, 簡化模式: {use_simple}")
        
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

    def get_tactic_context(self, query: str) -> str:
        """查詢真實騙案範例作為「話術靈感」，避免離題。"""
        try:
            results = query_db(query, n_results=2)
            if not results or not results.get('documents'):
                return "（暫時搵唔到相似案例）"
            out = []
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                out.append(f"《{meta.get('title','N/A')}》{meta.get('date','N/A')}: {doc}")
            return "\n".join(out[:2])
        except Exception as e:
            log.warning(f"scammer RAG error: {e}")
            return "（RAG 發生錯誤）"
