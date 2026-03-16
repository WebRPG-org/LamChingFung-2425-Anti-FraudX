"""
Local Monitoring Service - 本地監控服務
支持 Anti-FraudX 本地部署的監控和指標
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from utils.logger import log


class LocalMonitoringService:
    """
    本地監控服務類
    管理 Anti-FraudX 本地部署的監控指標
    """
    
    _instance = None
    _metrics_file = None
    _metrics = {}
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(LocalMonitoringService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, metrics_file: Optional[str] = None):
        """
        初始化本地監控
        
        Args:
            metrics_file: 指標文件路徑
        """
        if LocalMonitoringService._metrics_file is None:
            LocalMonitoringService._metrics_file = metrics_file or os.getenv(
                "METRICS_FILE",
                "./backend/logs/metrics.json"
            )
            
            # 創建目錄
            Path(LocalMonitoringService._metrics_file).parent.mkdir(parents=True, exist_ok=True)
            
            # 加載現有指標
            self._load_metrics()
            
            log.info(
                f"[LOCAL_MONITORING_SERVICE] ✅ 本地監控初始化成功 - "
                f"指標文件: {LocalMonitoringService._metrics_file}"
            )
    
    def _load_metrics(self) -> None:
        """加載現有指標"""
        try:
            if os.path.exists(LocalMonitoringService._metrics_file):
                with open(LocalMonitoringService._metrics_file, 'r', encoding='utf-8') as f:
                    LocalMonitoringService._metrics = json.load(f)
            else:
                LocalMonitoringService._metrics = {}
        except Exception as e:
            log.error(f"[LOCAL_MONITORING_SERVICE] ❌ 加載指標失敗: {str(e)}")
            LocalMonitoringService._metrics = {}
    
    def _save_metrics(self) -> None:
        """保存指標到文件"""
        try:
            with open(LocalMonitoringService._metrics_file, 'w', encoding='utf-8') as f:
                json.dump(LocalMonitoringService._metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"[LOCAL_MONITORING_SERVICE] ❌ 保存指標失敗: {str(e)}")
    
    def write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        寫入指標
        
        Args:
            metric_type: 指標類型
            value: 指標值
            labels: 標籤字典
        
        Returns:
            bool: 是否成功
        """
        try:
            timestamp = datetime.now().isoformat()
            
            if metric_type not in LocalMonitoringService._metrics:
                LocalMonitoringService._metrics[metric_type] = []
            
            metric_entry = {
                "timestamp": timestamp,
                "value": value,
                "labels": labels or {}
            }
            
            LocalMonitoringService._metrics[metric_type].append(metric_entry)
            
            # 保留最近 1000 條記錄
            if len(LocalMonitoringService._metrics[metric_type]) > 1000:
                LocalMonitoringService._metrics[metric_type] = \
                    LocalMonitoringService._metrics[metric_type][-1000:]
            
            self._save_metrics()
            
            log.debug(
                f"[LOCAL_MONITORING_SERVICE] ✅ 指標已寫入 - "
                f"類型: {metric_type}, 值: {value}"
            )
            return True
        except Exception as e:
            log.error(f"[LOCAL_MONITORING_SERVICE] ❌ 寫入指標失敗: {str(e)}")
            return False
    
    def record_api_latency(self, endpoint: str, latency_ms: float) -> bool:
        """
        記錄 API 延遲
        
        Args:
            endpoint: API 端點
            latency_ms: 延遲（毫秒）
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="api_latency",
            value=latency_ms,
            labels={"endpoint": endpoint}
        )
    
    def record_error_count(self, error_type: str, count: int = 1) -> bool:
        """
        記錄錯誤計數
        
        Args:
            error_type: 錯誤類型
            count: 計數
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="error_count",
            value=float(count),
            labels={"error_type": error_type}
        )
    
    def record_game_session_count(self, count: int) -> bool:
        """
        記錄遊戲會話計數
        
        Args:
            count: 計數
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="game_session_count",
            value=float(count)
        )
    
    def record_active_users(self, count: int) -> bool:
        """
        記錄活躍用戶數
        
        Args:
            count: 計數
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="active_users",
            value=float(count)
        )
    
    def record_model_inference_time(self, model_name: str, inference_time_ms: float) -> bool:
        """
        記錄模型推理時間
        
        Args:
            model_name: 模型名稱
            inference_time_ms: 推理時間（毫秒）
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="model_inference_time",
            value=inference_time_ms,
            labels={"model": model_name}
        )
    
    def record_token_usage(self, model: str, tokens: int) -> bool:
        """
        記錄 Token 使用量
        
        Args:
            model: 模型名稱
            tokens: Token 數量
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="token_usage",
            value=float(tokens),
            labels={"model": model}
        )
    
    def record_database_operation(self, operation: str, duration_ms: float) -> bool:
        """
        記錄數據庫操作
        
        Args:
            operation: 操作類型
            duration_ms: 持續時間（毫秒）
        
        Returns:
            bool: 是否成功
        """
        return self.write_metric(
            metric_type="database_operation_time",
            value=duration_ms,
            labels={"operation": operation}
        )
    
    def get_metrics(self, metric_type: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取指標
        
        Args:
            metric_type: 指標類型（None 則返回所有）
        
        Returns:
            dict: 指標數據
        """
        if metric_type:
            return {metric_type: LocalMonitoringService._metrics.get(metric_type, [])}
        else:
            return LocalMonitoringService._metrics
    
    def get_metric_summary(self, metric_type: str) -> Dict[str, Any]:
        """
        獲取指標摘要
        
        Args:
            metric_type: 指標類型
        
        Returns:
            dict: 指標摘要（平均值、最小值、最大值等）
        """
        try:
            metrics = LocalMonitoringService._metrics.get(metric_type, [])
            
            if not metrics:
                return {
                    "count": 0,
                    "avg": 0,
                    "min": 0,
                    "max": 0
                }
            
            values = [m["value"] for m in metrics]
            
            return {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else 0
            }
        except Exception as e:
            log.error(f"[LOCAL_MONITORING_SERVICE] ❌ 獲取指標摘要失敗: {str(e)}")
            return {}
    
    def clear_metrics(self, metric_type: Optional[str] = None) -> bool:
        """
        清除指標
        
        Args:
            metric_type: 指標類型（None 則清除所有）
        
        Returns:
            bool: 是否成功
        """
        try:
            if metric_type:
                if metric_type in LocalMonitoringService._metrics:
                    del LocalMonitoringService._metrics[metric_type]
            else:
                LocalMonitoringService._metrics = {}
            
            self._save_metrics()
            log.info(f"[LOCAL_MONITORING_SERVICE] ✅ 指標已清除")
            return True
        except Exception as e:
            log.error(f"[LOCAL_MONITORING_SERVICE] ❌ 清除指標失敗: {str(e)}")
            return False

