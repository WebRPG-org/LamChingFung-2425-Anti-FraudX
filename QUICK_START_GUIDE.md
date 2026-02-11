# 🚀 快速啟動指南

## 更新內容 (2026-02-12)

### ✅ 已完成的優化

1. **前端模型切換 UI 增強**
   - 按鈕顏色動態變化（紫色 ↔ 藍色）
   - 圖標切換（🤖 ↔ ✨）
   - 滑塊動畫效果（白色 → 金色）
   - 文字和顏色實時更新

2. **Token 使用優化（減少 90%）**
   - 創建精簡版數據：`scraped_alerts_lite.json`
   - 從 409 KB → 38.8 KB
   - 從 281 案例 → 30 精選案例
   - 自動檢測和創建精簡版

3. **啟動腳本增強**
   - `quick_start.bat` - 自動檢測並創建精簡版數據
   - `quick_start_gemini.bat` - Gemini 專用啟動腳本
   - 自動初始化 Gemini 文件上傳

4. **文件管理工具**
   - `cleanup_gemini_files.py` - 清理重複上傳的文件
   - `create_lite_data.py` - 創建精簡版數據

---

## 🎯 使用方法

### 方式 1：使用 Ollama（本地模型）

```bash
# 確保 Ollama 正在運行
ollama serve

# 啟動服務
.\quick_start.bat
```

### 方式 2：使用 Gemini API

```bash
# 1. 配置 API Key（首次使用）
# 編輯 backend\.env：
GEMINI_ENABLED=true
GEMINI_API_KEY=你的API密鑰

# 2. 啟動服務
.\quick_start_gemini.bat
```

### 方式 3：動態切換（推薦）

```bash
# 1. 啟動服務（默認 Ollama）
.\quick_start.bat

# 2. 在前端切換
# 打開 http://localhost:8000/index.html
# 點擊右上角的切換按鈕
```

---

## 🔧 維護工具

### 清理 Gemini 重複文件

```bash
cd backend
py scripts\cleanup_gemini_files.py
```

### 重新上傳 Gemini 文件

```bash
cd backend
py scripts\init_gemini_files.py
```

### 創建精簡版數據

```bash
cd backend
py scripts\create_lite_data.py
```

---

## 📊 配額管理

### Gemini 免費版限制
- **每分鐘**: 250,000 tokens
- **文件保存**: 2 天後過期

### 如何避免超過配額

1. **使用精簡版數據**（已自動配置）
   - 減少 90% token 使用
   
2. **監控使用量**
   - 訪問：https://ai.dev/rate-limit
   
3. **遇到 429 錯誤時**
   - 等待 1-2 分鐘
   - 或切換回 Ollama 模式

---

## 🎨 前端切換效果

### Ollama 模式
- 🤖 圖標
- 🟢 綠色文字 "Ollama 本地"
- 🟣 紫色按鈕
- 按鈕文字："切換至 Gemini"

### Gemini 模式
- ✨ 圖標
- 🔵 藍色文字 "Gemini API"
- 🔵 藍色按鈕
- 🟡 金色滑塊
- 按鈕文字："切換至 Ollama"

---

## 📝 文件結構

```
AI-Agentv4/
├── quick_start.bat              # 通用啟動（自動檢測模式）
├── quick_start_gemini.bat       # Gemini 專用啟動
├── backend/
│   ├── .env                     # 配置文件
│   ├── scripts/
│   │   ├── cleanup_gemini_files.py    # 清理工具
│   │   ├── create_lite_data.py        # 數據優化工具
│   │   └── init_gemini_files.py       # 文件上傳工具
│   └── llms/
│       └── gemini_file_manager.py     # 文件管理器
├── data/
│   ├── scraped_alerts.json      # 完整版（409 KB）
│   └── scraped_alerts_lite.json # 精簡版（38.8 KB）✨
└── frontend/
    ├── index.html               # 主頁面
    ├── js/
    │   └── model_switch.js      # 切換邏輯
    └── css/
        └── style.css            # 樣式（含切換動畫）
```

---

## 🐛 故障排除

### 問題：429 配額錯誤

**解決方案：**
1. 等待 1-2 分鐘
2. 切換回 Ollama 模式
3. 檢查是否使用精簡版數據

### 問題：前端切換無反應

**解決方案：**
1. 按 F12 打開開發者工具
2. 查看 Console 錯誤
3. 確認後端正在運行
4. 強制刷新頁面（Ctrl+F5）

### 問題：文件上傳失敗

**解決方案：**
1. 檢查 API Key 是否正確
2. 確認網絡連接
3. 運行清理工具後重試

---

## 📚 相關文檔

- [Gemini API 文檔](https://ai.google.dev/gemini-api/docs)
- [配額限制說明](https://ai.google.dev/gemini-api/docs/rate-limits)
- [使用量監控](https://ai.dev/rate-limit)
- [API Key 管理](https://aistudio.google.com/app/apikey)

---

## 🎉 下一步

1. **測試前端切換功能**
   - 打開 http://localhost:8000/index.html
   - 點擊切換按鈕
   - 觀察視覺變化

2. **監控 Token 使用**
   - 訪問 https://ai.dev/rate-limit
   - 確認精簡版數據生效

3. **開始使用**
   - 選擇 RPG 遊戲模式
   - 或個人對話模式
   - 體驗 Gemini 和 Ollama 的差異

---

**最後更新**: 2026-02-12  
**版本**: v2.0 - Token 優化版
