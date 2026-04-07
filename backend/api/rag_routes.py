"""
api/rag_routes.py - RAG系統API路由
提供RAG相關的API端點
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from services.session_manager_with_rag import get_session_manager_with_rag
from services.firestore_rag_fraud_loader import FirestoreRAGContextProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])

# ============================================================
# 數據模型
# ============================================================

class InitializeSessionRequest(BaseModel):
    """初始化Session請求"""
    session_id: str
    scam_type: str
    player_role: str  # scammer, expert, victim


class SendMessageRequest(BaseModel):
    """發送消息請求"""
    message: str
    role: Optional[str] = None


class EvaluateDialogueRequest(BaseModel):
    """評估對話請求"""
    session_id: str


# ============================================================
# API端點
# ============================================================

@router.post("/session/initialize")
async def initialize_session(request: InitializeSessionRequest) -> Dict[str, Any]:
    """
    初始化Session
    
    Args:
        request: 初始化請求
    
    Returns:
        初始化結果
    """
    try:
        logger.info(f"🔄 初始化Session: {request.session_id}")
        
        session_manager = get_session_manager_with_rag()
        
        result = await session_manager.initialize_session(
            session_id=request.session_id,
            scam_type=request.scam_type,
            player_role=request.player_role
        )
        
        logger.info(f"✅ Session初始化成功: {request.session_id}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Session初始化失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/send")
async def send_message(request: SendMessageRequest) -> Dict[str, Any]:
    """
    發送消息並進行完整分析
    
    Args:
        request: 消息請求
    
    Returns:
        包含LLM回應和分析結果的字典
    """
    try:
        logger.info(f"📨 發送消息: {request.message[:50]}...")
        
        session_manager = get_session_manager_with_rag()
        
        result = await session_manager.send_message(
            message=request.message,
            role=request.role
        )
        
        logger.info(f"✅ 消息處理完成")
        return result
    
    except Exception as e:
        logger.error(f"❌ 消息處理失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dialogue/evaluate")
async def evaluate_dialogue(request: EvaluateDialogueRequest) -> Dict[str, Any]:
    """
    評估對話（使用RAG數據）
    
    Args:
        request: 評估請求
    
    Returns:
        評估結果
    """
    try:
        logger.info(f"🔄 評估對話: {request.session_id}")
        
        session_manager = get_session_manager_with_rag()
        
        evaluation = await session_manager.evaluate_dialogue()
        
        logger.info(f"✅ 對話評估完成")
        return evaluation
    
    except Exception as e:
        logger.error(f"❌ 對話評估失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dialogue/report/{session_id}")
async def get_session_report(session_id: str) -> Dict[str, Any]:
    """
    獲取Session報告
    
    Args:
        session_id: Session ID
    
    Returns:
        完整的Session報告
    """
    try:
        logger.info(f"📋 獲取Session報告: {session_id}")
        
        session_manager = get_session_manager_with_rag()
        
        report = await session_manager.get_session_report()
        
        logger.info(f"✅ 報告生成完成")
        return report
    
    except Exception as e:
        logger.error(f"❌ 報告生成失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/scammer/{scam_type}")
async def get_scammer_context(scam_type: str) -> Dict[str, Any]:
    """
    獲取騙徒上下文
    
    Args:
        scam_type: 騙案類型
    
    Returns:
        騙徒上下文
    """
    try:
        logger.info(f"📖 獲取騙徒上下文: {scam_type}")
        
        provider = FirestoreRAGContextProvider()
        
        context = await provider.get_scammer_context(scam_type)
        
        return {
            "status": "success",
            "scam_type": scam_type,
            "context": context
        }
    
    except Exception as e:
        logger.error(f"❌ 獲取騙徒上下文失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/expert/{scam_type}")
async def get_expert_context(scam_type: str) -> Dict[str, Any]:
    """
    獲取專家上下文
    
    Args:
        scam_type: 騙案類型
    
    Returns:
        專家上下文
    """
    try:
        logger.info(f"📖 獲取專家上下文: {scam_type}")
        
        provider = FirestoreRAGContextProvider()
        
        context = await provider.get_expert_context(scam_type)
        
        return {
            "status": "success",
            "scam_type": scam_type,
            "context": context
        }
    
    except Exception as e:
        logger.error(f"❌ 獲取專家上下文失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warning-signs/{scam_type}")
async def get_warning_signs(scam_type: str) -> Dict[str, Any]:
    """
    獲取警告信號
    
    Args:
        scam_type: 騙案類型
    
    Returns:
        警告信號列表
    """
    try:
        logger.info(f"⚠️ 獲取警告信號: {scam_type}")
        
        provider = FirestoreRAGContextProvider()
        
        warning_signs = await provider.get_warning_signs(scam_type)
        
        return {
            "status": "success",
            "scam_type": scam_type,
            "warning_signs": warning_signs
        }
    
    except Exception as e:
        logger.error(f"❌ 獲取警告信號失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prevention-tips/{scam_type}")
async def get_prevention_tips(scam_type: str) -> Dict[str, Any]:
    """
    獲取防騙建議
    
    Args:
        scam_type: 騙案類型
    
    Returns:
        防騙建議列表
    """
    try:
        logger.info(f"💡 獲取防騙建議: {scam_type}")
        
        provider = FirestoreRAGContextProvider()
        
        prevention_tips = await provider.get_prevention_tips(scam_type)
        
        return {
            "status": "success",
            "scam_type": scam_type,
            "prevention_tips": prevention_tips
        }
    
    except Exception as e:
        logger.error(f"❌ 獲取防騙建議失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/load-from-file")
async def load_data_from_file(file_type: str) -> Dict[str, Any]:
    """
    從本地文件加載數據到Firestore
    
    Args:
        file_type: "generator" 或 "adcc"
    
    Returns:
        加載結果
    """
    try:
        import os
        from services.firestore_rag_fraud_loader import FirestoreRAGDataLoader
        
        logger.info(f"📥 開始加載{file_type}數據到Firestore...")
        
        loader = FirestoreRAGDataLoader()
        
        if file_type == "generator":
            generator_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'massive_generator.py')
            if not os.path.exists(generator_path):
                raise FileNotFoundError(f"生成式數據文件不存在: {generator_path}")
            
            count = await loader.load_generator_data(generator_path)
            logger.info(f"✅ 生成式數據加載完成: {count}個特徵")
            return {
                "status": "success",
                "file_type": "generator",
                "count": count,
                "message": f"成功加載{count}個生成式特徵到Firestore"
            }
        
        elif file_type == "adcc":
            adcc_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'scraped_alerts.json')
            if not os.path.exists(adcc_path):
                raise FileNotFoundError(f"ADCC數據文件不存在: {adcc_path}")
            
            count = await loader.load_adcc_data(adcc_path)
            logger.info(f"✅ ADCC數據加載完成: {count}個案例")
            return {
                "status": "success",
                "file_type": "adcc",
                "count": count,
                "message": f"成功加載{count}個ADCC案例到Firestore"
            }
        
        else:
            raise ValueError(f"不支持的文件類型: {file_type}")
    
    except Exception as e:
        logger.error(f"❌ 數據加載失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/check-exists")
async def check_data_exists() -> Dict[str, Any]:
    """
    檢查Firestore中是否已有RAG數據
    
    Returns:
        數據存在狀態
    """
    try:
        from services.firestore_rag_fraud_loader import FirestoreRAGContextProvider
        
        provider = FirestoreRAGContextProvider()
        has_data = await provider.check_data_exists()
        
        return {
            "status": "ok",
            "has_data": has_data,
            "message": "Firestore中已有RAG數據" if has_data else "Firestore中沒有RAG數據，需要加載"
        }
    
    except Exception as e:
        logger.error(f"❌ 檢查數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def rag_status() -> Dict[str, Any]:
    """
    獲取RAG系統狀態
    
    Returns:
        系統狀態
    """
    try:
        from services.firestore_rag_fraud_loader import FirestoreRAGContextProvider
        
        provider = FirestoreRAGContextProvider()
        has_data = await provider.check_data_exists()
        
        return {
            "status": "ok",
            "rag_system": "initialized",
            "has_firestore_data": has_data,
            "message": "RAG系統已初始化並準備就緒",
            "endpoints": {
                "initialize_session": "POST /api/rag/session/initialize",
                "send_message": "POST /api/rag/message/send",
                "evaluate_dialogue": "POST /api/rag/dialogue/evaluate",
                "get_report": "GET /api/rag/dialogue/report/{session_id}",
                "scammer_context": "GET /api/rag/context/scammer/{scam_type}",
                "expert_context": "GET /api/rag/context/expert/{scam_type}",
                "warning_signs": "GET /api/rag/warning-signs/{scam_type}",
                "prevention_tips": "GET /api/rag/prevention-tips/{scam_type}",
                "load_data": "POST /api/rag/data/load-from-file?file_type=generator|adcc",
                "check_data": "GET /api/rag/data/check-exists",
                "status": "GET /api/rag/status"
            }
        }
    
    except Exception as e:
        logger.error(f"❌ 獲取系統狀態失敗: {e}")
        return {
            "status": "error",
            "rag_system": "failed",
            "error": str(e)
        }

