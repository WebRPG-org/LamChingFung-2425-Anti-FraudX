# 多媒體輸入API文檔

## 概述

本系統現在支持多種輸入方式，包括文字、語音和文件上傳，為用戶提供更豐富的交互體驗。

## 新增功能

### 1. 語音輸入 (Audio Processing)

#### 支持的音頻格式
- `.wav` - WAV音頻文件
- `.mp3` - MP3音頻文件
- `.m4a` - M4A音頻文件
- `.flac` - FLAC音頻文件
- `.ogg` - OGG音頻文件
- `.webm` - WebM音頻文件

#### 最大文件大小
- 25MB

#### API端點

##### 1.1 上傳音頻並進行AI分析
```
POST /api/v1/audio/upload
```

**參數:**
- `audio_file`: 音頻文件 (multipart/form-data)
- `session_id`: 會話ID (可選，默認: "default")
- `use_ai_analysis`: 是否使用AI分析 (可選，默認: true)

**響應:**
```json
{
  "success": true,
  "message": "音頻處理完成",
  "text": "轉換後的文字內容",
  "ai_analysis": {
    "response": "AI分析結果",
    "metadata": {...}
  },
  "file_info": {
    "filename": "audio.wav",
    "size": 1024000,
    "content_type": "audio/wav"
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

##### 1.2 僅語音轉文字
```
POST /api/v1/audio/transcribe
```

**參數:**
- `audio_file`: 音頻文件 (multipart/form-data)

##### 1.3 音頻聊天
```
POST /api/v1/audio/chat
```

**參數:**
- `audio_file`: 音頻文件 (multipart/form-data)
- `session_id`: 會話ID (可選，默認: "default")

##### 1.4 獲取支持的音頻格式
```
GET /api/v1/audio/supported-formats
```

### 2. 文件上傳 (File Processing)

#### 支持的文件格式
- `.pdf` - PDF文檔
- `.docx` - Word文檔 (新格式)
- `.doc` - Word文檔 (舊格式)
- `.txt` - 純文字文件
- `.xlsx` - Excel表格 (新格式)
- `.xls` - Excel表格 (舊格式)
- `.csv` - CSV文件

#### 最大文件大小
- 10MB

#### 最大文字長度
- 50,000字符

#### API端點

##### 2.1 上傳文件並進行AI分析
```
POST /api/v1/file/upload
```

**參數:**
- `file`: 文件 (multipart/form-data)
- `session_id`: 會話ID (可選，默認: "default")
- `use_ai_analysis`: 是否使用AI分析 (可選，默認: true)

**響應:**
```json
{
  "success": true,
  "message": "文件處理完成",
  "text": "提取的文字內容",
  "ai_analysis": {
    "response": "AI分析結果",
    "metadata": {...}
  },
  "file_info": {
    "filename": "document.pdf",
    "size": 2048000,
    "type": "pdf",
    "content_type": "application/pdf",
    "text_length": 5000
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

##### 2.2 僅提取文字
```
POST /api/v1/file/extract-text
```

**參數:**
- `file`: 文件 (multipart/form-data)

##### 2.3 文件聊天
```
POST /api/v1/file/chat
```

**參數:**
- `file`: 文件 (multipart/form-data)
- `session_id`: 會話ID (可選，默認: "default")

##### 2.4 文檔分析（專門用於詐騙檢測）
```
POST /api/v1/file/analyze-document
```

**參數:**
- `file`: 文件 (multipart/form-data)
- `analysis_type`: 分析類型 (可選，默認: "fraud_detection")
- `session_id`: 會話ID (可選，默認: "default")

##### 2.5 獲取支持的文件格式
```
GET /api/v1/file/supported-formats
```

### 3. 多媒體聊天 (Multimedia Chat)

#### 3.1 多媒體聊天
```
POST /api/v1/chat/multimedia
```

**參數:**
- `text_query`: 文字查詢 (可選)
- `audio_file`: 音頻文件 (可選)
- `file`: 文件 (可選)
- `session_id`: 會話ID (可選，默認: "default")
- `use_rag`: 是否使用RAG (可選，默認: true)

**說明:**
- 可以同時上傳多種類型的輸入
- 系統會將所有輸入組合後進行AI分析
- 至少需要提供一種輸入類型

**響應:**
```json
{
  "success": true,
  "response": "AI分析結果",
  "metadata": {...},
  "source": "unified_ai",
  "input_sources": ["text", "audio", "file"],
  "combined_text": "組合後的輸入文字",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### 3.2 獲取支持的多媒體格式
```
GET /api/v1/chat/supported-formats
```

## 使用示例

### Python示例

```python
import requests

# 1. 上傳音頻文件
with open('audio.wav', 'rb') as f:
    files = {'audio_file': f}
    data = {'session_id': 'user123', 'use_ai_analysis': True}
    response = requests.post('http://localhost:8000/api/v1/audio/upload', 
                           files=files, data=data)
    print(response.json())

# 2. 上傳文件
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'session_id': 'user123', 'use_ai_analysis': True}
    response = requests.post('http://localhost:8000/api/v1/file/upload', 
                           files=files, data=data)
    print(response.json())

# 3. 多媒體聊天
with open('audio.wav', 'rb') as audio, open('document.pdf', 'rb') as doc:
    files = {'audio_file': audio, 'file': doc}
    data = {
        'text_query': '請分析這個音頻和文件內容',
        'session_id': 'user123'
    }
    response = requests.post('http://localhost:8000/api/v1/chat/multimedia', 
                           files=files, data=data)
    print(response.json())
```

### JavaScript示例

```javascript
// 1. 上傳音頻文件
const formData = new FormData();
formData.append('audio_file', audioFile);
formData.append('session_id', 'user123');
formData.append('use_ai_analysis', 'true');

fetch('/api/v1/audio/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// 2. 多媒體聊天
const multimediaFormData = new FormData();
multimediaFormData.append('text_query', '請分析這些內容');
multimediaFormData.append('audio_file', audioFile);
multimediaFormData.append('file', documentFile);
multimediaFormData.append('session_id', 'user123');

fetch('/api/v1/chat/multimedia', {
    method: 'POST',
    body: multimediaFormData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 技術實現

### 語音處理
- 使用 **OpenAI Whisper** 進行高精度語音識別
- 支持多種音頻格式自動轉換
- 備用 **SpeechRecognition** 庫作為fallback

### 文件處理
- 使用 **python-magic** 進行文件類型檢測
- 支持PDF、Word、Excel等多種格式
- 自動文字清理和長度限制

### 多媒體整合
- 支持同時處理多種輸入類型
- 智能組合不同來源的文字內容
- 統一的AI分析流程

## 錯誤處理

所有API端點都包含完整的錯誤處理：

```json
{
  "success": false,
  "error": "錯誤描述",
  "message": "用戶友好的錯誤信息"
}
```

常見錯誤：
- 文件格式不支持
- 文件大小超限
- 音頻/文件處理失敗
- AI服務不可用

## 性能優化

- 異步處理所有文件操作
- 智能緩存機制
- 文件大小和文字長度限制
- 優雅的錯誤降級
