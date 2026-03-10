#!/bin/bash

# 香港反詐騙AI模型訓練腳本

echo "開始訓練反詐騙專家模型..."

# 找到最新的訓練數據
EXPERT_TRAIN=$(ls -t expert_train_*.jsonl | head -1)
SCAMMER_TRAIN=$(ls -t scammer_train_*.jsonl | head -1)

if [ -z "$EXPERT_TRAIN" ]; then
    echo "錯誤：未找到專家訓練數據"
    exit 1
fi

if [ -z "$SCAMMER_TRAIN" ]; then
    echo "錯誤：未找到騙徒訓練數據"
    exit 1
fi

echo "使用訓練數據："
echo "  專家: $EXPERT_TRAIN"
echo "  騙徒: $SCAMMER_TRAIN"

# 訓練專家模型
echo "\n=== 訓練專家模型 ==="
ollama create anti-fraud-expert-hk -f Modelfile.expert --adapter $EXPERT_TRAIN

if [ $? -eq 0 ]; then
    echo "✅ 專家模型訓練完成: anti-fraud-expert-hk"
else
    echo "❌ 專家模型訓練失敗"
fi

# 訓練騙徒模擬模型
echo "\n=== 訓練騙徒模擬模型 ==="
ollama create scam-simulator-hk -f Modelfile.scammer --adapter $SCAMMER_TRAIN

if [ $? -eq 0 ]; then
    echo "✅ 騙徒模擬模型訓練完成: scam-simulator-hk"
else
    echo "❌ 騙徒模擬模型訓練失敗"
fi

echo "\n=== 訓練完成 ==="
echo "可用模型："
echo "  - anti-fraud-expert-hk (專家模型)"
echo "  - scam-simulator-hk (騙徒模擬模型)"
echo ""
echo "測試模型："
echo "  ollama run anti-fraud-expert-hk"
echo "  ollama run scam-simulator-hk"
