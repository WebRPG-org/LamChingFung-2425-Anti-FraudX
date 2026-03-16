# AI 防詐騙訓練系統 - 2D RPG 平台 (Option B)

**版本:** 1.0.0  
**狀態:** 🚀 原型已完成  
**技術棧:** Phaser.js + TypeScript + Vite

---

## 📋 項目概述

這是一個基於 Phaser.js 的 2D RPG 平台，用於 AI 防詐騙訓練。玩家可以在開放世界中自由探索，與 NPC 互動，並通過角色扮演學習防詐騙知識。

### 核心特性

✅ **動態角色切換** - 隨時在受害者、騙徒、專家之間切換  
✅ **開放世界探索** - 自由移動，尋找 NPC 互動  
✅ **實時對話系統** - 與 AI 代理進行多輪對話  
✅ **自動模式** - AI 自動運行訓練模擬  
✅ **現代化 UI** - 流暢的動畫和響應式設計  

---

## 🚀 快速開始

### 前置要求

- Node.js 18+ 
- npm 或 yarn
- 現代瀏覽器（Chrome, Firefox, Edge）

### 安裝步驟

```bash
# 1. 進入項目目錄
cd rpg-platform-v2

# 2. 安裝依賴
npm install

# 3. 啟動開發服務器
npm run dev

# 4. 打開瀏覽器訪問
# http://localhost:3000
```

### 構建生產版本

```bash
# 構建
npm run build

# 預覽構建結果
npm run preview
```

---

## 🎮 遊戲操作

### 主選單
- **點擊角色卡片** - 選擇你的角色（受害者/騙徒/專家）
- **點擊自動模式** - 進入 AI 自動訓練模式

### 世界地圖
- **方向鍵 / WASD** - 移動角色
- **E 鍵** - 與附近的 NPC 互動
- **1/2/3 鍵** - 快速切換角色
- **ESC 鍵** - 返回主選單

### 對話場景
- **輸入文字** - 在輸入框中輸入回應
- **Enter / 點擊發送** - 發送訊息
- **返回按鈕** - 結束對話，返回世界地圖

### 自動模式
- **開始按鈕** - 啟動自動模擬
- **停止按鈕** - 暫停自動模擬
- **返回按鈕** - 返回主選單

---

## 📁 項目結構

```
rpg-platform-v2/
├── src/
│   ├── main.ts                 # 遊戲入口
│   ├── scenes/                 # 遊戲場景
│   │   ├── BootScene.ts        # 啟動場景（資源加載）
│   │   ├── MainMenuScene.ts    # 主選單
│   │   ├── WorldMapScene.ts    # 世界地圖
│   │   ├── BattleScene.ts      # 對話場景
│   │   └── AutoModeScene.ts    # 自動模式
│   ├── entities/               # 遊戲實體
│   │   ├── Player.ts           # 玩家角色
│   │   └── NPC.ts              # NPC 角色
│   ├── systems/                # 遊戲系統
│   │   └── RoleManager.ts      # 角色管理器
│   └── api/                    # 後端 API 集成
│       └── BackendClient.ts    # （待實現）
├── public/
│   └── assets/                 # 遊戲資源
├── index.html                  # HTML 入口
├── package.json                # 依賴配置
├── tsconfig.json               # TypeScript 配置
├── vite.config.ts              # Vite 配置
└── README.md                   # 本文件
```

---

## 🎨 角色系統

### 🛡️ 受害者（Victim）
- **顏色:** 藍色 (#0984E3)
- **目標:** 識別詐騙手法，保護自己
- **對手:** 騙徒 AI、專家 AI、記錄員 AI

### 🎭 騙徒（Scammer）
- **顏色:** 紅色 (#FF6B6B)
- **目標:** 使用心理戰術操縱受害者
- **對手:** 受害者 AI、專家 AI、記錄員 AI

### 👮 防詐專家（Expert）
- **顏色:** 綠色 (#00B894)
- **目標:** 介入詐騙，教育受害者
- **對手:** 騙徒 AI、受害者 AI、記錄員 AI

---

## 🔧 技術細節

### 核心技術

- **遊戲引擎:** Phaser 3.60.0
- **語言:** TypeScript 5.0
- **構建工具:** Vite 5.0
- **狀態管理:** Zustand 4.4

### 性能優化

- ✅ 使用 WebGL 渲染
- ✅ 精靈圖集優化
- ✅ 按需加載資源
- ✅ 對象池管理

### 瀏覽器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 🔌 後端集成

### API 端點

```typescript
// 啟動模擬
POST /api/simulation/start
{
  "victim_persona": "elderly",
  "scam_tactic": "investment",
  "mode": "fast",
  "player_role": "victim"
}

// WebSocket 連接
WS /ws/simulation/{simulation_id}
```

### 集成步驟

1. 確保後端服務運行在 `http://localhost:8000`
2. Vite 會自動代理 API 請求
3. WebSocket 連接會自動建立

---

## 📊 開發狀態

### ✅ 已完成

- [x] 基礎遊戲引擎設置
- [x] 主選單場景
- [x] 世界地圖場景
- [x] 角色移動系統
- [x] NPC 互動系統
- [x] 角色切換系統
- [x] 對話場景（基礎版）
- [x] 自動模式場景（基礎版）

### 🚧 進行中

- [ ] 後端 API 集成
- [ ] 真實 AI 對話
- [ ] 信任度系統
- [ ] 語音輸入/輸出

### 📋 待開發

- [ ] 完整的地圖設計
- [ ] 更多 NPC 類型
- [ ] 成就系統
- [ ] 數據統計面板
- [ ] 音效和背景音樂
- [ ] 移動端適配

---

## 🎯 下一步計劃

### Phase 1: 完善核心功能（本週）
1. 集成後端 API
2. 實現真實 AI 對話
3. 添加信任度顯示
4. 優化 UI/UX

### Phase 2: 增強遊戲性（下週）
1. 設計完整地圖
2. 添加更多 NPC
3. 實現成就系統
4. 添加音效

### Phase 3: 高級功能（第三週）
1. 語音輸入/輸出
2. 自動模式完整實現
3. 數據分析面板
4. 性能優化

---

## 🐛 已知問題

1. **對話場景** - 目前使用模擬回應，需要集成真實 AI
2. **自動模式** - 統計數據為模擬數據，需要連接後端
3. **資源** - 使用佔位符圖形，需要設計師提供真實資源

---

## 🤝 貢獻指南

### 開發流程

1. Fork 本項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 代碼規範

- 使用 TypeScript 嚴格模式
- 遵循 ESLint 規則
- 添加適當的註釋
- 編寫單元測試

---

## 📝 更新日誌

### v1.0.0 (2026-02-04)
- 🎉 初始版本發布
- ✨ 實現核心遊戲循環
- ✨ 添加角色切換系統
- ✨ 創建基礎場景

---

## 📄 授權

本項目採用 MIT 授權 - 詳見 LICENSE 文件

---

## 👥 團隊

- **開發:** AI Anti-Scam Team
- **設計:** 待定
- **測試:** 待定

---

## 📞 聯繫方式

- **問題反饋:** GitHub Issues
- **功能建議:** GitHub Discussions
- **緊急聯繫:** [待定]

---

## 🙏 致謝

- Phaser.js 社區
- TypeScript 團隊
- Vite 開發團隊

---

**準備好開始了嗎？運行 `npm run dev` 開始你的防詐騙訓練之旅！** 🚀
