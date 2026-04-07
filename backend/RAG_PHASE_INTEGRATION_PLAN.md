# RAG系統與Phase 2.1-2.3集成方案

## 📌 集成概述

RAG系統與Phase 2.1-2.3的關係：

```
RAG系統 (Firestore)
    ↓
生成更真實、多樣的對話內容
    ↓
LLM生成騙徒/專家/受害者回應
    ↓
Phase 2.1: 騙術分析 (分析對話內容)
    ↓
Phase 2.2: 勝負判定 (判定對話結果)
    ↓
Phase 2.3: 評分系統 (評分對話質量)
    ↓
對話評估 (使用RAG數據作為參考)
```

---

## 🎯 RAG系統的三個用途

### 1️⃣ 對話生成 (SessionManager)
```python
# 在SessionManager中初始化時
system_prompt = await rag_integration.get_scammer_system_prompt(scam_type)

# 發送到LLM
response = await llm_client.chat(
    system_prompt=system_prompt,  # ← 包含Firestore中的真實案例
    user_message=user_message
)
```

**作用**：
- 提升對話的真實性
- 增加對話的多樣性
- 讓AI生成更自然的回應

### 2️⃣ 對話分析 (Phase 2.1-2.2)
```python
# Phase 2.1: 騙術分析
tactic_result = await tactic_analyzer.analyze_scammer_message(
    message=response,  # ← 由RAG增強的LLM回應
    session_id=session_id
)

# Phase 2.2: 勝負判定
verdict_result = await verdict_judge.judge_scammer_win(
    message=response,  # ← 由RAG增強的LLM回應
    session_id=session_id
)
```

**作用**：
- 分析RAG增強後的對話內容
- 判定對話的勝負結果
- 不需要修改Phase 2.1和2.2的邏輯

### 3️⃣ 對話評估 (Phase 2.3後)
```python
# 對話結束後，用RAG數據評估質量
real_cases = await rag_provider.get_expert_context(scam_type)
warning_signs = await rag_provider.get_warning_signs(scam_type)

evaluation = {
    'realism_score': compare_with_real_cases(dialogue, real_cases),
    'authenticity': check_authenticity(dialogue, real_cases),
    'warning_signs_coverage': check_coverage(dialogue, warning_signs)
}
```

**作用**：
- 評估對話的真實性
- 評估對話的質量
- 提供改進建議

---

## 📁 集成文件清單

### 已創建的RAG文件
```
backend/services/
├── firestore_rag_fraud_loader.py          ✅ 核心RAG系統
├── session_manager_rag_integration.py     ✅ SessionManager集成
└── firestore_rag_service.py               ✅ 現有Firestore服務

backend/
├── FIRESTORE_RAG_GUIDE.md                 ✅ 使用指南
└── FIRESTORE_RAG_DELIVERY.md              ✅ 交付總結
```

### 現有的Phase文件
```
backend/services/
├── tactic_analyzer.py                     ✅ Phase 2.1
├── verdict_judge.py                       ✅ Phase 2.2
└── scam_scoring_v2.py                     ✅ Phase 2.3

backend/tests/
├── test_tactic_analyzer.py                ✅ Phase 2.1測試
├── test_verdict_judge.py                  ✅ Phase 2.2測試
└── test_scam_scoring_v2.py                ✅ Phase 2.3測試
```

---

## 🔄 完整的對話流程

### 步驟1: 初始化Session (使用RAG)
```python
class SessionManager:
    async def initialize_session(self, scam_type, player_role):
        # 1. 初始化RAG集成
        self.rag_integration = SessionManagerRAGIntegration()
        
        # 2. 獲取RAG增強的system prompt
        if player_role == "scammer":
            system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
        elif player_role == "expert":
            system_prompt = await self.rag_integration.get_expert_system_prompt(scam_type)
        else:
            system_prompt = await self.rag_integration.get_victim_system_prompt(scam_type)
        
        # 3. 初始化LLM
        self.llm_client.set_system_prompt(system_prompt)
        
        # 4. 初始化分析器 (Phase 2.1, 2.2, 2.3)
        self.tactic_analyzer = get_tactic_analyzer()
        self.verdict_judge = get_verdict_judge()
        self.scam_scorer = get_scam_scorer()
```

### 步驟2: 生成對話 (RAG增強)
```python
async def send_message(self, role, message):
    # 1. 發送到LLM (使用RAG增強的system prompt)
    response = await self.llm_client.chat(
        system_prompt=self.system_prompt,  # ← RAG數據在這裡
        user_message=message
    )
    
    # 2. 分析對話內容 (Phase 2.1)
    tactic_result = await self.tactic_analyzer.analyze_scammer_message(
        message=response,
        session_id=self.session_id
    )
    
    # 3. 判定勝負 (Phase 2.2)
    verdict_result = await self.verdict_judge.judge_scammer_win(
        message=response,
        session_id=self.session_id
    )
    
    # 4. 評分 (Phase 2.3)
    score_result = await self.scam_scorer.score_message(
        message=response,
        session_id=self.session_id
    )
    
    return {
        'response': response,
        'tactic_analysis': tactic_result,
        'verdict': verdict_result,
        'score': score_result
    }
```

### 步驟3: 對話評估 (使用RAG數據)
```python
async def evaluate_dialogue(self, scam_type):
    # 1. 獲取RAG數據
    real_cases = await self.rag_provider.get_expert_context(scam_type)
    warning_signs = await self.rag_provider.get_warning_signs(scam_type)
    prevention_tips = await self.rag_provider.get_prevention_tips(scam_type)
    
    # 2. 評估對話質量
    evaluation = {
        'realism_score': self._evaluate_realism(self.dialogue, real_cases),
        'authenticity': self._evaluate_authenticity(self.dialogue, real_cases),
        'warning_signs_coverage': self._evaluate_coverage(self.dialogue, warning_signs),
        'prevention_tips_coverage': self._evaluate_coverage(self.dialogue, prevention_tips)
    }
    
    return evaluation
```

---

## 💻 集成代碼示例

### 在SessionManager中集成RAG
```python
from services.session_manager_rag_integration import SessionManagerRAGIntegration
from services.tactic_analyzer import get_tactic_analyzer
from services.verdict_judge import get_verdict_judge
from services.scam_scoring_v2 import get_scam_scorer

class SessionManager:
    def __init__(self):
        self.rag_integration = SessionManagerRAGIntegration()
        self.tactic_analyzer = get_tactic_analyzer()
        self.verdict_judge = get_verdict_judge()
        self.scam_scorer = get_scam_scorer()
    
    async def initialize_session(self, scam_type, player_role):
        # 獲取RAG增強的system prompt
        if player_role == "scammer":
            self.system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
        elif player_role == "expert":
            self.system_prompt = await self.rag_integration.get_expert_system_prompt(scam_type)
        else:
            self.system_prompt = await self.rag_integration.get_victim_system_prompt(scam_type)
        
        self.scam_type = scam_type
        self.player_role = player_role
    
    async def send_message(self, message):
        # 1. 生成回應 (使用RAG增強的system prompt)
        response = await self.llm_client.chat(
            system_prompt=self.system_prompt,
            user_message=message
        )
        
        # 2. Phase 2.1: 騙術分析
        tactic_result = await self.tactic_analyzer.analyze_scammer_message(
            message=response,
            session_id=self.session_id
        )
        
        # 3. Phase 2.2: 勝負判定
        verdict_result = await self.verdict_judge.judge_scammer_win(
            message=response,
            session_id=self.session_id
        )
        
        # 4. Phase 2.3: 評分
        score_result = await self.scam_scorer.score_message(
            message=response,
            session_id=self.session_id
        )
        
        return {
            'response': response,
            'analysis': {
                'tactics': tactic_result,
                'verdict': verdict_result,
                'score': score_result
            }
        }
```

---

## 📊 數據流圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Firestore RAG數據                         │
│  (massive_generator.py + scraped_alerts.json)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │  FirestoreRAGPromptBuilder     │
        │  生成System Prompt              │
        └────────────┬───────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │  LLM (Gemini/Claude)           │
        │  生成對話內容                   │
        └────────────┬───────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ↓                         ↓
   ┌─────────────┐         ┌──────────────┐
   │ Phase 2.1   │         │ Phase 2.2    │
   │ 騙術分析    │         │ 勝負判定     │
   └──────┬──────┘         └──────┬───────┘
          │                       │
          └───────────┬───────────┘
                      ↓
              ┌──────────────────┐
              │ Phase 2.3        │
              │ 評分系統         │
              └────────┬─────────┘
                       │
                       ↓
        ┌──────────────────────────────┐
        │ 對話評估 (使用RAG數據)        │
        │ - 真實性評分                  │
        │ - 真實案例對比                │
        │ - 警告信號覆蓋率              │
        └──────────────────────────────┘
```

---

## ✅ 集成檢查清單

### 初始化階段
- [ ] 確保Firestore RAG數據已加載
  ```python
  loader = FirestoreRAGDataLoader()
  await loader.load_generator_data(...)
  await loader.load_adcc_data(...)
  ```

- [ ] SessionManager已導入RAG集成
  ```python
  from services.session_manager_rag_integration import SessionManagerRAGIntegration
  ```

### 對話生成階段
- [ ] SessionManager在initialize_session中使用RAG
  ```python
  system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
  ```

- [ ] LLM使用RAG增強的system prompt
  ```python
  response = await llm_client.chat(system_prompt=system_prompt, ...)
  ```

### 對話分析階段
- [ ] Phase 2.1正常分析RAG增強的對話
- [ ] Phase 2.2正常判定RAG增強的對話
- [ ] Phase 2.3正常評分RAG增強的對話

### 對話評估階段
- [ ] 對話結束後使用RAG數據評估
  ```python
  real_cases = await rag_provider.get_expert_context(scam_type)
  evaluation = compare_with_real_cases(dialogue, real_cases)
  ```

---

## 🚀 實施步驟

### Step 1: 加載RAG數據 (應用啟動時)
```python
# main.py 或 app.py
from services.firestore_rag_fraud_loader import FirestoreRAGDataLoader

async def startup():
    loader = FirestoreRAGDataLoader()
    await loader.load_generator_data("path/to/massive_generator.py")
    await loader.load_adcc_data("path/to/scraped_alerts.json")
    print("✅ RAG數據已加載到Firestore")
```

### Step 2: 在SessionManager中集成RAG
```python
# backend/services/session_manager.py
from services.session_manager_rag_integration import SessionManagerRAGIntegration

class SessionManager:
    def __init__(self):
        self.rag_integration = SessionManagerRAGIntegration()
        # ... 其他初始化 ...
    
    async def initialize_session(self, scam_type, player_role):
        # 獲取RAG增強的system prompt
        if player_role == "scammer":
            self.system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
        # ... 其他初始化 ...
```

### Step 3: 驗證集成
```bash
# 運行測試
pytest backend/tests/test_rag_integration.py -v
pytest backend/tests/test_tactic_analyzer.py -v
pytest backend/tests/test_verdict_judge.py -v
pytest backend/tests/test_scam_scoring_v2.py -v
```

### Step 4: 監控和優化
- 監控對話質量
- 監控RAG數據的使用情況
- 根據反饋優化prompt

---

## 📈 預期效果

### 對話質量提升
- ✅ 對話更真實
- ✅ 對話更多樣
- ✅ 對話更自然

### 系統穩定性
- ✅ Phase 2.1-2.3無需修改
- ✅ 現有邏輯保持不變
- ✅ 只是輸入數據質量提升

### 評估準確性
- ✅ 可以用真實案例評估
- ✅ 可以計算真實性評分
- ✅ 可以提供改進建議

---

## 📝 文檔參考

- **RAG使用指南**: `backend/FIRESTORE_RAG_GUIDE.md`
- **RAG交付總結**: `backend/FIRESTORE_RAG_DELIVERY.md`
- **Phase 2.1**: `backend/docs/PROGRESS_REPORT_Phase2.1.md`
- **Phase 2.2**: `backend/docs/PROGRESS_REPORT_Phase2.2.md`
- **Phase 2.3**: `backend/docs/PROGRESS_REPORT_Phase2.3.md`

---

## ✨ 總結

✅ **RAG系統的角色**：提升對話質量  
✅ **Phase 2.1-2.3的角色**：分析和評分對話  
✅ **集成方式**：RAG → LLM → Phase 2.1/2.2/2.3 → 評估  
✅ **無需修改**：Phase 2.1、2.2、2.3的邏輯保持不變  
✅ **只需集成**：在SessionManager中使用RAG增強的system prompt  

**系統已準備好集成！** 🚀

---

**版本**: 1.0.0  
**最後更新**: 2026年3月16日  
**狀態**: ✅ 完成


