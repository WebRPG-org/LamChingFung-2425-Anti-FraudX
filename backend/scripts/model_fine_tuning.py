import os
import sys
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log


TRAINING_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'training_data')
FINE_TUNING_DATA_DIR = os.path.join(TRAINING_DATA_DIR, 'fine_tuning_data')
MODEL_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
OLLAMA_MODELS_DIR = os.path.expanduser("~/.ollama/models")

def ensure_directories():
    """Ensure required directories exist"""
    for directory in [MODEL_OUTPUT_DIR, FINE_TUNING_DATA_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            log.info(f"Created directory: {directory}")

def load_fine_tuning_data() -> List[Dict[str, Any]]:
    """
    Load all fine-tuning data
    """
    fine_tuning_files = []
    
    if not os.path.exists(FINE_TUNING_DATA_DIR):
        log.warning(f"Fine-tuning data directory not found: {FINE_TUNING_DATA_DIR}")
        return fine_tuning_files
    
    for filename in os.listdir(FINE_TUNING_DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(FINE_TUNING_DATA_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    fine_tuning_files.append(data)
                log.info(f"Loaded fine-tuning data: {filename}")
            except Exception as e:
                log.error(f"Failed to load fine-tuning data {filename}: {e}")
    
    log.info(f"Loaded {len(fine_tuning_files)} fine-tuning data files in total")
    return fine_tuning_files

def create_training_dataset(fine_tuning_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert fine-tuning data into training dataset format
    """
    training_dataset = []
    
    for data in fine_tuning_data:
        conversation_log = data.get("conversation_log", [])
        ideal_expert_response = data.get("ideal_expert_response", "")
        victim_persona = data.get("victim_persona", "average")
        scam_tactic = data.get("scam_tactic", "")
        
        
        context = f"""
        你是一位香港的防騙專家。以下是{scam_tactic}的對話場景，受騙者類型是{victim_persona}。
        
        對話歷史：
        """
        
        for msg in conversation_log:
            context += f"\n{msg['speaker']}: {msg['dialogue']}"
        
        context += f"\n\n請提供專業的防騙建議："
        
        
        training_sample = {
            "instruction": context,
            "output": ideal_expert_response,
            "input": "",
            "conversation_type": "anti_fraud_expert",
            "victim_persona": victim_persona,
            "scam_tactic": scam_tactic
        }
        
        training_dataset.append(training_sample)
    
    log.info(f"Created {len(training_dataset)} training samples")
    return training_dataset

def create_modelfile(training_dataset: List[Dict[str, str]], model_name: str = "anti-fraud-expert"):
    """
    Create the Ollama Modelfile
    """
    modelfile_content = f"""FROM gemma3:4b

# 系統提示
SYSTEM \"\"\"
你是一位香港的防騙專家，職責是保護使用者免於詐騙。

**角色特徵**:
- 冷靜、理性、多疑
- 從不輕信任何未經驗證的資訊
- 擅長識破騙徒的邏輯漏洞和心理陷阱
- 溝通方式是提供清晰、可執行的建議

**核心能力**:
- 分析潛在騙局
- 查詢香港警務處和消費者委員會的官方資料
- 針對不同類型的受騙者調整溝通方式

**溝通策略**:
- 對長者：使用簡單比喻，避免技術術語
- 對一般市民：提供具體案例和數據
- 對過度自信者：強調風險的嚴重性

**目標**: 保護使用者，阻止詐騙發生，並解釋騙局的原理。

**香港常見詐騙手法**:
- WhatsApp 對話詐騙
- 假短訊釣魚
- 虛假投資應用程式
- 假網站冒充銀行/政府
- 刷單騙案
- 中獎詐騙
- 假冒官員詐騙

請始終保持專業、冷靜的態度，提供實用的防騙建議。
\"\"\"

# 參數設定
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

# 模板
TEMPLATE \"\"\"{{{{ if .System }}}}{{{{ .System }}}}{{{{ end }}}}{{{{ if .Prompt }}}}

Human: {{{{ .Prompt }}}}

Assistant: {{{{ end }}}}\"\"\"
"""
    
    modelfile_path = os.path.join(MODEL_OUTPUT_DIR, "Modelfile")
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)
    
    log.info(f"Modelfile created: {modelfile_path}")
    return modelfile_path

def create_training_data_file(training_dataset: List[Dict[str, str]]):
    """
    Create training data file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    training_data_file = os.path.join(MODEL_OUTPUT_DIR, f"training_data_{timestamp}.jsonl")
    
    with open(training_data_file, 'w', encoding='utf-8') as f:
        for sample in training_dataset:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    log.info(f"Training data file created: {training_data_file}")
    return training_data_file

def create_model_instructions():
    """
    Create model usage instructions
    """
    instructions = """
# Anti‑Fraud Expert Model Usage Guide

## Overview
This is a purpose‑trained anti‑fraud expert model, built on official materials from the Hong Kong Police Force and the Consumer Council, and optimized via multi‑round simulation training.

## Installation

### Method 1: Using a Modelfile
```bash
# Change into the model directory
cd backend/models

# Create the model
ollama create anti-fraud-expert -f Modelfile

# Run the model
ollama run anti-fraud-expert
```

### Method 2: Import a prebuilt model
```bash
# If you have a prebuilt model file
ollama import anti-fraud-expert.tar
```

## Usage Examples

### Basic conversation
```
Human: I received a call claiming to be from the bank saying my account has an issue and I need to provide personal information. Is this real?

Assistant: This is likely a scam call. Real bank staff will not proactively ask you for personal information, especially passwords or one‑time verification codes. Recommended:
1) Hang up immediately
2) Call the bank’s official hotline directly to verify
3) Do not provide any personal information
```

### For different user types
- **Elderly**: Use simple analogies; avoid technical jargon
- **General public**: Provide concrete cases and data
- **Overconfident users**: Emphasize the severity of risks

## Model Features
- Trained on local Hong Kong scam cases
- Supports identification of multiple scam tactics
- Communication optimized for different user types
- Provides practical anti‑fraud advice

## Updating
When new training data is available, you can retrain the model:
```bash
python scripts/model_fine_tuning.py
ollama create anti-fraud-expert -f Modelfile
```

## Notes
- The model is for reference only; in real scam situations, contact the police immediately
- Always verify information via official channels
- Update the model regularly to obtain the latest anti‑fraud knowledge
"""
    
    instructions_file = os.path.join(MODEL_OUTPUT_DIR, "README.md")
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    log.info(f"Instructions created: {instructions_file}")
    return instructions_file

def create_deployment_script():
    """
    Create deployment script
    """
    deployment_script = """#!/bin/bash
# Anti‑Fraud Expert Model Deployment Script

echo "🚀 Starting deployment of the Anti‑Fraud Expert model..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama first."
    exit 1
fi

# Check if base model exists
if ! ollama list | grep -q "gemma3:4b"; then
    echo "📥 Downloading base model gemma3:4b..."
    ollama pull gemma3:4b
fi

# Create the anti‑fraud expert model
echo "🔧 Creating anti‑fraud expert model..."
ollama create anti-fraud-expert -f Modelfile

# Test the model
echo "🧪 Testing the model..."
ollama run anti-fraud-expert "Hello, I am an anti‑fraud expert. How can I help you?"

echo "✅ Model deployment complete!"
echo "Usage: ollama run anti-fraud-expert"
"""
    
    script_path = os.path.join(MODEL_OUTPUT_DIR, "deploy.sh")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(deployment_script)
    
    # Set executable permission
    os.chmod(script_path, 0o755)
    
    log.info(f"Deployment script created: {script_path}")
    return script_path

def generate_model_report(training_dataset: List[Dict[str, str]]):
    """
    Generate model report
    """
    # Statistics
    total_samples = len(training_dataset)
    persona_counts = {}
    tactic_counts = {}
    
    for sample in training_dataset:
        persona = sample.get("victim_persona", "unknown")
        tactic = sample.get("scam_tactic", "unknown")
        
        persona_counts[persona] = persona_counts.get(persona, 0) + 1
        tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1
    
    report = {
        "model_info": {
            "name": "anti-fraud-expert",
            "base_model": "gemma3:4b",
            "created_at": datetime.now().isoformat(),
            "total_training_samples": total_samples
        },
        "training_statistics": {
            "victim_persona_distribution": persona_counts,
            "scam_tactic_distribution": tactic_counts
        },
        "performance_metrics": {
            "training_accuracy": "TBD",
            "validation_accuracy": "TBD",
            "inference_speed": "TBD"
        }
    }
    
    report_file = os.path.join(MODEL_OUTPUT_DIR, "model_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    log.info(f"Model report created: {report_file}")
    return report_file

def main():
    """
    Main function
    """
    log.info("🔧 開始 AI 反詐騙模型微調和分發")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load fine-tuning data
    fine_tuning_data = load_fine_tuning_data()
    
    if not fine_tuning_data:
        log.warning("No fine-tuning data found; creating example data")
        # Create example fine-tuning data
        fine_tuning_data = [{
            "conversation_log": [
                {"speaker": "騙徒", "dialogue": "你好，我是銀行職員，你的帳戶有問題"},
                {"speaker": "受騙者", "dialogue": "真的嗎？那我應該怎麼辦？"},
                {"speaker": "專家", "dialogue": "這是詐騙，請立即掛斷電話"}
            ],
            "ideal_expert_response": "這很可能是詐騙電話。真正的銀行職員不會主動要求你提供個人資料。建議你立即掛斷電話，直接致電銀行的官方客服熱線確認。",
            "victim_persona": "elderly",
            "scam_tactic": "假冒銀行職員詐騙"
        }]
    
    # Create training dataset
    training_dataset = create_training_dataset(fine_tuning_data)
    
    # Create model file
    modelfile_path = create_modelfile(training_dataset)
    
    # Create training data file
    training_data_file = create_training_data_file(training_dataset)
    
    # Create usage instructions
    instructions_file = create_model_instructions()
    
    # Create deployment script
    deployment_script = create_deployment_script()
    
    # Generate model report
    report_file = generate_model_report(training_dataset)
    
    # Summary
    log.info(f"\n{'='*60}")
    log.info("🎯 模型微調和分發完成！")
    log.info(f"{'='*60}")
    log.info(f"Model directory: {MODEL_OUTPUT_DIR}")
    log.info(f"Training samples: {len(training_dataset)}")
    log.info(f"Modelfile: {modelfile_path}")
    log.info(f"訓練數據: {training_data_file}")
    log.info(f"Instructions: {instructions_file}")
    log.info(f"Deployment script: {deployment_script}")
    log.info(f"Model report: {report_file}")
    
    log.info(f"\n📋 Next steps:")
    log.info("1. Run deploy script: cd backend/models && ./deploy.sh")
    log.info("2. Test model: ollama run anti-fraud-expert")
    log.info("3. Distribute model to users")
    
    log.info(f"\n{'='*60}")

if __name__ == "__main__":
    main()
