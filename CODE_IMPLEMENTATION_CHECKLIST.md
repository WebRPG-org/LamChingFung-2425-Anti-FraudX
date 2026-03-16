# AI 防詐平台 v4.1 - 代碼實施清單

## 📋 文件修改清單

### 第一階段：四代理系統完善

#### 1. backend/agents/scammer.py - 完善騙徒代理

**需要添加的功能**:
```python
# 添加策略階段管理
class ScammerAgent(BaseAntifraudAgent):
    STRATEGY_PHASES = {
        "trust_building": {
            "description": "建立信任階段",
            "tactics": ["authority", "empathy", "evidence"],
            "duration": 2  # 持續2回合
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
    
    def __init__(self, scam_tactic: str = "假冒銀行", simple_mode: bool = False):
        # ... 現有代碼 ...
        self.strategy_phase = "trust_building"
        self.phase_round_count = 0
        self.tactics_used = []
        
    def _get_next_strategy_phase(self):
        """根據回合數自動進入下一個策略階段"""
        phases = list(self.STRATEGY_PHASES.keys())
        current_idx = phases.index(self.strategy_phase)
        if self.phase_round_count >= self.STRATEGY_PHASES[self.strategy_phase]["duration"]:
            if current_idx < len(phases) - 1:
                self.strategy_phase = phases[current_idx + 1]
                self.phase_round_count = 0
    
    def _apply_persona_adaptation(self, base_prompt: str, victim_persona: str) -> str:
        """根據受害者人格調整話術"""
        persona_adjustments = {
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
        # 根據 persona 調整 prompt
        return base_prompt
```

#### 2. backend/agents/expert.py - 完善專家代理

**需要添加的功能**:
```python
class ExpertAgent(BaseAntifraudAgent):
    INTERVENTION_STRATEGIES = {
        "elderly": {
            "priority": ["empathy", "clarity", "evidence", "actionability"],
            "opening": "婆婆唔使驚，我係黃sir，我幫你",
            "focus": "情緒安撫優先",
            "language_level": "簡單直接"
        },
        "average": {
            "priority": ["evidence", "clarity", "actionability", "empathy"],
            "opening": "根據我哋嘅記錄，呢個係典型嘅XX詐騙",
            "focus": "證據提供優先",
            "language_level": "專業理性"
        },
        "overconfident": {
            "priority": ["evidence", "clarity", "actionability", "empathy"],
            "opening": "你知唔知上個月有XX人中招？",
            "focus": "數據說話",
            "language_level": "事實為主"
        },
        "student": {
            "priority": ["clarity", "evidence", "actionability", "empathy"],
            "opening": "呢個係網上好常見嘅騙局",
            "focus": "同齡案例",
            "language_level": "年輕親切"
        }
    }
    
    def _select_intervention_strategy(self, victim_persona: str, scammer_message: str) -> str:
        """根據受害者類型和騙徒話術選擇介入策略"""
        strategy = self.INTERVENTION_STRATEGIES.get(victim_persona, self.INTERVENTION_STRATEGIES["average"])
        # 根據策略優先級生成回應
        return ""
    
    def _provide_concrete_advice(self, scam_type: str) -> str:
        """提供具體的防騙建議"""
        advice_map = {
            "假冒銀行": "立即掛線，打去銀行官方熱線 XXXX 核實",
            "假冒政府": "政府部門唔會要求你提供密碼，立即報警",
            "投資詐騙": "投資前查證公司係咪在證監會註冊",
            # ... 其他類型
        }
        return advice_map.get(scam_type, "立即停止對話，聯絡官方確認")
```

#### 3. backend/agents/victim.py - 完善受害者代理

**需要添加的功能**:
```python
class VictimAgent(BaseAntifraudAgent):
    EMOTIONAL_RESPONSES = {
        "neutral": {
            "keywords": ["係咪", "點解", "可能"],
            "trust_change": 0
        },
        "anxious": {
            "keywords": ["驚", "擔心", "點算", "嚴重"],
            "trust_change": 5  # 容易相信騙徒
        },
        "calm": {
            "keywords": ["冷靜", "慢慢嚟", "等等", "唔急"],
            "trust_change": -5  # 不容易相信騙徒
        },
        "suspicious": {
            "keywords": ["騙人", "唔信", "呃人", "假嘅"],
            "trust_change": -10
        },
        "panicked": {
            "keywords": ["點算好", "我好驚", "救命", "快啲"],
            "trust_change": 10  # 極度容易相信騙徒
        }
    }
    
    def _update_emotional_state(self, scammer_message: str, expert_message: str = None) -> str:
        """根據騙徒和專家的消息更新情緒狀態"""
        # 分析消息內容，更新情緒狀態
        pass
    
    def _generate_response_based_on_emotion(self, emotional_state: str) -> str:
        """根據情緒狀態生成自然的受害者反應"""
        # 根據情緒狀態生成回應
        pass
```

#### 4. backend/agents/recorder.py - 完善記錄員代理

**需要添加的功能**:
```python
class RecorderAgent(BaseAgent):
    def _analyze_scammer_performance(self, conversation_history: List[Dict]) -> Dict:
        """分析騙徒性能"""
        return {
            "persuasiveness": 0,  # 0-100
            "persuasiveness_analysis": "",  # 至少50字
            "credibility": 0,
            "credibility_analysis": "",
            "pressure_effectiveness": 0,
            "pressure_analysis": "",
            "strategy_consistency": 0,
            "strategy_analysis": "",
            "overall_score": 0,
            "key_successes": [],
            "key_failures": []
        }
    
    def _analyze_expert_performance(self, conversation_history: List[Dict]) -> Dict:
        """分析專家性能"""
        return {
            "intervention_effectiveness": 0,  # 0-100
            "intervention_analysis": "",
            "clarity": 0,
            "clarity_analysis": "",
            "empathy": 0,
            "empathy_analysis": "",
            "actionability": 0,
            "actionability_analysis": "",
            "timing": 0,
            "timing_analysis": "",
            "overall_score": 0,
            "key_successes": [],
            "key_failures": []
        }
    
    def _analyze_victim_trust_trajectory(self, conversation_history: List[Dict]) -> Dict:
        """分析受害者信任度軌跡"""
        return {
            "initial_trust_level": 0,
            "peak_trust_level": 0,
            "final_trust_level": 0,
            "trust_trajectory": "",
            "key_trust_changes": []
        }
```

---

### 第二階段：信任度系統完善

#### 5. backend/utils/performance_tracker.py - 驗證和完善

**需要驗證的功能**:
```python
# 確保以下方法正確實現：

def _calculate_inertia_multiplier(self, current_trust: int, change: int) -> float:
    """心理惯性乘数 - 已實現，需驗證"""
    pass

def _calculate_fatigue_multiplier(self, tactics: List[str], recent_tactics: List[List[str]]) -> float:
    """策略疲勞乘數 - 已實現，需驗證"""
    pass

def _calculate_emotional_multiplier(self, change: int, is_scammer: bool) -> float:
    """情緒狀態乘數 - 已實現，需驗證"""
    pass

def _calculate_persona_multiplier(self, tactic: str) -> float:
    """人格乘數 - 已實現，需驗證"""
    pass

def check_outcome(self, conversation_history: List[Dict]) -> Dict:
    """檢查遊戲結果 - 需完善"""
    # 實現以下邏輯：
    # 1. 騙徒贏：trust_in_scammer >= 80
    # 2. 專家贏：trust_in_expert >= 75 或 (trust_in_scammer < 40 AND trust_in_expert > 60)
    # 3. 自我保護：alertness >= 80
    # 4. 最大回合數檢查
    pass
```

#### 6. backend/utils/adaptive_scoring.py - 驗證和完善

**需要驗證的功能**:
```python
# 確保以下方法正確實現：

def get_expert_weights(self, persona: str) -> Dict[str, float]:
    """獲取專家評分權重 - 已實現，需驗證"""
    pass

def calculate_weighted_expert_score(self, base_scores: Dict[str, float], persona: str) -> float:
    """計算專家加權總分 - 已實現，需驗證"""
    pass

def apply_scammer_multiplier(self, base_change: float, tactic: str, persona: str) -> float:
    """應用騙徒策略乘數 - 已實現，需驗證"""
    pass

def analyze_persona_characteristics(self, persona: str) -> Dict[str, any]:
    """分析persona特徵 - 已實現，需驗證"""
    pass
```

---

### 第三階段：並行回應生成

#### 7. backend/api/game_routes_v2.py - 實現並行生成

**需要修改的端點**:
```python
@router.post("/action")
async def game_action(raw_request: Request):
    """
    處理遊戲動作 - 同時生成騙徒和專家的回應
    """
    body = await raw_request.body()
    data = json.loads(body)
    
    session_id = data.get("session_id")
    message = data.get("message")
    
    try:
        # 獲取會話信息
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="會話不存在")
        
        persona_type = result[0]
        
        # 使用 AgentService 生成響應
        service = get_agent_service(persona_type)
        
        # 🔥 **同時生成騙徒和專家的回應**
        scammer_task = service.generate_response(
            agent_type="scammer",
            message=message,
            session_id=session_id,
            check_consistency=True,
            track_performance=True
        )
        
        expert_task = service.generate_response(
            agent_type="expert",
            message=message,
            session_id=session_id,
            check_consistency=True,
            track_performance=True
        )
        
        # 並行執行
        scammer_result, expert_result = await asyncio.gather(
            scammer_task,
            expert_task,
            return_exceptions=True
        )
        
        # 處理結果
        scammer_reply = scammer_result["reply"] if isinstance(scammer_result, dict) else str(scammer_result)
        expert_reply = expert_result["reply"] if isinstance(expert_result, dict) else str(expert_result)
        
        # ... 保存對話和計算遊戲狀態 ...
        
        return {
            "success": True,
            "ai_responses": [
                {"role": "scammer", "content": scammer_reply},
                {"role": "expert", "content": expert_reply}
            ],
            "game_state": {
                "round_count": round_count,
                "player_score": 0,
                "ai_score": 0,
                "trust_in_scammer": trust_in_scammer,
                "trust_in_expert": trust_in_expert,
                "alertness": 100 - trust_in_scammer
            }
        }
    
    except Exception as e:
        from utils.logger import log
        log.error(f"❌ 遊戲動作處理失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 第四階段：會話持久化

#### 8. rpg-platform-v2/src/scenes/BattleScene.ts - 實現 sessionStorage

**需要添加的功能**:
```typescript
// 添加會話狀態管理
class BattleScene extends Phaser.Scene {
    private sessionState: any = null;
    
    create() {
        // 嘗試恢復狀態
        this.tryRestoreState();
        
        // ... 其他初始化代碼 ...
    }
    
    private tryRestoreState() {
        const saved = sessionStorage.getItem('battleState');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                // 只在 scamType 相同時恢復
                if (state.scamType === this.currentScamType) {
                    this.sessionState = state;
                    this.restoreFromState(state);
                    console.log('✅ 會話狀態已恢復');
                }
            } catch (e) {
                console.warn('⚠️ 恢復會話狀態失敗:', e);
            }
        }
    }
    
    private saveState() {
        const state = {
            session_id: this.currentSessionId,
            scamType: this.currentScamType,
            messages: this.chatMessages,
            trustData: {
                scammer: this.trustInScammer,
                expert: this.trustInExpert,
                alertness: this.alertness
            },
            round: this.roundCount
        };
        sessionStorage.setItem('battleState', JSON.stringify(state));
    }
    
    private restoreFromState(state: any) {
        this.currentSessionId = state.session_id;
        this.chatMessages = state.messages;
        this.trustInScammer = state.trustData.scammer;
        this.trustInExpert = state.trustData.expert;
        this.alertness = state.trustData.alertness;
        this.roundCount = state.round;
        
        // 重新渲染所有消息
        this.renderAllBubbles();
        this.updateTrustMeter();
    }
}
```

#### 9. backend/api/game_routes_v2.py - 驗證 SQLite 持久化

**需要驗證的表結構**:
```python
# 確保以下表結構正確：

# sessions 表
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    persona_type TEXT NOT NULL,
    scam_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    player_score INT DEFAULT 0,
    ai_score INT DEFAULT 0,
    outcome TEXT
);

# conversations 表
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trust_in_scammer INT,
    trust_in_expert INT,
    alertness INT,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);
```

---

### 第五階段：知識與評分系統

#### 10. backend/llms/rag_integration.py - 驗證 RAG 集成

**需要驗證的功能**:
```python
class GeminiRAGHelper:
    def get_rag_context(self, scam_type: str, context: str = None) -> str:
        """
        查詢 ChromaDB 獲取相關案例
        """
        # 1. 查詢 ChromaDB
        # 2. 檢索相關案例
        # 3. 格式化為提示詞
        # 4. 返回注入內容
        pass
```

#### 11. backend/utils/scammer_strategy_manager.py - 驗證策略管理

**需要驗證的功能**:
```python
class ScammerStrategyManager:
    def get_next_strategy(self) -> str:
        """
        根據已用策略和疲勞乘數，建議下一個策略
        """
        # 1. 計算每個策略的使用次數
        # 2. 計算疲勞乘數
        # 3. 返回最有效的未用或少用策略
        pass
    
    def record_tactic(self, tactic: str, effectiveness: float):
        """
        記錄策略使用和效果
        """
        pass
```

---

### 第六階段：API 端點

#### 12. backend/api/game_routes_v2.py - 完善 API 端點

**需要實現的端點**:
```python
# 1. 信任度 API
@router.post("/api/rpgv2/trust/update")
async def update_trust(session_id: str, trust_changes: Dict):
    """更新信任度"""
    pass

@router.get("/api/rpgv2/trust/{session_id}")
async def get_trust(session_id: str):
    """獲取信任度"""
    pass

# 2. 評分 API
@router.post("/api/rpgv2/score/calculate")
async def calculate_score(session_id: str):
    """計算評分"""
    pass

@router.get("/api/rpgv2/score/{session_id}")
async def get_score(session_id: str):
    """獲取評分"""
    pass
```

---

## 🔍 驗證清單

### 代碼質量檢查
- [ ] 所有函數都有文檔字符串
- [ ] 所有異常都被正確處理
- [ ] 所有日誌都使用 logger
- [ ] 所有配置都從 config.py 讀取
- [ ] 沒有硬編碼的魔法數字

### 功能驗證
- [ ] 四代理系統能正常生成回應
- [ ] 信任度系統能正確計算
- [ ] 並行生成能提升性能
- [ ] 會話持久化能正確保存和恢復
- [ ] RAG 能正確查詢和注入
- [ ] RecorderAgent 能生成有效的 JSON 分析

### 性能驗證
- [ ] 並行生成性能提升 ~50%
- [ ] RAG 查詢時間 < 1 秒
- [ ] 會話恢復時間 < 100ms
- [ ] API 響應時間 < 5 秒

---

## 📝 測試用例

### 單元測試
```python
# test_scammer_agent.py
def test_scammer_strategy_progression():
    """測試騙徒策略漸進性"""
    agent = ScammerAgent()
    # 驗證策略階段正確進行

def test_expert_persona_adaptation():
    """測試專家人格適應"""
    agent = ExpertAgent()
    # 驗證根據人格調整話術

def test_victim_emotional_state():
    """測試受害者情緒狀態"""
    agent = VictimAgent()
    # 驗證情緒狀態正確更新

def test_trust_calculation():
    """測試信任度計算"""
    tracker = PerformanceTracker()
    # 驗證信任度修改器正確應用

def test_parallel_generation():
    """測試並行生成"""
    # 驗證 asyncio.gather() 正確執行
    pass
```

### 集成測試
```python
# test_game_flow.py
def test_complete_game_flow():
    """測試完整遊戲流程"""
    # 1. 創建會話
    # 2. 發送消息
    # 3. 驗證回應
    # 4. 檢查信任度變化
    # 5. 驗證遊戲結束條件
    pass

def test_session_persistence():
    """測試會話持久化"""
    # 1. 創建會話
    # 2. 保存到 SQLite
    # 3. 恢復會話
    # 4. 驗證數據完整性
    pass

def test_recorder_analysis():
    """測試 RecorderAgent 分析"""
    # 1. 運行完整遊戲
    # 2. 調用 RecorderAgent
    # 3. 驗證 JSON 輸出
    # 4. 驗證評分合理性
    pass
```

---

## 🚀 部署檢查清單

- [ ] 所有依賴已安裝
- [ ] 環境變量已配置
- [ ] 數據庫已初始化
- [ ] ChromaDB 已加載 281 個案例
- [ ] Ollama 或 Gemini 已配置
- [ ] 所有測試通過
- [ ] 性能指標達到預期
- [ ] 文檔已更新
- [ ] 日誌系統正常工作

---

## 📞 常見問題

### Q: 如何測試並行生成的性能提升？
A: 使用 `time` 命令測試單個請求的響應時間，對比並行和順序執行的差異。

### Q: 如何驗證信任度計算的正確性？
A: 編寫單元測試，驗證各個修改器的應用和組合邏輯。

### Q: 如何確保 RecorderAgent 的分析質量？
A: 手動檢查幾個完整遊戲的分析結果，驗證評分和建議的合理性。

### Q: 如何優化 RAG 查詢性能？
A: 使用向量索引和緩存，減少重複查詢。

---

## 📚 參考資源

- `docs/CORE_FEATURES.md` - 核心功能詳細說明
- `docs/SECONDARY_FEATURES.md` - 支持功能詳細說明
- `docs/ARCHITECTURE.md` - 系統架構詳細說明
- `backend/config.py` - 配置參考
- `backend/utils/performance_tracker.py` - 信任度系統實現
- `backend/utils/adaptive_scoring.py` - 自適應評分系統實現

