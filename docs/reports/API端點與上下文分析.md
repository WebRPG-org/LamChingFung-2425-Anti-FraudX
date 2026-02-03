# API 端點與對話上下文分析

## 📊 您的系統架構

您的系統使用了 **兩種不同的模式** 來處理 AI 對話：

---

## 1️⃣ `/api/chat` 模式 (game_routes.py & chat_routes.py)

### 使用場景
- 簡單的遊戲對話
- RPG Maker 插件
- 前端聊天功能

### 上下文處理方式
```python
# backend/api/game_routes.py
messages = [
    {"role": "system", "content": system_prompt},
    *history,  # ← 完整的對話歷史
    {"role": "user", "content": message}
]

payload = {
    "model": "gemma3:4b",
    "messages": messages,  # ← Ollama 自動處理上下文
    "stream": False
}
```

✅ **上下文管理**: Ollama 自動處理  
✅ **對話記憶**: 有  
✅ **代碼複雜度**: 低

---

## 2️⃣ `/api/generate` 模式 (Agent 系統 + ADK)

### 使用場景
- 複雜的 Agent 對話系統
- 防詐騙模擬訓練
- 需要精細控制的場景

### 上下文處理方式

#### 當前實現 (ollama_llm.py)
```python
# 從 LlmRequest 提取文本
prompt = _extract_text_from_contents(llm_request.contents)

payload = {
    "model": self.model,
    "prompt": prompt,  # ← 只有當前消息！
    "system": system_text,
    "stream": False
}
```

**問題**: `contents` 理論上可以包含多個消息，但實際上只傳遞了**當前消息**

#### ADK Runner 調用 (real_dialogue_runner.py)
```python
# 每次只傳遞單個消息
content_msg = genai_types.Content(
    role="user",
    parts=[genai_types.Part(text=message)]
)

req = LlmRequest(
    contents=[content_msg],  # ← 只有當前消息
    system_instruction=sys_inst
)
```

❌ **上下文管理**: 無！每次都是新對話  
❌ **對話記憶**: 無  
⚠️ **潛在問題**: Agent 無法記住之前說過的話

---

## 🔍 實際情況驗證

### 測試方法
在 `ollama_llm.py` 中添加日誌：

```python
def _extract_text_from_contents(contents: List[genai_types.Content]) -> str:
    lines: List[str] = []
    if not contents:
        return ""
    
    # 添加調試
    print(f"[DEBUG] Contents 數量: {len(contents)}")
    for i, c in enumerate(contents):
        print(f"[DEBUG] Content {i}: role={c.role}, parts={len(c.parts) if c.parts else 0}")
    
    for c in contents:
        if not getattr(c, "parts", None):
            continue
        for p in c.parts:
            txt = getattr(p, "text", None)
            if txt:
                lines.append(txt)
    
    result = "\n".join(lines).strip()
    print(f"[DEBUG] 最終 prompt 長度: {len(result)}")
    return result
```

---

## 💡 問題分析

### 您是對的！

`/api/generate` **確實可以支持上下文**，但需要：

1. **手動構建完整的 prompt**
   ```python
   prompt = """
   系統: 你是一個騙徒
   
   用戶: 你好
   助手: 你好！我是客服
   
   用戶: 我想投資
   助手: 太好了！我們有高回報項目
   
   用戶: 需要多少錢？
   """
   ```

2. **或者傳遞多個 Content**
   ```python
   contents = [
       Content(role="user", parts=[Part(text="你好")]),
       Content(role="assistant", parts=[Part(text="你好！")]),
       Content(role="user", parts=[Part(text="我想投資")])
   ]
   ```

---

## 🎯 解決方案建議

### 選項 A: 修改 ADK 傳遞歷史 ⭐ (推薦)

```python
# real_dialogue_runner.py
async def run_agent_with_adk(self, agent, message: str, session_id: str, history: list = None) -> str:
    # 構建完整的對話歷史
    contents = []
    
    # 添加歷史消息
    if history:
        for msg in history:
            role = "assistant" if msg["speaker"] == agent.name else "user"
            contents.append(genai_types.Content(
                role=role,
                parts=[genai_types.Part(text=msg["dialogue"])]
            ))
    
    # 添加當前消息
    contents.append(genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)]
    ))
    
    req = LlmRequest(contents=contents, system_instruction=sys_inst)
```

### 選項 B: 在 prompt 中包含歷史

```python
# ollama_llm.py
def _extract_text_from_contents(contents: List[genai_types.Content]) -> str:
    # 如果有多個 contents，構建完整對話
    if len(contents) > 1:
        lines = []
        for c in contents:
            role = "用戶" if c.role == "user" else "助手"
            for p in c.parts:
                if p.text:
                    lines.append(f"{role}: {p.text}")
        return "\n\n".join(lines)
    # 單個消息，直接返回
    ...
```

### 選項 C: 使用 `/api/chat` 替代

簡化 Agent 系統，直接使用 `/api/chat` 端點

---

## 📈 性能對比

| 方案 | 優點 | 缺點 |
|------|------|------|
| 保持 `/api/generate` + 添加歷史 | 靈活控制、精細調優 | 需要手動管理歷史 |
| 改用 `/api/chat` | 自動管理上下文、代碼簡單 | 控制較少 |

---

## 🔧 快速修復

想要我幫您實現 **選項 A** (在 ADK 中傳遞完整歷史) 嗎？

這樣您的 Agent 就能真正記住對話內容，防詐騙訓練會更有效！

