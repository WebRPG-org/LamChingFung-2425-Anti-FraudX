"""
批量評估API
支持一次性評估多個對話
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import logging

from utils.victim_evaluator import VictimEvaluator
from agents.victim import VictimAgent
from utils.performance_tracker import PerformanceTracker
from utils.scoring_monitor import get_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/batch", tags=["batch-evaluation"])

# 評估器緩存（複用scoring_v2_routes的緩存）
_evaluator_cache: Dict[str, VictimEvaluator] = {}


class Message(BaseModel):
    """對話訊息"""
    role: str = Field(..., description="角色: scammer/victim/expert")
    content: str = Field(..., description="訊息內容")
    strategy: Optional[str] = Field(None, description="策略類型（可選）")


class ConversationRequest(BaseModel):
    """單個對話請求"""
    conversation_id: Optional[str] = Field(None, description="對話ID（可選）")
    conversation_history: List[Message] = Field(..., description="對話歷史")
    persona_type: str = Field("average", description="人設類型")
    initial_trust: int = Field(50, ge=0, le=100, description="初始信任度")


class BatchEvaluationRequest(BaseModel):
    """批量評估請求"""
    conversations: List[ConversationRequest] = Field(..., description="對話列表")
    rule_weight: float = Field(0.7, ge=0, le=1, description="規則評分權重")
    agent_weight: float = Field(0.3, ge=0, le=1, description="Agent評分權重")
    enable_agent_scoring: bool = Field(True, description="是否啟用Agent評分")
    max_concurrent: int = Field(5, ge=1, le=20, description="最大併發數")


class ConversationResult(BaseModel):
    """單個對話結果"""
    conversation_id: Optional[str]
    success: bool
    trust_change: Optional[float] = None
    confidence: Optional[float] = None
    method: Optional[str] = None
    evaluation_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class BatchEvaluationResponse(BaseModel):
    """批量評估回應"""
    success: bool
    total_conversations: int
    successful_evaluations: int
    failed_evaluations: int
    total_time_ms: float
    results: List[ConversationResult]


def get_or_create_evaluator(
    persona_type: str,
    rule_weight: float = 0.7,
    agent_weight: float = 0.3,
    enable_agent_scoring: bool = True
) -> VictimEvaluator:
    """獲取或創建評估器實例（帶緩存）"""
    cache_key = f"{persona_type}_{rule_weight}_{agent_weight}_{enable_agent_scoring}"
    
    if cache_key not in _evaluator_cache:
        logger.info(f"創建新的評估器實例: {cache_key}")
        
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
    
    return _evaluator_cache[cache_key]


async def evaluate_single_conversation(
    conversation: ConversationRequest,
    rule_weight: float,
    agent_weight: float,
    enable_agent_scoring: bool,
    monitor
) -> ConversationResult:
    """評估單個對話"""
    start_time = datetime.now()
    
    try:
        # 獲取評估器
        evaluator = get_or_create_evaluator(
            persona_type=conversation.persona_type,
            rule_weight=rule_weight,
            agent_weight=agent_weight,
            enable_agent_scoring=enable_agent_scoring
        )
        
        # 轉換訊息格式
        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "strategy": msg.strategy or "none"
            }
            for msg in conversation.conversation_history
        ]
        
        # 執行評估
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation_history,
            persona_type=conversation.persona_type,
            initial_trust=conversation.initial_trust
        )
        
        # 計算執行時間
        evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 記錄到監控系統
        monitor.record_evaluation(
            persona_type=conversation.persona_type,
            trust_change=result.trust_change,
            confidence=result.confidence,
            method=result.method,
            latency_ms=evaluation_time,
            success=True
        )
        
        return ConversationResult(
            conversation_id=conversation.conversation_id,
            success=True,
            trust_change=result.trust_change,
            confidence=result.confidence,
            method=result.method,
            evaluation_time_ms=evaluation_time
        )
        
    except Exception as e:
        evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 記錄失敗到監控系統
        monitor.record_evaluation(
            persona_type=conversation.persona_type,
            trust_change=0,
            confidence=0,
            method="error",
            latency_ms=evaluation_time,
            success=False,
            error_message=str(e)
        )
        
        logger.error(f"評估失敗 (ID: {conversation.conversation_id}): {e}")
        
        return ConversationResult(
            conversation_id=conversation.conversation_id,
            success=False,
            error_message=str(e)
        )


@router.post("/evaluate", response_model=BatchEvaluationResponse)
async def batch_evaluate(request: BatchEvaluationRequest):
    """
    批量評估對話
    
    一次性評估多個對話，支持併發處理以提高效率
    """
    start_time = datetime.now()
    monitor = get_monitor()
    
    # 驗證輸入
    if not request.conversations:
        raise HTTPException(status_code=400, detail="對話列表不能為空")
    
    if len(request.conversations) > 100:
        raise HTTPException(status_code=400, detail="單次最多評估100個對話")
    
    if request.rule_weight + request.agent_weight != 1.0:
        raise HTTPException(
            status_code=400,
            detail=f"權重總和必須為1.0，當前為{request.rule_weight + request.agent_weight}"
        )
    
    logger.info(f"開始批量評估: {len(request.conversations)}個對話")
    
    # 使用信號量控制併發數
    semaphore = asyncio.Semaphore(request.max_concurrent)
    
    async def evaluate_with_semaphore(conv):
        async with semaphore:
            return await evaluate_single_conversation(
                conversation=conv,
                rule_weight=request.rule_weight,
                agent_weight=request.agent_weight,
                enable_agent_scoring=request.enable_agent_scoring,
                monitor=monitor
            )
    
    # 併發評估所有對話
    tasks = [evaluate_with_semaphore(conv) for conv in request.conversations]
    results = await asyncio.gather(*tasks)
    
    # 統計結果
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    total_time = (datetime.now() - start_time).total_seconds() * 1000
    
    logger.info(
        f"批量評估完成: 總數={len(results)}, "
        f"成功={successful}, 失敗={failed}, "
        f"耗時={total_time:.0f}ms"
    )
    
    return BatchEvaluationResponse(
        success=True,
        total_conversations=len(results),
        successful_evaluations=successful,
        failed_evaluations=failed,
        total_time_ms=total_time,
        results=results
    )


@router.get("/status")
async def get_batch_status():
    """
    獲取批量評估狀態
    
    返回當前緩存的評估器數量和統計信息
    """
    return {
        "success": True,
        "evaluator_cache_size": len(_evaluator_cache),
        "max_concurrent_default": 5,
        "max_conversations_per_batch": 100,
        "timestamp": datetime.now().isoformat()
    }


# 使用示例
"""
# 批量評估
POST /api/v2/batch/evaluate
{
    "conversations": [
        {
            "conversation_id": "conv_001",
            "conversation_history": [
                {"role": "scammer", "content": "你好，我是警察", "strategy": "authority"},
                {"role": "victim", "content": "有什麼事嗎？"}
            ],
            "persona_type": "elderly",
            "initial_trust": 50
        },
        {
            "conversation_id": "conv_002",
            "conversation_history": [
                {"role": "scammer", "content": "恭喜中獎", "strategy": "greed"},
                {"role": "victim", "content": "真的嗎？"}
            ],
            "persona_type": "student",
            "initial_trust": 40
        }
    ],
    "rule_weight": 0.7,
    "agent_weight": 0.3,
    "enable_agent_scoring": true,
    "max_concurrent": 5
}

# 回應
{
    "success": true,
    "total_conversations": 2,
    "successful_evaluations": 2,
    "failed_evaluations": 0,
    "total_time_ms": 523.4,
    "results": [
        {
            "conversation_id": "conv_001",
            "success": true,
            "trust_change": -15.5,
            "confidence": 85.0,
            "method": "hybrid",
            "evaluation_time_ms": 245.3
        },
        {
            "conversation_id": "conv_002",
            "success": true,
            "trust_change": -8.2,
            "confidence": 78.5,
            "method": "rule",
            "evaluation_time_ms": 278.1
        }
    ]
}
"""
