import os
import io
import tempfile
import logging
from typing import Optional, Dict, Any
import speech_recognition as sr
import whisper
from pydub import AudioSegment
import aiofiles
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class AudioService:
    """語音處理服務，支持多種語音轉文字方法"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.whisper_model = None
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm']
        self.max_file_size = 25 * 1024 * 1024  # 25MB
        
    async def initialize_whisper(self):
        """初始化Whisper模型"""
        try:
            if not self.whisper_model:
                # 使用base模型，平衡速度和準確度
                self.whisper_model = whisper.load_model("base")
                logger.info("Whisper model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            self.whisper_model = None
    
    async def process_audio_file(self, audio_file: UploadFile) -> Dict[str, Any]:
        """
        處理音頻文件並轉換為文字
        """
        try:
            # 驗證文件
            if not self._validate_audio_file(audio_file):
                raise HTTPException(status_code=400, detail="不支援的音頻格式或文件過大")
            
            # 讀取文件內容
            content = await audio_file.read()
            
            # 轉換音頻格式
            audio_data = await self._convert_audio_format(content, audio_file.filename)
            
            # 使用Whisper進行語音識別
            text = await self._transcribe_with_whisper(audio_data)
            
            return {
                "success": True,
                "text": text,
                "method": "whisper",
                "file_info": {
                    "filename": audio_file.filename,
                    "size": len(content),
                    "content_type": audio_file.content_type
                }
            }
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return {
                "success": False,
                "error": f"音頻處理失敗: {str(e)}",
                "text": ""
            }
    
    def _validate_audio_file(self, audio_file: UploadFile) -> bool:
        """驗證音頻文件"""
        if not audio_file.filename:
            return False
        
        # 檢查文件擴展名
        file_ext = os.path.splitext(audio_file.filename.lower())[1]
        if file_ext not in self.supported_formats:
            return False
        
        # 檢查文件大小（這裡只是預檢查，實際大小在讀取時檢查）
        return True
    
    async def _convert_audio_format(self, audio_content: bytes, filename: str) -> bytes:
        """轉換音頻格式為WAV"""
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_input:
                temp_input.write(audio_content)
                temp_input_path = temp_input.name
            
            # 使用pydub轉換為WAV格式
            audio = AudioSegment.from_file(temp_input_path)
            
            # 轉換為單聲道，16kHz採樣率（Whisper推薦格式）
            audio = audio.set_channels(1).set_frame_rate(16000)
            
            # 導出為WAV格式
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_output:
                audio.export(temp_output.name, format="wav")
                temp_output_path = temp_output.name
            
            # 讀取轉換後的文件
            with open(temp_output_path, 'rb') as f:
                wav_content = f.read()
            
            # 清理臨時文件
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
            
            return wav_content
            
        except Exception as e:
            logger.error(f"Audio format conversion failed: {e}")
            raise HTTPException(status_code=400, detail=f"音頻格式轉換失敗: {str(e)}")
    
    async def _transcribe_with_whisper(self, audio_data: bytes) -> str:
        """使用Whisper進行語音識別"""
        try:
            # 確保Whisper模型已初始化
            if not self.whisper_model:
                await self.initialize_whisper()
            
            if not self.whisper_model:
                raise Exception("Whisper模型未初始化")
            
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # 使用Whisper轉錄
                result = self.whisper_model.transcribe(temp_file_path, language="zh")
                text = result["text"].strip()
                
                logger.info(f"Whisper transcription completed: {len(text)} characters")
                return text
                
            finally:
                # 清理臨時文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise Exception(f"語音識別失敗: {str(e)}")
    
    async def _transcribe_with_speech_recognition(self, audio_data: bytes) -> str:
        """使用SpeechRecognition進行語音識別（備用方法）"""
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # 使用SpeechRecognition
                with sr.AudioFile(temp_file_path) as source:
                    audio = self.recognizer.record(source)
                
                # 嘗試多種識別服務
                text = ""
                try:
                    # 使用Google語音識別（支持中文）
                    text = self.recognizer.recognize_google(audio, language="zh-TW")
                except sr.UnknownValueError:
                    try:
                        # 備用：使用英文識別
                        text = self.recognizer.recognize_google(audio, language="en-US")
                    except sr.UnknownValueError:
                        text = "無法識別語音內容"
                except sr.RequestError as e:
                    text = f"語音識別服務錯誤: {e}"
                
                logger.info(f"SpeechRecognition transcription completed: {len(text)} characters")
                return text
                
            finally:
                # 清理臨時文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"SpeechRecognition transcription failed: {e}")
            raise Exception(f"語音識別失敗: {str(e)}")
    
    def get_supported_formats(self) -> list:
        """獲取支援的音頻格式"""
        return self.supported_formats
    
    def get_max_file_size(self) -> int:
        """獲取最大文件大小"""
        return self.max_file_size

# 創建全局實例
audio_service = AudioService()
