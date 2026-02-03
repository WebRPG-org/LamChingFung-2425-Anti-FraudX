# 🚀 快速啟動指南

## 當前狀態

✅ **開發伺服器已啟動**: http://localhost:3000/
✅ **素材生成器已打開**: 在瀏覽器中
✅ **資料夾結構已創建**: public/assets/{sprites,maps,ui}

## 📋 接下來的 3 個步驟

### 步驟 1: 下載素材 (1 分鐘)

在已打開的瀏覽器頁面中：

1. 查看生成的素材預覽
2. 點擊 **「💾 下載所有素材」** 按鈕
3. 等待 6 個 PNG 檔案下載完成

### 步驟 2: 安裝素材 (30 秒)

**選項 A - 自動安裝（推薦）**:
```powershell
cd C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2
.\move-assets.ps1
```

**選項 B - 手動安裝**:
將下載的檔案從 `Downloads` 資料夾移動到：
- `player.png`, `npc-*.png` → `public/assets/sprites/`
- `world-map.png` → `public/assets/maps/`
- `dialogue-box.png`, `button.png` → `public/assets/ui/`

### 步驟 3: 測試遊戲 (2 分鐘)

1. 打開瀏覽器訪問: http://localhost:3000/
2. 您應該看到主選單場景
3. 選擇角色（Victim/Scammer/Expert）
4. 進入世界地圖，使用 WASD 移動
5. 靠近 NPC 按空白鍵互動

## 🎮 遊戲控制

| 按鍵 | 功能 |
|------|------|
| **W/↑** | 向上移動 |
| **S/↓** | 向下移動 |
| **A/←** | 向左移動 |
| **D/→** | 向右移動 |
| **空白鍵** | 與 NPC 互動 |
| **ESC** | 返回主選單 |

## 📂 專案結構

```
rpg-platform-v2/
├── public/
│   └── assets/              ← 素材資料夾
│       ├── sprites/         ← 角色精靈圖
│       ├── maps/            ← 地圖背景
│       └── ui/              ← UI 元素
├── src/
│   ├── main.ts              ← 遊戲入口
│   ├── scenes/              ← 遊戲場景
│   │   ├── BootScene.ts     ← 載入場景
│   │   ├── MainMenuScene.ts ← 主選單
│   │   ├── WorldMapScene.ts ← 世界地圖
│   │   ├── BattleScene.ts   ← 戰鬥/對話
│   │   └── AutoModeScene.ts ← 自動觀察
│   ├── entities/            ← 遊戲實體
│   │   ├── Player.ts        ← 玩家類
│   │   └── NPC.ts           ← NPC 類
│   └── systems/             ← 遊戲系統
│       └── RoleManager.ts   ← 角色管理
├── index.html               ← HTML 入口
├── package.json             ← 依賴配置
├── tsconfig.json            ← TypeScript 配置
├── vite.config.ts           ← Vite 配置
├── generate-placeholder-assets.html  ← 素材生成器
├── move-assets.ps1          ← 自動安裝腳本
├── ASSETS_GUIDE.md          ← 素材使用指南
├── README.md                ← 完整文檔
└── IMPLEMENTATION_SUMMARY.md ← 實現總結
```

## 🔧 開發命令

```powershell
# 啟動開發伺服器（已運行）
npm run dev

# 構建生產版本
npm run build

# 預覽生產版本
npm run preview

# 安裝依賴
npm install

# 移動素材
.\move-assets.ps1
```

## ✅ 驗證清單

完成安裝後，確認以下項目：

- [ ] 開發伺服器運行在 http://localhost:3000/
- [ ] 6 個素材檔案已下載
- [ ] 素材已移動到正確的資料夾
- [ ] 瀏覽器顯示主選單場景
- [ ] 可以選擇角色並進入遊戲
- [ ] 玩家角色可以移動
- [ ] NPC 顯示在地圖上
- [ ] 可以與 NPC 互動

## 🐛 故障排除

### 問題 1: 開發伺服器沒有運行
```powershell
cd C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2
npm run dev
```

### 問題 2: 素材無法載入
1. 檢查檔案是否在正確的資料夾
2. 確認檔案名稱正確（區分大小寫）
3. 重新整理瀏覽器 (Ctrl+F5)

### 問題 3: 畫面是黑色的
1. 打開開發者工具 (F12)
2. 查看 Console 是否有錯誤
3. 確認素材已正確載入

### 問題 4: 下載的檔案找不到
檢查瀏覽器下載資料夾：
```
C:\Users\fungr\Downloads\
```

## 📚 相關文檔

- **ASSETS_GUIDE.md** - 素材使用詳細指南
- **README.md** - 完整專案文檔
- **IMPLEMENTATION_SUMMARY.md** - 技術實現總結
- **PROPOSAL_2D_RPG_PLATFORM_OPTION_B.md** - 原始提案文檔

## 🎯 下一步開發

素材安裝完成後，您可以：

1. **整合後端 API**
   - 連接現有的 AI 反詐騙後端 (http://localhost:8000)
   - 實現 WebSocket 通訊
   - 整合 AI 對話系統

2. **添加遊戲功能**
   - 實現語音輸入/輸出
   - 添加保存/載入系統
   - 創建更多場景和 NPC

3. **優化體驗**
   - 添加音效和背景音樂
   - 實現動畫效果
   - 優化 UI/UX

4. **替換專業素材**
   - 使用專業的像素藝術
   - 添加更多角色和場景
   - 創建完整的遊戲世界

## 💡 提示

- 使用 **F12** 打開開發者工具查看日誌
- 修改代碼後會自動熱重載
- 素材更新後需要重新整理瀏覽器
- 建議使用 Chrome 或 Edge 瀏覽器

---

**準備好了嗎？** 執行步驟 1-3，開始體驗您的 2D RPG 平台！🎮
