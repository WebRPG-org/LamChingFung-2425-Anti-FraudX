# Google 語音服務集成方案

## 📋 目前狀態

**好消息！** 系統已經在使用Google的語音技術了！

在Chrome和Edge瀏覽器中：
- 🎤 **Web Speech API** 的語音識別 = Google Speech Recognition
- 🔊 **Web Speech API** 的語音合成 = Google Text-to-Speech

---

## 🎯 兩種實現方案對比

### 方案A：Web Speech API（已實現）✅

#### 優點
- ✅ **完全免費**
- ✅ **無需API密鑰**
- ✅ **零配置**
- ✅ **瀏覽器原生支持**
- ✅ **自動使用Google技術**（Chrome/Edge）

#### 缺點
- ⚠️ **瀏覽器兼容性限制**
- ⚠️ **需要網絡連接**
- ⚠️ **參數調整有限**

#### 當前實現
```javascript
// 語音識別（使用Google）
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
recognition = new SpeechRecognition();
recognition.lang = 'zh-HK'; // 廣東話

// 語音合成（使用Google）
const utterance = new SpeechSynthesisUtterance(text);
utterance.lang = 'zh-HK';
speechSynthesis.speak(utterance);
```

---

### 方案B：Google Cloud Speech API（雲端服務）

#### 優點
- ✅ **更高準確度**
- ✅ **支持更多語言**
- ✅ **自定義訓練模型**
- ✅ **豐富的API參數**
- ✅ **不受瀏覽器限制**

#### 缺點
- ❌ **需要Google Cloud賬號**
- ❌ **需要API密鑰管理**
- ❌ **可能產生費用**
- ❌ **需要後端支持**

#### 費用參考（2024）
- **Speech-to-Text**：前60分鐘/月免費，之後 $0.006/15秒
- **Text-to-Speech**：前100萬字符/月免費，之後 $4/100萬字符

---

## 🚀 實施建議

### 推薦：繼續使用 Web Speech API ✅

**理由**：
1. 已經在使用Google技術
2. 完全免費
3. 用戶體驗良好
4. 無需額外配置

### 如果需要升級到 Google Cloud API

**適用場景**：
- 需要更高的識別準確度
- 需要支持Firefox等瀏覽器
- 需要自定義語音模型
- 有預算支持

---

## 💻 Google Cloud API 實現方案

### 1. 準備工作

#### 1.1 創建Google Cloud項目
```bash
# 訪問 Google Cloud Console
https://console.cloud.google.com/

# 創建新項目
1. 點擊「選擇項目」
2. 點擊「新增專案」
3. 輸入專案名稱
4. 點擊「建立」
```

#### 1.2 啟用API
```bash
# 啟用 Speech-to-Text API
https://console.cloud.google.com/apis/library/speech.googleapis.com

# 啟用 Text-to-Speech API
https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
```

#### 1.3 創建API密鑰
```bash
# 在 Google Cloud Console
1. 前往「API和服務」→「憑證」
2. 點擊「建立憑證」→「API金鑰」
3. 複製API金鑰
4. 限制API金鑰使用範圍（安全性）
```

---

### 2. 後端實現（Python）

#### 2.1 安裝依賴
```bash
pip install google-cloud-speech google-cloud-texttospeech
```

#### 2.2 創建後端API

**`backend/api/google_voice_routes.py`**
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import os
import io
from pydantic import BaseModel

router = APIRouter(tags=["GoogleVoice"])

# 設置Google Cloud憑證
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/credentials.json"

# 初始化客戶端
speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()

class TextToSpeechRequest(BaseModel):
    text: str
    language_code: str = "yue-HK"  # 廣東話
    voice_name: str = "yue-HK-Standard-A"

@router.post("/api/google/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Google Speech-to-Text API
    將語音轉換為文字
    """
    try:
        # 讀取音頻文件
        content = await audio_file.read()
        
        # 配置識別請求
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="yue-HK",  # 廣東話
            enable_automatic_punctuation=True,
            model="default"
        )
        
        # 執行識別
        response = speech_client.recognize(config=config, audio=audio)
        
        # 提取文字
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        
        return {
            "success": True,
            "transcript": transcript,
            "confidence": response.results[0].alternatives[0].confidence if response.results else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/google/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Google Text-to-Speech API
    將文字轉換為語音
    """
    try:
        # 設置文字輸入
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        
        # 配置語音參數
        voice = texttospeech.VoiceSelectionParams(
            language_code=request.language_code,
            name=request.voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # 配置音頻輸出
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
            volume_gain_db=0.0
        )
        
        # 執行合成
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # 返回音頻數據（Base64編碼）
        import base64
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        return {
            "success": True,
            "audio": audio_base64,
            "format": "mp3"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/google/voices")
async def list_voices(language_code: str = "yue-HK"):
    """
    獲取可用的語音列表
    """
    try:
        response = tts_client.list_voices(language_code=language_code)
        
        voices = []
        for voice in response.voices:
            voices.append({
                "name": voice.name,
                "language_codes": voice.language_codes,
                "gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name
            })
        
        return {
            "success": True,
            "voices": voices
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2.3 註冊路由

**`backend/main.py`**
```python
from api.google_voice_routes import router as google_voice_router

app.include_router(google_voice_router)
```

---

### 3. 前端實現

#### 3.1 修改語音輸入

**替換 `frontend/personal_chat.html` 中的語音輸入函數**
```javascript
// 使用Google Cloud API進行語音識別
async function toggleVoiceInput() {
    if (isRecording) {
        await stopRecordingWithGoogle();
    } else {
        await startRecordingWithGoogle();
    }
}

let mediaRecorder = null;
let audioChunks = [];

async function startRecordingWithGoogle() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudioToGoogle(audioBlob);
        };

        mediaRecorder.start();
        startRecording(); // UI更新
    } catch (error) {
        console.error('無法訪問麥克風:', error);
        alert('無法訪問麥克風，請檢查權限設置');
    }
}

async function stopRecordingWithGoogle() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        stopRecording(); // UI更新
    }
}

async function sendAudioToGoogle(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.webm');

        const response = await fetch(`${API_BASE_URL}/api/google/speech-to-text`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            document.getElementById('messageInput').value = data.transcript;
            console.log('識別結果:', data.transcript);
            console.log('信心度:', data.confidence);
        } else {
            alert('語音識別失敗');
        }
    } catch (error) {
        console.error('發送音頻失敗:', error);
        alert('語音識別失敗，請重試');
    }
}
```

#### 3.2 修改語音播放

**替換語音合成函數**
```javascript
// 使用Google Cloud API進行語音合成
async function speakText(text) {
    // 檢查是否啟用自動播放
    const autoSpeak = document.getElementById('autoSpeakToggle').checked;
    if (!autoSpeak) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/google/text-to-speech`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                language_code: 'yue-HK',
                voice_name: 'yue-HK-Standard-A'
            })
        });

        const data = await response.json();
        
        if (data.success) {
            // 將Base64音頻轉換為可播放格式
            const audioData = atob(data.audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const view = new Uint8Array(arrayBuffer);
            
            for (let i = 0; i < audioData.length; i++) {
                view[i] = audioData.charCodeAt(i);
            }
            
            const blob = new Blob([arrayBuffer], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(blob);
            
            // 播放音頻
            const audio = new Audio(audioUrl);
            audio.play();
            
            // 播放完成後清理
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
            
            console.log('開始播放Google語音');
        }
    } catch (error) {
        console.error('語音合成失敗:', error);
    }
}
```

---

### 4. 配置文件

#### 4.1 環境變量

**`.env`**
```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-key.json
GOOGLE_PROJECT_ID=your-project-id

# 語音設置
DEFAULT_VOICE_LANGUAGE=yue-HK
DEFAULT_VOICE_NAME=yue-HK-Standard-A
```

#### 4.2 憑證文件

**`credentials/google-cloud-key.json`**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

⚠️ **重要**：不要將此文件提交到Git！添加到 `.gitignore`

---

## 📊 功能對比

| 功能 | Web Speech API | Google Cloud API |
|-----|---------------|------------------|
| **成本** | 免費 | 有免費額度，超出收費 |
| **準確度** | 高 | 更高 |
| **延遲** | 低 | 稍高（網絡請求） |
| **瀏覽器支持** | Chrome/Edge/Safari | 全部（通過後端） |
| **配置** | 零配置 | 需要設置API密鑰 |
| **自定義** | 有限 | 豐富 |
| **離線支持** | 否 | 否 |

---

## 🎯 推薦方案

### 場景1：個人學習/小型項目
**推薦**：繼續使用 Web Speech API ✅
- 完全免費
- 已經實現
- 效果良好

### 場景2：商業項目/高要求
**推薦**：升級到 Google Cloud API
- 更高準確度
- 更多自定義選項
- 支持更多瀏覽器

### 場景3：混合方案
**推薦**：優先使用Web Speech API，失敗時降級到Google Cloud
```javascript
async function speakText(text) {
    try {
        // 優先使用Web Speech API
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'zh-HK';
            speechSynthesis.speak(utterance);
        } else {
            // 降級到Google Cloud API
            await speakTextWithGoogleCloud(text);
        }
    } catch (error) {
        // 最後的降級方案
        await speakTextWithGoogleCloud(text);
    }
}
```

---

## 🚀 快速決策指南

### 使用 Web Speech API（當前方案），如果：
- ✅ 主要用戶使用Chrome/Edge
- ✅ 預算有限或零預算
- ✅ 當前效果已滿足需求
- ✅ 想要快速上線

### 升級到 Google Cloud API，如果：
- ✅ 需要支持所有瀏覽器（包括Firefox）
- ✅ 需要更高的識別準確度
- ✅ 需要自定義語音模型
- ✅ 有預算支持（每月數美元）
- ✅ 需要詳細的使用分析

---

## 📞 下一步

### 選項A：繼續使用當前方案 ✅
**無需任何操作**，系統已經在使用Google技術！

### 選項B：升級到Google Cloud API
**需要執行**：
1. 創建Google Cloud項目
2. 啟用API並獲取密鑰
3. 實施後端代碼
4. 修改前端代碼
5. 測試和部署

---

## 💡 我的建議

**建議繼續使用Web Speech API**，原因：

1. **已經是Google技術** - Chrome/Edge中就是Google提供的
2. **完全免費** - 無需擔心費用
3. **效果良好** - 廣東話識別準確
4. **零維護** - 無需管理API密鑰
5. **即時可用** - 已經實現並運行

除非您有以下特殊需求：
- 必須支持Firefox
- 需要極高的準確度
- 需要自定義訓練模型
- 有充足預算

---

**您想要哪種方案？**
1. 繼續使用當前的Web Speech API（推薦）
2. 升級到Google Cloud API（我可以幫您完整實現）
3. 混合方案（智能降級）

請告訴我您的選擇，我會提供相應的實施方案！🚀
