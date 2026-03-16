"""
評分系統監控模組
提供性能監控、指標追蹤和告警功能
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetric:
    """評估指標"""
    timestamp: datetime
    persona_type: str
    trust_change: float
    confidence: float
    method: str
    latency_ms: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class MonitorStats:
    """監控統計"""
    total_evaluations: int = 0
    successful_evaluations: int = 0
    failed_evaluations: int = 0
    
    # 方法分布
    rule_only_count: int = 0
    agent_only_count: int = 0
    hybrid_count: int = 0
    
    # 性能指標
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    
    # 準確性指標
    total_confidence: float = 0.0
    total_trust_change: float = 0.0
    
    # 人設分布
    persona_distribution: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_evaluations == 0:
            return 0.0
        return (self.successful_evaluations / self.total_evaluations) * 100
    
    @property
    def avg_latency_ms(self) -> float:
        """平均延遲"""
        if self.successful_evaluations == 0:
            return 0.0
        return self.total_latency_ms / self.successful_evaluations
    
    @property
    def avg_confidence(self) -> float:
        """平均信心度"""
        if self.successful_evaluations == 0:
            return 0.0
        return self.total_confidence / self.successful_evaluations
    
    @property
    def avg_trust_change(self) -> float:
        """平均信任度變化"""
        if self.successful_evaluations == 0:
            return 0.0
        return self.total_trust_change / self.successful_evaluations


class ScoringMonitor:
    """評分系統監控器"""
    
    def __init__(self, max_history: int = 1000):
        """
        初始化監控器
        
        Args:
            max_history: 最大歷史記錄數
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.stats = MonitorStats()
        self.start_time = datetime.now()
        
        # 告警閾值
        self.alert_thresholds = {
            "max_latency_ms": 1000,      # 最大延遲
            "min_success_rate": 95.0,    # 最小成功率
            "min_confidence": 70.0,      # 最小信心度
        }
        
        logger.info("📊 評分系統監控器已啟動")
    
    def record_evaluation(
        self,
        persona_type: str,
        trust_change: float,
        confidence: float,
        method: str,
        latency_ms: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        記錄評估
        
        Args:
            persona_type: 人設類型
            trust_change: 信任度變化
            confidence: 信心度
            method: 評估方法
            latency_ms: 延遲（毫秒）
            success: 是否成功
            error_message: 錯誤訊息（如果失敗）
        """
        # 創建指標
        metric = EvaluationMetric(
            timestamp=datetime.now(),
            persona_type=persona_type,
            trust_change=trust_change,
            confidence=confidence,
            method=method,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        
        # 添加到歷史
        self.metrics_history.append(metric)
        
        # 更新統計
        self._update_stats(metric)
        
        # 檢查告警
        self._check_alerts(metric)
        
        # 記錄日誌
        if success:
            logger.info(
                f"✅ 評估記錄: persona={persona_type}, "
                f"trust_change={trust_change:+.2f}, "
                f"confidence={confidence:.1f}%, "
                f"method={method}, "
                f"latency={latency_ms:.0f}ms"
            )
        else:
            logger.error(
                f"❌ 評估失敗: persona={persona_type}, "
                f"error={error_message}, "
                f"latency={latency_ms:.0f}ms"
            )
    
    def _update_stats(self, metric: EvaluationMetric):
        """更新統計數據"""
        self.stats.total_evaluations += 1
        
        if metric.success:
            self.stats.successful_evaluations += 1
            
            # 更新方法計數
            if metric.method == "rule":
                self.stats.rule_only_count += 1
            elif metric.method == "agent":
                self.stats.agent_only_count += 1
            elif metric.method == "hybrid":
                self.stats.hybrid_count += 1
            
            # 更新性能指標
            self.stats.total_latency_ms += metric.latency_ms
            self.stats.min_latency_ms = min(self.stats.min_latency_ms, metric.latency_ms)
            self.stats.max_latency_ms = max(self.stats.max_latency_ms, metric.latency_ms)
            
            # 更新準確性指標
            self.stats.total_confidence += metric.confidence
            self.stats.total_trust_change += abs(metric.trust_change)
            
            # 更新人設分布
            if metric.persona_type not in self.stats.persona_distribution:
                self.stats.persona_distribution[metric.persona_type] = 0
            self.stats.persona_distribution[metric.persona_type] += 1
        else:
            self.stats.failed_evaluations += 1
    
    def _check_alerts(self, metric: EvaluationMetric):
        """檢查告警條件"""
        alerts = []
        
        # 檢查延遲
        if metric.latency_ms > self.alert_thresholds["max_latency_ms"]:
            alerts.append(
                f"⚠️ 高延遲告警: {metric.latency_ms:.0f}ms "
                f"(閾值: {self.alert_thresholds['max_latency_ms']}ms)"
            )
        
        # 檢查成功率
        if self.stats.success_rate < self.alert_thresholds["min_success_rate"]:
            alerts.append(
                f"⚠️ 低成功率告警: {self.stats.success_rate:.1f}% "
                f"(閾值: {self.alert_thresholds['min_success_rate']}%)"
            )
        
        # 檢查信心度
        if metric.success and metric.confidence < self.alert_thresholds["min_confidence"]:
            alerts.append(
                f"⚠️ 低信心度告警: {metric.confidence:.1f}% "
                f"(閾值: {self.alert_thresholds['min_confidence']}%)"
            )
        
        # 記錄告警
        for alert in alerts:
            logger.warning(alert)
    
    def get_stats(self) -> Dict:
        """
        獲取統計數據
        
        Returns:
            統計數據字典
        """
        uptime = datetime.now() - self.start_time
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split('.')[0],
            
            "total_evaluations": self.stats.total_evaluations,
            "successful_evaluations": self.stats.successful_evaluations,
            "failed_evaluations": self.stats.failed_evaluations,
            "success_rate": round(self.stats.success_rate, 2),
            
            "method_distribution": {
                "rule": self.stats.rule_only_count,
                "agent": self.stats.agent_only_count,
                "hybrid": self.stats.hybrid_count
            },
            
            "performance": {
                "avg_latency_ms": round(self.stats.avg_latency_ms, 2),
                "min_latency_ms": round(self.stats.min_latency_ms, 2) if self.stats.min_latency_ms != float('inf') else 0,
                "max_latency_ms": round(self.stats.max_latency_ms, 2)
            },
            
            "accuracy": {
                "avg_confidence": round(self.stats.avg_confidence, 2),
                "avg_trust_change": round(self.stats.avg_trust_change, 2)
            },
            
            "persona_distribution": self.stats.persona_distribution,
            
            "history_size": len(self.metrics_history),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_recent_metrics(self, limit: int = 10) -> List[Dict]:
        """
        獲取最近的指標
        
        Args:
            limit: 返回數量
        
        Returns:
            指標列表
        """
        recent = list(self.metrics_history)[-limit:]
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "persona_type": m.persona_type,
                "trust_change": round(m.trust_change, 2),
                "confidence": round(m.confidence, 2),
                "method": m.method,
                "latency_ms": round(m.latency_ms, 2),
                "success": m.success,
                "error_message": m.error_message
            }
            for m in recent
        ]
    
    def get_time_series(self, minutes: int = 60) -> Dict:
        """
        獲取時間序列數據
        
        Args:
            minutes: 時間範圍（分鐘）
        
        Returns:
            時間序列數據
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # 過濾時間範圍內的指標
        filtered_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not filtered_metrics:
            return {
                "time_range_minutes": minutes,
                "data_points": 0,
                "series": []
            }
        
        # 按分鐘分組
        time_buckets = {}
        for metric in filtered_metrics:
            bucket_key = metric.timestamp.strftime("%Y-%m-%d %H:%M")
            
            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = {
                    "count": 0,
                    "total_latency": 0,
                    "total_confidence": 0,
                    "successes": 0
                }
            
            bucket = time_buckets[bucket_key]
            bucket["count"] += 1
            
            if metric.success:
                bucket["total_latency"] += metric.latency_ms
                bucket["total_confidence"] += metric.confidence
                bucket["successes"] += 1
        
        # 生成時間序列
        series = []
        for timestamp, bucket in sorted(time_buckets.items()):
            series.append({
                "timestamp": timestamp,
                "count": bucket["count"],
                "success_rate": (bucket["successes"] / bucket["count"]) * 100 if bucket["count"] > 0 else 0,
                "avg_latency_ms": bucket["total_latency"] / bucket["successes"] if bucket["successes"] > 0 else 0,
                "avg_confidence": bucket["total_confidence"] / bucket["successes"] if bucket["successes"] > 0 else 0
            })
        
        return {
            "time_range_minutes": minutes,
            "data_points": len(series),
            "series": series
        }
    
    def export_metrics(self, filepath: str):
        """
        導出指標到文件
        
        Args:
            filepath: 文件路徑
        """
        data = {
            "export_time": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "persona_type": m.persona_type,
                    "trust_change": m.trust_change,
                    "confidence": m.confidence,
                    "method": m.method,
                    "latency_ms": m.latency_ms,
                    "success": m.success,
                    "error_message": m.error_message
                }
                for m in self.metrics_history
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 指標已導出到: {filepath}")
    
    def reset_stats(self):
        """重置統計數據"""
        self.stats = MonitorStats()
        self.metrics_history.clear()
        self.start_time = datetime.now()
        logger.info("🔄 統計數據已重置")


# 全局監控器實例
_global_monitor: Optional[ScoringMonitor] = None


def get_monitor() -> ScoringMonitor:
    """獲取全局監控器實例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ScoringMonitor()
    return _global_monitor


# 使用示例
if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建監控器
    monitor = ScoringMonitor()
    
    # 模擬評估
    import random
    
    personas = ["elderly", "average", "overconfident", "student"]
    methods = ["rule", "agent", "hybrid"]
    
    for i in range(100):
        monitor.record_evaluation(
            persona_type=random.choice(personas),
            trust_change=random.uniform(-30, 30),
            confidence=random.uniform(60, 95),
            method=random.choice(methods),
            latency_ms=random.uniform(50, 500),
            success=random.random() > 0.05  # 95% 成功率
        )
        
        time.sleep(0.01)
    
    # 獲取統計
    stats = monitor.get_stats()
    print("\n📊 統計數據:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 獲取最近指標
    recent = monitor.get_recent_metrics(limit=5)
    print("\n📈 最近5次評估:")
    print(json.dumps(recent, indent=2, ensure_ascii=False))
    
    # 導出指標
    monitor.export_metrics("monitor_export.json")
