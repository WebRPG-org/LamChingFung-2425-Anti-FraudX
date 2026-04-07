# ✅ Phase 3 & 4 完整實現計畫

## 📋 Phase 3：優化與改進

### Phase 3.1：專家口語化

#### 3.1.1 更新ExpertAgent System Prompt
```python
# backend/services/expert_agent.py

EXPERT_SYSTEM_PROMPT_V2 = """
你是一位防詐騙專家。你的目標是幫助受害者識別詐騙並提供防騙建議。

重要要求：
1. 使用自然對話風格，不要使用格式化標記（如【分析】、**加粗**等）
2. 直接說出你的想法，就像和朋友聊天一樣
3. 例如：「呢個係詐騙嚟，你聽我講...」而不是「【分析】這是詐騙」
4. 保持親切、友好的語氣
5. 給出具體的防騙建議

防騙方向：
- 識別冒充身份
- 識別虛假承諾
- 識別緊急壓力
- 識別要求敏感信息
- 識別可疑鏈接或轉賬

回應時：
1. 先表達同情和理解
2. 指出詐騙跡象
3. 給出具體建議
4. 鼓勵採取行動
"""
```

#### 3.1.2 實現口語化處理
```python
# backend/services/response_processor.py

async def apply_conversational_style(response: str) -> str:
    """應用口語化風格"""
    
    # 移除格式化標記
    response = response.replace('【', '').replace('】', '')
    response = response.replace('**', '').replace('__', '')
    response = response.replace('##', '').replace('###', '')
    
    # 轉換為口語
    conversions = {
        '這是詐騙': '呢個係詐騙嚟',
        '分析：': '',
        '建議：': '',
        '警告：': '',
        '注意：': '你要留意',
    }
    
    for formal, casual in conversions.items():
        response = response.replace(formal, casual)
    
    return response
```

### Phase 3.2：回應長度控制

#### 3.2.1 智能截斷實現
```python
# backend/services/response_processor.py

async def smart_truncate(response: str, max_length: int = 80) -> str:
    """智能截斷回應，保留完整句子"""
    
    if len(response) <= max_length:
        return response
    
    # 在max_length處截斷
    truncated = response[:max_length]
    
    # 找到最後一個完整句子
    last_period = truncated.rfind('。')
    last_comma = truncated.rfind('，')
    last_space = truncated.rfind(' ')
    
    # 優先選擇句號
    if last_period > max_length * 0.7:
        return truncated[:last_period + 1]
    elif last_comma > max_length * 0.7:
        return truncated[:last_comma + 1]
    elif last_space > max_length * 0.7:
        return truncated[:last_space]
    else:
        return truncated
```

#### 3.2.2 Token計數驗證
```python
# backend/services/token_counter.py

async def count_tokens(text: str) -> int:
    """計算Token數量"""
    # 使用tiktoken或類似庫
    import tiktoken
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(text)
    return len(tokens)

async def validate_response_length(response: str, max_tokens: int = 100) -> bool:
    """驗證回應長度"""
    token_count = await count_tokens(response)
    return token_count <= max_tokens
```

### Phase 3.3：系統集成測試

#### 3.3.1 集成測試清單
```bash
# 1. Session隔離測試
POST /api/rag/session/initialize
{
  "session_id": "test_session_1",
  "scam_type": "phone_scam",
  "player_role": "victim"
}

# 2. RAG集成測試
GET /api/rag/context/scammer/phone_scam
GET /api/rag/warning-signs/phone_scam

# 3. 騙術分析測試
POST /api/evaluation/tactic/analyze
{
  "message": "我是銀行客服",
  "role": "scammer"
}

# 4. 勝負判定測試
POST /api/evaluation/verdict/judge
{
  "message": "我的銀行密碼是 123456",
  "role": "victim"
}

# 5. 評分系統測試
POST /api/evaluation/score/update
{
  "session_id": "test_session_1",
  "victim_response": "我完全相信你",
  "role": "scammer"
}

# 6. 完整對話流程測試
POST /api/rag/message/send
{
  "message": "你好，我是銀行客服",
  "role": "scammer"
}

# 7. 評估測試
POST /api/rag/dialogue/evaluate
{
  "session_id": "test_session_1"
}

# 8. 報告測試
GET /api/rag/dialogue/report/test_session_1
```

#### 3.3.2 性能測試
```bash
# 測試API響應時間
time curl http://localhost:8080/api/rag/status

# 測試並發請求
for i in {1..10}; do
  curl -X POST http://localhost:8080/api/rag/message/send \
    -H "Content-Type: application/json" \
    -d '{"message":"test","role":"scammer"}' &
done
wait

# 測試Firestore查詢性能
GET /api/rag/dialogue/report/test_session_1
```

---

## 📋 Phase 4：部署與上線

### Phase 4.1：代碼審查與優化

#### 4.1.1 代碼審查清單
```
✅ 檢查所有新代碼的質量
✅ 檢查錯誤處理
✅ 檢查日誌記錄
✅ 檢查安全性
✅ 檢查性能
✅ 檢查文檔
```

#### 4.1.2 性能優化
```python
# 1. 優化LLM調用
- 使用緩存減少重複調用
- 批量處理請求
- 使用異步調用

# 2. 優化Firestore查詢
- 添加索引
- 使用分頁
- 使用緩存

# 3. 優化內存使用
- 清理過期Session
- 使用流式處理大數據
- 優化數據結構
```

### Phase 4.2：預發布測試

#### 4.2.1 灰度測試
```bash
# 部署到測試環境
gcloud run deploy anti-fraudx-backend-test \
  --image us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:test \
  --region us-central1 \
  --allow-unauthenticated

# 運行功能測試
pytest backend/tests/test_rag_integration.py -v
pytest backend/tests/test_evaluation_system.py -v

# 運行性能測試
locust -f backend/tests/load_test.py --host=http://localhost:8080
```

#### 4.2.2 用戶驗收測試
```
測試場景：
1. 完整遊戲流程
2. 多個並發Session
3. 長時間運行穩定性
4. 錯誤恢復能力
```

#### 4.2.3 安全測試
```
安全審計：
- 檢查認證機制
- 檢查授權機制
- 檢查數據加密
- 檢查SQL注入防護
- 檢查XSS防護

數據隱私檢查：
- 檢查敏感數據加密
- 檢查訪問控制
- 檢查審計日誌
```

### Phase 4.3：正式部署

#### 4.3.1 部署準備
```bash
# 1. 準備部署計畫
- 確定部署時間
- 準備回滾方案
- 準備監控方案
- 準備通知計畫

# 2. 檢查清單
✅ 所有測試通過
✅ 代碼審查完成
✅ 文檔完善
✅ 監控配置完成
✅ 告警規則配置完成
```

#### 4.3.2 正式部署
```bash
# 執行部署指令
cd /path/to/AI-Agent-main

# 後端部署
gcloud builds submit --tag us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:v1.0
gcloud run deploy anti-fraudx-backend \
  --image us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:v1.0 \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 3600 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=anti-fraudx,VERTEX_AI_MODEL=gemini-2.5-flash,GCP_LOCATION=us-central1,AUTO_LOAD_ON_STARTUP=true,FIRESTORE_PROJECT_ID=anti-fraudx,TACTIC_ANALYZER_ENABLED=true,VERDICT_JUDGE_ENABLED=true,SCAM_SCORER_ENABLED=true

# 前端部署
cd frontend
gcloud builds submit --tag us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-frontend:v1.0
cd ..
gcloud run deploy anti-fraudx-frontend \
  --image us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-frontend:v1.0 \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080

# 驗證部署
BACKEND_URL=$(gcloud run services describe anti-fraudx-backend --region us-central1 --format="value(status.url)")
curl "$BACKEND_URL/health"
curl "$BACKEND_URL/rag/status"
```

#### 4.3.3 上線後支持
```bash
# 1. 監控系統運行
- 監控API響應時間
- 監控錯誤率
- 監控Firestore使用量
- 監控Cloud Run資源使用

# 2. 收集用戶反饋
- 監控用戶報告的問題
- 收集性能反饋
- 收集功能反饋

# 3. 進行問題修復
- 快速響應用戶問題
- 發布補丁更新
- 持續優化性能
```

---

## 📊 部署時間表

| Phase | 任務 | 預計時間 | 狀態 |
|-------|------|---------|------|
| 3.1 | 專家口語化 | 1天 | ⏳ |
| 3.2 | 回應長度控制 | 1天 | ⏳ |
| 3.3 | 系統集成測試 | 2天 | ⏳ |
| 4.1 | 代碼審查與優化 | 1天 | ⏳ |
| 4.2 | 預發布測試 | 2天 | ⏳ |
| 4.3 | 正式部署 | 1天 | ⏳ |

**總計：約8天**

---

## ✅ 完成檢查清單

### Phase 3完成後
- [ ] 專家口語化已實現
- [ ] 回應長度控制已實現
- [ ] 所有集成測試通過
- [ ] 性能測試通過
- [ ] 用戶體驗測試通過

### Phase 4完成後
- [ ] 代碼審查完成
- [ ] 灰度測試通過
- [ ] 用戶驗收測試通過
- [ ] 安全測試通過
- [ ] 正式部署完成
- [ ] 監控系統運行正常

---

## 🎉 系統完整功能

所有Phase完成後，系統將具備：

✅ **完整的RAG系統**
- 真實騙案數據庫
- 智能上下文檢索
- 動態System Instruction注入

✅ **智能的騙術分析**
- LLM分析騙術方向
- 動態評分系統
- 防騙方向識別

✅ **精準的勝負判定**
- LLM智能分析
- 上下文語境理解
- 信心度計算

✅ **動態的評分系統**
- 基於受害者反應
- 騙徒信用度計算
- 專家信用度計算
- 警覺性動態計算

✅ **完整的評估系統**
- 受害者評估
- 騙徒評估
- 專家評估
- 三角評估

✅ **自然的對話風格**
- 口語化表達
- 移除格式化標記
- 親切友好的語氣

✅ **優化的性能**
- 回應長度控制
- Token優化
- 並發支持

✅ **完善的部署**
- Docker自動化
- Cloud Run部署
- 監控告警系統

---

## 🚀 立即開始

### 執行部署指令
```bash
# 從command.sh執行部署
bash command.sh
```

### 驗證系統
```bash
# 檢查健康狀態
curl $BACKEND_URL/health

# 檢查RAG系統
curl $BACKEND_URL/rag/status

# 檢查評估系統
curl $BACKEND_URL/api/evaluation/status
```

---

**Phase 3 & 4計畫完成日期**：2026-03-16
**預計上線日期**：2026-03-24
**狀態**：✅ 準備就緒


