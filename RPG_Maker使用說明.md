# RPG Maker 使用說明

## 📂 項目文件位置

**RPG Maker 項目文件**：
```
C:\Users\andy1\Desktop\4116M\AI-Agent-12-11-2025\AI-Agent-main\RPG_platform\RPG_Project\Game.rpgproject
```

---

## 🎮 如何用 RPG Maker 打開

### 方法1：直接雙擊打開 ✨ 最簡單

1. 找到文件：
   ```
   RPG_platform\RPG_Project\Game.rpgproject
   ```

2. 雙擊 `Game.rpgproject`

3. 應該會自動用 RPG Maker MV 或 MZ 打開

---

### 方法2：從 RPG Maker 中打開

1. 啟動 **RPG Maker MV** 或 **RPG Maker MZ**

2. 點擊 **File** → **Open Project**

3. 瀏覽到：
   ```
   C:\Users\andy1\Desktop\4116M\AI-Agent-12-11-2025\AI-Agent-main\RPG_platform\RPG_Project\
   ```

4. 選擇 `Game.rpgproject`

5. 點擊 **Open**

---

## 🔧 RPG Maker 編輯器功能

### 打開後您可以：

#### 1. **編輯地圖** 🗺️
- 設計遊戲場景
- 放置NPC角色
- 設置觸發事件

#### 2. **修改事件** 📝
- 編輯NPC對話
- 設置遊戲邏輯
- 配置訓練模式

#### 3. **管理資源** 🎨
- 添加/修改圖片
- 管理音效
- 配置插件

#### 4. **測試遊戲** 🎮
- 點擊綠色▶️按鈕
- 或按 `F12`
- 在編輯器中直接運行測試

---

## 📁 項目目錄結構

```
RPG_Project/
│
├── Game.rpgproject        ← RPG Maker 項目文件 ✨
│
├── 📁 data/               ← 遊戲數據
│   ├── Map001.json       ← 地圖數據
│   ├── Actors.json       ← 角色數據
│   ├── CommonEvents.json ← 公共事件
│   └── ...
│
├── 📁 js/                 ← JavaScript 代碼
│   ├── 📁 libs/          ← 遊戲引擎庫
│   │   ├── pixi.js       ← PIXI渲染引擎
│   │   └── ...
│   ├── 📁 plugins/       ← RPG Maker 插件
│   ├── rpg_core.js       ← 核心代碼
│   ├── rpg_managers.js   ← 管理器
│   ├── rpg_objects.js    ← 遊戲對象
│   ├── rpg_scenes.js     ← 場景
│   ├── rpg_sprites.js    ← 精靈
│   ├── rpg_windows.js    ← 窗口
│   ├── plugins.js        ← 插件配置
│   └── main.js           ← 入口文件
│
├── 📁 img/                ← 圖片資源
│   ├── 📁 characters/    ← 角色行走圖
│   ├── 📁 faces/         ← 頭像
│   ├── 📁 tilesets/      ← 地圖圖塊
│   └── ...
│
├── 📁 audio/              ← 音頻資源
│   ├── 📁 bgm/           ← 背景音樂
│   ├── 📁 bgs/           ← 背景音效
│   ├── 📁 me/            ← 音樂效果
│   └── 📁 se/            ← 音效
│
├── 📁 fonts/              ← 字體
├── 📁 icon/               ← 圖標
├── 📁 movies/             ← 視頻
│
├── index.html             ← 瀏覽器入口
├── rpg_game.html          ← 遊戲主頁面 ✨
├── test_ai_agent_v2.5.html ← 自動模擬頁面
└── test_plugin.html       ← API測試頁面
```

---

## 🎯 兩種使用方式

### 1. RPG Maker 編輯器 🔧

**用途**：開發和編輯遊戲

**打開方式**：
- 雙擊 `Game.rpgproject`
- 用 RPG Maker MV/MZ 打開

**功能**：
- 編輯地圖和事件
- 測試遊戲
- 配置插件
- 管理資源

**測試運行**：
- 按 F12 或點擊▶️
- 在編輯器內運行

---

### 2. Web 瀏覽器 🌐

**用途**：實際遊戲運行和AI功能

**打開方式**：
```bash
# 啟動後端
python backend/main.py

# 訪問網址
http://localhost:8000/
```

**功能**：
- 完整的AI對話系統
- WebSocket實時通信
- 防詐訓練功能
- 多種遊戲模式

---

## ⚙️ RPG Maker 版本

這個項目是用 **RPG Maker MV** 開發的。

### 檢查您的版本

1. 打開 RPG Maker
2. 點擊 **Help** → **About**
3. 查看版本號

### 如果沒有 RPG Maker

**下載地址**：
- 官網：https://www.rpgmakerweb.com/
- Steam：搜索 "RPG Maker MV"

---

## 🔌 重要插件說明

### AI 對話插件

位置：`js/plugins/`

這些插件負責：
- 與後端API通信
- WebSocket連接
- AI回應處理
- 訓練模式控制

**注意**：編輯插件參數時要小心，可能影響AI功能！

---

## 📝 常見操作

### 1. 編輯 NPC 對話

1. 在 RPG Maker 中打開地圖
2. 雙擊 NPC 事件
3. 編輯事件命令
4. 修改對話文本

### 2. 添加新 NPC

1. 切換到事件模式
2. 在地圖上右鍵
3. 選擇 "Create Event"
4. 設置外觀和對話

### 3. 修改地圖

1. 選擇地圖編輯工具
2. 選擇圖塊
3. 在地圖上繪製
4. 保存 (Ctrl + S)

### 4. 測試遊戲

1. 按 `F12` 鍵
2. 或點擊工具欄的▶️按鈕
3. 遊戲會在測試窗口啟動

---

## 🎮 遊戲測試 vs Web運行

### RPG Maker 測試模式

**特點**：
- 快速啟動
- 即時修改測試
- 開發者工具
- **沒有AI功能**（需要後端）

**適合**：
- 測試地圖設計
- 檢查事件邏輯
- 調試基本功能

---

### Web瀏覽器運行

**特點**：
- 需要啟動後端
- 完整AI功能
- WebSocket通信
- 所有遊戲模式

**適合**：
- 完整功能測試
- AI對話測試
- 防詐訓練演示
- 最終產品體驗

---

## 🚀 開發工作流程

### 推薦流程

```
1. 用 RPG Maker 開發
   ├─ 設計地圖
   ├─ 配置事件
   └─ 基本測試 (F12)

2. 用 Web 瀏覽器測試
   ├─ 啟動後端
   ├─ 訪問 http://localhost:8000/
   └─ 測試AI功能

3. 修改和優化
   ├─ 在 RPG Maker 中調整
   ├─ 保存項目
   └─ 刷新瀏覽器測試

4. 重複 2-3
```

---

## 💡 重要提示

### ✅ 可以在 RPG Maker 中做的

- 編輯地圖和事件
- 修改NPC外觀
- 調整對話流程
- 配置基本遊戲邏輯
- 測試地圖設計

### ❌ 需要在代碼中修改的

- AI對話生成邏輯
- WebSocket通信
- 後端API調用
- 訓練模式邏輯
- 人設和騙局配置

---

## 📋 快速檢查清單

### 開始編輯前

```
□ 已安裝 RPG Maker MV
□ 找到 Game.rpgproject 文件
□ 雙擊打開項目
□ 項目成功載入
□ 可以看到地圖編輯器
```

### 測試遊戲

```
□ 在 RPG Maker 中按 F12
  → 測試基本功能
  
□ 啟動後端服務
  → python backend/main.py
  
□ 訪問 http://localhost:8000/
  → 測試完整功能
```

---

## 🔗 相關文件

- **遊戲主頁面**：`rpg_game.html`
- **自動模擬**：`test_ai_agent_v2.5.html`
- **API測試**：`test_plugin.html`
- **系統架構**：`系統架構圖.md`
- **問題排查**：`RPG模式文件找不到問題排查.md`

---

## 🎓 學習資源

### RPG Maker MV 教程

- 官方文檔：https://www.rpgmakerweb.com/support/products/rpg-maker-mv
- 中文教程：搜索 "RPG Maker MV 教程"
- YouTube視頻教程

### JavaScript 插件開發

- 官方插件開發指南
- 社區插件範例
- RPG Maker 論壇

---

## ❓ 常見問題

### Q: 雙擊 .rpgproject 文件沒反應？

**可能原因**：
1. 未安裝 RPG Maker MV
2. 文件關聯損壞

**解決**：
- 從 RPG Maker 中用 File → Open Project 打開

---

### Q: 在 RPG Maker 中測試沒有AI對話？

**這是正常的**！

AI功能需要：
1. 後端服務運行
2. 通過瀏覽器訪問

RPG Maker 的測試模式只能測試基本功能。

---

### Q: 修改後在瀏覽器中沒變化？

**解決步驟**：
1. 在 RPG Maker 中保存 (Ctrl + S)
2. 刷新瀏覽器 (Ctrl + F5)
3. 清除瀏覽器緩存

---

### Q: 如何備份項目？

**建議**：
1. 複製整個 `RPG_Project` 文件夾
2. 使用 Git 版本控制
3. 定期壓縮備份

---

**開始編輯您的 RPG 防詐教育遊戲吧！** 🎮✨

---

*創建時間: 2025-11-17*  
*版本: v1.0*
