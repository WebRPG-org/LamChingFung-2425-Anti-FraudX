📝 使用說明
1. 保持現有配置（使用 Ollama）
您當前的 .env 文件已經配置好了 Ollama，只需添加這一行：
GEMINI_ENABLED=false
2. 如果要使用 Gemini
在您的 .env 文件中添加：
# 啟用 GeminiGEMINI_ENABLED=true# 添加 API KeyGEMINI_API_KEY=your_actual_api_key_here# 如果有 fine-tuned 模型，可以指定（可選）GEMINI_MODEL_SCAMMER=tunedModels/your-scammer-model-idGEMINI_MODEL_EXPERT=tunedModels/your-expert-model-id
3. 一鍵切換
您也可以不修改 .env 文件，直接在 Web UI 上切換：
啟動服務後訪問 http://localhost:8000
點擊右上角的「切換至 Gemini」按鈕
在彈出的對話框中輸入 API Key
系統會自動保存配置
🎯 您目前的配置很好！
您已經有：
✅ 專業化的 fine-tuned 模型（scammer 和 expert）
✅ 本地 Ollama 配置
✅ Docker 配置（已註釋）
只需要添加 Gemini 相關配置即可實現雙模式支持。現在可以：
# 安裝依賴py -m pip install -r requirements.txt# 啟動服務py main.py
服務啟動後，您就可以在 UI 上自由切換 Ollama 和 Gemini 了！
1條api key可以使用4個fine tune模型嗎 , 我還未fine tune , 我不打算使用現有的訓練數據而是使用新的jsonl文件進行 ,我應該如何做

好問題！讓我為您詳細解答：
🔑 關於 API Key
是的，1 條 API Key 可以使用多個 fine-tuned 模型！
1 個 Google Cloud 項目 = 1 個 API Key
這個 API Key 可以訪問該項目下的所有模型（包括所有 fine-tuned 模型）
您可以在同一個項目中訓練 4 個不同的模型，然後用同一個 API Key 調用它們
📋 Fine-tuning 完整流程
步驟 1: 準備訓練數據（JSONL 格式）
您需要為每個 Agent 準備一個 JSONL 文件。格式如下：
騙徒模型 (scammer_training.jsonl)
{"text_input": "你好，我是銀行職員", "output": "你好！我係XX銀行嘅客戶服務專員，工號係12345。請問你係咪陳先生？"}{"text_input": "是的，有什麼事嗎？", "output": "陳先生，我哋發現你嘅帳戶有異常交易，需要立即處理，否則你嘅帳戶會被凍結。"}{"text_input": "什麼異常交易？", "output": "有人試圖從你嘅帳戶轉走 50,000 港幣。為咗保護你嘅資金安全，我哋需要你提供驗證碼確認身份。"}
專家模型 (expert_training.jsonl)
{"text_input": "有人說我的銀行帳戶有問題", "output": "🚨 **呢個好可能係詐騙！**📋 **點解係騙案**：• 真正嘅銀行職員唔會主動打電話要求提供驗證碼• 銀行唔會用電話處理帳戶凍結問題• 製造緊急感係典型詐騙手法\n✅ **你應該做**：1. 立即掛斷電話2. 打去銀行官方熱線確認3. 唔好提供任何個人資料或驗證碼"}{"text_input": "他說要我提供驗證碼", "output": "⚠️ **千祈唔好俾！**驗證碼係用嚟確認交易嘅，一旦俾咗騙徒，佢哋就可以轉走你嘅錢。真正嘅銀行職員絕對唔會要求你提供驗證碼。✅ **立即行動**：1. 掛斷電話2. 打 18222 報警3. 聯絡你嘅銀行確認"}
受害者模型 (victim_training.jsonl)
{"text_input": "你好，我是銀行職員", "output": "你好...有咩事？（有啲緊張）"}{"text_input": "你的帳戶有異常交易", "output": "吓？異常交易？咩嚟㗎？我好驚呀...（開始恐慌）"}{"text_input": "需要你提供驗證碼", "output": "驗證碼？係咪我手機收到嗰個？我而家俾你好唔好？（猶豫中）"}
記錄員模型 (recorder_training.jsonl)
{"text_input": "分析這段對話...", "output": "{\"outcome\": \"FAILURE\", \"victim_persona\": \"elderly\", \"scammer_performance\": {\"persuasiveness\": 85, \"credibility\": 80}, \"expert_performance\": {\"intervention_effectiveness\": 45}}"}
步驟 2: 在 Google AI Studio 進行 Fine-tuning
2.1 訪問 Google AI Studio
前往 https://aistudio.google.com/
登錄您的 Google 帳號
點擊左側菜單的「Tuned models」
2.2 創建第一個模型（騙徒）
點擊「New tuned model」
選擇基礎模型：Gemini 1.5 Flash 或 Gemini 2.0 Flash
上傳 scammer_training.jsonl
配置訓練參數：
Model name: anti-fraud-scammer
Epochs: 3-5（根據數據量調整）
Learning rate: 0.001（默認）
Batch size: 4-8
點擊「Start tuning」
等待訓練完成（通常 10-30 分鐘）
訓練完成後，複製模型 ID（格式：tunedModels/anti-fraud-scammer-xxxxx）
2.3 重複創建其他 3 個模型
專家模型: anti-fraud-expert
受害者模型: anti-fraud-victim
記錄員模型: anti-fraud-recorder
步驟 3: 獲取 API Key
在 Google AI Studio 中，點擊左側的「Get API key」
選擇或創建一個項目
點擊「Create API key」
複製生成的 API Key（格式：AIzaSy...）
步驟 4: 配置到系統中
方法 A: 修改 .env 文件
# 啟用 GeminiGEMINI_ENABLED=true# 您的 API KeyGEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX# 您的 4 個 fine-tuned 模型 IDGEMINI_MODEL_SCAMMER=tunedModels/anti-fraud-scammer-xxxxxGEMINI_MODEL_VICTIM=tunedModels/anti-fraud-victim-xxxxxGEMINI_MODEL_EXPERT=tunedModels/anti-fraud-expert-xxxxxGEMINI_MODEL_RECORDER=tunedModels/anti-fraud-recorder-xxxxx
方法 B: 使用 Web UI 配置
啟動服務：py main.py
訪問 http://localhost:8000
點擊右上角「切換至 Gemini」
在對話框中輸入：
API Key
4 個模型 ID
點擊「驗證配置」
驗證成功後點擊「保存並切換」
📊 訓練數據準備建議
數據量建議
最少: 每個模型 50-100 條對話
推薦: 每個模型 200-500 條對話
最佳: 每個模型 500-1000 條對話
數據質量要點
多樣性: 涵蓋不同的詐騙場景和對話風格
真實性: 基於真實案例或合理模擬
一致性: 保持角色特徵一致
平衡性: 包含成功和失敗的案例
從現有系統導出數據（可選）
如果您想參考現有的對話數據：
# 查看訓練數據目錄ls backend/training_data/# 轉換為 JSONL 格式（需要編寫腳本）py scripts/convert_to_jsonl.py
🎯 完整流程總結
1. 準備 4 個 JSONL 文件   ├── scammer_training.jsonl (騙徒)   ├── victim_training.jsonl (受害者)   ├── expert_training.jsonl (專家)   └── recorder_training.jsonl (記錄員)2. 在 Google AI Studio 訓練 4 個模型   ├── 上傳 JSONL 文件   ├── 配置訓練參數   ├── 等待訓練完成   └── 獲取 4 個模型 ID3. 獲取 1 個 API Key   └── 可以訪問所有 4 個模型4. 配置到系統   ├── 方法 A: 修改 .env 文件   └── 方法 B: 使用 Web UI5. 測試   └── 啟動服務並測試對話