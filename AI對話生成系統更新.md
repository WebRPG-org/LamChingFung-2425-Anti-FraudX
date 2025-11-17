# AI對話生成系統更新說明

## 問題描述
原先的對話內容是固定的模板,沒有真正使用AI根據prompt動態生成。

## 解決方案
✅ 已修改前端和後端,實現**完全由AI動態生成**的對話系統。

---

## 🎯 修改內容

### 一、前端修改 (`RotatingScamSystem.js`)

#### 1. **受害者回應生成** (`generateVictimResponse`)

**修改前:**
```javascript
fetch(`${API_URL}/chat`, {
    method: 'POST',
    body: JSON.stringify({
        role: `你正在與${scam.name}的騙徒對話...`,
        message: "請繼續對話",  // ❌ 固定訊息
        history: history.slice(-4)
    })
})
```

**修改後:**
```javascript
// 構建包含上下文的動態prompt
const lastScammerMsg = history.length > 0 ? history[history.length - 1].scammer : scam.opening;
const victimPrompt = `騙徒剛剛說：「${lastScammerMsg}」

請以你的角色身份自然回應。注意：這是一個${scam.name}的騙局，但你現在可能還不確定是否為詐騙。請根據你的人設特點來回應。`;

// 使用正確的API endpoint
fetch(`${API_URL}/api/game/message`, {
    method: 'POST',
    body: JSON.stringify({
        session_id: sessionId,
        message: victimPrompt,  // ✅ 動態prompt
        target_ai: "AI-A",      // 受害者AI
        persona_type: personaType
    })
})
```

**改進點:**
- ✅ 使用 `/api/game/message` API (支持人設系統)
- ✅ 包含騙徒的上一句話作為上下文
- ✅ 明確告知AI當前騙局類型
- ✅ 自動應用當前人設特性
- ✅ 添加詳細的console日誌

#### 2. **騙徒回應生成** (`generateScammerResponse`)

**修改前:**
```javascript
fetch(`${API_URL}/chat`, {
    method: 'POST',
    body: JSON.stringify({
        role: `你是${scam.role}，正在進行${scam.name}...`,
        message: victimMsg,  // ❌ 只有受害者訊息
        history: []
    })
})
```

**修改後:**
```javascript
// 構建詳細的騙徒prompt
const tactics = scam.tactics.join('、');
const scammerPrompt = `受害者剛剛說：「${victimMsg}」

你是${scam.role}，正在進行${scam.name}。你的詐騙手法包括：${tactics}。

請根據受害者的回應，繼續你的詐騙行為。記住要保持角色一致性，不要暴露自己是騙徒。用廣東話回應，保持真實感。`;

// 使用正確的API endpoint
fetch(`${API_URL}/api/game/message`, {
    method: 'POST',
    body: JSON.stringify({
        session_id: sessionId,
        message: scammerPrompt,  // ✅ 動態prompt
        target_ai: "AI-D",       // 詐騙者AI
        persona_type: personaType
    })
})
```

**改進點:**
- ✅ 包含騙局的具體tactics
- ✅ 明確指示AI的角色和目標
- ✅ 要求廣東話對話
- ✅ 強調保持真實感

#### 3. **增強的Fallback機制**

```javascript
// 受害者Fallback - 根據人設返回不同預設回應
const fallbacks = {
    'A': '呃...我唔太明白，你可唔可以講清楚啲？',      // 長者
    'B': '等等，我需要確認一下這個資訊...',           // 一般市民
    'C': '我知道啦，但我想先了解清楚細節。',          // 過度自信
    'D': '這個...聽起來有點奇怪，你能證明嗎？'        // 年輕學生
};

// 騙徒Fallback - 根據騙局類型返回預設回應
const fallbacks = {
    '電話詐騙': '陳先生，你嘅銀行戶口真係有問題...',
    '投資詐騙': '呢個投資機會真係千載難逢...',
    '網購詐騙': '你嘅訂單有問題，需要你提供銀行資料...',
    // ... 更多類型
};
```

---

### 二、後端修改 (`game_routes.py`)

#### 1. **數據模型擴展**

```python
# 新增 scam_type 欄位
class GameStartRequest(BaseModel):
    persona_type: str
    scam_type: Optional[str] = None  # ✅ 新增

class GameStartResponse(BaseModel):
    session_id: str
    persona: Dict[str, Any]
    scam_type: Optional[str] = None  # ✅ 新增
    success: bool = True
```

#### 2. **數據庫結構更新**

```python
# 新增 scam_type 欄位到 sessions 表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        persona_type TEXT NOT NULL,
        scam_type TEXT,              -- ✅ 新增
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active'
    )
''')
```

#### 3. **AI System Prompt 優化**

**AI-A (受害者):**
```python
f"""你是 {persona['name']}，一個{persona['background']}。
你的特點：{', '.join(persona['characteristics'])}。
{"當前你正在面對「" + scam_type + "」的詐騙情境。" if scam_type else ""}
請以這個角色的身份回應，保持角色設定的一致性。
回應時要自然、真實，不要暴露這是在演戲。
請用繁體中文（廣東話風格）回應，每次回應控制在50-80字內。"""
```

**AI-D (騙徒):**
```python
f"""你是專業詐騙者，{"正在進行「" + scam_type + "」詐騙。" if scam_type else "正在試圖詐騙受害者。"}
你會使用常見的詐騙手法：
1. 建立信任和權威感
2. 製造緊迫感和恐懼
3. 要求提供個人資訊或金錢
4. 使用情感操控

重要規則：
- 保持真實感，不要太過明顯
- 不要暴露自己是騙徒
- 不要使用「詐騙」「騙局」等詞
- 不要使用旁白或括號標記如（）【】
- 用廣東話自然對話
- 每次回應控制在60-100字內
- 根據受害者的回應調整策略"""
```

#### 4. **函數簽名更新**

```python
# get_ai_system_prompt 新增 scam_type 參數
def get_ai_system_prompt(role: str, persona_type: str = "A", scam_type: str = None) -> str:
    ...

# call_ollama 新增 scam_type 參數
async def call_ollama(role: str, message: str, history: List[Dict] = None, 
                      persona_type: str = "A", scam_type: str = None) -> str:
    ...

# send_message 從數據庫讀取 scam_type
@router.post("/message")
async def send_message(request: GameMessageRequest):
    cursor.execute("SELECT persona_type, scam_type FROM sessions WHERE id = ?", ...)
    persona_type = result[0]
    scam_type = result[1] if len(result) > 1 else None
    
    ai_reply = await call_ollama(request.target_ai, request.message, 
                                  history, persona_type, scam_type)  # ✅ 傳入騙局類型
    ...
```

---

## 🎬 完整對話流程

### 1. **啟動對話** (玩家點擊NPC)

```javascript
// 前端: talkToScammer()
startAIBattle(npcId, scam)
    ↓
// 前端: startAIBattle()
fetch('/api/game/start', {
    persona_type: 'A',      // 當前人設
    scam_type: '電話詐騙'    // 當前騙局
})
    ↓
// 後端: start_game()
session_id = uuid.uuid4()
保存 persona_type='A', scam_type='電話詐騙' 到數據庫
    ↓
返回 session_id
```

### 2. **對話輪次循環**

```javascript
// 前端: startDialogueLoop()
第1輪對話:
    ↓
1. generateVictimResponse() 
   - 構建prompt: "騙徒剛剛說：「你的銀行戶口有問題...」請自然回應"
   - 調用 /api/game/message (target_ai="AI-A")
   - 後端使用人設A (長者) 的system prompt生成回應
   - AI回應: "呃...真係咩？我唔太清楚..."
    ↓
2. generateScammerResponse()
   - 構建prompt: "受害者剛剛說：「呃...真係咩？」繼續詐騙..."
   - 調用 /api/game/message (target_ai="AI-D")
   - 後端使用騙徒的system prompt (包含騙局tactics) 生成回應
   - AI回應: "陳先生，情況緊急，你必須立即配合..."
    ↓
3. 顯示對話到遊戲訊息框
4. recordDialogue() 記錄到變數23
5. 2秒後進入第2輪...
```

### 3. **對話結束**

```javascript
// 前端: endBattle()
- 獲取完整對話歷史 (變數23)
- 調用AI評分 (使用 /api/game/message, target_ai="AI-B")
- 顯示評分結果
- 輪換騙局 (rotateToNextScam)
- 輪換人設 (rotateToNextPersona)  ✅
- 清空對話記錄
- 顯示下次騙局和人設
```

---

## 🔍 AI Prompt 範例

### 受害者 AI-A 接收的完整訊息

**System:**
```
你是陳老伯（長者），一個退休教師，對新科技不熟悉，容易相信權威。
你的特點：信任權威、不熟悉科技、善良單純。
當前你正在面對「電話詐騙」的詐騙情境。
請以這個角色的身份回應，保持角色設定的一致性。
回應時要自然、真實，不要暴露這是在演戲。
請用繁體中文（廣東話風格）回應，每次回應控制在50-80字內。
```

**User:**
```
騙徒剛剛說：「你的銀行戶口有問題，需要立即凍結處理！」

請以你的角色身份自然回應。注意：這是一個電話詐騙的騙局，但你現在可能還不確定是否為詐騙。請根據你的人設特點來回應。
```

**AI回應範例:**
```
咦？我嘅戶口有問題？係咩問題呀？我最近都冇用過啲卡嘅...你真係銀行嘅人？
```

### 騙徒 AI-D 接收的完整訊息

**System:**
```
你是專業詐騙者，正在進行「電話詐騙」詐騙。
你會使用常見的詐騙手法：
1. 建立信任和權威感
2. 製造緊迫感和恐懼
3. 要求提供個人資訊或金錢
4. 使用情感操控

重要規則：
- 保持真實感，不要太過明顯
- 不要暴露自己是騙徒
- 不要使用「詐騙」「騙局」等詞
- 不要使用旁白或括號標記
- 用廣東話自然對話
- 每次回應控制在60-100字內
- 根據受害者的回應調整策略
```

**User:**
```
受害者剛剛說：「咦？我嘅戶口有問題？你真係銀行嘅人？」

你是假公安，正在進行電話詐騙。你的詐騙手法包括：假冒公職人員、製造恐慌、要求提供銀行資訊、威脅法律後果。

請根據受害者的回應，繼續你的詐騙行為。記住要保持角色一致性，不要暴露自己是騙徒。用廣東話回應，保持真實感。
```

**AI回應範例:**
```
陳先生，我係公安局嘅，唔係銀行。你嘅戶口涉及一宗洗黑錢案件，而家必須配合調查。如果你唔配合，我哋只能即時凍結你嘅資產。你明唔明白事態嘅嚴重性？
```

---

## ✅ 改進總結

| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| **API Endpoint** | `/chat` (通用) | `/api/game/message` (遊戲專用) |
| **人設應用** | ❌ 未使用 | ✅ 自動應用 (A/B/C/D) |
| **騙局資訊** | ❌ 未傳遞 | ✅ 傳遞到後端 |
| **上下文感知** | ❌ 固定訊息 | ✅ 包含上輪對話 |
| **Prompt質量** | ❌ 簡單模板 | ✅ 詳細情境描述 |
| **對話歷史** | ❌ 未使用 | ✅ 自動維護 |
| **角色一致性** | ❌ 弱 | ✅ 強制規則 |
| **字數控制** | ❌ 無限制 | ✅ 50-100字 |
| **語言風格** | ❌ 未指定 | ✅ 廣東話 |
| **Fallback** | ❌ 通用錯誤訊息 | ✅ 針對性回應 |

---

## 🧪 測試方法

### 1. 檢查Console日誌
```javascript
[開始對話] 騙局：電話詐騙, 人設：A (長者)
會話創建：abc-123-def, 騙局：電話詐騙, 人設：A
[受害者回應 - 人設A]: 咦？我嘅戶口有問題？...
[騙徒回應 - 假公安]: 陳先生，我係公安局嘅...
```

### 2. 驗證對話多樣性
- 連續與同一NPC對話3次
- 每次對話內容應該**不同**
- 受害者應該根據人設展現不同反應
- 騙徒應該根據tactics調整策略

### 3. 驗證人設輪換
```
第1次: 人設A (長者) - 困惑、容易相信
第2次: 人設B (一般市民) - 謹慎、要求確認
第3次: 人設C (過度自信) - 質疑、展現知識
第4次: 人設D (年輕學生) - 懷疑、要求證據
```

### 4. 檢查數據庫
```bash
sqlite3 anti_fraud_game.db
SELECT id, persona_type, scam_type FROM sessions ORDER BY created_at DESC LIMIT 5;
```

應該看到每次對話的人設和騙局都有記錄。

---

## 📊 預期效果

### 對話質量提升
- ✅ **真實感**: AI根據情境動態生成,不再重複
- ✅ **角色一致**: 人設特徵明顯 (長者vs學生)
- ✅ **策略性**: 騙徒根據tactics調整話術
- ✅ **教育性**: 玩家能體驗不同人設的弱點

### 系統完整性
- ✅ **前後端協調**: Session管理完善
- ✅ **數據記錄**: 所有對話可追溯
- ✅ **錯誤處理**: Fallback機制健全
- ✅ **可擴展性**: 易於新增騙局/人設

---

## 🚀 下一步建議

1. **增加對話歷史感知**
   - 讓AI能記住前幾輪對話
   - 避免重複相同問題

2. **情緒跟蹤**
   - 追蹤受害者的懷疑程度
   - 騙徒根據情緒調整策略

3. **專家介入**
   - 在對話中途加入防騙專家 (AI-C)
   - 提供即時建議

4. **評分細化**
   - 分項評分 (警覺性/判斷力/應對)
   - 提供具體改進建議

現在系統已經實現**完全由AI動態生成對話**,不再依賴固定模板! 🎉
