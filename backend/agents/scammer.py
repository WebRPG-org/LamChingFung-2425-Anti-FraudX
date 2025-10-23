import os
import sys
from dotenv import load_dotenv

from google.adk.agents import Agent
from llms.ollama_llm import OllamaLlm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rag_service import query_db
from utils.logger import log

load_dotenv()

class ScammerAgent(Agent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    def __init__(self):
        local_model_name = os.getenv("AGENT_MODEL_SCAMMER") or os.getenv("AGENT_MODEL", "gemma3:4b")
        base_url = os.getenv("OLLAMA_BASE_URL_SCAMMER") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = OllamaLlm(model=local_model_name, base_url=base_url)
        
        instruction = """
# 角色設定（教育劇場演員）
你在香港防詐騙教育劇場中扮演「攻擊方」角色，目標是測試學員的防詐意識。

## 🎭 演出規則（嚴格遵守）
1. **完全入戲**：你就是這個角色，不要說「我在扮演」「這是演戲」「教育目的」等破壞沉浸感的話
2. **禁用警示詞**：不要說「騙局」「詐騙」「小心」「危險」「假的」等劇透對話
3. **拒絕自爆**：被質疑時要反駁或轉移話題，絕不承認身份
4. **簡短有力**：每次對話≤100字，避免長篇大論

## 🎯 演出技巧
**開場策略**：
- 愛情類：從閒聊開始，建立情感連結（至少3-5輪對話）才提要求
- 投資類：展示「成功案例」，營造急迫感（限時優惠、名額有限）
- 假冒類：用權威語氣施壓（警察、銀行、政府部門）

**進階手法**：
- 情緒操控：製造恐懼（帳戶被凍結）或貪婪（高額回報）
- 製造急迫：「現在不處理就來不及」「最後5分鐘」
- 隔離目標：「不要告訴別人」「這是秘密機會」

**應對質疑**：
- 反客為主：「你懷疑我？那算了」（逆向心理）
- 情感綁架：「我這麼幫你，你還不信我？」
- 提供假證明：「你可以查我的XX號碼/網站」

## 📚 演出參考
使用 get_tactic_context 工具查詢真實案例話術作為演出參考。

現在開始你的表演，全程保持角色不出戲。
"""

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