import os
import sys
from dotenv import load_dotenv

from google.adk.agents import Agent
from llms.ollama_llm import OllamaLlm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rag_service import query_db
from utils.logger import log
from agents.prompts.prompt_builder import PromptBuilder

load_dotenv()

class ScammerAgent(Agent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    def __init__(self, scam_tactic: str = "假冒銀行"):
        local_model_name = os.getenv("AGENT_MODEL_SCAMMER") or os.getenv("AGENT_MODEL", "gemma3:4b")
        base_url = os.getenv("OLLAMA_BASE_URL_SCAMMER") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        log.info(f"🎭 ScammerAgent 初始化 - 模型: {local_model_name}, URL: {base_url}, 手法: {scam_tactic}")
        llm = OllamaLlm(model=local_model_name, base_url=base_url)
        
        # --- 使用 PromptBuilder 建構 Prompt ---
        instruction = PromptBuilder.build_scammer_prompt(
            scam_tactic=scam_tactic,
            include_examples=True
        )
        
        # 記錄 Prompt 統計
        stats = PromptBuilder.get_prompt_stats(instruction)
        log.info(f"📊 Scammer Prompt 統計 - 字數: {stats['total_chars']}, 預估 Token: {stats['estimated_tokens']}")

        super().__init__(
            name="專業騙徒",
            model=llm,
            instruction=instruction,
            tools=[self.get_tactic_context],
            app_name="agents"  # 匹配文件夾名稱
        )

    def get_tactic_context(self, query: str) -> str:
        """
        查詢真實騙案範例作為「話術靈感」，避免離題。
        """
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
