# RPG模式文件找不到問題排查

## ❌ 錯誤信息

```
找不到您的檔案
檔案可能已移至其他位置或遭到刪除。
ERR_FILE_NOT_FOUND
```

---

## 🔍 問題原因

### 最常見原因：直接打開HTML文件 ❌

**錯誤方式**：
- 雙擊打開 `rpg_game.html`
- 使用檔案總管拖曳到瀏覽器
- 網址欄顯示 `file:///C:/Users/...`

**為什麼會出錯**：
```
當用file://協議打開時：
rpg_game.html
  └─ 嘗試加載 js/libs/pixi.js
  └─ 路徑變成 file:///C:/Users/.../js/libs/pixi.js
  └─ ❌ 瀏覽器安全限制，無法加載本地文件
```

---

## ✅ 正確解決方案

### 方法1：通過HTTP服務器訪問 ✨ 推薦

#### 步驟1：確保後端正在運行

```bash
# 在項目根目錄下
cd AI-Agent-main

# 啟動後端
python backend/main.py
```

**應該看到**：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ 已掛載RPG項目靜態文件
```

---

#### 步驟2：使用正確的URL訪問

**正確的訪問方式** ✅：

```
主頁:
http://localhost:8000/

RPG遊戲模式:
http://localhost:8000/RPG_Project/rpg_game.html

自動模擬模式:
http://localhost:8000/RPG_Project/test_ai_agent_v2.5.html

API測試模式:
http://localhost:8000/RPG_Project/test_plugin.html

個人對話模式:
http://localhost:8000/personal_chat.html
```

---

### 方法2：檢查後端配置

確認後端正確掛載了靜態文件：

```python
# backend/main.py 應該有這段代碼

from fastapi.staticfiles import StaticFiles

# 掛載RPG項目的靜態文件
rpg_project_path = os.path.join(os.path.dirname(__file__), '..', 'RPG_platform', 'RPG_Project')
app.mount("/RPG_Project", StaticFiles(directory=rpg_project_path, html=True), name="rpg_project")
```

---

## 🧪 快速測試

### 測試1：檢查後端是否運行

在瀏覽器訪問：
```
http://localhost:8000/
```

**正常情況**：應該看到主頁（RPG入口頁面）  
**異常情況**：無法連接 → 後端未啟動

---

### 測試2：檢查靜態文件是否可訪問

在瀏覽器訪問：
```
http://localhost:8000/RPG_Project/js/libs/pixi.js
```

**正常情況**：顯示JavaScript代碼  
**異常情況**：404 Not Found → 靜態文件未正確掛載

---

### 測試3：檢查控制台錯誤

1. 打開RPG頁面：`http://localhost:8000/RPG_Project/rpg_game.html`
2. 按 `F12` 打開開發者工具
3. 查看 Console 標籤

**正常情況**：
```
Loading plugins...
Game initialized
```

**異常情況**：
```
Failed to load resource: net::ERR_FILE_NOT_FOUND
```

---

## 📋 完整檢查清單

```
□ 後端已啟動
  python backend/main.py
  
□ 看到掛載成功信息
  ✅ 已掛載RPG項目靜態文件
  
□ 使用HTTP協議訪問
  http://localhost:8000/...
  ❌ 不要用 file:///...
  
□ 網址正確
  http://localhost:8000/RPG_Project/rpg_game.html
  
□ 控制台沒有紅色錯誤
  按F12查看Console
  
□ 靜態文件可訪問
  測試 http://localhost:8000/RPG_Project/js/libs/pixi.js
```

---

## 🔧 常見問題

### Q1: 後端啟動失敗

**症狀**：
```
ModuleNotFoundError: No module named 'fastapi'
```

**解決**：
```bash
pip install fastapi uvicorn
```

---

### Q2: 端口被占用

**症狀**：
```
ERROR: [Errno 10048] 只允許使用一次該地址
```

**解決**：
```bash
# 方法1：關閉占用8000端口的程序
netstat -ano | findstr :8000

# 方法2：使用其他端口
uvicorn backend.main:app --port 8001
```

---

### Q3: 路徑不存在警告

**症狀**：
```
⚠️ RPG項目路徑不存在: ...
```

**解決**：
檢查目錄結構：
```
AI-Agent-main/
├── backend/
│   └── main.py
└── RPG_platform/
    └── RPG_Project/
        ├── rpg_game.html
        ├── js/
        ├── css/
        └── ...
```

確保 `RPG_platform/RPG_Project/` 目錄存在。

---

### Q4: CORS錯誤

**症狀**：
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**解決**：
已在 `backend/main.py` 中配置CORS，應該不會有此問題。如果出現，檢查：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 正確的訪問流程

```
┌──────────────────┐
│  用戶打開瀏覽器   │
└──────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  輸入正確的HTTP地址               │
│  http://localhost:8000/          │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  點擊 "RPG遊戲模式"              │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  瀏覽器請求：                     │
│  http://localhost:8000/          │
│  RPG_Project/rpg_game.html       │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  FastAPI後端處理請求              │
│  StaticFiles中間件               │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  返回 rpg_game.html              │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  瀏覽器加載頁面並請求資源：       │
│  - js/libs/pixi.js               │
│  - css/...                       │
│  - fonts/...                     │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  所有資源成功加載                 │
│  RPG遊戲正常運行 ✅              │
└──────────────────────────────────┘
```

---

## ❌ 錯誤的訪問流程

```
┌──────────────────────────┐
│  用戶雙擊 rpg_game.html   │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  瀏覽器用file://協議打開   │
│  file:///C:/Users/.../    │
│  rpg_game.html           │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  嘗試加載資源：           │
│  file:///.../js/...      │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  ❌ ERR_FILE_NOT_FOUND   │
│  瀏覽器安全限制           │
└──────────────────────────┘
```

---

## 💡 關鍵要點

### ✅ 正確做法

1. **啟動後端服務器**
   ```bash
   python backend/main.py
   ```

2. **使用HTTP訪問**
   ```
   http://localhost:8000/
   ```

3. **從主頁導航**
   - 點擊 "RPG遊戲模式" 卡片
   - 自動跳轉到正確URL

---

### ❌ 錯誤做法

1. ❌ 雙擊HTML文件打開
2. ❌ 使用 file:// 協議
3. ❌ 後端未啟動就訪問
4. ❌ 使用錯誤的URL路徑

---

## 🎯 快速解決步驟

### 1分鐘修復方案

```bash
# 步驟1：打開命令提示符（CMD）
Win + R → 輸入 cmd → Enter

# 步驟2：切換到項目目錄
cd C:\Users\andy1\Desktop\4116M\AI-Agent-12-11-2025\AI-Agent-main

# 步驟3：啟動後端
python backend/main.py

# 步驟4：等待看到啟動成功
# 看到：INFO: Uvicorn running on http://127.0.0.1:8000

# 步驟5：打開瀏覽器訪問
http://localhost:8000/
```

然後點擊 "RPG遊戲模式" 就可以了！ 🎉

---

## 📞 如果仍然有問題

### 收集診斷信息

1. **後端日誌**：
   - 啟動時的所有輸出
   - 是否有紅色錯誤

2. **瀏覽器控制台**：
   - 按 F12
   - Console 標籤的所有錯誤
   - Network 標籤失敗的請求

3. **網址欄**：
   - 確認顯示的完整URL
   - 是 `http://` 還是 `file://`

4. **目錄結構**：
   - 確認 RPG_platform/RPG_Project/ 存在
   - 確認 js/ css/ fonts/ 子目錄存在

---

**記住：永遠通過 HTTP 服務器訪問，不要直接打開HTML文件！** 🚀

---

*創建時間: 2025-11-17*  
*版本: v1.0*
