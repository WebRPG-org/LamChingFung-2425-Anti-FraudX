# Recorder 統一評分系統設計方案

## 🎯 核心理念

**「Recorder 兼任評分分析師」**

讓 RecorderAgent 不僅記錄對話，還負責所有的性能評分和分析。這樣可以：
- ✅ 評分更準確（基於完整對話上下文）
- ✅ 評分更一致（由單一 AI 判斷）
- ✅ 簡化模擬邏輯（模擬時只記錄，不評分）
- ✅ 更靈活的評分維度（Recorder 可以分析任何維度）

---

## 📐 架構設計

### 當前架構（問題）

```
模擬過程中：
  每輪對話後 → PerformanceTracker.analyze_*_turn()
    → 即時計算評分（基於關鍵詞匹配）
    → 更新累積評分
    → 記錄在 tracker.scammer_perf / expert_perf

問題：
  ❌ 評分邏輯簡單（只基於關鍵詞）
  ❌ 無法考慮完整上下文
  ❌ 評分分散在多個地方
  ❌ 難以調整評分標準
```

### 新架構（Recorder 統一評分）

```
模擬過程中：
  每輪對話 → 只記錄對話內容
           → 簡單追蹤信任度變化
           → 不做詳細評分

模擬結束後：
  RecorderAgent.analyze_complete_simulation()
    → 閱讀完整對話歷史
    → 分析每輪的策略和效果
    → 為騙徒和專家打分
    → 識別關鍵時刻
    → 提供改進建議
    
輸出JSON包含：
  {
    "scammer_performance": {
      "persuasiveness": 75/100,
      "credibility": 80/100,
      "pressure_effectiveness": 70/100,
      "strategy_consistency": 85/100,
      "overall_score": 78/100,
      "turn_by_turn_analysis": [...]
    },
    "expert_performance": {
      "intervention_effectiveness": 60/100,
      "clarity": 70/100,
      "empathy": 65/100,
      "actionability": 55/100,
      "timing": 50/100,
      "overall_score": 60/100,
      "turn_by_turn_analysis": [...]
    },
    ...
  }
```

---

## 📊 Recorder 評分維度

### 騙徒評分（ScammerPerformance）

#### 1. 說服力（Persuasiveness）0-100

**評分標準**:
- **0-20分**: 話術生硬，邏輯漏洞明顯，受害者立刻懷疑
- **21-40分**: 話術基本，有一定說服力但容易被質疑
- **41-60分**: 話術流暢，能夠回應受害者的疑問
- **61-80分**: 話術高明，成功打消大部分疑慮
- **81-100分**: 話術極具說服力，受害者完全相信

**分析要點**:
- 話術的流暢度和專業性
- 是否成功回應受害者的疑問
- 是否成功打消受害者的顧慮
- 受害者的信任度變化趨勢

#### 2. 可信度（Credibility）0-100

**評分標準**:
- **角色一致性**: 是否保持專業銀行職員/政府官員的形象
- **細節真實性**: 提供的信息（如帳號、流程）是否看起來真實
- **專業術語**: 是否使用了適當的專業術語
- **避免破綻**: 是否避免了明顯的邏輯漏洞

**分析要點**:
- 是否有破綻或被專家揭穿
- 受害者是否對身份產生懷疑
- 是否成功模仿權威機構的語氣

#### 3. 施壓效果（Pressure Effectiveness）0-100

**評分標準**:
- **時間壓力**: 是否成功製造「立即處理」的緊迫感
- **後果威脅**: 是否成功製造「不處理會很嚴重」的恐懼
- **情緒操控**: 是否成功讓受害者進入恐慌/焦慮/貪婪狀態
- **行動催促**: 是否成功催促受害者採取行動

**分析要點**:
- 受害者的情緒變化（焦慮、恐慌、急躁）
- 受害者是否表現出「我需要立即行動」的態度
- 施壓是否過度（導致受害者反感或求助）

#### 4. 策略一致性（Strategy Consistency）0-100

**評分標準**:
- **策略連貫**: 從頭到尾使用一致的策略（authority/urgency/benefits等）
- **角色不破功**: 沒有說出破壞角色設定的話（如「我係騙徒」、「點解要」等）
- **應對靈活**: 面對專家挑戰時能夠靈活應對，不破功

**分析要點**:
- 是否有破壞角色的語句
- 策略是否前後矛盾
- 面對挑戰時的應對是否合理

#### 5. 總體得分（Overall Score）0-100

**計算方式**:
```
overall_score = (
    persuasiveness * 0.3 +
    credibility * 0.25 +
    pressure_effectiveness * 0.25 +
    strategy_consistency * 0.20
)

調整因素:
  + 成功操控次數 * 5
  - 被識破次數 * 10
  - 角色破功次數 * 15
```

---

### 專家評分（ExpertPerformance）

#### 1. 干預效果（Intervention Effectiveness）0-100

**評分標準**:
- **0-20分**: 干預無效，受害者完全忽視
- **21-40分**: 干預引起注意但未改變決定
- **41-60分**: 干預讓受害者猶豫，但未完全阻止
- **61-80分**: 干預成功降低信任度，受害者開始懷疑
- **81-100分**: 干預非常成功，受害者立即停止並採取防範措施

**分析要點**:
- 專家介入後受害者的信任度變化
- 受害者是否接受專家的建議
- 是否成功阻止受害者採取危險行動

#### 2. 清晰度（Clarity）0-100

**評分標準**:
- **語言簡潔**: 是否使用受害者能理解的語言（避免術語）
- **邏輯清晰**: 是否有清晰的論證邏輯
- **證據具體**: 是否提供具體的證據和例子
- **指令明確**: 是否提供明確可執行的步驟

**分析要點**:
- 受害者是否理解專家的說法
- 是否有「我唔明」「你講咩」等表示不理解的回應
- 建議是否具體可執行

#### 3. 同理心（Empathy）0-100

**評分標準**:
- **情緒安撫**: 是否安撫受害者的恐慌/焦慮情緒
- **理解表達**: 是否表達「我理解你的擔心」
- **語氣溫和**: 是否使用溫和、支持性的語氣
- **避免指責**: 是否避免「你點解咁蠢」等指責性語言

**分析要點**:
- 對 elderly 型受害者尤其重要
- 是否讓受害者感到被支持
- 是否建立了信任關係

#### 4. 可執行性（Actionability）0-100

**評分標準**:
- **具體步驟**: 是否提供具體的行動步驟（如「打去XX熱線」）
- **優先順序**: 是否明確指出「立即做什麼」
- **可行性**: 建議是否現實可行（不是「報警」這種太泛的建議）
- **資源提供**: 是否提供具體資源（電話號碼、網址等）

**分析要點**:
- 受害者是否採取了專家建議的行動
- 建議是否具體到可以立即執行
- 是否提供了必要的資源

#### 5. 時機把握（Timing）0-100

**評分標準**:
- **介入時機**: 是否在最佳時機介入（不太早也不太晚）
- **太早**: 受害者還沒意識到危險，覺得專家多管閒事
- **剛好**: 受害者開始有疑慮，正需要幫助
- **太晚**: 受害者已經完全相信騙徒，很難扭轉

**分析要點**:
- 介入時受害者對騙徒的信任度
- 介入後的效果（信任度變化）
- 是否錯過了最佳介入時機

#### 6. 總體得分（Overall Score）0-100

**計算方式**:
```
overall_score = (
    intervention_effectiveness * 0.30 +
    clarity * 0.20 +
    empathy * 0.20 +
    actionability * 0.15 +
    timing * 0.15
)

調整因素:
  + 成功警告次數 * 5
  - 警告被忽視次數 * 3
  + 成功阻止危險行動 * 10
```

---

## 🔄 實施方案

### 階段 1: 更新 Recorder Instruction

#### 新增評分維度到 Recorder 指令中

```python
# backend/agents/recorder.py

instruction = """
# ... 現有指令 ...

## 性能評分職責（新增）

除了記錄和分析對話，你還需要為騙徒和專家進行專業的性能評分。

### 騙徒性能評分（Scammer Performance）

請從以下維度評分（0-100）：

1. **persuasiveness（說服力）**: 
   - 評估：話術流暢度、邏輯嚴密性、說服力強度
   - 0-20: 話術生硬，立刻被懷疑
   - 21-40: 話術基本，容易被質疑
   - 41-60: 話術流暢，能回應疑問
   - 61-80: 話術高明，打消大部分疑慮
   - 81-100: 話術極具說服力，完全被信任

2. **credibility（可信度）**:
   - 評估：角色一致性、細節真實性、專業術語使用
   - 是否有破綻或被揭穿？
   - 是否成功模仿權威機構？

3. **pressure_effectiveness（施壓效果）**:
   - 評估：時間壓力、後果威脅、情緒操控、行動催促
   - 受害者是否進入恐慌/焦慮/急躁狀態？
   - 是否成功催促行動？

4. **strategy_consistency（策略一致性）**:
   - 評估：策略連貫性、角色是否破功、應對靈活性
   - 是否有破壞角色的語句（如「我係騙徒」、「點解要」）？
   - 面對挑戰時是否合理應對？

5. **overall_score（總體得分）**:
   - 綜合計算：persuasiveness×0.3 + credibility×0.25 + pressure_effectiveness×0.25 + strategy_consistency×0.20
   - 調整：+成功操控×5，-被識破×10，-角色破功×15

### 專家性能評分（Expert Performance）

請從以下維度評分（0-100）：

1. **intervention_effectiveness（干預效果）**:
   - 評估：干預後信任度變化、受害者是否接受建議、是否阻止危險行動
   - 0-20: 完全無效
   - 21-40: 引起注意但未改變決定
   - 41-60: 讓受害者猶豫
   - 61-80: 成功降低信任度
   - 81-100: 非常成功，立即停止並防範

2. **clarity（清晰度）**:
   - 評估：語言簡潔性、邏輯清晰度、證據具體性、指令明確性
   - 受害者是否理解？
   - 建議是否具體可執行？

3. **empathy（同理心）**:
   - 評估：情緒安撫、理解表達、語氣溫和、避免指責
   - 對elderly型特別重要
   - 是否讓受害者感到被支持？

4. **actionability（可執行性）**:
   - 評估：具體步驟、優先順序、可行性、資源提供
   - 是否提供具體行動步驟（如電話號碼）？
   - 建議是否現實可行？

5. **timing（時機把握）**:
   - 評估：介入時機是否合適（不太早也不太晚）
   - 太早：受害者覺得多管閒事
   - 剛好：受害者正需要幫助
   - 太晚：已經完全相信騙徒

6. **overall_score（總體得分）**:
   - 綜合計算：intervention_effectiveness×0.30 + clarity×0.20 + empathy×0.20 + actionability×0.15 + timing×0.15
   - 調整：+成功警告×5，-被忽視×3，+阻止危險行動×10

### 逐輪分析（Turn-by-Turn Analysis）

對於每一輪對話，請提供：
```json
{
  "round": 1,
  "speaker": "騙徒",
  "dialogue": "...",
  "strategy_used": ["authority", "urgency"],
  "effectiveness": "high",
  "trust_impact": +30,
  "analysis": "騙徒在此輪使用權威和緊迫策略，成功製造恐慌..."
}
```

## 輸出格式（更新）

```json
{
  "outcome": "SUCCESS" | "FAILURE" | "PARTIAL",
  "victim_persona": "elderly" | "average" | "overconfident",
  
  "scammer_performance": {
    "persuasiveness": 75,
    "persuasiveness_analysis": "騙徒的話術流暢且專業，成功模仿銀行職員的語氣...",
    "credibility": 80,
    "credibility_analysis": "騙徒保持角色一致性，沒有明顯破綻...",
    "pressure_effectiveness": 70,
    "pressure_analysis": "成功製造時間壓力，但施壓過度導致部分反感...",
    "strategy_consistency": 85,
    "strategy_analysis": "策略一致，從頭到尾使用authority+urgency組合...",
    "overall_score": 78,
    "key_successes": ["第2輪成功製造恐慌", "第4輪成功打消疑慮"],
    "key_failures": ["第6輪被專家揭穿部分漏洞"],
    "turn_by_turn": [
      {
        "round": 1,
        "strategy": ["authority"],
        "effectiveness": "medium",
        "trust_impact": +20,
        "analysis": "..."
      }
    ]
  },
  
  "expert_performance": {
    "intervention_effectiveness": 60,
    "intervention_analysis": "專家的介入引起了受害者注意，但未完全阻止...",
    "clarity": 70,
    "clarity_analysis": "語言清晰，提供了具體證據，但部分術語對elderly型較難理解...",
    "empathy": 65,
    "empathy_analysis": "有嘗試安撫情緒，但不夠充分...",
    "actionability": 55,
    "actionability_analysis": "提供了建議但不夠具體，缺少可執行的步驟...",
    "timing": 50,
    "timing_analysis": "介入時機略晚，受害者對騙徒的信任度已達80/100...",
    "overall_score": 60,
    "key_successes": ["第3輪成功揭穿騙徒部分謊言"],
    "key_failures": ["介入時機太晚", "缺少情緒安撫"],
    "turn_by_turn": [
      {
        "round": 2,
        "approach": ["evidence", "actionable"],
        "effectiveness": "medium",
        "trust_impact": +15,
        "analysis": "..."
      }
    ]
  },
  
  "victim_trust_analysis": {
    "initial_trust_level": 70,
    "peak_trust_level": 95,
    "final_trust_level": 30,
    "trust_trajectory": "...",
    "key_trust_changes": [
      {
        "round": 2,
        "from": 70,
        "to": 95,
        "trigger": "騙徒製造恐慌",
        "analysis": "..."
      }
    ]
  },
  
  "scam_tactic": "...",
  "key_moment": "...",
  "failure_reason": "...",  // 僅 FAILURE 時
  "success_reason": "...",  // 僅 SUCCESS 時
  "improvement_suggestion": "...",
  "full_conversation_log": [...]
}
```

**評分原則**：
1. 基於完整對話上下文，不只看關鍵詞
2. 考慮受害者類型的差異（elderly需要更多安撫，average需要更多證據）
3. 評分要有理有據，附帶具體分析
4. 指出具體的成功和失敗之處，便於改進
"""
```

---

### 階段 2: 簡化 PerformanceTracker

#### 現有功能保留
- ✅ 信任度追蹤（`VictimTrustState`）
- ✅ 關鍵時刻記錄（`key_moments`）
- ✅ 基本統計（輪次計數等）

#### 移除功能
- ❌ `ScammerPerformance` 詳細評分
- ❌ `ExpertPerformance` 詳細評分
- ❌ `analyze_scammer_turn()` 複雜分析
- ❌ `analyze_expert_turn()` 複雜分析

#### 簡化後的 PerformanceTracker

```python
class PerformanceTracker:
    """簡化版性能追蹤器 - 只追蹤基本信息，詳細評分由 Recorder 負責"""
    
    def __init__(self):
        self.victim_trust = VictimTrustState()
        self.turn_count = 0
        self.key_moments = []
        self.conversation_log = []  # 簡單記錄對話
    
    def record_turn(self, speaker: str, dialogue: str, trust_change: Optional[int] = None):
        """簡單記錄每輪對話"""
        self.turn_count += 1
        self.conversation_log.append({
            "round": self.turn_count,
            "speaker": speaker,
            "dialogue": dialogue,
            "trust_in_scammer": self.victim_trust.trust_in_scammer,
            "trust_in_expert": self.victim_trust.trust_in_expert,
            "timestamp": datetime.now().isoformat()
        })
        
        if trust_change:
            self.victim_trust.update(speaker.lower(), trust_change, f"{speaker}發言")
    
    def add_key_moment(self, description: str):
        """記錄關鍵時刻"""
        self.key_moments.append({
            "round": self.turn_count,
            "description": description,
            "trust_state": {
                "scammer": self.victim_trust.trust_in_scammer,
                "expert": self.victim_trust.trust_in_expert
            }
        })
    
    def get_current_state(self) -> Dict:
        """獲取當前狀態"""
        return {
            "turn_count": self.turn_count,
            "trust_in_scammer": self.victim_trust.trust_in_scammer,
            "trust_in_expert": self.victim_trust.trust_in_expert,
            "alertness": self.victim_trust.alertness,
            "emotional_state": self.victim_trust.emotional_state
        }
```

---

### 階段 3: 更新模擬流程

#### simulation_routes.py 修改

```python
# 每輪對話後：只記錄，不評分
tracker.record_turn("騙徒", scammer_turn)
tracker.record_turn("受害者", victim_turn)
tracker.record_turn("專家", expert_turn)

# 簡化的日誌輸出
log.info(f"📊 [第{tracker.turn_count}輪] 信任度 - 騙徒: {tracker.victim_trust.trust_in_scammer}/100, 專家: {tracker.victim_trust.trust_in_expert}/100")

# 模擬結束後：調用 Recorder 進行完整分析
analysis = await _generate_recorder_analysis(
    runner=runner,
    conversation_history=tracker.conversation_log,  # 傳遞完整對話記錄
    simulation_id=simulation_id,
    victim_persona=victim_persona,
    scam_tactic=scam_tactic,
    outcome_type=outcome_type,
    outcome_description=outcome_description,
    tracker=tracker
)

# analysis 中包含完整的評分
scammer_score = analysis["scammer_performance"]["overall_score"]
expert_score = analysis["expert_performance"]["overall_score"]

log.info(f"📊 [最終評分] 騙徒: {scammer_score}/100, 專家: {expert_score}/100")
```

---

## 📈 優勢分析

### 相比當前系統的改進

| 方面 | 當前系統 | Recorder 統一評分 |
|-----|---------|------------------|
| **評分準確性** | 🟡 基於關鍵詞匹配 | 🟢 基於完整上下文理解 |
| **評分一致性** | 🟡 分散在多個函數 | 🟢 由單一 AI 判斷 |
| **評分靈活性** | 🔴 難以調整標準 | 🟢 修改 instruction 即可 |
| **代碼複雜度** | 🟡 多個分析函數 | 🟢 邏輯集中在 Recorder |
| **即時反饋** | 🟢 每輪都有評分 | 🟡 結束後才有完整評分 |
| **評分深度** | 🟡 只有數值 | 🟢 數值 + 詳細分析 |
| **可解釋性** | 🔴 不知道為何得分 | 🟢 附帶詳細分析文字 |

### 實際效果對比

#### 當前系統輸出

```
📊 [騙徒][第4輪] 使用策略: [urgency] 共1項, 信任變化: +10, 效果: ⏳進行中 | 累積評分 - 說服力: 58/100, 可信度: 65/100
```

**問題**:
- ❌ 為什麼說服力是 58？沒有解釋
- ❌ 基於簡單關鍵詞匹配，不準確
- ❌ 無法考慮上下文（如之前的對話）

#### Recorder 評分輸出

```json
{
  "scammer_performance": {
    "persuasiveness": 75,
    "persuasiveness_analysis": "騙徒在整場對話中展現出專業且流暢的話術。特別是在第2輪，當受害者質疑身份時，騙徒用『我可以提供工作編號XXX』來打消疑慮，這個細節非常真實。在第4輪使用的『你帳戶會被凍結』威脅，成功觸發了elderly型受害者對財務損失的恐懼。唯一的小瑕疵是在第5輪對專家的反駁略顯生硬，沒有完全打消受害者的疑慮（信任度從95下降到85）。整體說服力評分75/100。",
    
    "credibility": 80,
    "credibility_analysis": "騙徒成功保持了銀行職員的角色一致性，使用了大量專業術語如『反洗黑錢條例』『帳戶凍結流程』。提供的細節（如工作編號、部門名稱）增強了可信度。沒有出現破壞角色的語句。唯一的破綻是在第6輪，專家指出『銀行不會要求你提供密碼』時，騙徒的回應有些迴避，導致可信度略有下降。整體可信度評分80/100。",
    
    "overall_score": 78,
    
    "key_successes": [
      "第2輪：成功打消身份疑慮（提供工作編號）",
      "第4輪：成功製造恐慌（財務損失威脅）",
      "第7輪：靈活應對專家挑戰（製造對立）"
    ],
    
    "key_failures": [
      "第5輪：對專家反駁略顯生硬",
      "第6輪：面對密碼質疑時回應迴避"
    ]
  }
}
```

**優勢**:
- ✅ 評分有詳細解釋
- ✅ 基於完整對話上下文
- ✅ 指出具體成功和失敗之處
- ✅ 便於理解和改進

---

## 🔄 遷移步驟

### 步驟 1: 更新 RecorderAgent（最重要）

```bash
# 文件: backend/agents/recorder.py
# 添加性能評分維度到 instruction
```

### 步驟 2: 創建簡化版 PerformanceTracker

```bash
# 文件: backend/utils/performance_tracker_simple.py
# 創建簡化版，只追蹤基本信息
```

### 步驟 3: 更新 simulation_routes.py

```bash
# 移除即時評分邏輯
# 改為模擬結束後調用 Recorder
```

### 步驟 4: 更新日誌輸出

```bash
# 簡化即時日誌（只顯示信任度）
# 最終日誌顯示 Recorder 的評分
```

### 步驟 5: 測試驗證

```bash
# 運行測試模擬
# 檢查 Recorder 輸出的評分是否合理
# 對比舊系統的評分，驗證準確性
```

---

## 🎯 實施優先級

### 優先級 1（核心功能）✅ 立即實施

- [x] 更新 RecorderAgent instruction，添加評分維度
- [x] 修改 `_generate_recorder_analysis` 確保返回評分
- [x] 簡化模擬過程中的即時評分邏輯

### 優先級 2（優化體驗）⏳ 近期實施

- [ ] 創建簡化版 PerformanceTracker
- [ ] 更新所有模擬路由使用新系統
- [ ] 更新日誌輸出格式

### 優先級 3（長期優化）📅 未來考慮

- [ ] 添加 Recorder 評分的可視化展示
- [ ] 提供評分趨勢分析（多次模擬對比）
- [ ] 基於 Recorder 評分優化 Fine-Tuning

---

## 💡 後續優化方向

### 1. 評分校準（Calibration）

定期檢查 Recorder 的評分是否合理：
```python
# 收集多次模擬的評分
# 分析評分分佈
# 調整評分標準（修改 instruction）
```

### 2. 多維度可視化

創建評分雷達圖：
```python
import matplotlib.pyplot as plt

scores = {
    "說服力": 75,
    "可信度": 80,
    "施壓效果": 70,
    "策略一致性": 85
}

# 生成雷達圖
```

### 3. 評分對比系統

對比不同策略的效果：
```python
# 策略A（authority + urgency）
scammer_score_A = 78

# 策略B（benefits + empathy）
scammer_score_B = 65

# 分析哪種策略更有效
```

---

## 🎉 總結

### 核心改變

**從「即時評分」到「事後分析」**

- ✅ 更準確：基於完整上下文
- ✅ 更一致：單一 AI 判斷
- ✅ 更靈活：調整 instruction 即可
- ✅ 更可解釋：附帶詳細分析

### 預期效果

1. **評分質量提升**: 從關鍵詞匹配 → AI 理解上下文
2. **代碼簡化**: 移除複雜的即時評分邏輯
3. **可維護性提高**: 評分邏輯集中在 Recorder instruction
4. **可解釋性增強**: 每個評分都有詳細分析

---

**設計版本**: v1.0  
**創建時間**: 2024-11-11  
**狀態**: ✅ 設計完成，待實施

