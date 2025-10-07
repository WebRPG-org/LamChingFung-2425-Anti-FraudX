from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import logging
from datetime import datetime

from app.file_service import file_service
from app.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/file/upload", tags=["File Processing"])
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form("default"),
    use_ai_analysis: Optional[bool] = Form(True)
):
    """
    上傳文件並提取文字內容
    """
    try:
        logger.info(f"Processing file: {file.filename} (Session: {session_id})")
        
        # 處理文件
        file_result = await file_service.process_file(file)
        
        if not file_result["success"]:
            raise HTTPException(status_code=400, detail=file_result["error"])
        
        extracted_text = file_result["text"]
        
        if not extracted_text:
            return {
                "success": False,
                "message": "無法從文件中提取文字內容",
                "text": "",
                "file_info": file_result["file_info"]
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
            "message": "文件處理完成",
            "text": extracted_text,
            "ai_analysis": ai_response,
            "file_info": file_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"文件處理失敗: {str(e)}")

@router.post("/file/extract-text", tags=["File Processing"])
async def extract_text_from_file(
    file: UploadFile = File(...)
):
    """
    僅提取文件文字內容，不進行AI分析
    """
    try:
        logger.info(f"Extracting text from file: {file.filename}")
        
        # 處理文件
        file_result = await file_service.process_file(file)
        
        if not file_result["success"]:
            raise HTTPException(status_code=400, detail=file_result["error"])
        
        return {
            "success": True,
            "text": file_result["text"],
            "file_info": file_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"文字提取失敗: {str(e)}")

@router.get("/file/supported-formats", tags=["File Processing"])
async def get_supported_file_formats():
    """
    獲取支援的文件格式
    """
    return {
        "supported_formats": file_service.get_supported_formats(),
        "max_file_size": file_service.get_max_file_size(),
        "max_file_size_mb": file_service.get_max_file_size() // (1024 * 1024),
        "max_text_length": file_service.get_max_text_length()
    }

@router.post("/file/chat", tags=["File Chat"])
async def file_chat(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form("default")
):
    """
    文件聊天：上傳文件，提取文字後進行AI對話
    """
    try:
        logger.info(f"File chat request: {file.filename} (Session: {session_id})")
        
        # 處理文件
        file_result = await file_service.process_file(file)
        
        if not file_result["success"]:
            raise HTTPException(status_code=400, detail=file_result["error"])
        
        extracted_text = file_result["text"]
        
        if not extracted_text:
            return {
                "success": False,
                "message": "無法從文件中提取文字內容",
                "response": "抱歉，我無法從這個文件中提取到有效的文字內容，請檢查文件格式或內容。",
                "source": "file_error"
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
            "file_info": file_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"文件聊天失敗: {str(e)}")

@router.post("/file/analyze-document", tags=["Document Analysis"])
async def analyze_document(
    file: UploadFile = File(...),
    analysis_type: Optional[str] = Form("fraud_detection"),
    session_id: Optional[str] = Form("default")
):
    """
    專門用於文檔分析的端點，針對金融詐騙檢測優化
    """
    try:
        logger.info(f"Document analysis request: {file.filename} (Type: {analysis_type})")
        
        # 處理文件
        file_result = await file_service.process_file(file)
        
        if not file_result["success"]:
            raise HTTPException(status_code=400, detail=file_result["error"])
        
        extracted_text = file_result["text"]
        
        if not extracted_text:
            return {
                "success": False,
                "message": "無法從文件中提取文字內容",
                "response": "抱歉，我無法從這個文件中提取到有效的文字內容。",
                "source": "file_error"
            }
        
        # 根據分析類型構建專門的提示
        if analysis_type == "fraud_detection":
            prompt = f"""
            你是一個專業的香港金融詐騙分析專家。請仔細分析以下文檔內容，識別潛在的詐騙風險和可疑元素。

            文檔內容：
            ---
            {extracted_text}
            ---

            請提供詳細的分析報告，包括：
            1. 風險評估等級（高/中/低/安全）
            2. 識別的可疑元素
            3. 具體的風險點
            4. 建議的防範措施
            5. 相關的監管信息

            請使用繁體中文回應，結構清晰，重點突出。
            """
        else:
            prompt = extracted_text
        
        # 使用AI服務處理
        ai_result = await ai_service.generate_response(prompt, session_id)
        
        if "error" in ai_result:
            return {
                "success": False,
                "message": "文檔分析失敗",
                "response": ai_result["error"],
                "source": "ai_error",
                "extracted_text": extracted_text
            }
        
        return {
            "success": True,
            "response": ai_result["response"],
            "metadata": ai_result.get("metadata", {}),
            "source": "document_analysis",
            "analysis_type": analysis_type,
            "extracted_text": extracted_text,
            "file_info": file_result["file_info"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"文檔分析失敗: {str(e)}")
