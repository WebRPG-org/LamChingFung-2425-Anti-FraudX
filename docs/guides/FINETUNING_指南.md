# Fine-Tuning 完整指南

> 如何有效訓練和優化反詐騙專家和騙徒模型

---

## 📋 目錄

1. [概述](#概述)
2. [系統架構](#系統架構)
3. [訓練數據生成](#訓練數據生成)
4. [Fine-Tuning流程](#fine-tuning流程)
5. [模型評估](#模型評估)
6. [最佳實踐](#最佳實踐)
7. [常見問題](#常見問題)

---

## 概述

### 為什麼需要Fine-Tuning？

基礎模型（如Llama 3.2）雖然強大，但在特定領域（如反詐騙）的表現不如專門訓練的模型。通過Fine-Tuning，我們可以：

1. **提升專業性**：讓模型掌握香港特有的詐騙手法和防騙話術
2. **增強一致性**：確保模型始終保持角色一致性（專家/騙徒）
3. **優化回應質量**：減少無效回應，提高干預成功率
4. **適應本地化**：使用廣東話和本地案例

### 訓練目標

#### 專家模型 (Expert Model)
- **目標**：學習如何有效識破騙局並勸導受害者
- **評估指標**：
  - 干預成功率（受害者最終拒絕騙徒的比例）
  - 信任度提升幅度
  - 回應質量（包含關鍵要素：情緒安撫、證據提供、行動建議）

#### 騙徒模型 (Scammer Model)
- **目標**：模擬真實騙徒行為，用於測試專家模型
- **評估指標**：
  - 話術有效性（受害者信任度提升）
  - 角色一致性（不露餡）
  - 策略多樣性（使用不同的心理操縱手法）

---

## 系統架構

### 數據流程圖

```
模擬對話 (Simulation)
    ↓
對話記錄 + 分析
    ↓
Fine-Tuning Formatter
    ↓
訓練數據 (.jsonl)
    ├── expert_training_*.jsonl
    └── scammer_training_*.jsonl
    ↓
Ollama Fine-Tuning
    ↓
Fine-Tuned Models
    ├── anti-fraud-expert-YYYYMMDD
    └── anti-fraud-scammer-YYYYMMDD
    ↓
評估 & 對比
    ↓
部署到生產環境
```

### 核心組件

1. **`finetuning_formatter.py`**：將模擬對話轉換為訓練格式
2. **`simulation_routes.py`**：在模擬結束時自動生成訓練數據
3. **`run_finetuning.py`**：執行完整的訓練流程
4. **`evaluate_finetuned_models.py`**：評估和對比模型性能

---

## 訓練數據生成

### 自動生成流程

系統在每次模擬結束時會自動生成兩種訓練數據：

1. **原始數據** (`training_data_ws_*.json`)
   - 完整對話歷史
   - RecorderAgent分析結果
   - 性能報告（信任度變化、關鍵時刻等）

2. **Fine-Tuning數據** (`finetune_expert_*.jsonl` / `finetune_scammer_*.jsonl`)
   - 已經格式化為Ollama訓練格式
   - 每個樣本包含：
     - `system`: 角色系統提示
     - `user`: 對話上下文
     - `assistant`: 模型應該生成的回應
     - `metadata`: 質量評分、結果等元數據

### 數據質量控制

#### 專家訓練數據篩選標準

```python
# 成功案例：所有專家回應都保留
if outcome == "SUCCESS":
    include_all_expert_responses = True

# 失敗案例：只保留高質量回應（quality_score > 50）
else:
    include_only_high_quality = True
```

**質量評分因素**：
- ✅ 回應長度適中（50-300字）
- ✅ 包含情緒安撫（「唔使驚」「冷靜」）
- ✅ 直接指出詐騙（「騙局」「假冒」）
- ✅ 提供具體行動建議（「掛線」「報警」）
- ✅ 引用真實案例
- ✅ 導致信任度正向變化

#### 騙徒訓練數據篩選標準

```python
# 失敗案例（騙徒成功）：所有騙徒話術都保留
if outcome == "FAILURE":
    include_all_scammer_responses = True

# 成功案例（專家成功）：只保留前期有效的話術
else:
    include_only_effective_tactics = True
```

**有效性評分因素**：
- ✅ 製造緊迫感（「立即」「馬上」）
- ✅ 偽裝權威（「警察」「銀行」）
- ✅ 利用恐懼或貪婪
- ✅ 導致受害者信任度提升

### 手動觸發訓練數據生成

如果需要從現有的原始數據生成訓練數據：

```bash
python backend/scripts/generate_finetuning_data.py --input backend/training_data/training_data_ws_*.json
```

---

## Fine-Tuning流程

### 完整訓練流程

#### 1. 準備訓練數據

```bash
# 運行多次模擬以收集數據
python start_server.py

# 前端：執行5-10次模擬，確保有成功和失敗案例
```

#### 2. 檢查訓練數據

```bash
# 查看已生成的訓練文件
ls backend/training_data/finetuning/

# 應該看到：
# finetune_expert_YYYYMMDD_HHMMSS_xxxxx.jsonl
# finetune_scammer_YYYYMMDD_HHMMSS_xxxxx.jsonl
```

#### 3. 執行訓練

```bash
# 訓練兩個模型（專家 + 騙徒）
python backend/scripts/run_finetuning.py --mode auto --model both

# 只訓練專家模型
python backend/scripts/run_finetuning.py --model expert

# 只訓練騙徒模型
python backend/scripts/run_finetuning.py --model scammer

# 限制訓練樣本數（避免過擬合）
python backend/scripts/run_finetuning.py --model both --max-samples 100
```

#### 4. 訓練完成後

系統會顯示訓練後的模型名稱：

```
✅ EXPERT 模型訓練完成
   模型名稱: anti-fraud-expert-20241111_183045
   訓練樣本數: 45

✅ SCAMMER 模型訓練完成
   模型名稱: anti-fraud-scammer-20241111_183125
   訓練樣本數: 52
```

---

## 模型評估

### 單一模型評估

```bash
# 評估專家模型
python backend/scripts/evaluate_finetuned_models.py \
  --model expert \
  --model-name anti-fraud-expert-20241111_183045

# 評估騙徒模型
python backend/scripts/evaluate_finetuned_models.py \
  --model scammer \
  --model-name anti-fraud-scammer-20241111_183125
```

### 對比兩個模型

```bash
# 對比新舊專家模型
python backend/scripts/evaluate_finetuned_models.py \
  --compare anti-fraud-expert-20241110 anti-fraud-expert-20241111_183045 \
  --model expert
```

### 評估指標

#### 專家模型評估指標

| 指標 | 說明 | 目標值 |
|-----|------|-------|
| 總分 | 綜合所有測試用例的平均分 | ≥ 70/100 |
| 通過率 | 通過測試的比例 | ≥ 80% |
| 關鍵詞覆蓋率 | 包含預期關鍵詞的比例 | ≥ 70% |
| 平均回應長度 | 回應的平均字數 | 50-300字 |

#### 騙徒模型評估指標

| 指標 | 說明 | 目標值 |
|-----|------|-------|
| 總分 | 綜合所有測試用例的平均分 | ≥ 65/100 |
| 通過率 | 通過測試的比例 | ≥ 75% |
| 關鍵詞覆蓋率 | 包含預期詐騙話術的比例 | ≥ 65% |
| 角色一致性 | 不露餡的比例 | 100% |

---

## 最佳實踐

### 訓練數據收集

#### 1. 數據多樣性

確保收集多種場景的數據：

- ✅ **不同詐騙類型**：電話詐騙、投資詐騙、網絡詐騙
- ✅ **不同受害者畫像**：average、elderly、overconfident
- ✅ **不同結果**：成功（專家勝）和失敗（騙徒勝）
- ✅ **不同難度**：簡單案例到複雜案例

**建議比例**：
```
成功案例 : 失敗案例 = 60% : 40%
```

原因：我們希望模型學習成功的策略，但也需要了解失敗的教訓。

#### 2. 數據量要求

| 模型類型 | 最少樣本數 | 推薦樣本數 | 最大樣本數 |
|---------|-----------|-----------|-----------|
| 專家模型 | 30 | 50-100 | 200 |
| 騙徒模型 | 40 | 60-120 | 250 |

**注意**：
- 樣本數過少：模型學不到足夠的模式
- 樣本數過多：可能過擬合，且訓練時間長

#### 3. 質量優於數量

❌ **錯誤做法**：
```python
# 保留所有數據，不管質量如何
include_all_samples = True
```

✅ **正確做法**：
```python
# 只保留高質量樣本
if quality_score > 50 or outcome == "SUCCESS":
    include_sample = True
```

### 訓練參數調整

#### Modelfile 參數說明

```
PARAMETER temperature 0.8    # 控制隨機性（0.0-1.0）
PARAMETER top_p 0.9          # 核採樣閾值
PARAMETER top_k 40           # 考慮的候選token數
PARAMETER repeat_penalty 1.1  # 重複懲罰
```

**參數調整建議**：

| 參數 | 專家模型 | 騙徒模型 | 說明 |
|-----|---------|---------|------|
| temperature | 0.7-0.8 | 0.8-0.9 | 專家需要更一致，騙徒可以更多樣 |
| top_p | 0.9 | 0.9 | 保持默認 |
| top_k | 40 | 50 | 騙徒可以更多變化 |
| repeat_penalty | 1.1 | 1.05 | 騙徒可以適當重複（強調） |

### 迭代訓練策略

#### 版本管理

```
anti-fraud-expert-v1.0     # 初始版本
anti-fraud-expert-v1.1     # 修復低信任度問題
anti-fraud-expert-v2.0     # 新增RAG集成
anti-fraud-expert-v2.1     # 優化情緒安撫
```

#### 持續改進循環

```
1. 訓練模型 → 2. 評估性能 → 3. 識別問題 → 4. 收集針對性數據 → 回到步驟1
```

**示例**：
- **問題**：專家模型在高壓場景下表現不佳
- **解決**：收集更多高壓場景的成功案例
- **結果**：下一版本在高壓場景的通過率從60%提升到85%

### 避免過擬合

#### 症狀識別

❌ **過擬合警示**：
- 訓練集表現優異（95%），但測試集表現差（60%）
- 模型輸出過於模板化，缺乏靈活性
- 對訓練數據中的具體案例過於敏感

#### 解決方法

1. **增加數據多樣性**
   ```bash
   # 運行不同配置的模擬
   # 變化：受害者畫像、詐騙策略、場景複雜度
   ```

2. **限制訓練樣本數**
   ```bash
   python backend/scripts/run_finetuning.py --max-samples 100
   ```

3. **使用Early Stopping**
   - Ollama目前不直接支持，需要手動監控

4. **定期評估**
   ```bash
   # 每次訓練後立即評估
   python backend/scripts/run_finetuning.py --evaluate
   ```

---

## 常見問題

### Q1: 訓練需要多長時間？

**答**：取決於：
- 基礎模型大小（3B vs 7B）
- 訓練樣本數（50 vs 200）
- 硬件配置（GPU vs CPU）

**估算**：
- Gemma 3 4B + 50樣本 + GPU: 5-10分鐘
- Gemma 3 4B + 50樣本 + CPU: 30-60分鐘

### Q2: 模型太大，如何選擇基礎模型？

**建議**：

| 用途 | 推薦模型 | 原因 |
|-----|---------|------|
| 開發測試 | gemma3:4b | 快速、輕量、優秀性能 |
| 生產環境 | gemma3:4b 或 gemma3:27b | 平衡性能和資源 |
| 高質量要求 | gemma3:27b 或 llama3.1:70b | 最佳性能 |

### Q3: 如何判斷是否需要重新訓練？

**觸發條件**：
- ✅ 新增了50+個高質量訓練樣本
- ✅ 發現當前模型的系統性問題（如某類詐騙識別率低）
- ✅ 模型版本已超過1個月未更新
- ✅ 評估分數下降超過10%

### Q4: Fine-Tuned模型能直接替換原模型嗎？

**答**：可以，但需要：

1. **更新模型配置**：
   ```python
   # backend/llms/ollama_llm.py 或配置文件
   EXPERT_MODEL_NAME = "anti-fraud-expert-20241111_183045"
   SCAMMER_MODEL_NAME = "anti-fraud-scammer-20241111_183125"
   ```

2. **測試驗證**：
   ```bash
   # 運行評估
   python backend/scripts/evaluate_finetuned_models.py --model expert --model-name anti-fraud-expert-20241111_183045
   
   # 運行實際模擬
   python start_server.py
   # 前端執行模擬，觀察表現
   ```

3. **逐步部署**：
   - 先在測試環境部署
   - A/B測試（50%流量使用新模型）
   - 監控關鍵指標
   - 全量部署

### Q5: 訓練失敗怎麼辦？

**常見錯誤及解決方法**：

#### 錯誤1：`ollama: command not found`
```bash
# 確認Ollama已安裝
ollama --version

# 如果未安裝，請安裝Ollama
# macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: 下載安裝器
```

#### 錯誤2：`model not found`
```bash
# 確認基礎模型已下載
ollama list

# 下載基礎模型
ollama pull gemma3:4b
```

#### 錯誤3：`insufficient memory`
```bash
# 使用更小的模型（如果4B仍太大）
python backend/scripts/run_finetuning.py --base-model gemma3:4b

# 或減少訓練樣本數
python backend/scripts/run_finetuning.py --max-samples 50
```

#### 錯誤4：訓練數據格式錯誤
```bash
# 檢查JSONL格式
cat backend/training_data/finetuning/finetune_expert_*.jsonl | head -1 | python -m json.tool

# 應該看到：
# {
#   "messages": [
#     {"role": "system", "content": "..."},
#     {"role": "user", "content": "..."},
#     {"role": "assistant", "content": "..."}
#   ],
#   "metadata": {...}
# }
```

---

## 進階主題

### 多模型集成

在生產環境中，可以使用多個Fine-Tuned模型的集成：

```python
class EnsembleExpertAgent:
    def __init__(self):
        self.models = [
            "anti-fraud-expert-v1.0",  # 通用版本
            "anti-fraud-expert-elderly-v1.0",  # 專門針對elderly persona
            "anti-fraud-expert-investment-v1.0"  # 專門針對投資詐騙
        ]
    
    def select_model(self, context):
        # 根據上下文選擇最合適的模型
        if context["victim_persona"] == "elderly":
            return self.models[1]
        elif context["scam_type"] == "investment":
            return self.models[2]
        else:
            return self.models[0]
```

### 增量訓練

當有新數據時，可以基於已訓練的模型繼續訓練：

```bash
# 基於現有模型繼續訓練
python backend/scripts/run_finetuning.py \
  --base-model anti-fraud-expert-20241111_183045 \
  --model expert
```

### 知識蒸餾

使用大模型（70B）訓練小模型（3B）：

1. 用大模型生成高質量標註數據
2. 用標註數據訓練小模型
3. 小模型可以在資源受限環境運行

---

## 參考資源

### 官方文檔
- [Ollama Documentation](https://ollama.com/docs)
- [Llama Models](https://www.llama.com/)

### 內部文檔
- `系統優化完成報告.md`: 系統整體優化總結
- `快速集成指南.md`: 如何集成新優化功能
- `項目架構文檔.md`: 系統整體架構

### 相關腳本
- `backend/scripts/run_finetuning.py`: 訓練腳本
- `backend/scripts/evaluate_finetuned_models.py`: 評估腳本
- `backend/utils/finetuning_formatter.py`: 格式化工具

---

## 版本歷史

| 版本 | 日期 | 變更內容 |
|-----|------|---------|
| 1.0 | 2024-11-11 | 初始版本，完整的Fine-Tuning系統 |

---

**維護者**: AI Agent Development Team  
**最後更新**: 2024-11-11

