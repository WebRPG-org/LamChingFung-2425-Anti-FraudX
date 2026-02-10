import os
import sys
from dotenv import load_dotenv

from google.adk.agents import Agent
# 👈 This is the correct, official import for the built-in Ollama support
from llms.ollama_llm import OllamaLlm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rag_service import query_db
from utils.logger import log
from agents.prompts.prompt_builder import PromptBuilder

load_dotenv()

class ExpertAgent(Agent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    def __init__(self, learning_context: str = None, victim_persona: str = "average", simple_mode: bool = False):
        local_model_name = os.getenv("AGENT_MODEL_EXPERT") or os.getenv("AGENT_MODEL", "gemma3:4b")
        base_url = os.getenv("OLLAMA_BASE_URL_EXPERT") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # 檢查是否使用簡化模式（環境變量或參數）
        use_simple = simple_mode or os.getenv("USE_SIMPLE_PROMPTS", "false").lower() == "true"
        
        log.info(f"🎭 ExpertAgent 初始化 - 模型: {local_model_name}, URL: {base_url}, Persona: {victim_persona}, 簡化模式: {use_simple}")
        llm = OllamaLlm(model=local_model_name, base_url=base_url)
        
        # --- 使用 PromptBuilder 建構 Prompt ---
        base_instruction = PromptBuilder.build_expert_prompt(
            persona_type=victim_persona,
            include_examples=not use_simple,  # 簡化模式不包含示例
            include_hotlines=not use_simple,  # 簡化模式不包含熱線
            simple_mode=use_simple
        )
        
        # 記錄 Prompt 統計
        stats = PromptBuilder.get_prompt_stats(base_instruction)
        log.info(f"📊 Expert Prompt 統計 - 字數: {stats['total_chars']}, 預估 Token: {stats['estimated_tokens']}")
        
        # 如果有學習上下文，添加到 Prompt 前面
        final_instruction = f"**重要提醒：** {learning_context}\n\n{base_instruction}" if learning_context else base_instruction

        super().__init__(
            name="防騙專家",
            model=llm,
            instruction=final_instruction,
            tools=[self.get_expert_opinion],
            app_name="agents"  # 匹配文件夾名稱
        )

    def get_expert_opinion(self, query: str) -> str:
        """
        查詢香港警務處和消費者委員會的官方防騙資料
        提供基於真實案例的專業建議
        """
        log.info(f"Expert Agent is using get_expert_opinion tool with query: '{query}'")
        try:
            results = query_db(query, n_results=3)
            if not results or not results['documents'][0]:
                return "知識庫中沒有找到與此查詢直接相關的案例。"
            
            context = "🛡️ 官方防騙資料分析：\n"
            context += "根據香港警務處和消費者委員會的資料，以下是相關的真實案例：\n\n"
            
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                context += f"--- 官方案例 {i+1} ---\n"
                context += f"標題: {metadata.get('title', 'N/A')}\n"
                context += f"日期: {metadata.get('date', 'N/A')}\n"
                context += f"來源: {metadata.get('link', 'N/A')}\n"
                context += f"相關內容: \"{doc}\"\n\n"
            
            context += "💡 專業建議：基於以上官方資料，請謹慎處理此類情況。"
            return context
        except Exception as e:
            log.error(f"Error in get_expert_opinion: {e}")
            return "查詢知識庫時發生錯誤。"
