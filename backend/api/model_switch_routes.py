"""
模型切換 API 路由
支持 Ollama 和 Gemini 之間的動態切換
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv, set_key, find_dotenv

from config import config
from llms.llm_factory import LlmFactory
from utils.logger import log

load_dotenv()

router = APIRouter(prefix="/api/model", tags=["Model Management"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ModelSwitchRequest(BaseModel):
    """模型切換請求"""
    use_gemini: bool = Field(..., description="是否使用 Gemini (true) 或 Ollama (false)")
    gemini_api_key: Optional[str] = Field(None, description="Gemini API Key (首次切換時需要)")
    gemini_models: Optional[Dict[str, str]] = Field(None, description="Gemini 模型 ID 配置")


class GeminiConfigRequest(BaseModel):
    """Gemini 配置請求"""
    api_key: str = Field(..., min_length=10, description="Gemini API Key")
    scammer_model: str = Field("gemini-2.0-flash-exp", description="騙徒模型 ID")
    victim_model: str = Field("gemini-2.0-flash-exp", description="受害者模型 ID")
    expert_model: str = Field("gemini-2.0-flash-exp", description="專家模型 ID")
    recorder_model: str = Field("gemini-2.0-flash-exp", description="記錄員模型 ID")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status")
async def get_model_status():
    """
    獲取當前使用的模型狀態
    
    Returns:
        dict: 當前模型提供者和配置信息
    """
    try:
        provider = LlmFactory.get_current_provider()
        provider_info = LlmFactory.get_provider_info()
        
        return {
            "success": True,
            "current_provider": provider,
            "gemini_enabled": config.gemini.GEMINI_ENABLED,
            "gemini_configured": config.gemini.is_configured(),
            "provider_info": provider_info
        }
    except Exception as e:
        log.error(f"[MODEL_API] 獲取模型狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch")
async def switch_model(request: ModelSwitchRequest):
    """
    切換模型提供者
    
    Args:
        request: 切換請求（包含目標提供者和配置）
    
    Returns:
        dict: 切換結果
    """
    try:
        current_provider = LlmFactory.get_current_provider()
        target_provider = "gemini" if request.use_gemini else "ollama"
        
        log.info(f"[MODEL_API] 切換模型: {current_provider} → {target_provider}")
        
        # 如果切換到 Gemini，需要驗證配置
        if request.use_gemini:
            # 檢查是否提供了 API Key
            if request.gemini_api_key:
                # 更新環境變量
                _update_env_variable("GEMINI_API_KEY", request.gemini_api_key)
                config.gemini.GEMINI_API_KEY = request.gemini_api_key
            
            # 檢查是否提供了模型配置
            if request.gemini_models:
                if "scammer" in request.gemini_models:
                    _update_env_variable("GEMINI_MODEL_SCAMMER", request.gemini_models["scammer"])
                    config.gemini.SCAMMER_MODEL_ID = request.gemini_models["scammer"]
                if "victim" in request.gemini_models:
                    _update_env_variable("GEMINI_MODEL_VICTIM", request.gemini_models["victim"])
                    config.gemini.VICTIM_MODEL_ID = request.gemini_models["victim"]
                if "expert" in request.gemini_models:
                    _update_env_variable("GEMINI_MODEL_EXPERT", request.gemini_models["expert"])
                    config.gemini.EXPERT_MODEL_ID = request.gemini_models["expert"]
                if "recorder" in request.gemini_models:
                    _update_env_variable("GEMINI_MODEL_RECORDER", request.gemini_models["recorder"])
                    config.gemini.RECORDER_MODEL_ID = request.gemini_models["recorder"]
            
            # 驗證配置
            validation = LlmFactory.validate_gemini_config()
            if not validation["valid"]:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Gemini 配置無效",
                        "errors": validation["errors"]
                    }
                )
            
            # 測試 API 連接
            try:
                test_result = await _test_gemini_connection()
                if not test_result["success"]:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "Gemini API 連接測試失敗",
                            "error": test_result.get("error")
                        }
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Gemini API 連接測試失敗",
                        "error": str(e)
                    }
                )
        
        # 更新 GEMINI_ENABLED 環境變量
        _update_env_variable("GEMINI_ENABLED", "true" if request.use_gemini else "false")
        config.gemini.GEMINI_ENABLED = request.use_gemini
        
        log.info(f"[MODEL_API] 模型切換成功: {target_provider}")
        
        return {
            "success": True,
            "message": f"已切換至 {target_provider.upper()}",
            "previous_provider": current_provider,
            "current_provider": target_provider,
            "requires_restart": False,  # 動態切換，無需重啟
            "provider_info": LlmFactory.get_provider_info()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[MODEL_API] 切換模型失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_gemini_config(request: GeminiConfigRequest):
    """
    驗證 Gemini API 配置
    
    Args:
        request: Gemini 配置
    
    Returns:
        dict: 驗證結果
    """
    try:
        log.info("[MODEL_API] 驗證 Gemini 配置")
        
        # 臨時設置配置（不保存）
        original_api_key = config.gemini.GEMINI_API_KEY
        config.gemini.GEMINI_API_KEY = request.api_key
        
        # 驗證配置格式
        validation = LlmFactory.validate_gemini_config()
        
        # 測試 API 連接
        connection_test = await _test_gemini_connection()
        
        # 恢復原配置
        config.gemini.GEMINI_API_KEY = original_api_key
        
        if not connection_test["success"]:
            return {
                "valid": False,
                "errors": [connection_test.get("error", "API 連接失敗")],
                "warnings": validation.get("warnings", [])
            }
        
        return {
            "valid": validation["valid"],
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", []),
            "connection_test": connection_test
        }
        
    except Exception as e:
        log.error(f"[MODEL_API] 驗證配置失敗: {e}")
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": []
        }


@router.post("/config/gemini")
async def save_gemini_config(request: GeminiConfigRequest):
    """
    保存 Gemini 配置到環境變量
    
    Args:
        request: Gemini 配置
    
    Returns:
        dict: 保存結果
    """
    try:
        log.info("[MODEL_API] 保存 Gemini 配置")
        
        # 先驗證配置
        validation_result = await validate_gemini_config(request)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "配置驗證失敗",
                    "errors": validation_result["errors"]
                }
            )
        
        # 保存到環境變量
        _update_env_variable("GEMINI_API_KEY", request.api_key)
        _update_env_variable("GEMINI_MODEL_SCAMMER", request.scammer_model)
        _update_env_variable("GEMINI_MODEL_VICTIM", request.victim_model)
        _update_env_variable("GEMINI_MODEL_EXPERT", request.expert_model)
        _update_env_variable("GEMINI_MODEL_RECORDER", request.recorder_model)
        
        # 更新配置對象
        config.gemini.GEMINI_API_KEY = request.api_key
        config.gemini.SCAMMER_MODEL_ID = request.scammer_model
        config.gemini.VICTIM_MODEL_ID = request.victim_model
        config.gemini.EXPERT_MODEL_ID = request.expert_model
        config.gemini.RECORDER_MODEL_ID = request.recorder_model
        
        log.info("[MODEL_API] Gemini 配置保存成功")
        
        return {
            "success": True,
            "message": "Gemini 配置已保存",
            "warnings": validation_result.get("warnings", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[MODEL_API] 保存配置失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_available_providers():
    """
    獲取可用的 LLM 提供者列表
    
    Returns:
        dict: 提供者列表和狀態
    """
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama (本地)",
                "description": "本地部署的 LLM，數據完全離線",
                "available": True,
                "configured": True
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "description": "Google Gemini API，支持 fine-tuned 模型",
                "available": True,
                "configured": config.gemini.is_configured()
            }
        ],
        "current": LlmFactory.get_current_provider()
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _update_env_variable(key: str, value: str):
    """更新 .env 文件中的環境變量"""
    try:
        env_file = find_dotenv()
        if not env_file:
            # 如果 .env 不存在，創建一個
            env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            with open(env_file, 'w') as f:
                f.write(f"{key}={value}\n")
        else:
            set_key(env_file, key, value)
        
        # 同時更新當前進程的環境變量
        os.environ[key] = value
        
        log.info(f"[MODEL_API] 環境變量已更新: {key}")
    except Exception as e:
        log.error(f"[MODEL_API] 更新環境變量失敗: {e}")
        raise


async def _test_gemini_connection() -> Dict[str, Any]:
    """測試 Gemini API 連接"""
    try:
        from google import genai
        from google.genai import types
        
        # 創建客戶端
        client = genai.Client(api_key=config.gemini.GEMINI_API_KEY)
        
        # 測試簡單的生成請求（使用正確的模型名稱）
        response = client.models.generate_content(
            model="models/gemini-3-flash-preview",
            contents=types.Content(
                parts=[types.Part(text="測試連接")]
            ),
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=50
            )
        )
        
        if response and response.text:
            log.info("[MODEL_API] Gemini API 連接測試成功")
            return {
                "success": True,
                "message": "API 連接正常",
                "test_response": response.text[:50] + "..." if len(response.text) > 50 else response.text
            }
        else:
            return {
                "success": False,
                "error": "API 返回空響應"
            }
            
    except Exception as e:
        log.error(f"[MODEL_API] Gemini API 連接測試失敗: {e}")
        return {
            "success": False,
            "error": str(e)
        }
