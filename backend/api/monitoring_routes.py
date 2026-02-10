"""
監控 API 路由
提供監控數據查詢和管理接口
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

from utils.scoring_monitor import get_monitor

router = APIRouter(prefix="/api/v2/monitoring", tags=["monitoring"])


class StatsResponse(BaseModel):
    """統計回應"""
    success: bool
    data: Dict


class MetricsResponse(BaseModel):
    """指標回應"""
    success: bool
    metrics: List[Dict]


class TimeSeriesResponse(BaseModel):
    """時間序列回應"""
    success: bool
    data: Dict


@router.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """
    獲取統計數據
    
    返回評分系統的整體統計信息
    """
    monitor = get_monitor()
    stats = monitor.get_stats()
    
    return StatsResponse(
        success=True,
        data=stats
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_recent_metrics(
    limit: int = Query(10, ge=1, le=100, description="返回數量")
):
    """
    獲取最近的評估指標
    
    Args:
        limit: 返回數量（1-100）
    """
    monitor = get_monitor()
    metrics = monitor.get_recent_metrics(limit=limit)
    
    return MetricsResponse(
        success=True,
        metrics=metrics
    )


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_time_series(
    minutes: int = Query(60, ge=1, le=1440, description="時間範圍（分鐘）")
):
    """
    獲取時間序列數據
    
    Args:
        minutes: 時間範圍（1-1440分鐘，即1分鐘到24小時）
    """
    monitor = get_monitor()
    data = monitor.get_time_series(minutes=minutes)
    
    return TimeSeriesResponse(
        success=True,
        data=data
    )


@router.post("/reset")
async def reset_statistics():
    """
    重置統計數據
    
    清除所有歷史數據和統計信息
    """
    monitor = get_monitor()
    monitor.reset_stats()
    
    return {
        "success": True,
        "message": "統計數據已重置",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check():
    """
    監控系統健康檢查
    """
    monitor = get_monitor()
    stats = monitor.get_stats()
    
    # 判斷健康狀態
    is_healthy = (
        stats["success_rate"] >= 95.0 and
        stats["performance"]["avg_latency_ms"] < 1000
    )
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "success_rate": stats["success_rate"],
        "avg_latency_ms": stats["performance"]["avg_latency_ms"],
        "total_evaluations": stats["total_evaluations"],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/dashboard")
async def get_dashboard_data():
    """
    獲取儀表板數據
    
    返回用於前端儀表板的綜合數據
    """
    monitor = get_monitor()
    
    stats = monitor.get_stats()
    recent_metrics = monitor.get_recent_metrics(limit=20)
    time_series = monitor.get_time_series(minutes=60)
    
    return {
        "success": True,
        "dashboard": {
            "overview": {
                "total_evaluations": stats["total_evaluations"],
                "success_rate": stats["success_rate"],
                "avg_latency_ms": stats["performance"]["avg_latency_ms"],
                "avg_confidence": stats["accuracy"]["avg_confidence"],
                "uptime": stats["uptime_formatted"]
            },
            "method_distribution": stats["method_distribution"],
            "persona_distribution": stats["persona_distribution"],
            "recent_metrics": recent_metrics,
            "time_series": time_series["series"]
        },
        "timestamp": datetime.now().isoformat()
    }


# 使用示例
"""
# 獲取統計數據
GET /api/v2/monitoring/stats

# 獲取最近10次評估
GET /api/v2/monitoring/metrics?limit=10

# 獲取過去1小時的時間序列
GET /api/v2/monitoring/timeseries?minutes=60

# 獲取儀表板數據
GET /api/v2/monitoring/dashboard

# 重置統計
POST /api/v2/monitoring/reset

# 健康檢查
GET /api/v2/monitoring/health
"""
