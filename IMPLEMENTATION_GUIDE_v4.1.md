# AI 防詐平台 v4.1 - 四代理系統集成實施指南

## 📋 執行摘要

本指南提供了完整的實施步驟，用於集成以下核心功能：
1. **四代理系統** - ScammerAgent、ExpertAgent、VictimAgent、RecorderAgent
2. **信任度系統** - 三維度追蹤、修改器、情緒狀態
3. **並行回應生成** - asyncio.gather()、性能優化
4. **會話持久化** - sessionStorage + SQLite
5. **知識與評分系統** - RAG、自適應評分、RecorderAgent分析

---

## 🎯 第一階段：驗證現有系統（1小時）

### 1.1 檢查清單
- [ ] 確認 `backend/.env` 已配置
- [ ] 確認 `config.py` 有完整配置
- [ ] 確認四個 Agent 類已存在：`ScammerAgent`、`ExpertAgent`、`VictimAgent`、`RecorderAgent`
- [ ] 確認 `PerformanceTracker` 已實現
- [ ] 確認 `AdaptiveWeightOptimizer` 已實現
- [ ] 確認 `RPGv2GameModeManager` 已實現

### 1.2 驗證命令
```bash
# 檢查 Python 環境
python --version

# 檢查依賴
pip list | grep -E "fastapi|pydantic|google|ollama"

# 測試導入
python -c "from backend.config import config; print('✅ Config OK')"
python -c "from backend.agents.scammer import ScammerAgent; print('✅ ScammerAgent OK')"
python -c "from backend.agents.expert import ExpertAgent; print('✅ ExpertAgent OK')"
python -c "from backend.agents.victim import VictimAgent; print('✅ VictimAgent OK')"
python -c "from backend.agents.recorder import RecorderAgent; print('✅ RecorderAgent OK')"
```

---

## 🔧 第二階段：完善四代理系統（2-3天）

### 2.1 ScammerAgent 完善清單

**文件**: `backend/agents/scammer.py`

**需要實現的功能**:
- [ ] 5種詐騙手法的完整實現
- [ ] 50-100字的字數限制
- [ ] 策略漸進性（信任建立 → 恐慌製造 → 行動催促）
- [ ] 人格適應（elderly/average/overconfident/student）
- [ ] 策略追蹤和疲勞計算

**關鍵代碼片段**:
```python
class ScammerAgent(BaseAntifraudAgent):
    def __init__(self, scam_tactic: str = "假冒銀行", simple_mode: bool = False):
        # 初始化時設置策略階段
        self.strategy_phase = "trust_building"  # trust_building → panic_creation → action_urging
        self.tactics_used = []
        self.current_round = 0
        
    async def generate(self, context: str, victim_response: str = "") -> str:
        # 1. 根據當前策略階段調整話術
        # 2. 根據受害者人格調整內容
        # 3. 限制字數 50-100
        # 4. 返回詐騙回應
        pass
```

### 2.2 ExpertAgent 完善清單

**文件**: `backend/agents/expert.py`

**需要實現的功能**:
- [ ] 防詐專家「黃 sir」角色完整實現
- [ ] 80-100字的字數限制
- [ ] 四種人格策略（elderly/average/overconfident/student）
- [ ] 具體防騙建議和官方熱線
- [ ] 情緒安撫和證據提供

**關鍵代碼片段**:
```python
class ExpertAgent(BaseAntifraudAgent):
    PERSONA_STRATEGIES = {
        "elderly": {
            "opening": "婆婆唔使驚，我係黃sir，我幫你",
            "focus": "情緒安撫",
            "language": "簡單直接"
        },
        "average": {
            "opening": "根據我哋嘅記錄，呢個係典型嘅XX詐騙",
            "focus": "證據提供",
            "language": "專業理性"
        },
        # ... 其他人格
    }
```

### 2.3 VictimAgent 完善清單

**文件**: `backend/agents/victim.py`

**需要實現的功能**:
- [ ] 4種受害者人格完整實現
- [ ] 情緒狀態變化（neutral → anxious → panicked → suspicious → calm）
- [ ] 30-80字的字數限制
- [ ] 自然的受害者反應
- [ ] 信任度變化的反映

### 2.4 RecorderAgent 完善清單

**文件**: `backend/agents/recorder.py`

**需要實現的功能**:
- [ ] 詳細的會話分析
- [ ] 純JSON輸出格式
- [ ] 騙徒性能評分（說服力、可信度、施壓效果、策略一致性）
- [ ] 專家性能評分（干預效果、清晰度、同理心、可執行性、時機把握）
- [ ] 失敗/成功原因深度分析
- [ ] 改進建議

---

## 💚 第三階段：完善信任度系統（1-2天）

### 3.1 VictimTrustState 實現清單

**文件**: `backend/utils/performance_tracker.py`

**已實現的功能**:
- ✅ 三維度追蹤（trust_in_scammer、trust_in_expert、alertness）
- ✅ 情緒狀態變化
- ✅ 變化歷史記錄

**需要驗證的功能**:
- [ ] 信任度限制在 0-100
- [ ] 情緒狀態正確更新
- [ ] 歷史記錄完整

### 3.2 信任度修改器實現清單

**文件**: `backend/utils/adaptive_scoring.py`

**已實現的功能**:
- ✅ 慣性修改器
- ✅ 疲勞修改器
- ✅ 情緒修改器
- ✅ 人格修改器

**需要驗證的功能**:
- [ ] 所有修改器正確應用
- [ ] 修改器組合邏輯正確
- [ ] 性能追蹤正確記錄

### 3.3 結果判定邏輯實現清單

**文件**: `backend/utils/performance_tracker.py`

**需要實現的功能**:
- [ ] 騙徒贏：trust_in_scammer ≥ 80
- [ ] 專家贏：trust_in_expert ≥ 75 或 (trust_in_scammer < 40 AND trust_in_expert > 60)
- [ ] 自我保護：alertness ≥ 80
- [ ] 最大回合數檢查

---

## ⚡ 第四階段：並行回應生成優化（1天）

### 4.1 asyncio.gather() 實現清單

**文件**: `backend/api/game_routes_v2.py`

**需要實現的功能**:
- [ ] 同時生成騙徒和專家回應
- [ ] 使用 asyncio.gather() 並行執行
- [ ] 性能測試（目標：~50% 提升）
- [ ] 錯誤處理和超時管理

**關鍵代碼片段**:
```python
async def game_action(session_id: str, message: str):
    service = get_agent_service(persona_type)
    
    # 並行生成
    scammer_task = service.generate_response(
        agent_type="scammer",
        message=message,
        session_id=session_id
    )
    
    expert_task = service.generate_response(
        agent_type="expert",
        message=message,
        session_id=session_id
    )
    
    # 等待兩個任務完成
    scammer_result, expert_result = await asyncio.gather(
        scammer_task,
        expert_task,
        return_exceptions=True
    )
    
    return {
        "scammer_response": scammer_result["reply"],
        "expert_response": expert_result["reply"],
        "trust_changes": calculate_trust_changes(...)
    }
```

### 4.2 三種遊戲模式實現清單

- [ ] **three_way**: 騙徒 + 專家 + 受害者（並行）
- [ ] **scammer_only**: 僅騙徒
- [ ] **expert_only**: 僅專家

---

## 💾 第五階段：會話持久化完善（1天）

### 5.1 sessionStorage 實現清單（前端）

**文件**: `rpg-platform-v2/src/scenes/BattleScene.ts`

**需要實現的功能**:
- [ ] 保存 session_id、消息、信任值、回合數
- [ ] 頁面刷新後恢復狀態
- [ ] 防止跨 NPC 污染

**關鍵代碼片段**:
```typescript
function saveState() {
    const state = {
        session_id: currentSessionId,
        scamType: currentScamType,
        messages: chatMessages,
        trustData: { scammer: 50, expert: 60, alertness: 40 },
        round: roundCount
    };
    sessionStorage.setItem('battleState', JSON.stringify(state));
}

function tryRestoreState() {
    const saved = sessionStorage.getItem('battleState');
    if (saved) {
        const state = JSON.parse(saved);
        if (state.scamType === currentScamType) {
            // 恢復狀態
            restoreFromState(state);
        }
    }
}
```

### 5.2 SQLite 持久化實現清單（後端）

**文件**: `backend/api/game_routes_v2.py`

**已實現的功能**:
- ✅ sessions 表
- ✅ conversations 表

**需要驗證的功能**:
- [ ] 表結構正確
- [ ] 數據保存完整
- [ ] 查詢性能良好

---

## 🧠 第六階段：知識與評分系統（2-3天）

### 6.1 RAG 知識庫集成清單

**文件**: `backend/llms/rag_integration.py`

**需要實現的功能**:
- [ ] ChromaDB 存儲 281 個真實香港詐騙案例
- [ ] 按詐騙類型查詢相關案例
- [ ] 注入到代理系統指令

### 6.2 自適應評分系統清單

**文件**: `backend/utils/adaptive_scoring.py`

**已實現的功能**:
- ✅ 基於人格的權重調整
- ✅ 騙徒性能評分
- ✅ 專家性能評分

**需要驗證的功能**:
- [ ] 權重計算正確
- [ ] 評分公式正確
- [ ] 結果合理

### 6.3 RecorderAgent 詳細評分清單

**文件**: `backend/agents/recorder.py`

**需要實現的功能**:
- [ ] 純 JSON 輸出
- [ ] 詳細的分析和建議
- [ ] 失敗/成功原因分析

### 6.4 騙徒策略管理清單

**文件**: `backend/utils/scammer_strategy_manager.py`

**需要實現的功能**:
- [ ] 追蹤已用策略
- [ ] 計算疲勞乘數
- [ ] 建議下一個策略

---

## 📡 第七階段：API 端點完善（1天）

### 7.1 RPGv2 遊戲 API 清單

- [ ] POST /api/rpgv2/game/start - 開始遊戲
- [ ] POST /api/rpgv2/game/message - 發送消息
- [ ] POST /api/rpgv2/game/action - 遊戲動作（並行生成）
- [ ] POST /api/rpgv2/game/analyze - 分析會話
- [ ] GET /api/rpgv2/game/state/{session_id} - 獲取遊戲狀態

### 7.2 信任度 API 清單

- [ ] POST /api/rpgv2/trust/update - 更新信任度
- [ ] GET /api/rpgv2/trust/{session_id} - 獲取信任度

### 7.3 評分 API 清單

- [ ] POST /api/rpgv2/score/calculate - 計算評分
- [ ] GET /api/rpgv2/score/{session_id} - 獲取評分

---

## 🔧 第八階段：配置與環境（1天）

### 8.1 backend/.env 配置清單

```bash
# LLM 提供者
GEMINI_ENABLED=false
GEMINI_API_KEY=your_key
AGENT_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434

# 性能調優
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=400
OLLAMA_TEMPERATURE=0.7

# 數據庫
CHROMA_PATH=backend/db/chroma_db
DATABASE_PATH=anti_fraud_game.db

# 功能開關
ENABLE_RAG=true
ENABLE_ADAPTIVE_SCORING=true
ENABLE_PARALLEL_GENERATION=true
```

### 8.2 config.py 配置驗證清單

- [ ] TrustConfig - 信任度閾值、變化限制
- [ ] SimulationConfig - 最大回合、時序延遲
- [ ] PersonaConfig - 四種人格配置
- [ ] ScamTacticsConfig - 十種詐騙策略

---

## 📊 第九階段：測試與驗證（1-2天）

### 9.1 單元測試清單

- [ ] 四代理系統測試
- [ ] 信任度計算測試
- [ ] 並行生成測試
- [ ] 會話持久化測試

### 9.2 集成測試清單

- [ ] 完整遊戲流程測試
- [ ] 多輪對話測試
- [ ] 評分系統測試

### 9.3 性能測試清單

- [ ] 並行生成性能（目標：~50% 提升）
- [ ] RAG 查詢性能
- [ ] 會話恢復性能

---

## 🚀 快速開始命令

### 啟動後端
```bash
cd backend
python main.py
```

### 啟動前端（RPGv2）
```bash
cd rpg-platform-v2
npm install
npm run dev
```

### 運行測試
```bash
pytest backend/tests/ -v
```

---

## 📈 預期成果

✅ 完整的四代理系統（騙徒、專家、受害者、記錄員）
✅ 動態信任度系統（三維度追蹤、修改器、情緒狀態）
✅ 並行回應生成（~50% 性能提升）
✅ 完整的會話持久化（前後端）
✅ 詳細的評分分析系統
✅ RAG 知識庫集成
✅ 自適應評分系統
✅ 完整的 API 端點
✅ 詳細的文檔和測試

---

## ⏱️ 時間估計

- 第一階段（驗證）：1 小時
- 第二階段（四代理）：2-3 天
- 第三階段（信任度）：1-2 天
- 第四階段（並行生成）：1 天
- 第五階段（會話持久化）：1 天
- 第六階段（知識評分）：2-3 天
- 第七階段（API）：1 天
- 第八階段（配置）：1 天
- 第九階段（測試）：1-2 天

**總計：11-16 天**

---

## 📞 支持

如有任何問題，請參考：
- `docs/CORE_FEATURES.md` - 核心功能文檔
- `docs/SECONDARY_FEATURES.md` - 支持功能文檔
- `docs/ARCHITECTURE.md` - 系統架構文檔

