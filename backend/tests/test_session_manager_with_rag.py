"""
SessionManager RAG集成測試
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.session_manager_with_rag import (
    SessionManagerWithRAG,
    get_session_manager_with_rag
)


class TestSessionManagerWithRAG:
    """SessionManager RAG集成測試"""
    
    @pytest.fixture
    def session_manager(self):
        """創建SessionManager實例"""
        return SessionManagerWithRAG()
    
    @pytest.mark.asyncio
    async def test_initialize_session_scammer(self, session_manager):
        """測試初始化騙徒Session"""
        result = await session_manager.initialize_session(
            session_id="test_001",
            scam_type="網上購物騙案",
            player_role="scammer"
        )
        
        assert result['status'] == 'success'
        assert result['session_id'] == "test_001"
        assert result['scam_type'] == "網上購物騙案"
        assert result['player_role'] == "scammer"
        assert result['system_prompt_loaded'] == True
    
    @pytest.mark.asyncio
    async def test_initialize_session_expert(self, session_manager):
        """測試初始化專家Session"""
        result = await session_manager.initialize_session(
            session_id="test_002",
            scam_type="電話騙案",
            player_role="expert"
        )
        
        assert result['status'] == 'success'
        assert result['player_role'] == "expert"
    
    @pytest.mark.asyncio
    async def test_initialize_session_victim(self, session_manager):
        """測試初始化受害者Session"""
        result = await session_manager.initialize_session(
            session_id="test_003",
            scam_type="投資騙案",
            player_role="victim"
        )
        
        assert result['status'] == 'success'
        assert result['player_role'] == "victim"
    
    @pytest.mark.asyncio
    async def test_initialize_session_invalid_role(self, session_manager):
        """測試無效角色"""
        result = await session_manager.initialize_session(
            session_id="test_004",
            scam_type="網上購物騙案",
            player_role="invalid"
        )
        
        assert result['status'] == 'error'
    
    @pytest.mark.asyncio
    async def test_send_message_without_init(self, session_manager):
        """測試未初始化時發送消息"""
        result = await session_manager.send_message("你好")
        
        assert result['status'] == 'error'
    
    @pytest.mark.asyncio
    async def test_send_message_with_init(self, session_manager):
        """測試初始化後發送消息"""
        # 初始化
        await session_manager.initialize_session(
            session_id="test_005",
            scam_type="網上購物騙案",
            player_role="scammer"
        )
        
        # Mock LLM客戶端
        with patch('services.session_manager_with_rag.get_llm_client') as mock_llm:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value="你好，我係淘寶客服")
            mock_llm.return_value = mock_client
            
            # 發送消息
            result = await session_manager.send_message("你好")
            
            assert result['status'] == 'success'
            assert result['user_message'] == "你好"
            assert 'llm_response' in result
            assert 'analysis' in result
    
    @pytest.mark.asyncio
    async def test_dialogue_history(self, session_manager):
        """測試對話歷史記錄"""
        # 初始化
        await session_manager.initialize_session(
            session_id="test_006",
            scam_type="網上購物騙案",
            player_role="scammer"
        )
        
        # 記錄對話
        session_manager._record_to_history(
            user_msg="你好",
            llm_response="你好，我係淘寶客服",
            tactic_result={'tactics': ['冒充身份']},
            verdict_result={'verdict': 'ongoing'},
            score_result={'score': 15}
        )
        
        assert len(session_manager.dialogue_history) == 1
        assert session_manager.dialogue_history[0]['user_message'] == "你好"
    
    @pytest.mark.asyncio
    async def test_evaluate_realism(self, session_manager):
        """測試真實性評估"""
        score = session_manager._evaluate_realism(
            "我係淘寶客服，你嘅訂單有問題",
            "淘寶客服通知訂單異常"
        )
        
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_evaluate_authenticity(self, session_manager):
        """測試真實案例相似度"""
        score = session_manager._evaluate_authenticity(
            "需要你提供銀行密碼和驗證碼",
            "騙徒要求提供銀行密碼"
        )
        
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_evaluate_coverage(self, session_manager):
        """測試覆蓋率評估"""
        items = ["報警", "停止對話", "向官方確認"]
        score = session_manager._evaluate_coverage(
            "我要報警，停止對話",
            items
        )
        
        assert 0 <= score <= 1
        assert score > 0  # 應該有覆蓋
    
    @pytest.mark.asyncio
    async def test_get_session_manager_singleton(self):
        """測試SessionManager單例"""
        manager1 = get_session_manager_with_rag()
        manager2 = get_session_manager_with_rag()
        
        assert manager1 is manager2


class TestSessionManagerIntegration:
    """SessionManager集成測試"""
    
    @pytest.mark.asyncio
    async def test_full_dialogue_flow(self):
        """測試完整對話流程"""
        session_manager = SessionManagerWithRAG()
        
        # 1. 初始化
        init_result = await session_manager.initialize_session(
            session_id="integration_001",
            scam_type="網上購物騙案",
            player_role="scammer"
        )
        assert init_result['status'] == 'success'
        
        # 2. 模擬對話
        session_manager._record_to_history(
            user_msg="你好",
            llm_response="你好，我係淘寶客服",
            tactic_result={'tactics': ['冒充身份'], 'score': 15},
            verdict_result={'verdict': 'ongoing'},
            score_result={'score': 15}
        )
        
        session_manager._record_to_history(
            user_msg="我嘅訂單有問題嗎？",
            llm_response="係，你嘅訂單需要補交運費",
            tactic_result={'tactics': ['要求轉賬'], 'score': 18},
            verdict_result={'verdict': 'ongoing'},
            score_result={'score': 18}
        )
        
        # 3. 評估對話
        evaluation = await session_manager.evaluate_dialogue()
        assert evaluation['session_id'] == "integration_001"
        assert evaluation['dialogue_length'] == 2
        assert 'quality_metrics' in evaluation
    
    @pytest.mark.asyncio
    async def test_multiple_roles(self):
        """測試多角色對話"""
        session_manager = SessionManagerWithRAG()
        
        # 初始化騙徒
        await session_manager.initialize_session(
            session_id="multi_role_001",
            scam_type="電話騙案",
            player_role="scammer"
        )
        
        # 記錄騙徒消息
        session_manager._record_to_history(
            user_msg="我係警察",
            llm_response="你涉嫌洗黑錢",
            tactic_result={'tactics': ['冒充身份']},
            verdict_result={'verdict': 'ongoing'},
            score_result={'score': 16}
        )
        
        # 記錄受害者消息
        session_manager._record_to_history(
            user_msg="我冇做過",
            llm_response="我要報警",
            tactic_result={},
            verdict_result={'verdict': 'expert_win'},
            score_result={'score': 12}
        )
        
        assert len(session_manager.dialogue_history) == 2


class TestRAGDataIntegration:
    """RAG數據集成測試"""
    
    @pytest.mark.asyncio
    async def test_rag_context_provider(self):
        """測試RAG上下文提供器"""
        from services.firestore_rag_fraud_loader import FirestoreRAGContextProvider
        
        provider = FirestoreRAGContextProvider()
        
        # 測試獲取警告信號
        warning_signs = await provider.get_warning_signs("網上購物騙案")
        assert isinstance(warning_signs, list)
        assert len(warning_signs) > 0
    
    @pytest.mark.asyncio
    async def test_rag_prompt_builder(self):
        """測試RAG Prompt構建器"""
        from services.firestore_rag_fraud_loader import FirestoreRAGPromptBuilder
        
        builder = FirestoreRAGPromptBuilder()
        
        # 測試構建騙徒prompt
        prompt = await builder.build_scammer_prompt("網上購物騙案")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "網上購物騙案" in prompt


# 運行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])


