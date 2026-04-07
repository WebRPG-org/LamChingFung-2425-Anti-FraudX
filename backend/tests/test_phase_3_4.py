"""
backend/tests/test_phase_3_4.py - Phase 3 & 4 測試套件
測試所有服務和API端點
"""

import pytest
import asyncio
from typing import Dict, Any

from backend.services.conversational_style_processor import get_conversational_style_processor
from backend.services.response_length_controller import get_response_length_controller
from backend.services.evaluation_integration import get_evaluation_integration
from backend.services.api_integration import get_api_integration


# ============ Fixtures ============

@pytest.fixture
def style_processor():
    """口語化處理器fixture"""
    return get_conversational_style_processor()


@pytest.fixture
def length_controller():
    """長度控制器fixture"""
    return get_response_length_controller(max_length=80, max_tokens=100)


@pytest.fixture
def evaluation_integration():
    """評估集成fixture"""
    return get_evaluation_integration()


@pytest.fixture
def api_integration():
    """API集成fixture"""
    return get_api_integration()


# ============ Phase 3.1 - 口語化處理測試 ============

class TestConversationalStyleProcessor:
    """口語化處理器測試"""
    
    @pytest.mark.asyncio
    async def test_remove_formatting_marks(self, style_processor):
        """測試移除格式化標記"""
        text = "**這是詐騙** 【警告】 __不要__ 轉賬"
        result = style_processor._remove_formatting_marks(text)
        
        assert "**" not in result
        assert "【" not in result
        assert "__" not in result
        assert "這是詐騙" in result
    
    @pytest.mark.asyncio
    async def test_convert_formal_to_casual(self, style_processor):
        """測試轉換正式用語為口語"""
        text = "這是詐騙 請注意 必須小心"
        result = style_processor._convert_formal_to_casual(text)
        
        assert "你要留意" in result or "小心" in result
    
    @pytest.mark.asyncio
    async def test_process_full_text(self, style_processor):
        """測試完整文本處理"""
        text = "**【分析】這是詐騙** __請注意__ 必須小心"
        result = await style_processor.process(text)
        
        assert "**" not in result
        assert "【" not in result
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_get_expert_prompt(self, style_processor):
        """測試獲取專家Prompt"""
        prompt = await style_processor.get_expert_prompt("冒充身份詐騙")
        
        assert len(prompt) > 0
        assert "防詐騙" in prompt or "詐騙" in prompt


# ============ Phase 3.2 - 長度控制測試 ============

class TestResponseLengthController:
    """長度控制器測試"""
    
    @pytest.mark.asyncio
    async def test_smart_truncate_short_text(self, length_controller):
        """測試短文本截斷"""
        text = "這是一個短文本"
        result = await length_controller.smart_truncate(text, max_length=80)
        
        assert result == text
    
    @pytest.mark.asyncio
    async def test_smart_truncate_long_text(self, length_controller):
        """測試長文本截斷"""
        text = "這是一個很長的文本。" * 20
        result = await length_controller.smart_truncate(text, max_length=80)
        
        assert len(result) <= 80
        assert result.endswith(('。', '，', ' '))
    
    @pytest.mark.asyncio
    async def test_count_tokens(self, length_controller):
        """測試Token計數"""
        text = "這是一個測試文本 with English words"
        tokens = await length_controller.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    @pytest.mark.asyncio
    async def test_validate_length_valid(self, length_controller):
        """測試有效長度驗證"""
        text = "這是一個短文本"
        is_valid, details = await length_controller.validate_length(text)
        
        assert is_valid is True
        assert details['char_valid'] is True
    
    @pytest.mark.asyncio
    async def test_validate_length_invalid(self, length_controller):
        """測試無效長度驗證"""
        text = "這是一個很長的文本。" * 50
        is_valid, details = await length_controller.validate_length(text)
        
        assert is_valid is False
        assert details['char_valid'] is False
    
    @pytest.mark.asyncio
    async def test_post_process_response(self, length_controller):
        """測試後處理回應"""
        text = "這是一個測試回應。  多個空格。"
        result = await length_controller.post_process_response(text)
        
        assert "  " not in result
        assert result.endswith(('。', '，', '！', '？'))


# ============ Phase 3.3 - 評估集成測試 ============

class TestEvaluationIntegration:
    """評估集成測試"""
    
    @pytest.mark.asyncio
    async def test_build_expert_system_prompt(self, evaluation_integration):
        """測試構建專家System Prompt"""
        prompt = await evaluation_integration.build_expert_system_prompt("冒充身份詐騙")
        
        assert len(prompt) > 0
        assert "防詐騙" in prompt or "詐騙" in prompt
    
    @pytest.mark.asyncio
    async def test_validate_response_quality_good(self, evaluation_integration):
        """測試驗證高質量回應"""
        response = "呢個係詐騙嚟，你聽我講，呢個係冒充身份詐騙。你要小心，唔好轉賬。"
        result = await evaluation_integration.validate_response_quality(
            response=response,
            scam_type="冒充身份詐騙"
        )
        
        assert result['quality_score'] >= 50
        assert result['is_conversational'] is True
    
    @pytest.mark.asyncio
    async def test_validate_response_quality_poor(self, evaluation_integration):
        """測試驗證低質量回應"""
        response = "**【分析】這是詐騙**"
        result = await evaluation_integration.validate_response_quality(
            response=response,
            scam_type="冒充身份詐騙"
        )
        
        assert result['quality_score'] < 100
        assert result['is_conversational'] is False


# ============ Phase 3.4 - API集成測試 ============

class TestAPIIntegration:
    """API集成測試"""
    
    @pytest.mark.asyncio
    async def test_handle_response_processing_full(self, api_integration):
        """測試完整回應處理"""
        response = "**【分析】這是詐騙** __請注意__"
        result = await api_integration.handle_response_processing(
            response=response,
            processing_type="full"
        )
        
        assert result['success'] is True
        assert 'final_response' in result['data']
    
    @pytest.mark.asyncio
    async def test_handle_response_processing_conversational(self, api_integration):
        """測試口語化處理"""
        response = "**【分析】這是詐騙**"
        result = await api_integration.handle_response_processing(
            response=response,
            processing_type="conversational"
        )
        
        assert result['success'] is True
        assert 'conversational_response' in result['data']
    
    @pytest.mark.asyncio
    async def test_handle_response_processing_length_control(self, api_integration):
        """測試長度控制"""
        response = "這是一個很長的文本。" * 50
        result = await api_integration.handle_response_processing(
            response=response,
            processing_type="length_control"
        )
        
        assert result['success'] is True
        assert 'length_controlled_response' in result['data']
    
    @pytest.mark.asyncio
    async def test_handle_quality_validation(self, api_integration):
        """測試質量驗證"""
        response = "呢個係詐騙嚟，你要小心。"
        result = await api_integration.handle_quality_validation(
            response=response,
            scam_type="冒充身份詐騙"
        )
        
        assert result['success'] is True
        assert 'quality_score' in result['data']
    
    @pytest.mark.asyncio
    async def test_handle_system_prompt_generation(self, api_integration):
        """測試System Prompt生成"""
        result = await api_integration.handle_system_prompt_generation(
            scam_type="冒充身份詐騙"
        )
        
        assert result['success'] is True
        assert 'system_prompt' in result['data']
        assert len(result['data']['system_prompt']) > 0


# ============ 集成測試 ============

class TestIntegration:
    """集成測試"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, api_integration):
        """測試完整管道"""
        # 1. 生成System Prompt
        prompt_result = await api_integration.handle_system_prompt_generation(
            scam_type="冒充身份詐騙"
        )
        assert prompt_result['success'] is True
        
        # 2. 處理回應
        response = "**【分析】這是詐騙** __請注意__ 必須小心"
        processing_result = await api_integration.handle_response_processing(
            response=response,
            processing_type="full"
        )
        assert processing_result['success'] is True
        
        # 3. 驗證質量
        final_response = processing_result['data']['final_response']
        quality_result = await api_integration.handle_quality_validation(
            response=final_response,
            scam_type="冒充身份詐騙"
        )
        assert quality_result['success'] is True
        
        # 驗證質量分數
        assert quality_result['data']['quality_score'] >= 0
        assert quality_result['data']['quality_level'] in ['優秀', '良好', '中等', '需改進']


# ============ 性能測試 ============

class TestPerformance:
    """性能測試"""
    
    @pytest.mark.asyncio
    async def test_processing_speed(self, api_integration):
        """測試處理速度"""
        import time
        
        response = "**【分析】這是詐騙**" * 10
        
        start = time.time()
        result = await api_integration.handle_response_processing(
            response=response,
            processing_type="full"
        )
        elapsed = time.time() - start
        
        assert result['success'] is True
        assert elapsed < 1.0  # 應該在1秒內完成


# ============ 運行測試 ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])


