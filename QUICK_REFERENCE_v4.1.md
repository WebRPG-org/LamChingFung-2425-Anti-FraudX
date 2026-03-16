# 🚀 AI 防詐平台 v4.1 - 快速參考指南

## 📌 核心改進一覽

### 1️⃣ ScammerAgent - 策略漸進性

```python
# 自動進入下一個策略階段
scammer._get_next_strategy_phase()

# 根據受害者人格調整話術
scammer._apply_persona_adaptation(base_prompt)
```

**三個策略階段**:
- `trust_building` - 建立信任（權威、同情、證據）
- `panic_creation` - 製造恐慌（恐懼、緊急、威脅）
- `action_urging` - 催促行動（緊急、壓力、期限）

**四種人格適應**:
- `elderly` - 溫柔耐心
- `average` - 專業理性
- `overconfident` - 挑戰激將
- `student` - 年輕親切

---

### 2️⃣ ExpertAgent - 四種人格策略

```python
# 選擇適合的介入策略
strategy = expert._select_intervention_strategy(scammer_message)

# 提供具體防騙建議
advice = expert._provide_concrete_advice(scam_type)
```

**四種介入策略**:
- `elderly` - 情緒安撫優先
- `average` - 證據提供優先
- `overconfident` - 數據說話
- `student` - 同齡案例

**具體建議**:
- 假冒銀行 → 打官方熱線 2860 5012
- 假冒政府 → 報警 999
- 投資詐騙 → 查證公司註冊
- 愛情詐騙 → 停止對話
- 求職詐騙 → 停止對話

---

### 3️⃣ VictimAgent - 情緒狀態追蹤

```python
# 根據消息更新情緒狀態
victim._update_emotional_state(scammer_message, expert_message)

# 根據情緒生成回應
response = victim._generate_response_based_on_emotion()
```

**五種情緒狀態**:
- `neutral` - 中立（信任度 ±0）
- `anxious` - 焦慮（信任度 +5）
- `calm` - 平靜（信任度 -5）
- `suspicious` - 懷疑（信任度 -10）
- `panicked` - 恐慌（信任度 +10）

**初始信任度**:
- elderly: 騙徒 70, 專家 50, 警覺 30
- average: 騙徒 50, 專家 60, 警覺 50
- overconfident: 騙徒 30, 專家 40, 警覺 70
- student: 騙徒 55, 專家 45, 警覺 45

---

### 4️⃣ RecorderAgent - 性能評分

```python
# 判定結果
outcome = recorder._determine_outcome(conversation_log, final_trust_level)

# 計算騙徒評分
scammer_score = recorder._calculate_scammer_score(metrics)

# 計算專家評分
expert_score = recorder._calculate_expert_score(metrics)

# 分析信任度軌跡
trust_analysis = recorder._analyze_trust_trajectory(trust_changes)

# 生成改進建議
suggestions = recorder._generate_improvement_suggestions(outcome, analysis)
```

**結果判定**:
- `SUCCESS` - 受害者成功拒絕
- `FAILURE` - 受害者被欺騙
- `PARTIAL` - 受害者猶豫

**騙徒評分維度** (0-100):
- persuasiveness（說服力）× 0.30
- credibility（可信度）× 0.25
- pressure_effectiveness（施壓效果）× 0.25
- strategy_consistency（策略一致性）× 0.20

**專家評分維度** (0-100):
- intervention_effectiveness（干預效果）× 0.30
- clarity（清晰度）× 0.20
- empathy（同理心）× 0.20
- actionability（可執行性）× 0.15
- timing（時機把握）× 0.15

---

### 5️⃣ AgentService - 並行生成

```python
# 並行生成所有回應
response = await service.generate_parallel_responses(
    victim_message="我唔知點算好",
    session_id=session_id,
    mode="full"  # full, expert_only, scammer_only
)

# 結果包含
{
    "scammer_response": {...},
    "expert_response": {...},
    "victim_response": {...},
    "execution_time_ms": 123
}
```

**三種模式**:
- `full` - 生成騙徒、專家、受害者三個回應
- `expert_only` - 只生成專家回應
- `scammer_only` - 只生成騙徒回應

**性能提升**: 比順序執行快 50-70%

---

## 🎯 使用流程

### 步驟 1: 初始化服務

```python
from services.agent_service import AgentService

service = AgentService(
    persona_type="elderly",  # elderly, average, overconfident, student
    scam_type="banking",     # 騙案類型
    enable_tracking=True     # 啟用性能追蹤
)
```

### 步驟 2: 創建 Session

```python
session_id = service.create_session()
# 或使用自定義 ID
session_id = service.create_session("my_session_123")
```

### 步驟 3: 生成回應

#### 方式 A: 單個回應

```python
response = await service.generate_response(
    agent_type="scammer",
    message="你好，我係銀行職員",
    session_id=session_id
)

print(response["reply"])  # 騙徒的回應
print(response["trust_in_scammer"])  # 對騙徒的信任度
```

#### 方式 B: 並行回應

```python
parallel = await service.generate_parallel_responses(
    victim_message="我唔知點算好",
    session_id=session_id,
    mode="full"
)

print(parallel["scammer_response"]["reply"])
print(parallel["expert_response"]["reply"])
print(parallel["victim_response"]["reply"])
print(f"耗時: {parallel['execution_time_ms']}ms")
```

### 步驟 4: 獲取統計信息

```python
# 獲取對話歷史
history = service.get_session_history(session_id)

# 獲取統計信息
stats = service.get_session_stats(session_id)
print(stats["turn_count"])  # 對話輪數
print(stats["trust_in_scammer"])  # 對騙徒的信任度
print(stats["trust_in_expert"])  # 對專家的信任度
```

### 步驟 5: 生成最終分析

```python
analysis = await service.generate_final_analysis(
    conversation_history=history,
    outcome_description="受害者被成功欺騙"
)

print(analysis["outcome"])  # SUCCESS, FAILURE, PARTIAL
print(analysis["scammer_performance"]["overall_score"])  # 騙徒評分
print(analysis["expert_performance"]["overall_score"])  # 專家評分
print(analysis["improvement_suggestion"])  # 改進建議
```

---

## 📊 數據結構

### Session 對象

```python
session = service.get_session(session_id)

# 屬性
session.session_id  # Session ID
session.persona_type  # 受害者人格類型
session.created_at  # 創建時間
session.conversation_history  # 對話歷史
session.trust_in_scammer  # 對騙徒的信任度 (0-100)
session.trust_in_expert  # 對專家的信任度 (0-100)
session.turn_count  # 對話輪數

# 方法
session.add_message(role, content)  # 添加消息
session.get_history(limit=10)  # 獲取對話歷史
session.get_context_for_agent(agent_type, limit=10)  # 獲取上下文
```

### 回應對象

```python
response = await service.generate_response(...)

# 結構
{
    "reply": "騙徒的回應",
    "agent": "scammer",
    "session_id": "session_xxx",
    "turn": 1,
    "metrics": {...},  # 性能指標
    "trust_in_scammer": 70,
    "trust_in_expert": 50
}
```

### 分析對象

```python
analysis = await service.generate_final_analysis(...)

# 結構
{
    "outcome": "SUCCESS|FAILURE|PARTIAL",
    "victim_persona": "elderly|average|overconfident|student",
    "scammer_performance": {
        "persuasiveness": 75,
        "credibility": 80,
        "pressure_effectiveness": 70,
        "strategy_consistency": 85,
        "overall_score": 78,
        "key_successes": [...],
        "key_failures": [...]
    },
    "expert_performance": {
        "intervention_effectiveness": 60,
        "clarity": 70,
        "empathy": 65,
        "actionability": 55,
        "timing": 50,
        "overall_score": 60,
        "key_successes": [...],
        "key_failures": [...]
    },
    "victim_trust_analysis": {
        "initial_trust_level": 70,
        "peak_trust_level": 95,
        "final_trust_level": 30,
        "trust_trajectory": "...",
        "key_trust_changes": [...]
    },
    "scam_tactic": "詳細描述",
    "key_moment": "轉折點分析",
    "failure_reason": "失敗原因分析",
    "improvement_suggestion": "改進建議"
}
```

---

## 🔍 常見場景

### 場景 1: 長者被騙

```python
service = AgentService(persona_type="elderly", scam_type="banking")
session_id = service.create_session()

# 騙徒開場
scammer_msg = await service.generate_response("scammer", "你好婆婆，我係銀行職員", session_id)
print(scammer_msg["reply"])

# 受害者反應
victim_msg = await service.generate_response("victim", scammer_msg["reply"], session_id)
print(victim_msg["reply"])

# 專家介入
expert_msg = await service.generate_response("expert", victim_msg["reply"], session_id)
print(expert_msg["reply"])

# 檢查信任度
print(f"對騙徒信任度: {victim_msg['trust_in_scammer']}")
print(f"對專家信任度: {victim_msg['trust_in_expert']}")
```

### 場景 2: 並行生成對比

```python
# 順序生成（慢）
start = time.time()
scammer = await service.generate_response("scammer", msg, session_id)
expert = await service.generate_response("expert", msg, session_id)
victim = await service.generate_response("victim", msg, session_id)
sequential_time = time.time() - start

# 並行生成（快）
start = time.time()
parallel = await service.generate_parallel_responses(msg, session_id, "full")
parallel_time = time.time() - start

print(f"順序執行: {sequential_time:.2f}s")
print(f"並行執行: {parallel_time:.2f}s")
print(f"性能提升: {(sequential_time/parallel_time - 1)*100:.1f}%")
```

### 場景 3: 性能分析

```python
# 完整對話後
history = service.get_session_history(session_id)
analysis = await service.generate_final_analysis(history)

# 騙徒表現
if analysis["scammer_performance"]["overall_score"] > 80:
    print("騙徒表現優秀")
else:
    print("騙徒表現一般")

# 專家表現
if analysis["expert_performance"]["overall_score"] > 70:
    print("專家干預有效")
else:
    print("專家干預無效，需要改進")

# 改進建議
print(analysis["improvement_suggestion"])
```

---

## ⚙️ 配置參數

### AgentService 初始化參數

```python
AgentService(
    persona_type="average",      # 受害者人格類型
    enable_tracking=True,        # 啟用性能追蹤
    scam_type="假冒銀行"         # 騙案類型
)
```

### generate_response 參數

```python
await service.generate_response(
    agent_type="scammer",        # Agent 類型
    message="...",               # 消息內容
    session_id=None,             # Session ID（可選）
    check_consistency=True,      # 檢查角色一致性
    track_performance=True       # 追蹤性能
)
```

### generate_parallel_responses 參數

```python
await service.generate_parallel_responses(
    victim_message="...",        # 受害者消息
    session_id=None,             # Session ID（可選）
    mode="full"                  # 生成模式：full, expert_only, scammer_only
)
```

---

## 🐛 調試技巧

### 1. 查看日誌

```python
from utils.logger import log

# 所有操作都會記錄日誌
log.info("自定義日誌")
log.warning("警告")
log.error("錯誤")
```

### 2. 檢查 Session 狀態

```python
session = service.get_session(session_id)
print(f"對話輪數: {session.turn_count}")
print(f"對話數量: {len(session.conversation_history)}")
print(f"對騙徒信任度: {session.trust_in_scammer}")
print(f"對專家信任度: {session.trust_in_expert}")
```

### 3. 查看完整對話歷史

```python
history = service.get_session_history(session_id)
for msg in history:
    print(f"{msg['role']}: {msg['content']}")
```

### 4. 性能分析

```python
import time

start = time.time()
response = await service.generate_response(...)
elapsed = time.time() - start

print(f"生成時間: {elapsed:.2f}s")
print(f"回應長度: {len(response['reply'])} 字")
```

---

## 📚 相關文檔

- `IMPLEMENTATION_COMPLETE_v4.1.md` - 完整實施報告
- `IMPLEMENTATION_GUIDE_v4.1.md` - 詳細實施指南
- `CODE_IMPLEMENTATION_CHECKLIST.md` - 代碼實施清單
- `QUICK_START_GUIDE.md` - 快速開始指南

---

**版本**: 4.1.0  
**最後更新**: 2025-03-16

