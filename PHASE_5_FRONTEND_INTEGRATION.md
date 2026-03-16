# 🎨 AI 防詐平台 v4.1 - 第五階段：前端集成

**階段**: 第五階段  
**開始日期**: 2025-03-16  
**預計完成**: 1 天  
**狀態**: ⏳ 進行中

---

## 📋 階段目標

將所有 v4.1 改進功能集成到前端，提供完整的用戶界面和交互體驗。

### 主要任務

1. ✅ 更新 API 路由以支持並行生成
2. ⏳ 更新前端 UI 以顯示信任度變化
3. ⏳ 更新前端 UI 以顯示性能評分
4. ⏳ 集成實時數據更新

---

## ✅ 已完成

### 1. API 路由更新 ✅

**文件**: `backend/api/game_routes_v2.py`

#### 新增端點

1. **POST /api/rpgv2/game/action** ✅
   - 同時生成騙徒和專家的回應
   - 返回遊戲狀態和信任度數據
   - 支持並行生成

2. **POST /api/rpgv2/game/analyze** ✅
   - 使用 RecorderAgent 分析會話
   - 返回詳細的性能評分
   - 支持多維度分析

3. **GET /api/rpgv2/game/scam-types** ✅
   - 獲取所有騙案類型列表
   - 返回騙案信息和危險等級

4. **GET /api/rpgv2/game/modes** ✅
   - 獲取可用的遊戲模式
   - 返回模式描述和難度

5. **POST /api/rpgv2/game/auto-play** ✅
   - 自動播放模式
   - 模擬多輪對話

6. **GET /api/rpgv2/game/state/{session_id}** ✅
   - 獲取遊戲狀態
   - 返回信任度和評分數據

#### 改進的端點

1. **POST /api/rpgv2/game/start** 改進
   - ✅ 支持騙案類型選擇
   - ✅ 返回初始信任度
   - ✅ 返回遊戲狀態

2. **POST /api/rpgv2/game/message** 改進
   - ✅ 集成 AgentService
   - ✅ 返回信任度數據
   - ✅ 返回性能指標

---

## ⏳ 下一步計劃

### 1. 前端 UI 更新（預計 4 小時）

**任務**:
- [ ] 添加信任度顯示組件
- [ ] 添加性能評分顯示組件
- [ ] 添加實時數據更新
- [ ] 添加動畫效果

**文件**: `frontend/src/components/`

### 2. 數據綁定（預計 2 小時）

**任務**:
- [ ] 綁定信任度數據
- [ ] 綁定評分數據
- [ ] 綁定遊戲狀態
- [ ] 實現實時更新

**文件**: `frontend/src/pages/Game.tsx`

### 3. 樣式優化（預計 2 小時）

**任務**:
- [ ] 優化信任度顯示樣式
- [ ] 優化評分顯示樣式
- [ ] 添加動畫效果
- [ ] 響應式設計

**文件**: `frontend/src/styles/`

---

## 📊 API 數據結構

### 遊戲狀態數據

```json
{
  "game_state": {
    "round_count": 1,
    "player_score": 0,
    "ai_score": 0,
    "trust_in_scammer": 70,
    "trust_in_expert": 50,
    "alertness": 30
  }
}
```

### 信任度數據

```json
{
  "trust_in_scammer": 70,      // 對騙徒的信任度 (0-100)
  "trust_in_expert": 50,       // 對專家的信任度 (0-100)
  "alertness": 30              // 警覺度 (0-100)
}
```

### 性能評分數據

```json
{
  "scammer_performance": {
    "persuasiveness": 75,
    "credibility": 80,
    "pressure_effectiveness": 70,
    "strategy_consistency": 85,
    "overall_score": 78
  },
  "expert_performance": {
    "intervention_effectiveness": 60,
    "clarity": 70,
    "empathy": 65,
    "actionability": 55,
    "timing": 50,
    "overall_score": 60
  }
}
```

---

## 🎨 前端組件設計

### 1. 信任度顯示組件

```typescript
// TrustMeter.tsx
interface TrustMeterProps {
  trustInScammer: number;      // 0-100
  trustInExpert: number;       // 0-100
  alertness: number;           // 0-100
}

// 顯示三個進度條
// - 紅色：對騙徒的信任度
// - 綠色：對專家的信任度
// - 黃色：警覺度
```

### 2. 性能評分組件

```typescript
// PerformanceScore.tsx
interface PerformanceScoreProps {
  scammerScore: number;        // 0-100
  expertScore: number;         // 0-100
  details?: {
    persuasiveness: number;
    credibility: number;
    // ... 其他維度
  }
}

// 顯示雷達圖或柱狀圖
```

### 3. 遊戲狀態組件

```typescript
// GameStatus.tsx
interface GameStatusProps {
  roundCount: number;
  playerScore: number;
  aiScore: number;
  gameOver: boolean;
  winner?: string;
}

// 顯示當前回合、分數、遊戲狀態
```

---

## 📱 前端頁面流程

### 遊戲開始頁面

1. 選擇受害者人格
2. 選擇騙案類型
3. 選擇遊戲模式
4. 點擊開始遊戲

### 遊戲進行頁面

1. 顯示騙徒開場白
2. 玩家輸入回應
3. 顯示騙徒和專家的回應
4. 實時更新信任度
5. 實時更新遊戲狀態

### 遊戲結束頁面

1. 顯示最終結果
2. 顯示性能評分
3. 顯示改進建議
4. 選擇重新開始或返回

---

## 🔄 數據流

```
前端 → API /game/action
  ↓
AgentService.generate_parallel_responses()
  ↓
騙徒回應 + 專家回應 + 遊戲狀態
  ↓
API → 前端
  ↓
更新 UI（信任度、評分、狀態）
```

---

## 📊 實時更新機制

### 方式 1: 輪詢（Polling）

```typescript
// 每 500ms 更新一次
setInterval(() => {
  fetchGameState(sessionId);
}, 500);
```

### 方式 2: WebSocket

```typescript
// 實時推送更新
socket.on('game-state-update', (data) => {
  updateGameState(data);
});
```

### 方式 3: Server-Sent Events (SSE)

```typescript
// 服務器推送事件
const eventSource = new EventSource(`/api/game/stream/${sessionId}`);
eventSource.onmessage = (event) => {
  updateGameState(JSON.parse(event.data));
};
```

---

## 🎯 前端集成檢查清單

### UI 組件

- [ ] 信任度顯示組件
- [ ] 性能評分組件
- [ ] 遊戲狀態組件
- [ ] 對話顯示組件
- [ ] 輸入框組件

### 數據綁定

- [ ] 信任度數據綁定
- [ ] 評分數據綁定
- [ ] 遊戲狀態綁定
- [ ] 對話歷史綁定

### 交互功能

- [ ] 發送消息功能
- [ ] 遊戲開始功能
- [ ] 遊戲結束功能
- [ ] 分析結果功能

### 樣式和動畫

- [ ] 信任度動畫
- [ ] 評分動畫
- [ ] 過渡效果
- [ ] 響應式設計

---

## 📚 相關文檔

- `PHASE_5_FRONTEND_INTEGRATION.md` - 前端集成詳細指南
- `IMPLEMENTATION_COMPLETE_v4.1.md` - 完整實施報告
- `QUICK_REFERENCE_v4.1.md` - 快速參考指南

---

## 🎉 下一步

完成本階段後，將進入**第六階段：會話持久化**

---

**階段狀態**: ⏳ 進行中  
**最後更新**: 2025-03-16  
**版本**: 4.1.0

