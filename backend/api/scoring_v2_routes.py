"""
評分系統 API 路由 (v2)
整合新的 VictimEvaluator 混合評分系統
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import logging

from utils.victim_evaluator import VictimEvaluator
from agents.victim import VictimAgent
from utils.performance_tracker import PerformanceTracker
from utils.scoring_monitor import get_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/scoring", tags=["scoring-v2"])

# 評估器緩存
_evaluator_cache: Dict[str, VictimEvaluator] = {}

# 獲取監控器
monitor = get_monitor()


class Message(BaseModel):
    """對話訊息"""
    role: str = Field(..., description="角色: scammer/victim/expert")
    content: str = Field(..., description="訊息內容")
    strategy: Optional[str] = Field(None, description="策略類型（可選）")


class EvaluationRequest(BaseModel):
    """評估請求"""
    conversation_history: List[Message] = Field(..., description="對話歷史")
    persona_type: str = Field("average", description="人設類型: elderly/average/overconfident/student")
    initial_trust: int = Field(50, ge=0, le=100, description="初始信任度")
    rule_weight: float = Field(0.7, ge=0, le=1, description="規則評分權重")
    agent_weight: float = Field(0.3, ge=0, le=1, description="Agent評分權重")
    enable_agent_scoring: bool = Field(True, description="是否啟用Agent評分")


class EvaluationResponse(BaseModel):
    """評估回應"""
    success: bool
    trust_change: float
    confidence: float
    method: str
    rule_score: Dict
    agent_score: Dict
    timestamp: str
    evaluation_time_ms: float


class HealthResponse(BaseModel):
    """健康檢查回應"""
    status: str
    version: str
    evaluator_cache_size: int
    timestamp: str


def get_or_create_evaluator(
    persona_type: str,
    rule_weight: float = 0.7,
    agent_weight: float = 0.3,
    enable_agent_scoring: bool = True
) -> VictimEvaluator:
    """
    獲取或創建評估器實例（帶緩存）
    
    Args:
        persona_type: 人設類型
        rule_weight: 規則權重
        agent_weight: Agent權重
        enable_agent_scoring: 是否啟用Agent評分
    
    Returns:
        VictimEvaluator實例
    """
    cache_key = f"{persona_type}_{rule_weight}_{agent_weight}_{enable_agent_scoring}"
    
    if cache_key not in _evaluator_cache:
        logger.info(f"創建新的評估器實例: {cache_key}")
        
        try:
            victim_agent = VictimAgent(persona_type=persona_type)
            performance_tracker = PerformanceTracker(victim_persona=persona_type)
            
            evaluator = VictimEvaluator(
                victim_agent=victim_agent,
                performance_tracker=performance_tracker,
                rule_weight=rule_weight,
                agent_weight=agent_weight,
                enable_agent_scoring=enable_agent_scoring
            )
            
            _evaluator_cache[cache_key] = evaluator
            logger.info(f"✅ 評估器創建成功: {cache_key}")
            
        except Exception as e:
            logger.error(f"❌ 評估器創建失敗: {e}")
            raise HTTPException(status_code=500, detail=f"評估器初始化失敗: {str(e)}")
    
    return _evaluator_cache[cache_key]


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_conversation(request: EvaluationRequest):
    """
    評估對話
    
    使用新的混合評分系統評估對話，返回信任度變化和詳細分析
    """
    start_time = datetime.now()
    
    try:
        # 驗證輸入
        if not request.conversation_history:
            raise HTTPException(status_code=400, detail="對話歷史不能為空")
        
        if request.rule_weight + request.agent_weight != 1.0:
            raise HTTPException(
                status_code=400,
                detail=f"權重總和必須為1.0，當前為{request.rule_weight + request.agent_weight}"
            )
        
        # 獲取評估器
        evaluator = get_or_create_evaluator(
            persona_type=request.persona_type,
            rule_weight=request.rule_weight,
            agent_weight=request.agent_weight,
            enable_agent_scoring=request.enable_agent_scoring
        )
        
        # 轉換訊息格式
        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "strategy": msg.strategy or "none"
            }
            for msg in request.conversation_history
        ]
        
        # 執行評估
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation_history,
            persona_type=request.persona_type,
            initial_trust=request.initial_trust
        )
        
        # 計算執行時間
        evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 記錄到監控系統
        monitor.record_evaluation(
            persona_type=request.persona_type,
            trust_change=result.trust_change,
            confidence=result.confidence,
            method=result.method,
            latency_ms=evaluation_time,
            success=True
        )
        
        logger.info(
            f"✅ 評估完成: persona={request.persona_type}, "
            f"trust_change={result.trust_change:+.2f}, "
            f"method={result.method}, "
            f"time={evaluation_time:.0f}ms"
        )
        
        return EvaluationResponse(
            success=True,
            trust_change=result.trust_change,
            confidence=result.confidence,
            method=result.method,
            rule_score=result.rule_score,
            agent_score=result.agent_score,
            timestamp=result.timestamp,
            evaluation_time_ms=evaluation_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 記錄失敗到監控系統
        evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
        monitor.record_evaluation(
            persona_type=request.persona_type,
            trust_change=0,
            confidence=0,
            method="error",
            latency_ms=evaluation_time,
            success=False,
            error_message=str(e)
        )
        
        logger.error(f"❌ 評估失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"評估失敗: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康檢查
    
    返回服務狀態和統計信息
    """
    return HealthResponse(
        status="healthy",
        version="2.0",
        evaluator_cache_size=len(_evaluator_cache),
        timestamp=datetime.now().isoformat()
    )


@router.post("/clear-cache")
async def clear_cache():
    """
    清除評估器緩存
    
    用於釋放內存或重新初始化評估器
    """
    global _evaluator_cache
    cache_size = len(_evaluator_cache)
    _evaluator_cache.clear()
    
    logger.info(f"🗑️ 清除評估器緩存: {cache_size}個實例")
    
    return {
        "success": True,
        "message": f"已清除{cache_size}個評估器實例",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_statistics():
    """
    獲取統計信息
    
    返回評估器的統計數據
    """
    stats = {}
    
    for cache_key, evaluator in _evaluator_cache.items():
        stats[cache_key] = {
            "total_evaluations": evaluator.stats["total_evaluations"],
            "rule_only": evaluator.stats["rule_only"],
            "agent_only": evaluator.stats["agent_only"],
            "hybrid": evaluator.stats["hybrid"],
            "avg_confidence": evaluator.stats["avg_confidence"],
            "evaluation_history_size": len(evaluator.evaluation_history)
        }
    
    return {
        "success": True,
        "cache_size": len(_evaluator_cache),
        "evaluators": stats,
        "timestamp": datetime.now().isoformat()
    }


# 使用示例
"""
# 評估對話
POST /api/v2/scoring/evaluate
{
    "conversation_history": [
        {"role": "scammer", "content": "你好，我是警察", "strategy": "authority"},
        {"role": "victim", "content": "有什麼事嗎？"},
        {"role": "scammer", "content": "你的帳戶有問題", "strategy": "urgency"}
    ],
    "persona_type": "elderly",
    "initial_trust": 50,
    "rule_weight": 0.7,
    "agent_weight": 0.3,
    "enable_agent_scoring": true
}

# 回應
{
    "success": true,
    "trust_change": -15.5,
    "confidence": 85.0,
    "method": "hybrid",
    "rule_score": {...},
    "agent_score": {...},
    "timestamp": "2026-02-10T23:20:00",
    "evaluation_time_ms": 245.3
}

# 健康檢查
GET /api/v2/scoring/health

# 獲取統計
GET /api/v2/scoring/stats

# 清除緩存
POST /api/v2/scoring/clear-cache
"""
