"""
Gemini LLM 單元測試
測試 Gemini API 集成和功能
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from llms.gemini_llm import GeminiLlm
from google.genai import types as genai_types


class TestGeminiLlm:
    """Gemini LLM 測試套件"""
    
    @pytest.fixture
    def mock_api_key(self):
        """模擬 API Key"""
        return "test_api_key_1234567890"
    
    @pytest.fixture
    def gemini_llm(self, mock_api_key):
        """創建 Gemini LLM 實例"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": mock_api_key}):
            return GeminiLlm(
                model="gemini-2.0-flash-exp",
                api_key=mock_api_key
            )
    
    def test_initialization(self, gemini_llm, mock_api_key):
        """測試初始化"""
        assert gemini_llm.model == "gemini-2.0-flash-exp"
        assert gemini_llm.api_key == mock_api_key
        assert gemini_llm.temperature == 0.7
        assert gemini_llm.top_p == 0.95
        assert gemini_llm.top_k == 40
        assert gemini_llm.max_output_tokens == 2048
    
    def test_initialization_without_api_key(self):
        """測試沒有 API Key 時初始化失敗"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY 未設置"):
                GeminiLlm(model="gemini-2.0-flash-exp")
    
    def test_supported_models(self):
        """測試支持的模型列表"""
        models = GeminiLlm.supported_models()
        assert "gemini-2.0-flash-exp" in models
        assert "gemini-1.5-flash" in models
        assert "gemini-1.5-pro" in models
        assert "tunedModels/*" in models
    
    def test_generation_config(self, gemini_llm):
        """測試生成配置"""
        config = gemini_llm._get_generation_config()
        assert config.temperature == 0.7
        assert config.top_p == 0.95
        assert config.top_k == 40
        assert config.max_output_tokens == 2048
    
    def test_safety_settings(self, gemini_llm):
        """測試安全設置"""
        settings = gemini_llm._get_safety_settings()
        assert len(settings) == 4  # 4 個安全類別
        # 驗證所有設置都是 BLOCK_NONE（適合詐騙模擬場景）
        for category, threshold in settings.items():
            assert threshold.name == "BLOCK_NONE"
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, gemini_llm):
        """測試成功生成內容"""
        # 模擬 LLM 請求
        mock_request = Mock()
        mock_content = Mock()
        mock_part = Mock()
        mock_part.text = "這是測試提示"
        mock_content.parts = [mock_part]
        mock_content.role = "user"
        mock_request.contents = [mock_content]
        mock_request.system_instruction = "你是測試助手"
        
        # 模擬 Gemini API 響應
        mock_response = Mock()
        mock_response.text = "這是測試響應"
        mock_response.candidates = [Mock()]
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            # 執行生成
            responses = []
            async for response in gemini_llm.generate_content_async(mock_request):
                responses.append(response)
            
            # 驗證
            assert len(responses) == 1
            assert responses[0].content.parts[0].text == "這是測試響應"
            assert responses[0].content.role == "model"
    
    @pytest.mark.asyncio
    async def test_generate_content_timeout(self, gemini_llm):
        """測試生成超時"""
        mock_request = Mock()
        mock_content = Mock()
        mock_part = Mock()
        mock_part.text = "測試"
        mock_content.parts = [mock_part]
        mock_content.role = "user"
        mock_request.contents = [mock_content]
        mock_request.system_instruction = ""
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            # 模擬超時
            async def slow_generate(*args, **kwargs):
                import asyncio
                await asyncio.sleep(100)
            
            mock_model.generate_content = slow_generate
            mock_model_class.return_value = mock_model
            
            # 設置短超時
            gemini_llm.timeout = 0.1
            
            with pytest.raises(Exception, match="超時"):
                async for _ in gemini_llm.generate_content_async(mock_request):
                    pass
    
    @pytest.mark.asyncio
    async def test_generate_content_retry(self, gemini_llm):
        """測試重試機制"""
        mock_request = Mock()
        mock_content = Mock()
        mock_part = Mock()
        mock_part.text = "測試"
        mock_content.parts = [mock_part]
        mock_content.role = "user"
        mock_request.contents = [mock_content]
        mock_request.system_instruction = ""
        
        # 模擬第一次失敗，第二次成功
        call_count = 0
        
        def generate_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("503 Service Unavailable")
            
            mock_response = Mock()
            mock_response.text = "成功響應"
            mock_response.candidates = [Mock()]
            return mock_response
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = generate_with_retry
            mock_model_class.return_value = mock_model
            
            # 執行生成
            responses = []
            async for response in gemini_llm.generate_content_async(mock_request):
                responses.append(response)
            
            # 驗證重試成功
            assert call_count == 2
            assert len(responses) == 1
            assert responses[0].content.parts[0].text == "成功響應"
    
    @pytest.mark.asyncio
    async def test_generate_content_empty_response(self, gemini_llm):
        """測試空響應處理"""
        mock_request = Mock()
        mock_content = Mock()
        mock_part = Mock()
        mock_part.text = "測試"
        mock_content.parts = [mock_part]
        mock_content.role = "user"
        mock_request.contents = [mock_content]
        mock_request.system_instruction = ""
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.candidates = []  # 空響應
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            with pytest.raises(Exception, match="空響應"):
                async for _ in gemini_llm.generate_content_async(mock_request):
                    pass
    
    @pytest.mark.asyncio
    async def test_generate_content_long_response_truncation(self, gemini_llm):
        """測試過長響應截斷"""
        mock_request = Mock()
        mock_content = Mock()
        mock_part = Mock()
        mock_part.text = "測試"
        mock_content.parts = [mock_part]
        mock_content.role = "user"
        mock_request.contents = [mock_content]
        mock_request.system_instruction = ""
        
        # 創建超長響應（6000 字元）
        long_text = "測試" * 3000
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = long_text
            mock_response.candidates = [Mock()]
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            responses = []
            async for response in gemini_llm.generate_content_async(mock_request):
                responses.append(response)
            
            # 驗證響應被截斷
            result_text = responses[0].content.parts[0].text
            assert len(result_text) <= 5000
    
    def test_custom_parameters(self):
        """測試自定義參數"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            llm = GeminiLlm(
                model="gemini-1.5-pro",
                api_key="test_key",
                temperature=0.9,
                top_p=0.8,
                top_k=50,
                max_output_tokens=4096,
                timeout=120.0,
                max_retries=5
            )
            
            assert llm.model == "gemini-1.5-pro"
            assert llm.temperature == 0.9
            assert llm.top_p == 0.8
            assert llm.top_k == 50
            assert llm.max_output_tokens == 4096
            assert llm.timeout == 120.0
            assert llm.max_retries == 5


class TestGeminiLlmIntegration:
    """Gemini LLM 集成測試（需要真實 API Key）"""
    
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_api_key_here",
        reason="需要真實的 GEMINI_API_KEY 環境變量"
    )
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """測試真實 API 調用（僅在有 API Key 時運行）"""
        llm = GeminiLlm(
            model="gemini-2.0-flash-exp",
            api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # 創建簡單請求
        mock_request = Mock()
        mock_content = Mock()
        mock_part = Mock()
        mock_part.text = "你好，請回答：1+1等於多少？"
        mock_content.parts = [mock_part]
        mock_content.role = "user"
        mock_request.contents = [mock_content]
        mock_request.system_instruction = "你是一個數學助手"
        
        # 執行生成
        responses = []
        async for response in llm.generate_content_async(mock_request):
            responses.append(response)
        
        # 驗證
        assert len(responses) == 1
        assert len(responses[0].content.parts[0].text) > 0
        print(f"API 響應: {responses[0].content.parts[0].text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
