"""
Cloud Monitoring Service - Google Cloud Monitoring 集成
支持 Anti-FraudX 在 Cloud 上的監控和指標
"""

import os
from typing import Optional, Dict, Any
from google.cloud import monitoring_v3
from google.api_core import gapic_v1
from utils.logger import log


class CloudMonitoringService:
    """
    Cloud Monitoring 服務類
    管理 Anti-FraudX 在 Google Cloud Monitoring 上的指標操作
    """
    
    _instance = None
    _client = None
    _project_id = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(CloudMonitoringService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, project_id: Optional[str] = None):
        """
        初始化 Cloud Monitoring 連接
        
        Args:
            project_id: Google Cloud 項目 ID
        """
        if CloudMonitoringService._client is None:
            try:
                # 初始化 Monitoring 客戶端
                CloudMonitoringService._project_id = project_id or os.getenv(
                    "GCP_PROJECT_ID",
                    "anti-fraudx-us-ci"
                )
                CloudMonitoringService._client = monitoring_v3.MetricServiceClient()
                
                log.info(
                    f"[CLOUD_MONITORING_SERVICE] ✅ Cloud Monitoring 連接成功 - "
                    f"項目: {CloudMonitoringService._project_id}"
                )
            except Exception as e:
                log.error(f"[CLOUD_MONITORING_SERVICE] ❌ Cloud Monitoring 初始化失敗: {str(e)}")
                raise
    
    def write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        resource_type: str = "global"
    ) -> bool:
        """
        寫入自定義指標
        
        Args:
            metric_type: 指標類型（如 "custom.googleapis.com/anti_fraudx/api_latency"）
            value: 指標值
            labels: 標籤字典
            resource_type: 資源類型
        
        Returns:
            bool: 是否成功
        """
        try:
            project_name = f"projects/{CloudMonitoringService._project_id}"
            
            # 構建時間序列
            series = monitoring_v3.TimeSeries()
            series.metric.type_ = metric_type
            
            # 添加標籤
            if labels:
                for key, value_str in labels.items():
                    series.metric.labels[key] = value_str
            
            # 設置資源
            series.resource.type = resource_type
            
            # 添加數據點
            now = monitoring_v3.time_pb2.Timestamp()
            now.GetCurrentTime()
            point = monitoring_v3.Point()
            point.interval.end_time = now
            point.value.double_value = value
            series.points = [point]
            
            # 寫入指標
            CloudMonitoringService._client.create_time_series(
                name=project_name,
                time_series=[series]
            )
            
            log.info(
                f"[CLOUD_MONITORING_SERVICE] ✅ 指標已寫入 - "
                f"類型: {metric_type}, 值: {value}"
            )
            return True
        except Exception as e:
            log.error(f"[CLOUD_MONITORING_SERVICE] ❌ 寫入指標失敗: {str(e)}")
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
            metric_type="custom.googleapis.com/anti_fraudx/api_latency",
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
            metric_type="custom.googleapis.com/anti_fraudx/error_count",
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
            metric_type="custom.googleapis.com/anti_fraudx/game_session_count",
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
            metric_type="custom.googleapis.com/anti_fraudx/active_users",
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
            metric_type="custom.googleapis.com/anti_fraudx/model_inference_time",
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
            metric_type="custom.googleapis.com/anti_fraudx/token_usage",
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
            metric_type="custom.googleapis.com/anti_fraudx/database_operation_time",
            value=duration_ms,
            labels={"operation": operation}
        )
    
    def get_client(self):
        """獲取 Monitoring 客戶端"""
        return CloudMonitoringService._client

