"""
LLM Factory - 統一管理 LLM 提供者選擇
支持 Ollama 和 Gemini API 動態切換
使用 RAG 系統代替文件上傳（優化 Token 使用）
"""

import os
from typing import Optional, Dict
from config import config
from utils.logger import log


class LlmFactory:
    """
    LLM 工廠類
    根據配置動態創建 Ollama 或 Gemini LLM 實例
    使用 RAG 系統進行知識檢索，避免上傳大文件
    """
    
    # 類變量：RAG 輔助類實例（單例）
    _rag_helper: Optional[any] = None
    
    @staticmethod
    def _get_rag_helper():
        """
        獲取 RAG 輔助類實例（單例模式）
        
        Returns:
            GeminiRAGHelper: RAG 輔助類實例
        """
        if LlmFactory._rag_helper is None:
            try:
                from llms.rag_integration import GeminiRAGHelper
                LlmFactory._rag_helper = GeminiRAGHelper(n_results=5, max_distance=10.0)
                log.info("[LLM_FACTORY] ✅ RAG 系統已初始化")
            except Exception as e:
                log.error(f"[LLM_FACTORY] ❌ RAG 系統初始化失敗: {e}")
                LlmFactory._rag_helper = None
        
        return LlmFactory._rag_helper
    
    @staticmethod
    def get_rag_context(scam_type: str = "", context: str = "") -> str:
        """
        使用 RAG 系統檢索相關案例（代替文件上傳）
        
        Args:
            scam_type: 騙案類型
            context: 額外上下文
        
        Returns:
            str: 格式化的相關案例文本
        """
        rag_helper = LlmFactory._get_rag_helper()
        
        if rag_helper is None:
            log.warning("[LLM_FACTORY] RAG 系統不可用，返回空上下文")
            return ""
        
        try:
            if scam_type:
                return rag_helper.format_for_prompt(scam_type, context)
            elif context:
                return rag_helper.get_relevant_cases(context)
            else:
                return ""
        except Exception as e:
            log.error(f"[LLM_FACTORY] RAG 檢索失敗: {e}")
            return ""
    
    @staticmethod
    def create_llm(agent_type: str, use_gemini: Optional[bool] = None, scam_type: str = "", context: str = ""):
        """
        創建 LLM 實例（支持 RAG 上下文注入）
        
        Args:
            agent_type: Agent 類型 ("scammer" | "victim" | "expert" | "recorder")
            use_gemini: 強制使用 Gemini（None 則讀取配置）
            scam_type: 騙案類型（用於 RAG 檢索）
            context: 額外上下文（用於 RAG 檢索）
        
        Returns:
            BaseLlm: OllamaLlm 或 GeminiLlm 實例
        
        Raises:
            ValueError: 如果 agent_type 無效或配置錯誤
        """
        # 驗證 agent_type
        valid_types = ["scammer", "victim", "expert", "recorder"]
        if agent_type not in valid_types:
            raise ValueError(f"無效的 agent_type: {agent_type}. 必須是 {valid_types} 之一")
        
        # 決定使用哪個提供者
        if use_gemini is None:
            use_gemini = config.gemini.GEMINI_ENABLED
        
        if use_gemini:
            return LlmFactory._create_gemini_llm(agent_type, scam_type, context)
        else:
            return LlmFactory._create_ollama_llm(agent_type)
    
    @staticmethod
    def _create_gemini_llm(agent_type: str, scam_type: str = "", context: str = ""):
        """創建 Gemini LLM 實例，使用 RAG 系統代替文件上傳"""
        try:
            from llms.gemini_llm import GeminiLlm
            
            # 檢查 API Key
            if not config.gemini.is_configured():
                raise ValueError(
                    "Gemini API Key 未配置。請設置 GEMINI_API_KEY 環境變量。"
                )
            
            # 獲取模型 ID
            model_id = config.gemini.get_model_id(agent_type)
            
            # 獲取 System Instruction
            try:
                from agents.system_instructions import get_system_instruction
                system_instruction = get_system_instruction(agent_type)
                log.info(f"[LLM_FACTORY] 載入 System Instruction: {len(system_instruction)} 字")
            except Exception as e:
                log.warning(f"[LLM_FACTORY] 無法載入 System Instruction: {e}")
                system_instruction = ""
            
            # ✅ 使用 RAG 系統注入相關案例到 System Instruction
            rag_context = ""
            if agent_type in ["scammer", "expert"] and (scam_type or context):
                rag_context = LlmFactory.get_rag_context(scam_type, context)
                if rag_context:
                    log.info(f"[LLM_FACTORY] ✅ RAG 檢索成功，注入 {len(rag_context)} 字上下文")
                    system_instruction = f"{system_instruction}\n\n{rag_context}"
                else:
                    log.warning(f"[LLM_FACTORY] ⚠️ RAG 檢索失敗或無結果")
            
            log.info(
                f"[LLM_FACTORY] 創建 Gemini LLM (使用 RAG) - "
                f"Agent: {agent_type}, 模型: {model_id}, "
                f"System Instruction: {len(system_instruction)} 字"
            )
            
            # 創建實例（不傳入 uploaded_files）
            return GeminiLlm(
                model=model_id,
                api_key=config.gemini.GEMINI_API_KEY,
                system_instruction=system_instruction,
                uploaded_files=[],  # ✅ 空列表，不上傳文件
                temperature=config.gemini.TEMPERATURE,
                top_p=config.gemini.TOP_P,
                top_k=config.gemini.TOP_K,
                max_output_tokens=config.gemini.MAX_OUTPUT_TOKENS,
                timeout=config.gemini.TIMEOUT,
                max_retries=config.gemini.MAX_RETRIES
            )
            
        except ImportError as e:
            log.error(f"[LLM_FACTORY] 無法導入 GeminiLlm: {e}")
            raise ValueError(
                "Gemini LLM 模塊未安裝。請運行: pip install google-generativeai"
            )
        except Exception as e:
            log.error(f"[LLM_FACTORY] 創建 Gemini LLM 失敗: {e}")
            raise
    
    @staticmethod
    def _create_ollama_llm(agent_type: str):
        """創建 Ollama LLM 實例"""
        try:
            from llms.ollama_llm import OllamaLlm
            
            # 獲取模型名稱和 URL
            model_mapping = {
                "scammer": config.llm.SCAMMER_MODEL,
                "victim": config.llm.VICTIM_MODEL,
                "expert": config.llm.EXPERT_MODEL,
                "recorder": config.llm.RECORDER_MODEL
            }
            
            url_mapping = {
                "scammer": config.llm.SCAMMER_BASE_URL,
                "victim": config.llm.VICTIM_BASE_URL,
                "expert": config.llm.EXPERT_BASE_URL,
                "recorder": config.llm.RECORDER_BASE_URL
            }
            
            model_name = model_mapping.get(agent_type, config.llm.DEFAULT_MODEL)
            base_url = url_mapping.get(agent_type, config.llm.DEFAULT_BASE_URL)
            
            log.info(
                f"[LLM_FACTORY] 創建 Ollama LLM - "
                f"Agent: {agent_type}, 模型: {model_name}, URL: {base_url}"
            )
            
            # 創建實例
            return OllamaLlm(
                model=model_name,
                base_url=base_url
            )
            
        except ImportError as e:
            log.error(f"[LLM_FACTORY] 無法導入 OllamaLlm: {e}")
            raise ValueError("Ollama LLM 模塊未找到")
        except Exception as e:
            log.error(f"[LLM_FACTORY] 創建 Ollama LLM 失敗: {e}")
            raise
    
    @staticmethod
    def get_current_provider() -> str:
        """
        獲取當前使用的 LLM 提供者
        
        Returns:
            str: "gemini" 或 "ollama"
        """
        return "gemini" if config.gemini.GEMINI_ENABLED else "ollama"
    
    @staticmethod
    def get_provider_info() -> dict:
        """
        獲取當前提供者的詳細信息
        
        Returns:
            dict: 提供者信息
        """
        provider = LlmFactory.get_current_provider()
        
        if provider == "gemini":
            return {
                "provider": "gemini",
                "enabled": True,
                "configured": config.gemini.is_configured(),
                "models": {
                    "scammer": config.gemini.SCAMMER_MODEL_ID,
                    "victim": config.gemini.VICTIM_MODEL_ID,
                    "expert": config.gemini.EXPERT_MODEL_ID,
                    "recorder": config.gemini.RECORDER_MODEL_ID
                },
                "parameters": {
                    "temperature": config.gemini.TEMPERATURE,
                    "top_p": config.gemini.TOP_P,
                    "top_k": config.gemini.TOP_K,
                    "max_output_tokens": config.gemini.MAX_OUTPUT_TOKENS
                }
            }
        else:
            return {
                "provider": "ollama",
                "enabled": True,
                "configured": True,
                "models": {
                    "scammer": config.llm.SCAMMER_MODEL,
                    "victim": config.llm.VICTIM_MODEL,
                    "expert": config.llm.EXPERT_MODEL,
                    "recorder": config.llm.RECORDER_MODEL
                },
                "base_urls": {
                    "scammer": config.llm.SCAMMER_BASE_URL,
                    "victim": config.llm.VICTIM_BASE_URL,
                    "expert": config.llm.EXPERT_BASE_URL,
                    "recorder": config.llm.RECORDER_BASE_URL
                }
            }
    
    @staticmethod
    def validate_gemini_config() -> dict:
        """
        驗證 Gemini 配置是否有效
        
        Returns:
            dict: 驗證結果
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        # 檢查 API Key
        if not config.gemini.GEMINI_API_KEY:
            result["errors"].append("GEMINI_API_KEY 未設置")
        elif len(config.gemini.GEMINI_API_KEY) < 10:
            result["errors"].append("GEMINI_API_KEY 格式無效（長度過短）")
        
        # 檢查模型 ID
        models = {
            "scammer": config.gemini.SCAMMER_MODEL_ID,
            "victim": config.gemini.VICTIM_MODEL_ID,
            "expert": config.gemini.EXPERT_MODEL_ID,
            "recorder": config.gemini.RECORDER_MODEL_ID
        }
        
        for agent_type, model_id in models.items():
            if not model_id:
                result["errors"].append(f"{agent_type} 模型 ID 未設置")
            elif model_id == "gemini-2.0-flash-exp" or model_id == "gemini-2.5-flash":
                result["warnings"].append(
                    f"{agent_type} 使用默認模型（未使用 System Instructions 優化）"
                )
        
        # 如果沒有錯誤，則配置有效
        result["valid"] = len(result["errors"]) == 0
        
        return result
