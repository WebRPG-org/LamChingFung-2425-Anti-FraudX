"""
Token 優化測試 - Phase 1.3 測試
測試 Token 計數、Context 壓縮、Prompt 優化
"""

import pytest
from backend.services.token_optimization import (
    TokenCounter,
    ContextCompressor,
    PromptOptimizer,
    TokenOptimizationService,
    get_token_optimization_service
)


class TestTokenCounter:
    """測試 Token 計數器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.counter = TokenCounter()
    
    def test_count_tokens_chinese(self):
        """測試中文 Token 計數"""
        text = "這是一個測試文本"
        tokens = self.counter.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_count_tokens_english(self):
        """測試英文 Token 計數"""
        text = "This is a test text"
        tokens = self.counter.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_count_tokens_mixed(self):
        """測試混合 Token 計數"""
        text = "這是 a test 文本"
        tokens = self.counter.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_count_tokens_empty(self):
        """測試空文本 Token 計數"""
        text = ""
        tokens = self.counter.count_tokens(text)
        
        assert tokens == 0
    
    def test_add_prompt_tokens(self):
        """測試添加 Prompt tokens"""
        text = "這是一個測試 prompt"
        tokens = self.counter.add_prompt_tokens(text)
        
        assert tokens > 0
        assert self.counter.prompt_tokens == tokens
        assert self.counter.total_tokens == tokens
    
    def test_add_completion_tokens(self):
        """測試添加 Completion tokens"""
        text = "這是一個測試回應"
        tokens = self.counter.add_completion_tokens(text)
        
        assert tokens > 0
        assert self.counter.completion_tokens == tokens
        assert self.counter.total_tokens == tokens
    
    def test_session_tokens_tracking(self):
        """測試 Session tokens 追蹤"""
        session_id = "test_session"
        text = "測試文本"
        
        self.counter.add_prompt_tokens(text, session_id)
        session_tokens = self.counter.get_session_tokens(session_id)
        
        assert session_tokens > 0
    
    def test_get_statistics(self):
        """測試獲取統計信息"""
        self.counter.add_prompt_tokens("Prompt 文本")
        self.counter.add_completion_tokens("Completion 文本")
        
        stats = self.counter.get_statistics()
        
        assert "total_tokens" in stats
        assert "prompt_tokens" in stats
        assert "completion_tokens" in stats
        assert stats["total_tokens"] > 0


class TestContextCompressor:
    """測試 Context 壓縮器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.compressor = ContextCompressor(compression_ratio=0.7)
    
    @pytest.mark.asyncio
    async def test_compress_conversation(self):
        """測試壓縮對話"""
        conversation = [
            {"role": "user", "content": "消息 1"},
            {"role": "assistant", "content": "回應 1"},
            {"role": "user", "content": "消息 2"},
            {"role": "assistant", "content": "回應 2"},
            {"role": "user", "content": "消息 3"},
            {"role": "assistant", "content": "回應 3"},
            {"role": "user", "content": "消息 4"},
            {"role": "assistant", "content": "回應 4"},
            {"role": "user", "content": "消息 5"},
            {"role": "assistant", "content": "回應 5"},
        ]
        
        compressed = await self.compressor.compress_conversation(conversation)
        
        assert len(compressed) <= len(conversation)
        assert len(compressed) > 0
    
    @pytest.mark.asyncio
    async def test_remove_redundant_messages(self):
        """測試移除冗餘消息"""
        conversation = [
            {"role": "user", "content": "消息 1"},
            {"role": "user", "content": "消息 1"},  # 重複
            {"role": "assistant", "content": "回應 1"},
            {"role": "assistant", "content": "回應 1"},  # 重複
            {"role": "user", "content": "消息 2"},
        ]
        
        filtered = await self.compressor.remove_redundant_messages(conversation)
        
        assert len(filtered) < len(conversation)
    
    @pytest.mark.asyncio
    async def test_summarize_conversation(self):
        """測試總結對話"""
        conversation = [
            {"role": "user", "content": "這是一個很長的用戶消息，包含很多信息"},
            {"role": "assistant", "content": "這是一個很長的助手回應，包含詳細的解釋"},
            {"role": "user", "content": "用戶的後續問題"},
        ]
        
        summary = await self.compressor.summarize_conversation(conversation, max_length=200)
        
        assert isinstance(summary, str)
        assert len(summary) <= 200


class TestPromptOptimizer:
    """測試 Prompt 優化器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.optimizer = PromptOptimizer()
    
    @pytest.mark.asyncio
    async def test_optimize_system_instruction(self):
        """測試優化系統指令"""
        instruction = "你是一個防詐專家。  你需要幫助用戶識別詐騙。  你應該提供建議。"
        optimized = await self.optimizer.optimize_system_instruction(instruction)
        
        assert len(optimized) <= len(instruction)
        assert "防詐專家" in optimized
    
    @pytest.mark.asyncio
    async def test_optimize_user_prompt(self):
        """測試優化用戶 Prompt"""
        prompt = "這是一個很長的用戶 prompt，包含很多不必要的信息和重複的內容。" * 10
        optimized = await self.optimizer.optimize_user_prompt(prompt, max_length=500)
        
        assert len(optimized) <= 500
    
    @pytest.mark.asyncio
    async def test_build_efficient_context(self):
        """測試構建高效 Context"""
        system_instruction = "你是一個防詐專家"
        conversation = [
            {"role": "user", "content": "消息 1"},
            {"role": "assistant", "content": "回應 1"},
            {"role": "user", "content": "消息 2"},
            {"role": "assistant", "content": "回應 2"},
        ]
        
        context, tokens = await self.optimizer.build_efficient_context(
            system_instruction,
            conversation,
            max_tokens=2000
        )
        
        assert isinstance(context, str)
        assert tokens > 0
        assert tokens <= 2000


class TestTokenOptimizationService:
    """測試 Token 優化服務"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.service = TokenOptimizationService()
    
    @pytest.mark.asyncio
    async def test_optimize_for_llm_call(self):
        """測試為 LLM 調用優化"""
        system_instruction = "你是一個防詐專家"
        conversation = [
            {"role": "user", "content": "消息 1"},
            {"role": "assistant", "content": "回應 1"},
            {"role": "user", "content": "消息 2"},
            {"role": "assistant", "content": "回應 2"},
        ]
        user_message = "請幫我分析這是否是詐騙"
        
        result = await self.service.optimize_for_llm_call(
            system_instruction,
            conversation,
            user_message,
            max_tokens=2000
        )
        
        assert "optimized_context" in result
        assert "optimized_message" in result
        assert "tokens_used" in result
        assert result["tokens_used"] > 0
    
    @pytest.mark.asyncio
    async def test_optimize_with_session_id(self):
        """測試帶 Session ID 的優化"""
        session_id = "test_session"
        system_instruction = "你是一個防詐專家"
        conversation = [
            {"role": "user", "content": "消息 1"},
        ]
        user_message = "測試消息"
        
        result = await self.service.optimize_for_llm_call(
            system_instruction,
            conversation,
            user_message,
            max_tokens=2000,
            session_id=session_id
        )
        
        assert result["tokens_used"] > 0
    
    @pytest.mark.asyncio
    async def test_get_optimization_report(self):
        """測試獲取優化報告"""
        # 先進行一些優化
        await self.service.optimize_for_llm_call(
            "系統指令",
            [{"role": "user", "content": "消息"}],
            "用戶消息",
            max_tokens=2000
        )
        
        report = await self.service.get_optimization_report()
        
        assert "total_tokens" in report
        assert "prompt_tokens" in report


class TestTokenOptimizationEffectiveness:
    """測試 Token 優化的有效性"""
    
    @pytest.mark.asyncio
    async def test_compression_effectiveness(self):
        """測試壓縮有效性"""
        compressor = ContextCompressor(compression_ratio=0.5)
        counter = TokenCounter()
        
        # 創建長對話
        conversation = []
        for i in range(100):
            conversation.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"消息 {i}" * 10
            })
        
        # 計算原始 tokens
        original_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation])
        original_tokens = counter.count_tokens(original_text)
        
        # 壓縮
        compressed = await compressor.compress_conversation(conversation)
        
        # 計算壓縮後 tokens
        compressed_text = "\n".join([f"{m['role']}: {m['content']}" for m in compressed])
        compressed_tokens = counter.count_tokens(compressed_text)
        
        # 驗證壓縮有效
        assert compressed_tokens < original_tokens
        assert len(compressed) < len(conversation)
    
    @pytest.mark.asyncio
    async def test_optimization_reduces_tokens(self):
        """測試優化減少 tokens"""
        service = TokenOptimizationService()
        
        # 創建長系統指令
        system_instruction = "你是一個防詐專家。" * 50
        
        # 創建長對話
        conversation = []
        for i in range(20):
            conversation.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"消息 {i}" * 20
            })
        
        user_message = "請幫我分析這是否是詐騙" * 10
        
        # 優化
        result = await service.optimize_for_llm_call(
            system_instruction,
            conversation,
            user_message,
            max_tokens=2000
        )
        
        # 驗證優化有效
        assert result["compression_ratio"] < 1.0
        assert result["compressed_history_length"] <= result["original_history_length"]


class TestTokenCountingAccuracy:
    """測試 Token 計數準確性"""
    
    def test_token_count_consistency(self):
        """測試 Token 計數一致性"""
        counter = TokenCounter()
        text = "這是一個測試文本"
        
        count1 = counter.count_tokens(text)
        count2 = counter.count_tokens(text)
        
        assert count1 == count2
    
    def test_token_count_proportionality(self):
        """測試 Token 計數比例性"""
        counter = TokenCounter()
        
        text1 = "測試"
        text2 = "測試測試"
        
        count1 = counter.count_tokens(text1)
        count2 = counter.count_tokens(text2)
        
        # 更長的文本應該有更多的 tokens
        assert count2 > count1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


