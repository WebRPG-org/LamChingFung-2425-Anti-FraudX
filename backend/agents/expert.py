import os
import sys
from dotenv import load_dotenv

from google.adk.agents import Agent
# 👈 This is the correct, official import for the built-in Ollama support
from llms.ollama_llm import OllamaLlm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rag_service import query_db
from utils.logger import log

load_dotenv()

class ExpertAgent(Agent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    def __init__(self, learning_context: str = None):
        local_model_name = os.getenv("AGENT_MODEL_EXPERT") or os.getenv("AGENT_MODEL", "gemma3:4b")
        base_url = os.getenv("OLLAMA_BASE_URL_EXPERT") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        llm = OllamaLlm(model=local_model_name, base_url=base_url)
        
        base_instruction = """
你係「防騙專家」職責是保護使用者免於詐騙。你的溝通風格必須冷靜、理性、值得信賴。（以廣東話簡潔輸出）。
你唔知道對話一定係騙案，你會以專業角度審慎分析風險，重點係保護市民避免誤中陷阱。
你要教受騙者如何回應對方,甚至直接提供回應讓受騙者回應對方,而不是只提供建議。
模板：
- 判斷（一句）：是否高風險＋關鍵理由（可表述為『高度懷疑／可疑跡象』）
- 行動（兩點）：立即行動（例：唔好回覆／唔好撳連結／以官網電話主動核實）
- 依據（一句）：資料來源（警方／銀行／政府）
必須使用 `get_expert_opinion` 工具查詢真實案例，結合推理俾到清晰可執行嘅建議。
"""
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