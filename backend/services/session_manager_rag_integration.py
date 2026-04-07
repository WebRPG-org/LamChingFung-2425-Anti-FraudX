"""
SessionManager RAG集成
將Firestore RAG系統集成到SessionManager中
為LLM提供動態上下文
"""

from typing import Dict, Optional, Any
from services.firestore_rag_fraud_loader import (
    FirestoreRAGContextProvider,
    FirestoreRAGPromptBuilder
)


class SessionManagerRAGIntegration:
    """SessionManager RAG集成類"""
    
    def __init__(self):
        self.context_provider = FirestoreRAGContextProvider()
        self.prompt_builder = FirestoreRAGPromptBuilder()
    
    async def get_scammer_system_prompt(self, scam_type: str) -> str:
        """
        獲取騙徒的system prompt（包含RAG上下文）
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            str: 完整的system prompt
        """
        return await self.prompt_builder.build_scammer_prompt(scam_type)
    
    async def get_expert_system_prompt(self, scam_type: str) -> str:
        """
        獲取專家的system prompt（包含RAG上下文）
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            str: 完整的system prompt
        """
        return await self.prompt_builder.build_expert_prompt(scam_type)
    
    async def get_victim_system_prompt(self, scam_type: str) -> str:
        """
        獲取受害者的system prompt（包含RAG上下文）
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            str: 完整的system prompt
        """
        return await self.prompt_builder.build_victim_prompt(scam_type)
    
    async def enhance_user_message(self, role: str, scam_type: str, user_message: str) -> str:
        """
        增強用戶消息（添加上下文）
        
        Args:
            role: AI角色 (scammer/expert/victim)
            scam_type: 騙案類型
            user_message: 用戶消息
        
        Returns:
            str: 增強後的消息
        """
        if role == "scammer":
            return await self.prompt_builder.build_scammer_prompt(scam_type, user_message)
        elif role == "expert":
            return await self.prompt_builder.build_expert_prompt(scam_type, user_message)
        elif role == "victim":
            return await self.prompt_builder.build_victim_prompt(scam_type, user_message)
        else:
            return user_message


# 在SessionManager中使用示例
"""
class SessionManager:
    def __init__(self):
        # ... 現有代碼 ...
        self.rag_integration = SessionManagerRAGIntegration()
    
    async def initialize_session(self, scam_type: str, player_role: str):
        # 獲取RAG增強的system prompt
        if player_role == "scammer":
            system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
        elif player_role == "expert":
            system_prompt = await self.rag_integration.get_expert_system_prompt(scam_type)
        else:
            system_prompt = await self.rag_integration.get_victim_system_prompt(scam_type)
        
        # 使用system_prompt初始化LLM
        # ...
    
    async def send_message(self, role: str, message: str):
        # 增強消息
        enhanced_message = await self.rag_integration.enhance_user_message(
            role, self.scam_type, message
        )
        
        # 發送到LLM
        # ...
"""


