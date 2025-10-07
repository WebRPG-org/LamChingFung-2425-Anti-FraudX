from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import logging
from datetime import datetime

from app.audio_service import audio_service
from app.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/audio/upload", tags=["Audio Processing"])
async def upload_audio(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form("default"),
    use_ai_analysis: Optional[bool] = Form(True)
):
    """
    上傳音頻文件並進行語音轉文字處理
    """
    try:
        logger.info(f"Processing audio file: {audio_file.filename} (Session: {session_id})")
        
        # 處理音頻文件
        audio_result = await audio_service.process_audio_file(audio_file)
        
        if not audio_result["success"]:
            raise HTTPException(status_code=400, detail=audio_result["error"])
        
        extracted_text = audio_result["text"]
        
        if not extracted_text:
            return {
                "success": False,
                "message": "無法從音頻中提取文字內容",
                "text": "",
                "file_info": audio_result["file_info"]
            }
        
        # 如果啟用AI分析，使用AI服務處理提取的文字
        ai_response = None
        if use_ai_analysis and extracted_text:
            try:
                ai_result = await ai_service.generate_response(extracted_text, session_id)
                if "error" not in ai_result:
                    ai_response = {
                        "response": ai_result["response"],
                        "metadata": ai_result.get("metadata", {})
                    }
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
                ai_response = {"error": f"AI分析失敗: {str(e)}"}
        
        return {
            "success": True,
            "message": "音頻處理完成",
            "text": extracted_text,
            "ai_analysis": ai_response,
            "file_info": audio_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"音頻處理失敗: {str(e)}")

@router.post("/audio/transcribe", tags=["Audio Processing"])
async def transcribe_audio(
    audio_file: UploadFile = File(...)
):
    """
    僅進行語音轉文字，不進行AI分析
    """
    try:
        logger.info(f"Transcribing audio file: {audio_file.filename}")
        
        # 處理音頻文件
        audio_result = await audio_service.process_audio_file(audio_file)
        
        if not audio_result["success"]:
            raise HTTPException(status_code=400, detail=audio_result["error"])
        
        return {
            "success": True,
            "text": audio_result["text"],
            "file_info": audio_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"語音轉文字失敗: {str(e)}")

@router.get("/audio/supported-formats", tags=["Audio Processing"])
async def get_supported_audio_formats():
    """
    獲取支援的音頻格式
    """
    return {
        "supported_formats": audio_service.get_supported_formats(),
        "max_file_size": audio_service.get_max_file_size(),
        "max_file_size_mb": audio_service.get_max_file_size() // (1024 * 1024)
    }

@router.post("/audio/chat", tags=["Audio Chat"])
async def audio_chat(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form("default")
):
    """
    音頻聊天：上傳音頻文件，轉換為文字後進行AI對話
    """
    try:
        logger.info(f"Audio chat request: {audio_file.filename} (Session: {session_id})")
        
        # 處理音頻文件
        audio_result = await audio_service.process_audio_file(audio_file)
        
        if not audio_result["success"]:
            raise HTTPException(status_code=400, detail=audio_result["error"])
        
        extracted_text = audio_result["text"]
        
        if not extracted_text:
            return {
                "success": False,
                "message": "無法從音頻中提取文字內容",
                "response": "抱歉，我無法理解您的語音內容，請重新錄製或使用文字輸入。",
                "source": "audio_error"
            }
        
        # 使用AI服務處理提取的文字
        ai_result = await ai_service.generate_response(extracted_text, session_id)
        
        if "error" in ai_result:
            return {
                "success": False,
                "message": "AI處理失敗",
                "response": ai_result["error"],
                "source": "ai_error",
                "extracted_text": extracted_text
            }
        
        return {
            "success": True,
            "response": ai_result["response"],
            "metadata": ai_result.get("metadata", {}),
            "source": "unified_ai",
            "extracted_text": extracted_text,
            "file_info": audio_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"音頻聊天失敗: {str(e)}")
