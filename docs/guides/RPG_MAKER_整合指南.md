# 🎮 RPG Maker 整合指南 - AI-Agent 系統

## 📋 **系統整合說明**

本系統已將防詐騙教育遊戲整合到 AI-Agent-main 後台，RPG Maker 可以通過統一的 API 端點訪問所有功能。

---

## 🏗️ **整合架構**

```
AI-Agent-main (Port 8000)
├── 原有功能
│   ├── /simulation/* - WebSocket 實時對話模擬
│   ├── /api/training/* - 訓練系統
│   └── / - AI-Agent Web UI (測試可視化)
│
└── 新增功能 (for RPG Maker)
    ├── /chat - 通用 AI 聊天 (AI_Bridge.js 使用)
    ├── /api/game/start - 開始遊戲
    ├── /api/game/message - 遊戲對話
    ├── /api/game/end - 結束遊戲
    └── /api/game/session/{id} - 獲取會話資訊
```

---

## 🚀 **快速開始**

### 1. 安裝依賴

```bash
cd AI-Agent-main/backend
pip install -r requirements.txt
```

### 2. 設置環境變數

在 `AI-Agent-main/backend/` 創建 `.env` 文件：

```env
# AI 模型設定
AGENT_MODEL=gemma3:4b
# 或使用較小的模型
# AGENT_MODEL=gemma:2b

# Ollama 連接
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### 3. 確保 Ollama 運行

```bash
# 下載模型
ollama pull gemma3:4b
# 或
ollama pull gemma:2b

# 確保 Ollama 服務運行
ollama serve
```

### 4. 啟動系統

```bash
# 方法 1: 使用啟動腳本
python start_server.py

# 方法 2: 直接啟動後台
cd backend
python main.py
```

系統將在 **http://localhost:8000** 啟動

---

## 🎮 **RPG Maker 插件安裝**

### 1. 複製插件文件

將以下文件複製到 RPG Maker 專案的 `js/plugins/` 資料夾：

```
AI-Agent-main/rpg_maker_plugins/
├── AI_Bridge.js          # 基礎 AI 通信插件
└── AntiFraudGame.js      # 完整遊戲系統插件
```

### 2. 啟用插件

1. 打開 RPG Maker MZ
2. 工具 → 插件管理器
3. 添加 `AI_Bridge` 和 `AntiFraudGame`
4. 確保兩個插件都已啟用
5. 確保插件順序：`AI_Bridge` 在前，`AntiFraudGame` 在後

---

## 📝 **RPG Maker 使用範例**

### 範例 1：基礎 AI 對話 (AI_Bridge.js)

```
事件內容：
◆ 文字顯示：NPC
  └ 歡迎來到村莊！
◆ 插件命令：AI_Bridge > sendToAI
  ├ AI 角色：一個友善的村民，住在這個村莊多年
  ├ 訊息內容：告訴我這個村莊的故事
  ├ 歷史記錄變量ID：1
  └ 回應變量ID：2
◆ 等待：30 幀
◆ 文字顯示：村民
  └ \V[2]
```

### 範例 2：防詐騙教育遊戲 (AntiFraudGame.js)

```
事件內容：
◆ 文字顯示：系統
  └ 歡迎來到防詐騙教育遊戲！
◆ 顯示選項：選擇角色 / (A) 長者 / (B) 一般市民 / (C) 過度自信者
  ├ 選擇 (A) 長者時
  │ ◆ 插件命令：AntiFraudGame > startGame
  │   ├ 角色類型：A
  │   └ 會話ID變量：10
  │ ◆ 等待：30 幀
  │ ◆ 插件命令：AntiFraudGame > startAutoDialogue
  │   ├ 會話ID變量：10
  │   ├ 對話記錄變量：11
  │   └ 對話輪數：5
  │ ◆ 等待：300 幀
  │ ◆ 插件命令：AntiFraudGame > getScore
  │   ├ 會話ID變量：10
  │   └ 評分結果變量：12
  │ ◆ 等待：30 幀
  │ ◆ 文字顯示：評分AI
  │   └ \V[12]
  │ ◆ 插件命令：AntiFraudGame > endGame
  │   └ 會話ID變量：10
```

### 範例 3：互動式詐騙對話

```
事件內容：
◆ 插件命令：AntiFraudGame > startGame
  ├ 角色類型：A
  └ 會話ID變量：10
◆ 文字顯示：陌生人
  └ 你好，我是銀行職員...
◆ 顯示選項：如何回應？ / 提供個人資訊 / 詢問證件 / 拒絕對話
  ├ 選擇 提供個人資訊 時
  │ ◆ 插件命令：AI_Bridge > sendToAI
  │   ├ AI 角色：防騙助手
  │   ├ 訊息內容：我剛剛提供了個人資訊給陌生人，這樣對嗎？
  │   ├ 歷史記錄變量ID：1
  │   └ 回應變量ID：2
  │ ◆ 等待：30 幀
  │ ◆ 文字顯示：防騙助手
  │   └ ⚠️ \V[2]
  ├ 選擇 詢問證件 時
  │ ◆ 文字顯示：防騙助手
  │   └ ✅ 做得好！總是要求對方出示證件！
```

---

## 🎯 **遊戲變量說明**

| 變量ID | 用途 | 數據類型 | 說明 |
|--------|------|----------|------|
| 1 | AI 對話歷史 | Array | 存儲通用 AI 對話的歷史記錄 |
| 2 | AI 回應 | String | 存儲 AI 的最新回應 |
| 10 | 遊戲會話ID | String | 防詐騙遊戲的唯一會話標識 |
| 11 | 對話記錄 | Array | 自動對話的完整記錄 |
| 12 | 評分結果 | String | 評分AI的分析結果 |
| 13-20 | 備用 | - | 供其他用途使用 |

---

## 🌐 **API 端點說明**

### 通用聊天 API
```
POST http://localhost:8000/chat
Content-Type: application/json

{
  "role": "AI 角色描述",
  "message": "用戶訊息",
  "history": []  // 可選：對話歷史
}

回應：
{
  "reply": "AI 回應內容",
  "success": true
}
```

### 遊戲 API

#### 開始遊戲
```
POST http://localhost:8000/api/game/start
{
  "persona_type": "A"  // A, B, C, D
}
```

#### 發送遊戲訊息
```
POST http://localhost:8000/api/game/message
{
  "session_id": "會話ID",
  "message": "訊息內容",
  "target_ai": "AI-D",  // AI-A, AI-B, AI-C, AI-D
  "persona_type": "A"
}
```

#### 結束遊戲
```
POST http://localhost:8000/api/game/end?session_id=會話ID
```

---

## 🔍 **測試與調試**

### 1. 測試 API 連接

打開瀏覽器訪問：
- http://localhost:8000 - AI-Agent Web UI
- http://localhost:8000/docs - API 文檔 (Swagger)
- http://localhost:8000/redoc - API 文檔 (ReDoc)

### 2. 測試 RPG Maker 連接

在 RPG Maker 的事件中：
```
◆ 插件命令：AI_Bridge > sendToAI
  └ 訊息：測試連接
◆ 條件分支：變量[2] ≠ ""
  ├ 是：顯示 "連接成功"
  └ 否：顯示 "連接失敗"
```

### 3. 查看控制台

在 RPG Maker 遊戲測試時按 F8 打開開發者工具，查看 Console 標籤的錯誤訊息

---

## ⚠️ **常見問題**

### Q1: 插件無法連接到 API
**A:** 確保 AI-Agent 後台正在運行在 port 8000

### Q2: 缺少 .env 文件
**A:** 在 `backend/` 資料夾創建 `.env` 文件，參考上面的範例

### Q3: Ollama 模型未找到
**A:** 執行 `ollama pull gemma:2b` 或 `ollama pull gemma3:4b`

### Q4: AI 回應為空
**A:** 
1. 檢查 Ollama 是否正在運行：`curl http://localhost:11434/api/tags`
2. 增加等待時間（RPG Maker 中的 "等待" 命令）
3. 查看後台日誌是否有錯誤

### Q5: CORS 錯誤
**A:** 後台已配置 CORS，如果仍有問題，檢查 `main.py` 中的 CORS 設置

---

## 📊 **系統狀態檢查**

訪問健康檢查端點：

```bash
# 通用健康檢查
curl http://localhost:8000/chat/health

# 遊戲系統健康檢查
curl http://localhost:8000/api/game/health
```

---

## 🎉 **完成！**

現在您可以在 RPG Maker 中使用完整的 AI-Agent 系統了！

### 特色功能
- ✅ 統一後台 (Port 8000)
- ✅ 完整的 AI 對話系統
- ✅ 防詐騙教育遊戲
- ✅ WebSocket 實時對話 (AI-Agent 原有功能)
- ✅ 訓練系統 (AI-Agent 原有功能)
- ✅ RPG Maker 完整支援
- ✅ Web UI 測試介面

---

**🎮 開始創建您的防詐騙教育 RPG 遊戲吧！** ✨


