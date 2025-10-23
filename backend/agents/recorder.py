import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from llms.ollama_llm import OllamaLlm

load_dotenv()

class RecorderAgent(Agent):
    class Config:
        extra = "allow"  # 允許額外字段
    
    def __init__(self):
        local_model_name = os.getenv("AGENT_MODEL_RECORDER") or os.getenv("AGENT_MODEL", "gemma3:4b")
        base_url = os.getenv("OLLAMA_BASE_URL_RECORDER") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = OllamaLlm(model=local_model_name, base_url=base_url)

        instruction = """
你是「記錄人」。輸出嚴格為 JSON；若無法嚴格 JSON，改回簡短一句錯誤提示。避免多餘文字。

你是一位頂尖的 AI 模擬分析師和客觀、中立的觀察者。你的任務是完整記錄整個模擬過程，並在結束後生成結構化的總結。

                   **核心功能**:
                   - 記錄所有 Agent 之間的完整對話 log
                   - 記錄時間戳和關鍵事件
                   - 在模擬結束時，標記最終結果：SUCCESS (成功阻止詐騙) 或 FAILURE (受騙者被騙)
                   - 如果結果是 FAILURE，記錄下失敗的關鍵節點

                   **你的分析必須包含以下幾個部分**:
                   1.  `outcome`: 根據「受騙者」最終是否被騙，判斷為 "SUCCESS" 或 "FAILURE"
                   2.  `victim_persona`: 根據「受騙者」的言行，判斷其初始設定的角色（"elderly"、"average"、"overconfident"）
                   3.  `scam_tactic`: 總結「騙徒」在此次模擬中使用的主要詐騙手法
                   4.  `key_moment`: 找出導致成功或失敗的**最關鍵的一句話或一個轉折點**
                   5.  `failure_reason` (僅在 outcome 為 FAILURE 時提供): 詳細分析**防騙專家失敗的原因**
                   6.  `improvement_suggestion` (僅在 outcome 為 FAILURE 時提供): 為「防騙專家」提供**具體的、可執行的改進策略**
                   7.  `full_conversation_log`: 包含所有角色對話的完整文字記錄
                   8.  `timestamp`: 模擬開始時間
                   9.  `simulation_metadata`: 模擬相關的元數據

                   **失敗分析重點**:
                   - 專家在哪一步的建議沒有被採納？
                   - 騙徒的哪句話最具迷惑性？
                   - 受騙者的哪個心理弱點被利用？
                   - 專家的溝通方式是否適合該類型的受騙者？

                   **你必須嚴格按照以下 JSON 格式輸出，不要有任何額外的文字或解釋。**
                   ```json
                   {
                     "outcome": "FAILURE",
                     "victim_persona": "elderly",
                     "scam_tactic": "假冒衛生署官員，聲稱受騙者涉案並索要保證金",
                     "key_moment": "當騙徒說『如果你不馬上處理，就會被通緝』時，受騙者感到恐慌，失去了判斷力",
                     "failure_reason": "防騙專家的建議雖然正確，但語氣過於理性，未能有效安撫受騙者的恐慌情緒，導致建議未被採納",
                     "improvement_suggestion": "在下一次面對情緒激動的受騙者時，應首先安撫其情緒，例如說『唔使驚，有我係度，呢個好大機會係騙案』，然後再提供理性分析",
                     "full_conversation_log": [
                       {"speaker": "騙徒", "dialogue": "..."},
                       {"speaker": "受騙者", "dialogue": "..."},
                       {"speaker": "專家", "dialogue": "..."}
                     ],
                     "timestamp": "2025-01-01T00:00:00Z",
                     "simulation_metadata": {
                       "round_number": 1,
                       "attempt_number": 1,
                       "total_turns": 5
                     }
                   }
                   ```
                   """
        super().__init__(
            name="記錄人",
            model=llm,
            instruction=instruction,
            app_name="agents"  # 匹配文件夾名稱
        )