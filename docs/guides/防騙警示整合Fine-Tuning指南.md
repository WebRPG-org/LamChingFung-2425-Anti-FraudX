# 防騙警示整合 Fine-Tuning 指南

## 📋 概述

本指南說明如何將 `scraped_alerts.json` 的防騙警示數據整合到 Fine-Tuning 訓練流程中。

## 🎯 目標

將香港警方的防騙警示轉換為專家訓練數據，增強 AI 模型的防騙知識庫。

## 📁 相關文件

```
AI-Agentv4/
├── data/
│   └── scraped_alerts.json                          # 防騙警示原始數據（270條）
├── backend/
│   ├── scripts/
│   │   ├── convert_alerts_to_finetuning.py         # 警示轉換腳本（新）
│   │   ├── merge_all_training_data.py              # 數據合併腳本（新）
│   │   ├── generate_finetuning_data.py             # 對話數據生成腳本
│   │   └── run_finetuning.py                       # 訓練執行腳本
│   └── training_data/
│       └── finetuning/                              # 訓練數據輸出目錄
```

## 🚀 快速開始

### 方案 A：完整流程（推薦）

```bash
# 1. 轉換防騙警示為訓練數據
python backend/scripts/convert_alerts_to_finetuning.py

# 2. 合併所有訓練數據（對話 + 警示）
python backend/scripts/merge_all_training_data.py

# 3. 訓練模型
python backend/scripts/run_finetuning.py --model expert
```

### 方案 B：僅使用警示數據

```bash
# 1. 轉換防騙警示
python backend/scripts/convert_alerts_to_finetuning.py

# 2. 直接訓練（使用生成的 alerts_expert_train_*.jsonl）
python backend/scripts/run_finetuning.py --model expert --data-pattern "alerts_expert_*.jsonl"
```

## 📊 數據轉換詳情

### 輸入數據格式

`scraped_alerts.json` 包含 270 條防騙警示，每條包含：

```json
{
  "title": "提防假冒警務人員電話騙案",
  "date": "2021-10-08",
  "link": "https://www.adcc.gov.hk/...",
  "source": "ADCC",
  "content": "手法\n...\n警方呼籲\n..."
}
```

### 輸出訓練樣本

每條警示生成 **4 種訓練場景**：

#### 1. 識別詐騙手法
```
用戶：黃sir，我想了解「提防假冒警務人員電話騙案」係咩嚟㗎？
專家：好，等我同你講解下...（詳細說明手法）
```

#### 2. 提供防範建議
```
用戶：黃sir，如果我遇到這種情況，我應該點做？
專家：好問題！遇到呢種情況，你要記住以下幾點...
```

#### 3. 案例分析
```
用戶：黃sir，最近有冇關於這個的真實案例？
專家：有㗎！根據警方嘅資料...
```

#### 4. 快速識別技巧
```
用戶：黃sir，點樣可以快速識別這種騙局？
專家：好！等我教你幾個快速識別嘅方法...
```

### 預期輸出

- **輸入**：270 條警示
- **輸出**：約 1,080 個訓練樣本（270 × 4）
- **格式**：JSONL（Ollama fine-tuning 格式）

## 🔧 腳本詳細說明

### 1. `convert_alerts_to_finetuning.py`

**功能**：將防騙警示轉換為訓練數據

**使用方法**：
```bash
python backend/scripts/convert_alerts_to_finetuning.py \
  --alerts-file data/scraped_alerts.json \
  --output-dir backend/training_data/finetuning \
  --split-ratio 0.9
```

**參數說明**：
- `--alerts-file`: 警示JSON文件路徑（默認：`data/scraped_alerts.json`）
- `--output-dir`: 輸出目錄（默認：`backend/training_data/finetuning`）
- `--split-ratio`: 訓練集比例（默認：0.9，即90%訓練，10%驗證）

**輸出文件**：
```
backend/training_data/finetuning/
├── alerts_expert_train_20251117_160000.jsonl    # 訓練集（~972樣本）
├── alerts_expert_val_20251117_160000.jsonl      # 驗證集（~108樣本）
└── alerts_conversion_stats_20251117_160000.json # 統計信息
```

### 2. `merge_all_training_data.py`

**功能**：合併對話訓練數據和警示訓練數據

**使用方法**：
```bash
python backend/scripts/merge_all_training_data.py \
  --output-dir backend/training_data/finetuning
```

**合併來源**：
1. 對話訓練數據：`finetune_expert_*.jsonl`
2. 警示訓練數據：`alerts_expert_*.jsonl`

**輸出文件**：
```
backend/training_data/finetuning/
├── merged_expert_train_20251117_160500.jsonl    # 合併訓練集
├── merged_expert_val_20251117_160500.jsonl      # 合併驗證集
├── merged_expert_stats_20251117_160500.json     # 統計信息
└── Modelfile.expert_merged_20251117_160500      # Modelfile配置
```

## 📈 訓練數據統計

### 數據來源對比

| 數據來源 | 樣本數量 | 特點 |
|---------|---------|------|
| 對話訓練數據 | ~100-500 | 實際對話場景，動態互動 |
| 警示訓練數據 | ~1,080 | 官方知識庫，全面覆蓋 |
| **合併總計** | **~1,180-1,580** | **兼具實戰與知識** |

### 訓練樣本類型分布

```
識別詐騙手法：  270 樣本 (25%)
防範建議：      270 樣本 (25%)
案例分析：      270 樣本 (25%)
快速識別技巧：  270 樣本 (25%)
```

## 🎓 訓練模型

### 使用合併數據訓練

```bash
# 方法1：自動使用最新的合併數據
python backend/scripts/run_finetuning.py --model expert

# 方法2：指定合併數據文件
python backend/scripts/run_finetuning.py \
  --model expert \
  --data-file backend/training_data/finetuning/merged_expert_train_20251117_160500.jsonl
```

### 訓練參數

```python
# 在 Modelfile 中配置
PARAMETER temperature 0.7        # 創造性（0.7 = 平衡）
PARAMETER top_p 0.9             # 多樣性
PARAMETER repeat_penalty 1.1    # 避免重複
PARAMETER num_ctx 4096          # 上下文長度
```

## 🧪 驗證和測試

### 1. 檢查生成的數據

```bash
# 查看訓練數據
head -n 1 backend/training_data/finetuning/alerts_expert_train_*.jsonl | python -m json.tool

# 統計樣本數量
wc -l backend/training_data/finetuning/alerts_expert_train_*.jsonl
```

### 2. 測試訓練後的模型

```bash
# 評估模型
python backend/scripts/evaluate_finetuned_models.py \
  --model expert \
  --model-name anti-fraud-expert-20251117_160000
```

### 3. 互動測試

```bash
# 直接與模型對話
ollama run anti-fraud-expert-20251117_160000

# 測試問題範例
> 黃sir，我想了解假冒警務人員電話騙案係咩嚟㗎？
> 如果我收到可疑來電，應該點做？
> 點樣可以快速識別詐騙電話？
```

## 📝 最佳實踐

### 1. 定期更新警示數據

```bash
# 爬取最新警示
python backend/scripts/scraper.py

# 轉換新警示
python backend/scripts/convert_alerts_to_finetuning.py

# 重新合併和訓練
python backend/scripts/merge_all_training_data.py
python backend/scripts/run_finetuning.py --model expert
```

### 2. 數據質量控制

- ✅ 確保警示內容完整（包含手法和呼籲）
- ✅ 檢查生成的樣本是否自然流暢
- ✅ 驗證訓練集和驗證集的分割比例
- ✅ 監控訓練過程中的損失值

### 3. 版本管理

```bash
# 為每次訓練創建標籤
git tag -a training-v1.2 -m "Added 270 alert samples"

# 記錄模型版本
echo "anti-fraud-expert-20251117_160000" > backend/models/latest_expert_model.txt
```

## 🔍 故障排除

### 問題1：找不到警示文件

```bash
# 檢查文件是否存在
ls -la data/scraped_alerts.json

# 如果不存在，先爬取
python backend/scripts/scraper.py
```

### 問題2：生成的樣本數量不對

```bash
# 檢查警示數據質量
python -c "
import json
with open('data/scraped_alerts.json', 'r', encoding='utf-8') as f:
    alerts = json.load(f)
    print(f'總警示數: {len(alerts)}')
    no_content = sum(1 for a in alerts if not a.get('content'))
    print(f'無內容警示: {no_content}')
"
```

### 問題3：訓練失敗

```bash
# 檢查JSONL格式
python -c "
import json
with open('backend/training_data/finetuning/alerts_expert_train_*.jsonl', 'r') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except:
            print(f'第{i}行格式錯誤')
"
```

## 📊 效果評估

### 預期改進

整合警示數據後，模型應該能夠：

1. ✅ **識別更多詐騙類型**（270種官方警示）
2. ✅ **提供更準確的防範建議**（基於警方呼籲）
3. ✅ **引用真實案例**（來自官方警示）
4. ✅ **給出具體行動步驟**（結構化建議）

### 評估指標

```bash
# 運行評估腳本
python backend/scripts/evaluate_finetuned_models.py \
  --model expert \
  --model-name anti-fraud-expert-20251117_160000 \
  --test-cases backend/test_cases/expert_test_cases.json
```

預期指標：
- **準確率**: > 85%
- **召回率**: > 80%
- **F1分數**: > 82%
- **用戶滿意度**: > 4.0/5.0

## 🚀 進階應用

### 1. 自動化流程

創建自動化腳本 `update_and_train.sh`：

```bash
#!/bin/bash

echo "🚀 開始自動化訓練流程..."

# 1. 爬取最新警示
echo "[1/4] 爬取最新警示..."
python backend/scripts/scraper.py

# 2. 轉換警示數據
echo "[2/4] 轉換警示數據..."
python backend/scripts/convert_alerts_to_finetuning.py

# 3. 合併所有數據
echo "[3/4] 合併訓練數據..."
python backend/scripts/merge_all_training_data.py

# 4. 訓練模型
echo "[4/4] 訓練模型..."
python backend/scripts/run_finetuning.py --model expert

echo "✅ 完成！"
```

### 2. 定期更新計劃

```bash
# 使用 Windows 任務計劃程序
# 每週執行一次更新和訓練

schtasks /create /tn "AI-Agent-Training" /tr "C:\path\to\update_and_train.bat" /sc weekly /d MON /st 02:00
```

### 3. 多語言支持

修改 `convert_alerts_to_finetuning.py` 以支持英文版本：

```python
# 添加英文樣本生成
samples.append({
    "system": "You are an anti-fraud expert...",
    "user": f"Can you explain '{title}'?",
    "assistant": f"Sure! Let me explain this scam type..."
})
```

## 📚 參考資源

- [Ollama Fine-Tuning 文檔](https://github.com/ollama/ollama/blob/main/docs/finetuning.md)
- [香港反詐騙協調中心](https://www.adcc.gov.hk/)
- [防騙易熱線 18222](https://www.police.gov.hk/ppp_tc/04_crime_matters/scam/)

## 💡 常見問題

**Q: 需要多久更新一次警示數據？**
A: 建議每週更新一次，確保模型掌握最新的詐騙手法。

**Q: 可以只使用警示數據訓練嗎？**
A: 可以，但建議結合對話數據，以獲得更好的互動效果。

**Q: 訓練需要多長時間？**
A: 取決於硬件配置，通常 10-30 分鐘（使用 GPU）。

**Q: 如何評估模型是否有改進？**
A: 使用評估腳本對比訓練前後的指標，並進行人工測試。

---

**更新日期**: 2025-11-17  
**版本**: v1.0.0  
**作者**: AI Agent Team
