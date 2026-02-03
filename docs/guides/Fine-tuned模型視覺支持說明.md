# Fine-tuned 模型視覺支持說明

## 🔍 當前問題

使用 `anti-fraud-expert-20251117_173453` fine-tuned 模型時，圖片分析功能不正常：
- ❌ 回應語無倫次
- ❌ 沒有結構化輸出
- ❌ 無法正確分析圖片內容

**原因**：Fine-tuning 過程可能導致視覺功能丟失或退化。

---

## 💡 解決方案

### 方案 1: 使用 Base Model（立即可用）

**優點**：
- ✅ 完整的視覺功能
- ✅ 立即可用
- ✅ 回應質量穩定

**缺點**：
- ❌ 沒有專門的防詐騙訓練
- ❌ 回應風格可能不夠本地化

**使用方法**：
```bash
# 方法 1: 使用測試腳本（推薦）
測試視覺功能_使用base模型.bat

# 方法 2: 修改 .env 文件
# 將 AGENT_MODEL_EXPERT 改為 gemma3:4b
AGENT_MODEL_EXPERT=gemma3:4b
```

---

### 方案 2: 混合模式（推薦）

**策略**：根據是否有圖片，動態選擇模型

**實現方法**：

#### 修改 `personal_chat_routes.py`

```python
# 根據是否有圖片選擇模型
if image_base64_list:
    # 有圖片：使用 base model（視覺功能完整）
    agent_service_vision = AgentService(persona_type="average", enable_tracking=False)
    # 臨時覆蓋 expert 模型
    from agents.expert import ExpertAgent
    agent_service_vision.expert = ExpertAgent()
    agent_service_vision.expert.model.model = "gemma3:4b"
    
    response = await agent_service_vision.generate_response(
        agent_type="expert",
        message=context_message,
        conversation_history=session["history"],
        images=image_base64_list,
        check_consistency=False,
        track_performance=False
    )
else:
    # 無圖片：使用 fine-tuned model（防詐騙專業）
    response = await agent_service.generate_response(
        agent_type="expert",
        message=context_message,
        conversation_history=session["history"],
        check_consistency=False,
        track_performance=False
    )
```

**優點**：
- ✅ 圖片分析使用視覺功能完整的 base model
- ✅ 文字對話使用專業的 fine-tuned model
- ✅ 兩全其美

---

### 方案 3: 重新訓練（長期方案）

**目標**：訓練一個既支持視覺又有防詐騙專業知識的模型

**挑戰**：
1. **視覺數據收集** - 需要大量詐騙圖片樣本
2. **訓練方法** - Ollama fine-tuning 可能不支持視覺
3. **模型選擇** - 需要支持多模態的 base model

**可行性**：
- ⚠️ Ollama 的 fine-tuning 主要針對文字
- ⚠️ 視覺功能可能無法通過簡單 fine-tuning 保留
- ⚠️ 需要更複雜的訓練流程

**替代方案**：
- 使用 Google Gemini API（完整多模態支持）
- 使用 OpenAI GPT-4 Vision
- 保持 base model + 優化提示詞

---

## 🎯 推薦方案

### 短期（立即使用）

**使用 Base Model 測試**：
```bash
測試視覺功能_使用base模型.bat
```

### 中期（最佳平衡）

**實現混合模式**：
- 圖片分析 → `gemma3:4b` (base model)
- 文字對話 → `anti-fraud-expert-20251117_173453` (fine-tuned)

### 長期（最佳效果）

**選項 1**: 使用雲端 API
- Google Gemini 1.5 Pro（視覺 + 多語言）
- 成本較高但效果最好

**選項 2**: 優化提示詞
- 保持 base model
- 通過詳細的提示詞注入防詐騙知識
- 使用 RAG 檢索真實案例

---

## 📊 對比分析

| 方案 | 視覺功能 | 防詐騙專業 | 實現難度 | 成本 |
|------|---------|-----------|---------|------|
| **Base Model** | ✅ 完整 | ⚠️ 一般 | ✅ 簡單 | ✅ 免費 |
| **Fine-tuned** | ❌ 不支持 | ✅ 專業 | ✅ 已完成 | ✅ 免費 |
| **混合模式** | ✅ 完整 | ✅ 專業 | ⚠️ 中等 | ✅ 免費 |
| **雲端 API** | ✅ 最佳 | ✅ 最佳 | ✅ 簡單 | ❌ 收費 |
| **重新訓練** | ❓ 未知 | ✅ 專業 | ❌ 困難 | ✅ 免費 |

---

## 🚀 立即測試

### 步驟 1: 使用 Base Model 測試

```bash
測試視覺功能_使用base模型.bat
```

### 步驟 2: 上傳圖片測試

1. 訪問 http://localhost:8000
2. 選擇「個人對話模式」→「防詐助手」
3. 上傳詐騙截圖
4. 觀察回應質量

### 步驟 3: 對比效果

**預期改進**：
- ✅ 結構化輸出
- ✅ 正確識別圖片內容
- ✅ 清晰的詐騙特徵分析
- ✅ 具體的行動建議

---

## 💡 為什麼 Fine-tuned 模型不支持視覺？

### Ollama Fine-tuning 的限制

1. **訓練數據格式**
   - Ollama fine-tuning 使用 JSONL 格式
   - 只包含文字對話
   - 沒有圖片數據

2. **訓練過程**
   - 基於文字 prompt-response pairs
   - 視覺層可能被凍結或忽略
   - 輸出層被重新訓練

3. **模型架構**
   - Base model 的視覺編碼器可能未被使用
   - Fine-tuning 只更新文字處理部分

### 解決方法

**方法 1**: 不使用 fine-tuned model 處理圖片
- 圖片 → base model
- 文字 → fine-tuned model

**方法 2**: 使用更高級的訓練方法
- LoRA (Low-Rank Adaptation)
- 保留視覺層，只訓練文字層
- 需要更複雜的訓練流程

**方法 3**: 使用雲端 API
- 完整的多模態支持
- 無需本地訓練

---

## 📝 總結

### 當前最佳方案

**立即使用**：
```bash
測試視覺功能_使用base模型.bat
```

**長期方案**：
實現混合模式，根據輸入類型動態選擇模型。

### 關鍵發現

1. ✅ Base model (`gemma3:4b`) 視覺功能完整
2. ❌ Fine-tuned model 視覺功能受限
3. 💡 混合模式可以兩全其美
4. 🎯 提示詞優化可以彌補專業知識差距

---

**更新日期**: 2025-11-17  
**狀態**: ✅ 問題已識別  
**建議**: 使用 Base Model 或混合模式
