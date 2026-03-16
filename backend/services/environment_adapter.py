"""
Environment Adapter - 環境適配層
根據部署環境自動選擇本地或 Cloud 服務
"""

import os
from typing import Optional, Dict, Any, Union
from utils.logger import log


class EnvironmentAdapter:
    """
    環境適配層
    根據 DEPLOYMENT_ENV 自動選擇本地或 Cloud 服務
    """
    
    # 環境常量
    ENV_LOCAL = "local"
    ENV_CLOUD = "cloud"
    
    # 當前環境
    _current_env = None
    
    # 服務實例緩存
    _services = {}
    
    @staticmethod
    def get_environment() -> str:
        """
        獲取當前部署環境
        
        Returns:
            str: "local" 或 "cloud"
        """
        if EnvironmentAdapter._current_env is None:
            EnvironmentAdapter._current_env = os.getenv(
                "DEPLOYMENT_ENV",
                EnvironmentAdapter.ENV_LOCAL
            ).lower()
            
            if EnvironmentAdapter._current_env not in [EnvironmentAdapter.ENV_LOCAL, EnvironmentAdapter.ENV_CLOUD]:
                log.warning(
                    f"[ENVIRONMENT_ADAPTER] ⚠️ 未知的環境: {EnvironmentAdapter._current_env}, "
                    f"默認使用 local"
                )
                EnvironmentAdapter._current_env = EnvironmentAdapter.ENV_LOCAL
            
            log.info(f"[ENVIRONMENT_ADAPTER] 當前環境: {EnvironmentAdapter._current_env}")
        
        return EnvironmentAdapter._current_env
    
    @staticmethod
    def is_cloud() -> bool:
        """檢查是否為 Cloud 環境"""
        return EnvironmentAdapter.get_environment() == EnvironmentAdapter.ENV_CLOUD
    
    @staticmethod
    def is_local() -> bool:
        """檢查是否為本地環境"""
        return EnvironmentAdapter.get_environment() == EnvironmentAdapter.ENV_LOCAL
    
    @staticmethod
    def get_database_service():
        """
        獲取數據庫服務
        
        Returns:
            FirestoreService (Cloud) 或 SQLiteService (Local)
        """
        if "database" in EnvironmentAdapter._services:
            return EnvironmentAdapter._services["database"]
        
        try:
            if EnvironmentAdapter.is_cloud():
                from services.firestore_service import FirestoreService
                service = FirestoreService()
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用 Firestore 數據庫")
            else:
                # 本地使用 SQLite（通過現有的 config）
                from config import config
                service = config.database
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用本地 SQLite 數據庫")
            
            EnvironmentAdapter._services["database"] = service
            return service
        except Exception as e:
            log.error(f"[ENVIRONMENT_ADAPTER] ❌ 獲取數據庫服務失敗: {str(e)}")
            raise
    
    @staticmethod
    def get_storage_service():
        """
        獲取存儲服務
        
        Returns:
            CloudStorageService (Cloud) 或 LocalStorageService (Local)
        """
        if "storage" in EnvironmentAdapter._services:
            return EnvironmentAdapter._services["storage"]
        
        try:
            if EnvironmentAdapter.is_cloud():
                from services.cloud_storage_service import CloudStorageService
                service = CloudStorageService()
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用 Cloud Storage")
            else:
                # 本地使用文件系統
                from services.local_storage_service import LocalStorageService
                service = LocalStorageService()
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用本地存儲")
            
            EnvironmentAdapter._services["storage"] = service
            return service
        except Exception as e:
            log.error(f"[ENVIRONMENT_ADAPTER] ❌ 獲取存儲服務失敗: {str(e)}")
            raise
    
    @staticmethod
    def get_logging_service():
        """
        獲取日誌服務
        
        Returns:
            CloudLoggingService (Cloud) 或 LocalLoggingService (Local)
        """
        if "logging" in EnvironmentAdapter._services:
            return EnvironmentAdapter._services["logging"]
        
        try:
            if EnvironmentAdapter.is_cloud():
                from services.cloud_logging_service import CloudLoggingService
                service = CloudLoggingService()
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用 Cloud Logging")
            else:
                # 本地使用標準日誌
                from utils.logger import log as local_logger
                service = local_logger
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用本地日誌")
            
            EnvironmentAdapter._services["logging"] = service
            return service
        except Exception as e:
            log.error(f"[ENVIRONMENT_ADAPTER] ❌ 獲取日誌服務失敗: {str(e)}")
            raise
    
    @staticmethod
    def get_monitoring_service():
        """
        獲取監控服務
        
        Returns:
            CloudMonitoringService (Cloud) 或 LocalMonitoringService (Local)
        """
        if "monitoring" in EnvironmentAdapter._services:
            return EnvironmentAdapter._services["monitoring"]
        
        try:
            if EnvironmentAdapter.is_cloud():
                from services.cloud_monitoring_service import CloudMonitoringService
                service = CloudMonitoringService()
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用 Cloud Monitoring")
            else:
                # 本地使用本地監控
                from services.local_monitoring_service import LocalMonitoringService
                service = LocalMonitoringService()
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用本地監控")
            
            EnvironmentAdapter._services["monitoring"] = service
            return service
        except Exception as e:
            log.error(f"[ENVIRONMENT_ADAPTER] ❌ 獲取監控服務失敗: {str(e)}")
            raise
    
    @staticmethod
    def get_llm_service(agent_type: str = "expert"):
        """
        獲取 LLM 服務
        
        Returns:
            VertexAILLM (Cloud) 或 GeminiLLM/OllamaLLM (Local)
        """
        try:
            from llms.llm_factory import LlmFactory
            
            if EnvironmentAdapter.is_cloud():
                # Cloud 使用 Vertex AI
                use_gemini = False
                log.info("[ENVIRONMENT_ADAPTER] ✅ 使用 Vertex AI LLM")
            else:
                # 本地使用 Gemini 或 Ollama
                use_gemini = os.getenv("GEMINI_ENABLED", "true").lower() == "true"
                provider = "Gemini" if use_gemini else "Ollama"
                log.info(f"[ENVIRONMENT_ADAPTER] ✅ 使用 {provider} LLM")
            
            return LlmFactory.create_llm(agent_type, use_gemini=use_gemini)
        except Exception as e:
            log.error(f"[ENVIRONMENT_ADAPTER] ❌ 獲取 LLM 服務失敗: {str(e)}")
            raise
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        獲取環境配置
        
        Returns:
            dict: 環境配置信息
        """
        return {
            "environment": EnvironmentAdapter.get_environment(),
            "is_cloud": EnvironmentAdapter.is_cloud(),
            "is_local": EnvironmentAdapter.is_local(),
            "project_id": os.getenv("PROJECT_ID", "anti-fraudx-local"),
            "app_name": os.getenv("APP_NAME", "Anti-FraudX"),
            "app_version": os.getenv("APP_VERSION", "2.0.0"),
            "app_env": os.getenv("APP_ENV", "development"),
            "domain": os.getenv("DOMAIN_NAME", "localhost"),
            "log_level": os.getenv("LOG_LEVEL", "info")
        }
    
    @staticmethod
    def print_environment_info() -> None:
        """打印環境信息"""
        config = EnvironmentAdapter.get_config()
        
        log.info("=" * 50)
        log.info("Anti-FraudX 環境配置")
        log.info("=" * 50)
        log.info(f"環境: {config['environment'].upper()}")
        log.info(f"項目 ID: {config['project_id']}")
        log.info(f"應用名稱: {config['app_name']}")
        log.info(f"應用版本: {config['app_version']}")
        log.info(f"應用環境: {config['app_env']}")
        log.info(f"域名: {config['domain']}")
        log.info(f"日誌級別: {config['log_level']}")
        log.info("=" * 50)

