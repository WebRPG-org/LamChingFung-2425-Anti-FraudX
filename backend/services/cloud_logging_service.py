"""
Cloud Logging Service - Google Cloud Logging 集成
支持 Anti-FraudX 在 Cloud 上的日誌管理
"""

import os
import logging
from typing import Optional, Dict, Any
from google.cloud import logging as cloud_logging
from utils.logger import log


class CloudLoggingService:
    """
    Cloud Logging 服務類
    管理 Anti-FraudX 在 Google Cloud Logging 上的日誌操作
    """
    
    _instance = None
    _client = None
    _logger = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(CloudLoggingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_name: str = "anti-fraudx-logs"):
        """
        初始化 Cloud Logging 連接
        
        Args:
            log_name: 日誌名稱
        """
        if CloudLoggingService._client is None:
            try:
                # 初始化 Cloud Logging 客戶端
                CloudLoggingService._client = cloud_logging.Client()
                
                # 獲取日誌記錄器
                CloudLoggingService._logger = CloudLoggingService._client.logger(log_name)
                
                # 設置 Python 日誌處理器
                cloud_handler = cloud_logging.handlers.CloudLoggingHandler(
                    CloudLoggingService._client,
                    name=log_name
                )
                
                # 添加到 Python 日誌
                logging.getLogger().addHandler(cloud_handler)
                
                log.info(
                    f"[CLOUD_LOGGING_SERVICE] ✅ Cloud Logging 連接成功 - "
                    f"日誌名稱: {log_name}"
                )
            except Exception as e:
                log.error(f"[CLOUD_LOGGING_SERVICE] ❌ Cloud Logging 初始化失敗: {str(e)}")
                raise
    
    def log_info(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        """
        記錄信息級別日誌
        
        Args:
            message: 日誌消息
            labels: 標籤字典
        """
        try:
            CloudLoggingService._logger.log_struct(
                {
                    "message": message,
                    "severity": "INFO"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄信息日誌失敗: {str(e)}")
    
    def log_warning(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        """
        記錄警告級別日誌
        
        Args:
            message: 日誌消息
            labels: 標籤字典
        """
        try:
            CloudLoggingService._logger.log_struct(
                {
                    "message": message,
                    "severity": "WARNING"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄警告日誌失敗: {str(e)}")
    
    def log_error(self, message: str, error: Optional[Exception] = None, labels: Optional[Dict[str, str]] = None) -> None:
        """
        記錄錯誤級別日誌
        
        Args:
            message: 日誌消息
            error: 異常對象
            labels: 標籤字典
        """
        try:
            error_message = str(error) if error else ""
            CloudLoggingService._logger.log_struct(
                {
                    "message": message,
                    "error": error_message,
                    "severity": "ERROR"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄錯誤日誌失敗: {str(e)}")
    
    def log_debug(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        """
        記錄調試級別日誌
        
        Args:
            message: 日誌消息
            labels: 標籤字典
        """
        try:
            CloudLoggingService._logger.log_struct(
                {
                    "message": message,
                    "severity": "DEBUG"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄調試日誌失敗: {str(e)}")
    
    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        記錄事件日誌
        
        Args:
            event_type: 事件類型
            event_data: 事件數據
            labels: 標籤字典
        """
        try:
            CloudLoggingService._logger.log_struct(
                {
                    "event_type": event_type,
                    "event_data": event_data,
                    "severity": "INFO"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄事件日誌失敗: {str(e)}")
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        status: str = "success",
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        記錄性能日誌
        
        Args:
            operation: 操作名稱
            duration_ms: 持續時間（毫秒）
            status: 狀態（success/failure）
            labels: 標籤字典
        """
        try:
            CloudLoggingService._logger.log_struct(
                {
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "status": status,
                    "severity": "INFO"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄性能日誌失敗: {str(e)}")
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        記錄 API 請求日誌
        
        Args:
            method: HTTP 方法
            path: 請求路徑
            status_code: 狀態碼
            duration_ms: 持續時間（毫秒）
            labels: 標籤字典
        """
        try:
            CloudLoggingService._logger.log_struct(
                {
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "severity": "INFO"
                },
                labels=labels or {}
            )
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 記錄 API 日誌失敗: {str(e)}")
    
    def get_logger(self):
        """獲取 Cloud Logger 實例"""
        return CloudLoggingService._logger

