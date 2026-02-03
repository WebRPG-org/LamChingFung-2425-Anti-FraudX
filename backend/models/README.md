
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
