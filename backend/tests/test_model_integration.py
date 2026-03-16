"""
集成測試：模型切換和多模式測試
測試 Ollama 和 Gemini 之間的切換，以及各種模式下的功能
"""

import pytest
import os
from unittest.mock import patch, Mock
from llms.llm_factory import LlmFactory
from config import config


class TestModelSwitching:
    """模型切換測試"""
    
    def test_get_current_provider_ollama(self):
        """測試獲取當前提供者（Ollama）"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            provider = LlmFactory.get_current_provider()
            assert provider == "ollama"
    
    def test_get_current_provider_gemini(self):
        """測試獲取當前提供者（Gemini）"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "true"}):
            config.gemini.GEMINI_ENABLED = True
            provider = LlmFactory.get_current_provider()
            assert provider == "gemini"
    
    def test_create_ollama_llm(self):
        """測試創建 Ollama LLM"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            llm = LlmFactory.create_llm("scammer")
            
            # 驗證是 OllamaLlm 實例
            assert llm.__class__.__name__ == "OllamaLlm"
    
    def test_create_gemini_llm(self):
        """測試創建 Gemini LLM"""
        with patch.dict(os.environ, {
            "GEMINI_ENABLED": "true",
            "GEMINI_API_KEY": "test_key_1234567890"
        }):
            config.gemini.GEMINI_ENABLED = True
            config.gemini.GEMINI_API_KEY = "test_key_1234567890"
            
            llm = LlmFactory.create_llm("scammer")
            
            # 驗證是 GeminiLlm 實例
            assert llm.__class__.__name__ == "GeminiLlm"
    
    def test_create_llm_invalid_agent_type(self):
        """測試無效的 Agent 類型"""
        with pytest.raises(ValueError, match="無效的 agent_type"):
            LlmFactory.create_llm("invalid_agent")
    
    def test_create_gemini_llm_without_api_key(self):
        """測試沒有 API Key 時創建 Gemini LLM 失敗"""
        with patch.dict(os.environ, {
            "GEMINI_ENABLED": "true",
            "GEMINI_API_KEY": ""
        }):
            config.gemini.GEMINI_ENABLED = True
            config.gemini.GEMINI_API_KEY = ""
            
            with pytest.raises(ValueError, match="API Key 未配置"):
                LlmFactory.create_llm("scammer")
    
    def test_get_provider_info_ollama(self):
        """測試獲取 Ollama 提供者信息"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            info = LlmFactory.get_provider_info()
            
            assert info["provider"] == "ollama"
            assert info["enabled"] is True
            assert "models" in info
            assert "scammer" in info["models"]
    
    def test_get_provider_info_gemini(self):
        """測試獲取 Gemini 提供者信息"""
        with patch.dict(os.environ, {
            "GEMINI_ENABLED": "true",
            "GEMINI_API_KEY": "test_key"
        }):
            config.gemini.GEMINI_ENABLED = True
            config.gemini.GEMINI_API_KEY = "test_key"
            
            info = LlmFactory.get_provider_info()
            
            assert info["provider"] == "gemini"
            assert info["enabled"] is True
            assert "models" in info
            assert "parameters" in info
    
    def test_validate_gemini_config_valid(self):
        """測試驗證有效的 Gemini 配置"""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key_1234567890",
            "GEMINI_MODEL_SCAMMER": "gemini-2.0-flash-exp"
        }):
            config.gemini.GEMINI_API_KEY = "test_key_1234567890"
            config.gemini.SCAMMER_MODEL_ID = "gemini-2.0-flash-exp"
            
            result = LlmFactory.validate_gemini_config()
            
            assert result["valid"] is True
            assert len(result["errors"]) == 0
    
    def test_validate_gemini_config_missing_api_key(self):
        """測試驗證缺少 API Key 的配置"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            config.gemini.GEMINI_API_KEY = ""
            
            result = LlmFactory.validate_gemini_config()
            
            assert result["valid"] is False
            assert any("API Key" in error for error in result["errors"])
    
    def test_validate_gemini_config_short_api_key(self):
        """測試驗證過短的 API Key"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "short"}):
            config.gemini.GEMINI_API_KEY = "short"
            
            result = LlmFactory.validate_gemini_config()
            
            assert result["valid"] is False
            assert any("格式無效" in error for error in result["errors"])
    
    def test_switch_between_providers(self):
        """測試在提供者之間切換"""
        # 初始為 Ollama
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            assert LlmFactory.get_current_provider() == "ollama"
            
            llm1 = LlmFactory.create_llm("scammer")
            assert llm1.__class__.__name__ == "OllamaLlm"
        
        # 切換到 Gemini
        with patch.dict(os.environ, {
            "GEMINI_ENABLED": "true",
            "GEMINI_API_KEY": "test_key_1234567890"
        }):
            config.gemini.GEMINI_ENABLED = True
            config.gemini.GEMINI_API_KEY = "test_key_1234567890"
            
            assert LlmFactory.get_current_provider() == "gemini"
            
            llm2 = LlmFactory.create_llm("scammer")
            assert llm2.__class__.__name__ == "GeminiLlm"


class TestAgentInitialization:
    """Agent 初始化測試"""
    
    def test_scammer_agent_with_ollama(self):
        """測試使用 Ollama 初始化 ScammerAgent"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            
            from agents.scammer import ScammerAgent
            agent = ScammerAgent(scam_tactic="假冒銀行")
            
            assert agent.name == "專業騙徒"
            assert agent.model.__class__.__name__ == "OllamaLlm"
    
    def test_victim_agent_with_ollama(self):
        """測試使用 Ollama 初始化 VictimAgent"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            
            from agents.victim import VictimAgent
            agent = VictimAgent(persona_type="elderly")
            
            assert agent.name == "受騙者"
            assert agent.model.__class__.__name__ == "OllamaLlm"
    
    def test_expert_agent_with_ollama(self):
        """測試使用 Ollama 初始化 ExpertAgent"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            
            from agents.expert import ExpertAgent
            agent = ExpertAgent(victim_persona="average")
            
            assert agent.name == "防騙專家"
            assert agent.model.__class__.__name__ == "OllamaLlm"
    
    def test_recorder_agent_with_ollama(self):
        """測試使用 Ollama 初始化 RecorderAgent"""
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            
            from agents.recorder import RecorderAgent
            agent = RecorderAgent()
            
            assert agent.name == "記錄人"
            assert agent.model.__class__.__name__ == "OllamaLlm"
    
    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_api_key_here",
        reason="需要真實的 GEMINI_API_KEY"
    )
    def test_all_agents_with_gemini(self):
        """測試使用 Gemini 初始化所有 Agent（需要真實 API Key）"""
        with patch.dict(os.environ, {
            "GEMINI_ENABLED": "true",
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
        }):
            config.gemini.GEMINI_ENABLED = True
            config.gemini.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            
            from agents.scammer import ScammerAgent
            from agents.victim import VictimAgent
            from agents.expert import ExpertAgent
            from agents.recorder import RecorderAgent
            
            scammer = ScammerAgent(scam_tactic="假冒銀行")
            victim = VictimAgent(persona_type="elderly")
            expert = ExpertAgent(victim_persona="average")
            recorder = RecorderAgent()
            
            assert scammer.model.__class__.__name__ == "GeminiLlm"
            assert victim.model.__class__.__name__ == "GeminiLlm"
            assert expert.model.__class__.__name__ == "GeminiLlm"
            assert recorder.model.__class__.__name__ == "GeminiLlm"


class TestMultiModeIntegration:
    """多模式集成測試"""
    
    def test_rpg_mode_with_model_switch(self):
        """測試 RPG 模式下的模型切換"""
        # 模擬 RPG 遊戲請求
        from services.agent_service import AgentService
        
        # 使用 Ollama
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            service = AgentService(persona_type="average")
            assert service.victim.model.__class__.__name__ == "OllamaLlm"
    
    def test_simulation_mode_with_model_switch(self):
        """測試自動模擬模式下的模型切換"""
        from services.agent_service import AgentService
        
        # 使用 Ollama
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            service = AgentService(persona_type="elderly")
            
            assert service.scammer.model.__class__.__name__ == "OllamaLlm"
            assert service.victim.model.__class__.__name__ == "OllamaLlm"
            assert service.expert.model.__class__.__name__ == "OllamaLlm"
    
    def test_personal_chat_mode_with_model_switch(self):
        """測試個人對話模式下的模型切換"""
        from services.agent_service import AgentService
        
        # 使用 Ollama
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            service = AgentService(persona_type="overconfident")
            
            assert service.expert.model.__class__.__name__ == "OllamaLlm"


class TestModelSwitchAPI:
    """模型切換 API 測試"""
    
    @pytest.mark.asyncio
    async def test_get_model_status(self):
        """測試獲取模型狀態 API"""
        from api.model_switch_routes import get_model_status
        
        with patch.dict(os.environ, {"GEMINI_ENABLED": "false"}):
            config.gemini.GEMINI_ENABLED = False
            
            result = await get_model_status()
            
            assert result["success"] is True
            assert result["current_provider"] == "ollama"
            assert "provider_info" in result
    
    @pytest.mark.asyncio
    async def test_validate_gemini_config_api(self):
        """測試驗證 Gemini 配置 API"""
        from api.model_switch_routes import validate_gemini_config, GeminiConfigRequest
        
        request = GeminiConfigRequest(
            api_key="test_key_1234567890",
            scammer_model="gemini-2.0-flash-exp",
            victim_model="gemini-2.0-flash-exp",
            expert_model="gemini-2.0-flash-exp",
            recorder_model="gemini-2.0-flash-exp"
        )
        
        with patch('api.model_switch_routes._test_gemini_connection') as mock_test:
            mock_test.return_value = {"success": False, "error": "API Key 無效"}
            
            result = await validate_gemini_config(request)
            
            assert result["valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
