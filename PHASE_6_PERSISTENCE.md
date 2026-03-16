# 💾 AI 防詐平台 v4.1 - 第六階段：會話持久化

**階段**: 第六階段  
**開始日期**: 2025-03-16  
**預計完成**: 1 天  
**狀態**: ⏳ 計劃中

---

## 📋 階段目標

實現完整的會話持久化和數據管理，支持會話恢復、數據導出和分析。

### 主要任務

1. ⏳ 實現 Firestore 持久化
2. ⏳ 實現會話恢復
3. ⏳ 實現數據導出
4. ⏳ 實現數據分析

---

## 📊 持久化架構

### 數據存儲層次

```
Firestore (雲端持久化)
    ↓
Session Collection
    ├── session_id
    ├── persona_type
    ├── scam_type
    ├── created_at
    ├── updated_at
    ├── status
    └── metadata

Conversation Collection
    ├── session_id
    ├── round_number
    ├── speaker (scammer/victim/expert)
    ├── message
    ├── timestamp
    └── metrics

Analysis Collection
    ├── session_id
    ├── outcome
    ├── scammer_score
    ├── expert_score
    ├── trust_trajectory
    └── improvement_suggestions
```

---

## 🔧 實施計劃

### 1. Firestore 服務層（預計 3 小時）

**文件**: `backend/services/firestore_persistence_service.py`

**功能**:
- [ ] 初始化 Firestore 連接
- [ ] 實現 Session 保存
- [ ] 實現 Conversation 保存
- [ ] 實現 Analysis 保存
- [ ] 實現數據查詢

**代碼框架**:

```python
class FirestorePersistenceService:
    def __init__(self):
        # 初始化 Firestore
        pass
    
    async def save_session(self, session_data):
        # 保存會話
        pass
    
    async def save_conversation(self, session_id, conversation):
        # 保存對話
        pass
    
    async def save_analysis(self, session_id, analysis):
        # 保存分析結果
        pass
    
    async def get_session(self, session_id):
        # 獲取會話
        pass
    
    async def get_conversations(self, session_id):
        # 獲取對話歷史
        pass
    
    async def get_analysis(self, session_id):
        # 獲取分析結果
        pass
    
    async def list_sessions(self, user_id=None):
        # 列出所有會話
        pass
    
    async def export_session(self, session_id, format='json'):
        # 導出會話數據
        pass
```

### 2. 會話恢復（預計 2 小時）

**文件**: `backend/services/session_recovery_service.py`

**功能**:
- [ ] 實現會話恢復
- [ ] 實現狀態恢復
- [ ] 實現上下文恢復
- [ ] 實現錯誤恢復

**代碼框架**:

```python
class SessionRecoveryService:
    async def recover_session(self, session_id):
        # 恢復會話
        pass
    
    async def restore_state(self, session_id):
        # 恢復狀態
        pass
    
    async def restore_context(self, session_id):
        # 恢復上下文
        pass
    
    async def handle_recovery_error(self, session_id, error):
        # 處理恢復錯誤
        pass
```

### 3. 數據導出（預計 2 小時）

**文件**: `backend/services/data_export_service.py`

**功能**:
- [ ] 導出為 JSON
- [ ] 導出為 CSV
- [ ] 導出為 PDF
- [ ] 導出為 Excel

**支持格式**:
- JSON - 完整數據結構
- CSV - 對話記錄表格
- PDF - 分析報告
- Excel - 多工作表數據

### 4. 數據分析（預計 2 小時）

**文件**: `backend/services/data_analytics_service.py`

**功能**:
- [ ] 統計分析
- [ ] 趨勢分析
- [ ] 對比分析
- [ ] 報告生成

**分析指標**:
- 總會話數
- 平均遊戲時長
- 成功率
- 騙徒平均評分
- 專家平均評分
- 信任度變化趨勢

---

## 📁 數據結構

### Session 文檔

```json
{
  "session_id": "uuid",
  "user_id": "user_uuid",
  "persona_type": "elderly",
  "scam_type": "banking",
  "game_mode": "full",
  "created_at": "2025-03-16T10:00:00Z",
  "updated_at": "2025-03-16T10:30:00Z",
  "status": "completed",
  "metadata": {
    "duration_seconds": 1800,
    "round_count": 10,
    "final_outcome": "FAILURE"
  }
}
```

### Conversation 文檔

```json
{
  "session_id": "uuid",
  "round_number": 1,
  "speaker": "scammer",
  "message": "你好，我係銀行職員",
  "timestamp": "2025-03-16T10:00:05Z",
  "metrics": {
    "message_length": 15,
    "sentiment": "neutral",
    "confidence": 0.95
  }
}
```

### Analysis 文檔

```json
{
  "session_id": "uuid",
  "outcome": "FAILURE",
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
  },
  "victim_trust_analysis": {
    "initial_trust_level": 70,
    "peak_trust_level": 95,
    "final_trust_level": 30,
    "trust_trajectory": "先上升後下降"
  },
  "improvement_suggestions": "..."
}
```

---

## 🔄 集成流程

### 保存流程

```
遊戲進行中
    ↓
每條消息後
    ↓
保存到 Firestore
    ├── Session 更新
    ├── Conversation 保存
    └── 實時同步
```

### 恢復流程

```
用戶打開應用
    ↓
檢查未完成的會話
    ↓
恢復會話狀態
    ├── 恢復對話歷史
    ├── 恢復遊戲狀態
    └── 恢復上下文
    ↓
繼續遊戲
```

### 分析流程

```
遊戲結束
    ↓
生成分析結果
    ↓
保存到 Firestore
    ├── Analysis 文檔
    ├── 統計數據
    └── 改進建議
    ↓
用戶查看報告
```

---

## 📊 API 端點

### 會話管理

- `GET /api/sessions` - 列出所有會話
- `GET /api/sessions/{session_id}` - 獲取會話詳情
- `POST /api/sessions/{session_id}/recover` - 恢復會話
- `DELETE /api/sessions/{session_id}` - 刪除會話

### 數據導出

- `GET /api/sessions/{session_id}/export?format=json` - 導出為 JSON
- `GET /api/sessions/{session_id}/export?format=csv` - 導出為 CSV
- `GET /api/sessions/{session_id}/export?format=pdf` - 導出為 PDF
- `GET /api/sessions/{session_id}/export?format=excel` - 導出為 Excel

### 數據分析

- `GET /api/analytics/summary` - 獲取統計摘要
- `GET /api/analytics/trends` - 獲取趨勢數據
- `GET /api/analytics/comparison` - 獲取對比數據
- `GET /api/analytics/report` - 生成分析報告

---

## 🎯 實施檢查清單

### Firestore 服務

- [ ] 初始化 Firestore 連接
- [ ] 實現 Session 保存
- [ ] 實現 Conversation 保存
- [ ] 實現 Analysis 保存
- [ ] 實現數據查詢
- [ ] 實現批量操作
- [ ] 實現事務支持

### 會話恢復

- [ ] 實現會話恢復
- [ ] 實現狀態恢復
- [ ] 實現上下文恢復
- [ ] 實現錯誤恢復
- [ ] 實現超時處理

### 數據導出

- [ ] JSON 導出
- [ ] CSV 導出
- [ ] PDF 導出
- [ ] Excel 導出
- [ ] 自定義格式

### 數據分析

- [ ] 統計分析
- [ ] 趨勢分析
- [ ] 對比分析
- [ ] 報告生成
- [ ] 可視化

---

## 📈 預期結果

### 功能完整性

- ✅ 完整的會話持久化
- ✅ 會話恢復功能
- ✅ 多格式數據導出
- ✅ 完整的數據分析

### 性能指標

- 保存延遲: < 100ms
- 恢復時間: < 500ms
- 導出時間: < 2s
- 查詢時間: < 1s

### 數據安全

- ✅ 加密存儲
- ✅ 訪問控制
- ✅ 備份恢復
- ✅ 審計日誌

---

## 📚 相關文檔

- `PHASE_6_PERSISTENCE.md` - 持久化詳細指南
- `IMPLEMENTATION_COMPLETE_v4.1.md` - 完整實施報告
- `QUICK_REFERENCE_v4.1.md` - 快速參考指南

---

## 🎉 最終成果

完成本階段後，AI 防詐平台 v4.1 將具備：

✅ **完整的四代理系統** - 騙徒、專家、受害者、記錄員  
✅ **動態信任度系統** - 實時追蹤和變化  
✅ **多維度性能評分** - 深入分析和改進建議  
✅ **高效並行生成** - 性能提升 50-70%  
✅ **完整的會話管理** - 創建、恢復、分析  
✅ **多格式數據導出** - JSON、CSV、PDF、Excel  
✅ **完整的數據分析** - 統計、趨勢、對比  

---

**階段狀態**: ⏳ 計劃中  
**最後更新**: 2025-03-16  
**版本**: 4.1.0

