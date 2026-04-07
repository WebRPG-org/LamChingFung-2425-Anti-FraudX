"""
backend/config/rag_integration_config.py - RAG系統集成配置
"""

import os
from typing import Dict, Any

# ============================================================
# RAG系統配置
# ============================================================

RAG_CONFIG = {
    # Firestore配置
    "firestore": {
        "project_id": os.getenv("FIRESTORE_PROJECT_ID", "ai-agent-fraud"),
        "credentials_path": os.getenv("FIRESTORE_CREDENTIALS_PATH", None),
        "use_emulator": os.getenv("FIRESTORE_EMULATOR_HOST", None) is not None,
        "emulator_host": os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8081"),
    },
    
    # 數據加載配置
    "data_loading": {
        "generator_path": os.getenv("GENERATOR_DATA_PATH", "data/massive_generator.py"),
        "adcc_path": os.getenv("ADCC_DATA_PATH", "data/scraped_alerts.json"),
        "batch_size": int(os.getenv("BATCH_SIZE", "100")),
        "auto_load_on_startup": os.getenv("AUTO_LOAD_ON_STARTUP", "true").lower() == "true",
    },
    
    # Session配置
    "session": {
        "max_history": int(os.getenv("MAX_HISTORY", "10")),
        "session_timeout": int(os.getenv("SESSION_TIMEOUT", "3600")),
        "isolation_enabled": os.getenv("ISOLATION_ENABLED", "true").lower() == "true",
    },
    
    # LLM配置
    "llm": {
        "model": os.getenv("AGENT_MODEL", "gemma3:4b"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "500")),
        "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
    },
    
    # 分析器配置
    "analyzers": {
        "tactic_analyzer_enabled": os.getenv("TACTIC_ANALYZER_ENABLED", "true").lower() == "true",
        "verdict_judge_enabled": os.getenv("VERDICT_JUDGE_ENABLED", "true").lower() == "true",
        "scam_scorer_enabled": os.getenv("SCAM_SCORER_ENABLED", "true").lower() == "true",
    },
    
    # 日誌配置
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": os.getenv("LOG_FILE", "logs/rag_system.log"),
    },
}

# ============================================================
# 集合名稱配置
# ============================================================

FIRESTORE_COLLECTIONS = {
    "sessions": "sessions",
    "messages": "messages",
    "evaluations": "evaluations",
    "scam_cases": "scam_cases",
    "fraud_features": "fraud_features",
    "warning_signs": "warning_signs",
    "prevention_tips": "prevention_tips",
    "user_profiles": "user_profiles",
    "game_statistics": "game_statistics",
}

# ============================================================
# 騙案類型配置
# ============================================================

SCAM_TYPES = {
    "phone_scam": {
        "name": "電話詐騙",
        "description": "通過電話進行的詐騙",
        "keywords": ["銀行", "客服", "驗證", "密碼"],
    },
    "email_scam": {
        "name": "電郵詐騙",
        "description": "通過電郵進行的詐騙",
        "keywords": ["確認", "更新", "驗證", "帳號"],
    },
    "sms_scam": {
        "name": "短信詐騙",
        "description": "通過短信進行的詐騙",
        "keywords": ["驗證碼", "確認", "點擊", "鏈接"],
    },
    "social_engineering": {
        "name": "社交工程",
        "description": "通過社交工程進行的詐騙",
        "keywords": ["信任", "朋友", "介紹", "推薦"],
    },
}

# ============================================================
# 角色配置
# ============================================================

PLAYER_ROLES = {
    "scammer": {
        "name": "騙徒",
        "description": "扮演詐騙者",
        "objectives": ["獲取敏感信息", "進行轉賬", "建立信任"],
    },
    "expert": {
        "name": "專家",
        "description": "扮演防騙專家",
        "objectives": ["識別詐騙", "保護受害者", "提供建議"],
    },
    "victim": {
        "name": "受害者",
        "description": "扮演潛在受害者",
        "objectives": ["學習識別詐騙", "提高警覺性", "做出正確決定"],
    },
}

# ============================================================
# 評分配置
# ============================================================

SCORING_CONFIG = {
    "min_score": 1,
    "max_score": 20,
    "alertness_range": (0, 100),
    "credit_range": (0, 100),
    "response_types": {
        "fully_believe": {"scammer_credit": 20, "expert_credit": 0},
        "partially_believe": {"scammer_credit": 10, "expert_credit": 0},
        "suspicious": {"scammer_credit": 0, "expert_credit": 10},
        "reject": {"scammer_credit": 0, "expert_credit": 20},
    },
}

# ============================================================
# 勝負判定配置
# ============================================================

VERDICT_CONFIG = {
    "scammer_win_conditions": [
        "password_provided",
        "account_provided",
        "verification_code_provided",
        "transfer_completed",
        "id_provided",
    ],
    "expert_win_conditions": [
        "reported_to_police",
        "stopped_communication",
        "verified_with_official",
        "sought_help",
    ],
    "confidence_threshold": 0.8,
}

# ============================================================
# 輔助函數
# ============================================================

def get_rag_config() -> Dict[str, Any]:
    """獲取RAG配置"""
    return RAG_CONFIG


def get_firestore_collections() -> Dict[str, str]:
    """獲取Firestore集合名稱"""
    return FIRESTORE_COLLECTIONS


def get_scam_types() -> Dict[str, Dict[str, Any]]:
    """獲取騙案類型"""
    return SCAM_TYPES


def get_player_roles() -> Dict[str, Dict[str, Any]]:
    """獲取玩家角色"""
    return PLAYER_ROLES


def get_scoring_config() -> Dict[str, Any]:
    """獲取評分配置"""
    return SCORING_CONFIG


def get_verdict_config() -> Dict[str, Any]:
    """獲取勝負判定配置"""
    return VERDICT_CONFIG


