"""
api/evaluation_routes.py - 評估系統API路由
提供對話評估、計分、報告等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from services.session_manager_with_rag import get_session_manager_with_rag
from services.tactic_analyzer import get_tactic_analyzer
from services.verdict_judge import get_verdict_judge
from services.scam_scoring_v2 import get_scam_scorer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])

# ============================================================
# 數據模型
# ============================================================

class AnalyzeTacticRequest(BaseModel):
    """分析騙術請求"""
    message: str
    role: str  # scammer or expert


class JudgeVerdictRequest(BaseModel):
    """判定勝負請求"""
    message: str
    role: str


class UpdateScoreRequest(BaseModel):
    """更新評分請求"""
    session_id: str
    victim_response: str
    role: str  # scammer or expert


class GetSessionEvaluationRequest(BaseModel):
    """獲取Session評估請求"""
    session_id: str


# ============================================================
# API端點 - 騙術分析
# ============================================================

@router.post("/tactic/analyze")
async def analyze_tactic(request: AnalyzeTacticRequest) -> Dict[str, Any]:
    """
    分析騙術/防騙方向
    
    Args:
        request: 分析請求
    
    Returns:
        騙術分析結果
    """
    try:
        logger.info(f"🔍 分析騙術: {request.message[:50]}...")
        
        analyzer = get_tactic_analyzer()
        
        result = await analyzer.analyze_tactic(
            message=request.message,
            role=request.role
        )
        
        logger.info(f"✅ 騙術分析完成")
        return result
    
    except Exception as e:
        logger.error(f"❌ 騙術分析失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tactic/batch-analyze")
async def batch_analyze_tactics(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    批量分析騙術
    
    Args:
        messages: 消息列表 [{"message": "...", "role": "..."}]
    
    Returns:
        批量分析結果
    """
    try:
        logger.info(f"🔍 批量分析騙術: {len(messages)}條消息")
        
        analyzer = get_tactic_analyzer()
        
        results = []
        for msg in messages:
            result = await analyzer.analyze_tactic(
                message=msg["message"],
                role=msg["role"]
            )
            results.append(result)
        
        logger.info(f"✅ 批量分析完成")
        return {
            "status": "success",
            "total": len(messages),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"❌ 批量分析失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# API端點 - 勝負判定
# ============================================================

@router.post("/verdict/judge")
async def judge_verdict(request: JudgeVerdictRequest) -> Dict[str, Any]:
    """
    判定勝負
    
    Args:
        request: 判定請求
    
    Returns:
        勝負判定結果
    """
    try:
        logger.info(f"⚖️ 判定勝負: {request.message[:50]}...")
        
        judge = get_verdict_judge()
        
        result = await judge.judge_verdict(
            message=request.message,
            role=request.role
        )
        
        logger.info(f"✅ 勝負判定完成")
        return result
    
    except Exception as e:
        logger.error(f"❌ 勝負判定失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verdict/batch-judge")
async def batch_judge_verdicts(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    批量判定勝負
    
    Args:
        messages: 消息列表 [{"message": "...", "role": "..."}]
    
    Returns:
        批量判定結果
    """
    try:
        logger.info(f"⚖️ 批量判定勝負: {len(messages)}條消息")
        
        judge = get_verdict_judge()
        
        results = []
        for msg in messages:
            result = await judge.judge_verdict(
                message=msg["message"],
                role=msg["role"]
            )
            results.append(result)
        
        logger.info(f"✅ 批量判定完成")
        return {
            "status": "success",
            "total": len(messages),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"❌ 批量判定失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# API端點 - 評分系統
# ============================================================

@router.post("/score/update")
async def update_score(request: UpdateScoreRequest) -> Dict[str, Any]:
    """
    更新評分
    
    Args:
        request: 評分更新請求
    
    Returns:
        更新結果
    """
    try:
        logger.info(f"📊 更新評分: {request.session_id}")
        
        scorer = get_scam_scorer()
        
        result = await scorer.update_score(
            session_id=request.session_id,
            victim_response=request.victim_response,
            role=request.role
        )
        
        logger.info(f"✅ 評分更新完成")
        return result
    
    except Exception as e:
        logger.error(f"❌ 評分更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/current/{session_id}")
async def get_current_score(session_id: str) -> Dict[str, Any]:
    """
    獲取當前評分
    
    Args:
        session_id: Session ID
    
    Returns:
        當前評分
    """
    try:
        logger.info(f"📊 獲取當前評分: {session_id}")
        
        scorer = get_scam_scorer()
        
        score = await scorer.get_current_score(session_id)
        
        logger.info(f"✅ 評分獲取完成")
        return score
    
    except Exception as e:
        logger.error(f"❌ 評分獲取失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/history/{session_id}")
async def get_score_history(session_id: str) -> Dict[str, Any]:
    """
    獲取評分歷史
    
    Args:
        session_id: Session ID
    
    Returns:
        評分歷史
    """
    try:
        logger.info(f"📊 獲取評分歷史: {session_id}")
        
        scorer = get_scam_scorer()
        
        history = await scorer.get_score_history(session_id)
        
        logger.info(f"✅ 評分歷史獲取完成")
        return history
    
    except Exception as e:
        logger.error(f"❌ 評分歷史獲取失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# API端點 - 完整評估
# ============================================================

@router.post("/session/complete")
async def complete_session_evaluation(request: GetSessionEvaluationRequest) -> Dict[str, Any]:
    """
    完成Session評估
    
    Args:
        request: 評估請求
    
    Returns:
        完整評估結果
    """
    try:
        logger.info(f"📋 完成Session評估: {request.session_id}")
        
        session_manager = get_session_manager_with_rag()
        
        evaluation = await session_manager.complete_evaluation(request.session_id)
        
        logger.info(f"✅ Session評估完成")
        return evaluation
    
    except Exception as e:
        logger.error(f"❌ Session評估失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/report/{session_id}")
async def get_evaluation_report(session_id: str) -> Dict[str, Any]:
    """
    獲取評估報告
    
    Args:
        session_id: Session ID
    
    Returns:
        評估報告
    """
    try:
        logger.info(f"📋 獲取評估報告: {session_id}")
        
        session_manager = get_session_manager_with_rag()
        
        report = await session_manager.get_evaluation_report(session_id)
        
        logger.info(f"✅ 報告生成完成")
        return report
    
    except Exception as e:
        logger.error(f"❌ 報告生成失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/summary/{session_id}")
async def get_session_summary(session_id: str) -> Dict[str, Any]:
    """
    獲取Session摘要
    
    Args:
        session_id: Session ID
    
    Returns:
        Session摘要
    """
    try:
        logger.info(f"📋 獲取Session摘要: {session_id}")
        
        session_manager = get_session_manager_with_rag()
        
        summary = await session_manager.get_session_summary(session_id)
        
        logger.info(f"✅ 摘要生成完成")
        return summary
    
    except Exception as e:
        logger.error(f"❌ 摘要生成失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# API端點 - 系統狀態
# ============================================================

@router.get("/status")
async def evaluation_status() -> Dict[str, Any]:
    """
    獲取評估系統狀態
    
    Returns:
        系統狀態
    """
    try:
        return {
            "status": "ok",
            "evaluation_system": "initialized",
            "message": "評估系統已初始化並準備就緒",
            "endpoints": {
                "analyze_tactic": "POST /api/evaluation/tactic/analyze",
                "batch_analyze": "POST /api/evaluation/tactic/batch-analyze",
                "judge_verdict": "POST /api/evaluation/verdict/judge",
                "batch_judge": "POST /api/evaluation/verdict/batch-judge",
                "update_score": "POST /api/evaluation/score/update",
                "current_score": "GET /api/evaluation/score/current/{session_id}",
                "score_history": "GET /api/evaluation/score/history/{session_id}",
                "complete_session": "POST /api/evaluation/session/complete",
                "get_report": "GET /api/evaluation/session/report/{session_id}",
                "get_summary": "GET /api/evaluation/session/summary/{session_id}",
                "status": "GET /api/evaluation/status"
            }
        }
    
    except Exception as e:
        logger.error(f"❌ 獲取系統狀態失敗: {e}")
        return {
            "status": "error",
            "evaluation_system": "failed",
            "error": str(e)
        }


