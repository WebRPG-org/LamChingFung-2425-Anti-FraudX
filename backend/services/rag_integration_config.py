"""
RAG詐騙數據集成配置
定義如何在SessionManager中使用這個系統
"""

import json
from typing import Dict, List, Optional, Any
from enum import Enum


class AIRole(Enum):
    """AI角色"""
    SCAMMER = "scammer"  # 騙徒AI
    EXPERT = "expert"    # 防騙專家AI
    VICTIM = "victim"    # 受害者AI


class ContextType(Enum):
    """上下文類型"""
    FULL = "full"              # 完整上下文
    CASES = "cases"            # 案例
    PATTERNS = "patterns"      # 騙術模式
    VARIATIONS = "variations"  # 變體
    WARNING_SIGNS = "warning_signs"  # 警告信號
    PREVENTION = "prevention"  # 防騙建議


class RAGIntegrationConfig:
    """RAG集成配置"""
    
    # 數據源配置
    DATA_SOURCES = {
        "generator": {
            "path": r"c:\Users\andy1\Desktop\3-16-26-ANTI-FRAUDX\AI-Agent-main v9-3-11-26\AI-Agent-main\backend\data\scam_cases_samples.py",
            "type": "synthetic",
            "priority": 1,
            "description": "生成式數據 - 用於訓練騙徒和專家"
        },
        "adcc": {
            "path": r"c:\Users\andy1\Desktop\3-16-26-ANTI-FRAUDX\AI-Agent-main v9-3-11-26\AI-Agent-main\backend\data\scraped_alerts.json
            "priority": 2,
            "description": "ADCC爬蟲數據 - 真實案例"
        }
    }
    
    # 騙案類型配置
    SCAM_TYPES = [
        "網上購物騙案",
        "電話騙案",
        "求職騙案",
        "投資騙案",
        "網上情緣",
        "財務中介公司騙案",
        "裸聊騙案",
        "社交媒體騙案",
        "街頭騙案",
        "電郵騙案",
        "其他騙案"
    ]
    
    # 特徵優化配置
    FEATURE_OPTIMIZATION = {
        "max_features_per_type": 100,      # 每種騙案最多100個特徵
        "min_diversity_score": 0.3,        # 最小多樣性分數
        "token_limit_per_feature": 500,    # 每個特徵最多500個token
        "enable_deduplication": True,      # 啟用去重
        "enable_privacy_masking": True     # 啟用隱私遮蔽
    }
    
    # 變體生成配置
    VARIATION_CONFIG = {
        "variations_per_feature": 3,       # 每個特徵生成3個變體
        "ensure_uniqueness": True,         # 確保唯一性
        "randomization_level": "high"      # 隨機化級別
    }
    
    # 上下文配置
    CONTEXT_CONFIG = {
        "scammer": {
            "context_type": ContextType.FULL,
            "max_cases": 5,
            "max_patterns": 10,
            "include_variations": True,
            "include_real_cases": False  # 騙徒不能看真實案例
        },
        "expert": {
            "context_type": ContextType.FULL,
            "max_cases": 10,
            "include_warning_signs": True,
            "include_prevention_tips": True,
            "include_real_cases": True  # 專家可以看真實案例
        },
        "victim": {
            "context_type": ContextType.WARNING_SIGNS,
            "max_cases": 0,  # 受害者不能看案例
            "include_prevention_tips": True,
            "include_real_cases": False
        }
    }
    
    # 隱私配置
    PRIVACY_CONFIG = {
        "mask_phone_numbers": True,
        "mask_bank_accounts": True,
        "mask_names": True,
        "mask_urls": True,
        "remove_victim_data": True,
        "victim_data_keywords": [
            "受害者", "被害人", "報案", "損失", "金額",
            "個人資料", "身份證", "銀行帳戶"
        ]
    }
    
    # Token優化配置
    TOKEN_OPTIMIZATION = {
        "enable_compression": True,
        "remove_duplicates": True,
        "target_token_reduction": 0.3,  # 目標減少30%的token
        "compression_level": "medium"
    }
    
    # 數據庫配置
    DATABASE_CONFIG = {
        "db_path": "fraud_rag_database.json",
        "cache_enabled": True,
        "cache_ttl": 3600,  # 1小時
        "auto_save": True,
        "save_interval": 300  # 5分鐘
    }


class RAGIntegrationGuide:
    """RAG集成使用指南"""
    
    @staticmethod
    def get_initialization_steps() -> List[str]:
        """獲取初始化步驟"""
        return [
            "1. 確保massive_generator.py和scraped_alerts.json在正確位置",
            "2. 導入RAGFraudDatabase和RAGQueryEngine",
            "3. 創建數據庫實例: db = RAGFraudDatabase()",
            "4. 初始化: await db.initialize_from_files(generator_path, adcc_path)",
            "5. 創建查詢引擎: query_engine = RAGQueryEngine(db)",
            "6. 保存數據庫: await db.save_to_disk('fraud_rag_database.json')"
        ]
    
    @staticmethod
    def get_usage_examples() -> Dict[str, str]:
        """獲取使用示例"""
        return {
            "scammer_context": """
# 為騙徒AI獲取上下文
context = await query_engine.get_context_for_scammer(
    scam_type="網上購物騙案",
    context_type="full"
)
# 返回: {cases, patterns, variations}
            """,
            
            "expert_context": """
# 為防騙專家AI獲取上下文
context = await query_engine.get_context_for_expert(
    scam_type="網上購物騙案"
)
# 返回: {warning_signs, prevention_tips, real_cases}
            """,
            
            "search_similar": """
# 搜索相似案例
results = await db.search_similar_cases(
    query="淘寶訂單問題",
    scam_type="網上購物騙案",
    top_k=5
)
            """,
            
            "get_diverse_cases": """
# 獲取多樣化案例
cases = await db.get_diverse_cases(
    scam_type="電話騙案",
    count=5
)
            """,
            
            "get_random_case": """
# 獲取隨機案例（帶變體）
case = await db.get_random_case(
    scam_type="投資騙案",
    variation_id=0
)
            """
        }
    
    @staticmethod
    def get_integration_points() -> Dict[str, str]:
        """獲取集成點"""
        return {
            "SessionManager": """
在SessionManager中添加:
- rag_db: RAGFraudDatabase實例
- query_engine: RAGQueryEngine實例
- 在初始化時加載數據庫
- 在每次對話前獲取上下文
            """,
            
            "ScammerAI": """
在ScammerAI中使用:
- 獲取scammer_context
- 從context中提取cases和patterns
- 使用variations確保多樣性
- 不能訪問真實案例
            """,
            
            "ExpertAI": """
在ExpertAI中使用:
- 獲取expert_context
- 使用warning_signs和prevention_tips
- 可以訪問真實案例
- 提供基於真實數據的建議
            """,
            
            "VictimAI": """
在VictimAI中使用:
- 只能獲取warning_signs和prevention_tips
- 不能訪問任何案例
- 不能訪問真實數據
- 只用於防騙教育
            """
        }
    
    @staticmethod
    def get_privacy_guidelines() -> List[str]:
        """獲取隱私指南"""
        return [
            "✅ 騙徒AI可以看: 生成式案例、騙術模式、變體",
            "✅ 專家AI可以看: 所有數據（包括真實案例）",
            "❌ 受害者AI不能看: 任何案例、真實數據",
            "❌ 所有AI都不能看: 受害者個人信息、銀行帳戶、電話號碼",
            "🔒 自動遮蔽: 敏感信息會被自動遮蔽",
            "🔐 數據隔離: 受害者數據完全隔離"
        ]
    
    @staticmethod
    def get_optimization_tips() -> List[str]:
        """獲取優化建議"""
        return [
            "1. 使用get_diverse_cases而不是get_random_case以確保多樣性",
            "2. 定期調用db.save_to_disk()保存數據庫",
            "3. 使用TokenOptimizer.compress_features()減少token用量",
            "4. 啟用緩存以提高查詢速度",
            "5. 監控stats以了解數據庫使用情況",
            "6. 定期更新ADCC數據以保持真實性"
        ]


class RAGIntegrationExample:
    """RAG集成完整示例"""
    
    @staticmethod
    def get_session_manager_integration() -> str:
        """SessionManager集成示例"""
        return """
from rag_fraud_integration import RAGFraudDatabase, RAGQueryEngine
from rag_integration_config import RAGIntegrationConfig, AIRole

class SessionManager:
    def __init__(self):
        self.rag_db = RAGFraudDatabase()
        self.query_engine = None
        self.config = RAGIntegrationConfig()
    
    async def initialize(self):
        # 初始化RAG數據庫
        await self.rag_db.initialize_from_files(
            self.config.DATA_SOURCES["generator"]["path"],
            self.config.DATA_SOURCES["adcc"]["path"]
        )
        
        # 創建查詢引擎
        self.query_engine = RAGQueryEngine(self.rag_db)
        
        # 保存數據庫
        await self.rag_db.save_to_disk(
            self.config.DATABASE_CONFIG["db_path"]
        )
    
    async def get_context_for_ai(self, ai_role: AIRole, scam_type: str):
        if ai_role == AIRole.SCAMMER:
            return await self.query_engine.get_context_for_scammer(scam_type)
        elif ai_role == AIRole.EXPERT:
            return await self.query_engine.get_context_for_expert(scam_type)
        else:
            return {}  # 受害者不需要上下文
    
    async def start_dialogue(self, scam_type: str):
        # 為騙徒獲取上下文
        scammer_context = await self.get_context_for_ai(AIRole.SCAMMER, scam_type)
        
        # 為專家獲取上下文
        expert_context = await self.get_context_for_ai(AIRole.EXPERT, scam_type)
        
        # 開始對話...
        """
    
    @staticmethod
    def get_scammer_ai_integration() -> str:
        """ScammerAI集成示例"""
        return """
class ScammerAI:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.context = None
    
    async def initialize_for_scam(self, scam_type: str):
        # 獲取上下文
        self.context = await self.session_manager.get_context_for_ai(
            AIRole.SCAMMER, scam_type
        )
    
    async def generate_opening(self):
        # 從context中獲取案例
        cases = self.context.get('cases', [])
        
        if cases:
            # 使用第一個案例的變體
            case = cases[0]
            variation = case.get('variation', '')
            
            # 生成開場白
            return f"你好，{variation}..."
        
        return "你好"
    
    async def generate_response(self, user_message: str):
        # 使用context中的patterns生成回應
        patterns = self.context.get('patterns', [])
        
        # 選擇相關的pattern
        # 生成回應...
        """
    
    @staticmethod
    def get_expert_ai_integration() -> str:
        """ExpertAI集成示例"""
        return """
class ExpertAI:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.context = None
    
    async def initialize_for_scam(self, scam_type: str):
        # 獲取上下文
        self.context = await self.session_manager.get_context_for_ai(
            AIRole.EXPERT, scam_type
        )
    
    async def generate_warning(self):
        # 從context中獲取警告信號
        warning_signs = self.context.get('warning_signs', [])
        
        if warning_signs:
            return f"小心！呢個係典型嘅{warning_signs[0]}"
        
        return "小心受騙"
    
    async def generate_prevention_tip(self):
        # 從context中獲取防騙建議
        prevention_tips = self.context.get('prevention_tips', [])
        
        if prevention_tips:
            return prevention_tips[0]
        
        return "保持警惕"
        """


# 配置導出
def export_config_to_json(output_path: str = "rag_config.json"):
    """導出配置為JSON"""
    config = {
        "data_sources": RAGIntegrationConfig.DATA_SOURCES,
        "scam_types": RAGIntegrationConfig.SCAM_TYPES,
        "feature_optimization": RAGIntegrationConfig.FEATURE_OPTIMIZATION,
        "variation_config": RAGIntegrationConfig.VARIATION_CONFIG,
        "privacy_config": RAGIntegrationConfig.PRIVACY_CONFIG,
        "token_optimization": RAGIntegrationConfig.TOKEN_OPTIMIZATION,
        "database_config": RAGIntegrationConfig.DATABASE_CONFIG
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置已導出: {output_path}")


if __name__ == "__main__":
    # 導出配置
    export_config_to_json()
    
    # 打印指南
    guide = RAGIntegrationGuide()
    
    print("=" * 60)
    print("RAG詐騙數據集成指南")
    print("=" * 60)
    
    print("\n📋 初始化步驟:")
    for step in guide.get_initialization_steps():
        print(f"  {step}")
    
    print("\n🔒 隱私指南:")
    for guideline in guide.get_privacy_guidelines():
        print(f"  {guideline}")
    
    print("\n⚡ 優化建議:")
    for tip in guide.get_optimization_tips():
        print(f"  {tip}")


