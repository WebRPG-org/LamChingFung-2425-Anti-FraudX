# Fine-Tuning 快速開始指南

> 5分鐘內開始訓練你的第一個反詐騙模型

---

## 🚀 快速流程

```bash
# 步驟 1: 收集訓練數據（運行模擬）
python start_server.py
# 前端執行5-10次模擬

# 步驟 2: 檢查數據
ls backend/training_data/finetuning/
# 應該看到 finetune_expert_*.jsonl 和 finetune_scammer_*.jsonl

# 步驟 3: 訓練模型
python backend/scripts/run_finetuning.py --model both

# 步驟 4: 評估模型
python backend/scripts/evaluate_finetuned_models.py \
  --model expert \
  --model-name <你的模型名稱>

# 步驟 5: 使用新模型（更新配置）
# 編輯配置文件，將模型名稱改為新訓練的模型
```

---

## 📝 詳細步驟

### 步驟 1: 收集訓練數據

#### 1.1 啟動服務器
```bash
python start_server.py
```

#### 1.2 運行模擬
1. 打開瀏覽器訪問 `http://localhost:5000`
2. 選擇不同的配置運行多次模擬：
   - 受害者畫像：`average`, `elderly`, `overconfident`
   - 詐騙策略：`authority`, `investment`, `urgency`
3. 建議至少運行 **10次模擬**，包括：
   - 6次成功案例（專家勝）
   - 4次失敗案例（騙徒勝）

#### 1.3 確認數據生成
模擬結束後，系統會自動生成：
```
backend/training_data/training_data_ws_*.json  # 原始數據
backend/training_data/finetuning/finetune_expert_*.jsonl  # 專家訓練數據
backend/training_data/finetuning/finetune_scammer_*.jsonl  # 騙徒訓練數據
```

檢查文件：
```bash
ls -lh backend/training_data/finetuning/
```

---

### 步驟 2: 訓練模型

#### 2.1 訓練專家模型
```bash
python backend/scripts/run_finetuning.py --model expert
```

#### 2.2 訓練騙徒模型
```bash
python backend/scripts/run_finetuning.py --model scammer
```

#### 2.3 同時訓練兩個模型（推薦）
```bash
python backend/scripts/run_finetuning.py --model both
```

#### 訓練輸出示例
```
============================================================
開始 EXPERT 模型完整訓練流程
============================================================
找到 8 個 expert 訓練文件
✅ 合併完成：45 個樣本 -> backend/models/finetuned/merged_expert_20241111_183040.jsonl
✅ Modelfile創建完成: backend/models/finetuned/Modelfile.expert
執行命令: ollama create anti-fraud-expert-20241111_183045 -f Modelfile.expert
✅ 模型訓練成功: anti-fraud-expert-20241111_183045
============================================================
✅ EXPERT 模型訓練完成
   模型名稱: anti-fraud-expert-20241111_183045
   訓練樣本數: 45
============================================================
```

**記錄模型名稱**：`anti-fraud-expert-20241111_183045`（你的會不同）

---

### 步驟 3: 評估模型

#### 3.1 評估專家模型
```bash
python backend/scripts/evaluate_finetuned_models.py \
  --model expert \
  --model-name anti-fraud-expert-20241111_183045
```

#### 3.2 評估騙徒模型
```bash
python backend/scripts/evaluate_finetuned_models.py \
  --model scammer \
  --model-name anti-fraud-scammer-20241111_183125
```

#### 評估輸出示例
```
============================================================
開始評估模型: anti-fraud-expert-20241111_183045 (type=expert)
============================================================
加載 3 個 expert 測試用例
測試 1/3: expert_001
  ✅ 通過 (分數: 78.5)
測試 2/3: expert_002
  ✅ 通過 (分數: 85.2)
測試 3/3: expert_003
  ✅ 通過 (分數: 72.0)

============================================================
📊 評估結果總結
============================================================
模型: anti-fraud-expert-20241111_183045
總分: 78.6/100
通過率: 100.0%
通過: 3/3
結果已保存: backend/evaluation_results/eval_expert_20241111_183150.json
============================================================
```

---

### 步驟 4: 使用新模型

#### 方法 1: 直接測試（不修改代碼）
```bash
# 使用ollama命令行測試
ollama run anti-fraud-expert-20241111_183045

# 輸入測試提示
>>> 【對話記錄】
>>> 騙徒：我係警察李sir，你嘅銀行帳戶涉嫌洗黑錢。
>>> 受騙者：真的嗎？我應該點做？
>>> 
>>> 【你的任務】作為黃sir，請給出你的專業建議：
```

#### 方法 2: 更新系統配置

##### 4.1 找到配置文件
根據你的部署方式，配置可能在：
- `.env` 文件
- `backend/llms/ollama_llm.py`
- 環境變量

##### 4.2 更新模型名稱

**選項 A: 使用環境變量**
```bash
export EXPERT_MODEL_NAME="anti-fraud-expert-20241111_183045"
export SCAMMER_MODEL_NAME="anti-fraud-scammer-20241111_183125"
```

**選項 B: 修改代碼**
```python
# backend/llms/ollama_llm.py
class OllamaLlm:
    def __init__(self, model_name: str = None):
        if model_name is None:
            # 使用fine-tuned模型
            model_name = "anti-fraud-expert-20241111_183045"  # 改這裡
        self.model_name = model_name
```

**選項 C: 創建別名**
```bash
# 為新模型創建一個友好的別名
ollama cp anti-fraud-expert-20241111_183045 expert-latest
ollama cp anti-fraud-scammer-20241111_183125 scammer-latest

# 然後在代碼中使用
model_name = "expert-latest"
```

##### 4.3 重啟服務器
```bash
# 停止當前服務器 (Ctrl+C)

# 重新啟動
python start_server.py
```

##### 4.4 驗證
```bash
# 檢查日誌，確認使用了新模型
# 應該看到類似：
# INFO: Using model: anti-fraud-expert-20241111_183045
```

---

## 🎯 成功標準

### 訓練成功
- ✅ 訓練完成無錯誤
- ✅ 模型名稱已記錄
- ✅ 訓練樣本數 ≥ 30（專家）、≥ 40（騙徒）

### 評估成功
- ✅ 總分 ≥ 70/100（專家）、≥ 65/100（騙徒）
- ✅ 通過率 ≥ 80%（專家）、≥ 75%（騙徒）

### 部署成功
- ✅ 系統啟動無錯誤
- ✅ 日誌顯示使用新模型
- ✅ 模擬運行正常，回應質量符合預期

---

## ❌ 常見錯誤

### 錯誤 1: 沒有訓練數據
```
找到 0 個 expert 訓練文件
```
**解決**：運行更多模擬以生成訓練數據

### 錯誤 2: Ollama未運行
```
Connection refused: http://localhost:11434
```
**解決**：
```bash
# 啟動Ollama服務
ollama serve
```

### 錯誤 3: 基礎模型不存在
```
Error: model 'gemma3:4b' not found
```
**解決**：
```bash
# 下載基礎模型
ollama pull gemma3:4b
```

### 錯誤 4: 內存不足
```
Error: insufficient memory
```
**解決**：
```bash
# 減少訓練樣本數
python backend/scripts/run_finetuning.py --base-model gemma3:4b --max-samples 50
```

---

## 📚 下一步

完成快速開始後，建議閱讀：

1. **`FINETUNING_指南.md`**: 完整的Fine-Tuning指南
   - 深入理解訓練原理
   - 高級調優技巧
   - 最佳實踐

2. **`系統優化完成報告.md`**: 系統整體優化
   - 了解其他優化功能
   - Rewrite機制、Sliding Window等

3. **`快速集成指南.md`**: 集成新功能
   - 如何集成到現有系統
   - API使用方法

---

## 💡 小技巧

### 加速訓練
```bash
# 限制樣本數，減少訓練時間
python backend/scripts/run_finetuning.py --model both --max-samples 50
```

### 批量評估
```bash
# 一次評估多個模型（功能開發中）
python backend/scripts/evaluate_finetuned_models.py --batch
```

### 對比模型
```bash
# 對比新舊版本
python backend/scripts/evaluate_finetuned_models.py \
  --compare expert-v1.0 expert-v1.1 \
  --model expert
```

### 查看訓練歷史
```bash
# 查看所有訓練記錄
cat backend/models/training_history.json | python -m json.tool
```

---

## 🆘 需要幫助？

- 查看完整文檔：`FINETUNING_指南.md`
- 檢查日誌：`server.log`
- 聯繫開發團隊

---

**祝你訓練順利！** 🎉

