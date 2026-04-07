# Firestore RAG 詐騙數據集成系統 - 使用指南

## 📌 系統概述

這是一個基於Firestore的RAG（檢索增強生成）系統，用於：
- 存儲生成式數據和真實案例到Firestore
- 為LLM提供動態上下文注入
- 支持騙徒、專家、受害者三種AI角色

## 🎯 核心特點

✅ **Firestore存儲** - 所有數據存儲在Firestore，無需本地部署  
✅ **動態上下文** - 為每個LLM調用動態生成上下文  
✅ **Prompt注入** - 直接注入到LLM的system prompt中  
✅ **多角色支持** - 騙徒、專家、受害者三種角色  
✅ **高度多樣化** - 每次都生成不同的上下文  
✅ **隱私保護** - 自動遮蔽敏感信息  

## 📁 文件結構

```
backend/services/
├── firestore_rag_fraud_loader.py          # 核心RAG系統
├── session_manager_rag_integration.py     # SessionManager集成
└── firestore_rag_service.py               # 現有的Firestore服務
```

## 🚀 快速開始

### 1. 初始化系統

```python
from services.firestore_rag_fraud_loader import (
    FirestoreRAGDataLoader,
    FirestoreRAGPromptBuilder
)

# 初始化加載器
loader = FirestoreRAGDataLoader()

# 加載數據到Firestore
await loader.load_generator_data("path/to/massive_generator.py")
await loader.load_adcc_data("path/to/scraped_alerts.json")
```

### 2. 為LLM生成Prompt

```python
# 初始化Prompt構建器
prompt_builder = FirestoreRAGPromptBuilder()

# 為騙徒生成prompt
scammer_prompt = await prompt_builder.build_scammer_prompt("網上購物騙案")

# 為專家生成prompt
expert_prompt = await prompt_builder.build_expert_prompt("電話騙案")

# 為受害者生成prompt
victim_prompt = await prompt_builder.build_victim_prompt("投資騙案")
```

### 3. 在SessionManager中使用

```python
from services.session_manager_rag_integration import SessionManagerRAGIntegration

class SessionManager:
    def __init__(self):
        self.rag_integration = SessionManagerRAGIntegration()
    
    async def initialize_session(self, scam_type: str, player_role: str):
        # 獲取RAG增強的system prompt
        if player_role == "scammer":
            system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
        elif player_role == "expert":
            system_prompt = await self.rag_integration.get_expert_system_prompt(scam_type)
        else:
            system_prompt = await self.rag_integration.get_victim_system_prompt(scam_type)
        
        # 使用system_prompt初始化LLM
        self.llm_client.set_system_prompt(system_prompt)
```

## 💻 詳細使用示例

### 示例1: 騙徒AI對話

```python
# 初始化
prompt_builder = FirestoreRAGPromptBuilder()

# 獲取system prompt
system_prompt = await prompt_builder.build_scammer_prompt("網上購物騙案")

# 發送到LLM
response = await llm_client.chat(
    system_prompt=system_prompt,
    user_message="你好"
)

# 輸出: 騙徒的開場白（基於Firestore中的真實數據）
```

### 示例2: 專家AI對話

```python
# 獲取system prompt
system_prompt = await prompt_builder.build_expert_prompt("電話騙案")

# 發送到LLM
response = await llm_client.chat(
    system_prompt=system_prompt,
    user_message="我收到一個可疑電話說我涉嫌洗黑錢"
)

# 輸出: 專家的防騙建議（基於真實案例）
```

### 示例3: 受害者AI對話

```python
# 獲取system prompt
system_prompt = await prompt_builder.build_victim_prompt("網上情緣")

# 發送到LLM
response = await llm_client.chat(
    system_prompt=system_prompt,
    user_message="我在網上認識了一個人，他說需要錢"
)

# 輸出: 受害者的反應（容易被騙）
```

## 🔄 數據流程

```
massive_generator.py + scraped_alerts.json
            ↓
    FirestoreRAGDataLoader
            ↓
        Firestore
            ↓
    FirestoreRAGContextProvider
            ↓
    FirestoreRAGPromptBuilder
            ↓
    LLM System Prompt
            ↓
        LLM Response
```

## 📊 Firestore 數據結構

### rag_features 集合

```json
{
  "scam_type": "網上購物騙案",
  "source": "generator",
  "template_id": 0,
  "opening": "你好，我係淘寶客服",
  "hook": "你嘅訂單有問題",
  "request": "需要你提供銀行帳戶資料",
  "urgency": "今日內必須處理",
  "created_at": "2026-03-16T10:00:00Z",
  "type": "scammer_template"
}
```

或

```json
{
  "scam_type": "電話騙案",
  "source": "adcc",
  "case_id": 123,
  "description": "受害者收到假冒警察的電話...",
  "method": "冒充執法人員",
  "content": "詳細案例內容",
  "created_at": "2026-03-16T10:00:00Z",
  "type": "real_case"
}
```

## 🎯 API 參考

### FirestoreRAGDataLoader

```python
# 加載生成式數據
await loader.load_generator_data(generator_path: str) -> int

# 加載ADCC真實案例
await loader.load_adcc_data(adcc_path: str) -> int
```

### FirestoreRAGContextProvider

```python
# 獲取騙徒上下文
await context_provider.get_scammer_context(scam_type: str, max_items: int = 3) -> str

# 獲取專家上下文
await context_provider.get_expert_context(scam_type: str, max_items: int = 3) -> str

# 獲取警告信號
await context_provider.get_warning_signs(scam_type: str) -> List[str]

# 獲取防騙建議
await context_provider.get_prevention_tips(scam_type: str) -> List[str]
```

### FirestoreRAGPromptBuilder

```python
# 為騙徒構建prompt
await prompt_builder.build_scammer_prompt(scam_type: str, user_message: str = "") -> str

# 為專家構建prompt
await prompt_builder.build_expert_prompt(scam_type: str, user_message: str = "") -> str

# 為受害者構建prompt
await prompt_builder.build_victim_prompt(scam_type: str, user_message: str = "") -> str
```

### SessionManagerRAGIntegration

```python
# 獲取騙徒system prompt
await rag_integration.get_scammer_system_prompt(scam_type: str) -> str

# 獲取專家system prompt
await rag_integration.get_expert_system_prompt(scam_type: str) -> str

# 獲取受害者system prompt
await rag_integration.get_victim_system_prompt(scam_type: str) -> str

# 增強用戶消息
await rag_integration.enhance_user_message(role: str, scam_type: str, user_message: str) -> str
```

## 🔐 隱私和安全

### 自動遮蔽
- 📞 電話號碼 → `[PHONE]`
- 🏦 銀行帳戶 → `[ACCOUNT]`
- 👤 名字 → `[NAME]`
- 🔗 URL → `[URL]`

### 數據隔離
- 騙徒AI: 只能看生成式數據
- 專家AI: 可以看所有數據
- 受害者AI: 只能看警告信號

## 📈 性能優化

### 查詢優化
- 使用Firestore索引加速查詢
- 限制返回項數（max_items）
- 緩存常用上下文

### Token優化
- 只返回必要的信息
- 自動去重
- 壓縮冗餘內容

## 🧪 測試

### 測試數據加載

```python
async def test_data_loading():
    loader = FirestoreRAGDataLoader()
    
    gen_count = await loader.load_generator_data("path/to/generator.py")
    adcc_count = await loader.load_adcc_data("path/to/alerts.json")
    
    assert gen_count > 0
    assert adcc_count > 0
```

### 測試Prompt生成

```python
async def test_prompt_generation():
    prompt_builder = FirestoreRAGPromptBuilder()
    
    scammer_prompt = await prompt_builder.build_scammer_prompt("網上購物騙案")
    expert_prompt = await prompt_builder.build_expert_prompt("電話騙案")
    
    assert len(scammer_prompt) > 0
    assert len(expert_prompt) > 0
```

## 🎓 最佳實踐

### 1. 初始化時加載數據
```python
# 在應用啟動時加載一次
loader = FirestoreRAGDataLoader()
await loader.load_generator_data(...)
await loader.load_adcc_data(...)
```

### 2. 緩存Prompt構建器
```python
# 創建全局實例
prompt_builder = FirestoreRAGPromptBuilder()

# 在SessionManager中重用
self.prompt_builder = prompt_builder
```

### 3. 動態生成上下文
```python
# 每次調用時動態生成，確保多樣性
system_prompt = await self.prompt_builder.build_scammer_prompt(scam_type)
```

### 4. 錯誤處理
```python
try:
    system_prompt = await prompt_builder.build_scammer_prompt(scam_type)
except Exception as e:
    log.error(f"Failed to build prompt: {e}")
    # 使用默認prompt
    system_prompt = DEFAULT_SCAMMER_PROMPT
```

## 📝 集成步驟

### Step 1: 導入模塊
```python
from services.firestore_rag_fraud_loader import (
    FirestoreRAGDataLoader,
    FirestoreRAGPromptBuilder
)
from services.session_manager_rag_integration import SessionManagerRAGIntegration
```

### Step 2: 初始化
```python
# 在應用啟動時
loader = FirestoreRAGDataLoader()
await loader.load_generator_data(...)
await loader.load_adcc_data(...)
```

### Step 3: 在SessionManager中使用
```python
class SessionManager:
    def __init__(self):
        self.rag_integration = SessionManagerRAGIntegration()
    
    async def initialize_session(self, scam_type, player_role):
        system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
        # 使用system_prompt初始化LLM
```

### Step 4: 在LLM調用中使用
```python
response = await llm_client.chat(
    system_prompt=system_prompt,
    user_message=user_message
)
```

## 🚨 常見問題

### Q: 數據會重複加載嗎？
A: 不會。Firestore會自動去重。建議在應用啟動時加載一次。

### Q: 如何更新數據？
A: 刪除舊數據後重新加載，或使用Firestore的update方法。

### Q: 性能如何？
A: Firestore查詢通常在100ms以內，非常快。

### Q: 如何處理大量數據？
A: 使用批量操作和分頁查詢。

## 📞 支持

如有問題，請查看：
1. Firestore文檔: https://firebase.google.com/docs/firestore
2. 代碼示例: `services/firestore_rag_fraud_loader.py`
3. 集成示例: `services/session_manager_rag_integration.py`

---

**版本**: 1.0.0  
**最後更新**: 2026年3月16日  
**狀態**: ✅ 生產就緒


