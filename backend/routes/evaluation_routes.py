"""
backend/routes/evaluation_routes.py - 評估路由端點
提供REST API端點用於評估、處理、驗證
"""

import logging
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel

from backend.services.api_integration import get_api_integration

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])

# 獲取API集成實例
api_integration = get_api_integration()


# ============ 請求模型 ============

class ExpertEvaluationRequest(BaseModel):
    """專家評估請求"""
    session_id: str
    scam_type: str
    user_message: str
    expert_response: str
    metadata: Optional[Dict[str, Any]] = None


class ResponseProcessingRequest(BaseModel):
    """回應處理請求"""
    response: str
    processing_type: str = "full"  # 'full', 'conversational', 'length_control'


class QualityValidationRequest(BaseModel):
    """質量驗證請求"""
    response: str
    scam_type: str


class SystemPromptRequest(BaseModel):
    """System Prompt請求"""
    scam_type: str


# ============ 端點 ============

@router.post("/expert-evaluation")
async def expert_evaluation(request: ExpertEvaluationRequest) -> Dict[str, Any]:
    """
    處理專家評估
    
    Args:
        request: 專家評估請求
    
    Returns:
        評估結果
    """
    try:
        logger.info(f"📨 POST /expert-evaluation - session: {request.session_id}")
        
        result = await api_integration.handle_expert_evaluation(
            session_id=request.session_id,
            scam_type=request.scam_type,
            user_message=request.user_message,
            expert_response=request.expert_response,
            metadata=request.metadata
        )
        
        if not result.get('success'):
            logger.error(f"❌ Expert evaluation failed: {result.get('error')}")
            raise HTTPException(
                status_code=result.get('status_code', 500),
                detail=result.get('error')
            )
        
        logger.info(f"✅ Expert evaluation completed")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in expert evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-summary/{session_id}")
async def session_summary(session_id: str) -> Dict[str, Any]:
    """
    獲取會話摘要
    
    Args:
        session_id: 會話ID
    
    Returns:
        會話摘要
    """
    try:
        logger.info(f"📨 GET /session-summary/{session_id}")
        
        result = await api_integration.handle_session_summary(session_id)
        
        if not result.get('success'):
            logger.error(f"❌ Session summary failed: {result.get('error')}")
            raise HTTPException(
                status_code=result.get('status_code', 500),
                detail=result.get('error')
            )
        
        logger.info(f"✅ Session summary retrieved")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-response")
async def process_response(request: ResponseProcessingRequest) -> Dict[str, Any]:
    """
    處理回應（口語化、長度控制等）
    
    Args:
        request: 回應處理請求
    
    Returns:
        處理結果
    """
    try:
        logger.info(f"📨 POST /process-response - type: {request.processing_type}")
        
        result = await api_integration.handle_response_processing(
            response=request.response,
            processing_type=request.processing_type
        )
        
        if not result.get('success'):
            logger.error(f"❌ Response processing failed: {result.get('error')}")
            raise HTTPException(
                status_code=result.get('status_code', 500),
                detail=result.get('error')
            )
        
        logger.info(f"✅ Response processing completed")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in response processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-quality")
async def validate_quality(request: QualityValidationRequest) -> Dict[str, Any]:
    """
    驗證回應質量
    
    Args:
        request: 質量驗證請求
    
    Returns:
        驗證結果
    """
    try:
        logger.info(f"📨 POST /validate-quality - scam_type: {request.scam_type}")
        
        result = await api_integration.handle_quality_validation(
            response=request.response,
            scam_type=request.scam_type
        )
        
        if not result.get('success'):
            logger.error(f"❌ Quality validation failed: {result.get('error')}")
            raise HTTPException(
                status_code=result.get('status_code', 500),
                detail=result.get('error')
            )
        
        logger.info(f"✅ Quality validation completed")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in quality validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system-prompt")
async def system_prompt(request: SystemPromptRequest) -> Dict[str, Any]:
    """
    生成System Prompt
    
    Args:
        request: System Prompt請求
    
    Returns:
        生成的System Prompt
    """
    try:
        logger.info(f"📨 POST /system-prompt - scam_type: {request.scam_type}")
        
        result = await api_integration.handle_system_prompt_generation(
            scam_type=request.scam_type
        )
        
        if not result.get('success'):
            logger.error(f"❌ System prompt generation failed: {result.get('error')}")
            raise HTTPException(
                status_code=result.get('status_code', 500),
                detail=result.get('error')
            )
        
        logger.info(f"✅ System prompt generation completed")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in system prompt generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康檢查端點
    
    Returns:
        健康狀態
    """
    try:
        logger.info(f"📨 GET /health")
        
        return {
            'success': True,
            'status': 'healthy',
            'service': 'evaluation-routes',
            'version': '1.0.0'
        }
    
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


