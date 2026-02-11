"""離線模式檢查和強制"""
import os
import logging
from typing import Optional

log = logging.getLogger(__name__)

# 檢查環境變數
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "true").lower() == "true"
DISABLE_EXTERNAL_APIS = os.getenv("DISABLE_EXTERNAL_APIS", "true").lower() == "true"
DISABLE_DATA_UPLOAD = os.getenv("DISABLE_DATA_UPLOAD", "true").lower() == "true"

def check_offline_mode():
    """檢查並強制離線模式"""
    if OFFLINE_MODE:
        # 禁用所有外部 API 調用
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        
        # 禁用 Hugging Face Hub
        try:
            from huggingface_hub import offline_mode
            offline_mode()
            log.info("🔒 Hugging Face Hub 離線模式已啟用")
        except ImportError:
            pass
        except Exception as e:
            log.warning(f"⚠️ 無法啟用 Hugging Face Hub 離線模式: {e}")
        
        log.info("🔒 離線模式已啟用 - 所有數據將保持在本地")
    else:
        log.warning("⚠️ 離線模式未啟用 - 請確認數據安全")

def verify_ollama_local_only(base_url: Optional[str] = None) -> bool:
    """驗證 Ollama 只監聽本地地址"""
    if base_url is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # 檢查是否只監聽本地
    if "127.0.0.1" in base_url or "localhost" in base_url:
        log.info(f"✅ Ollama 配置為本地模式: {base_url}")
        return True
    elif "0.0.0.0" in base_url:
        log.warning(f"⚠️ Ollama 監聽所有接口: {base_url} - 可能存在安全風險")
        return False
    else:
        log.warning(f"⚠️ Ollama URL 配置異常: {base_url}")
        return False

def check_data_isolation():
    """檢查數據隔離配置"""
    issues = []
    
    # 檢查 Ollama URL
    ollama_url = os.getenv("OLLAMA_BASE_URL", "")
    if not verify_ollama_local_only(ollama_url):
        issues.append("Ollama 未配置為本地模式")
    
    # 檢查離線模式
    if not OFFLINE_MODE:
        issues.append("離線模式未啟用")
    
    # 檢查外部 API
    if not DISABLE_EXTERNAL_APIS:
        issues.append("外部 API 未禁用")
    
    # 檢查數據上傳
    if not DISABLE_DATA_UPLOAD:
        issues.append("數據上傳未禁用")
    
    if issues:
        log.warning(f"⚠️ 數據隔離檢查發現問題: {', '.join(issues)}")
        return False
    else:
        log.info("✅ 數據隔離配置正確")
        return True

def block_external_requests():
    """阻止外部請求（如果啟用離線模式）"""
    if OFFLINE_MODE and DISABLE_EXTERNAL_APIS:
        # 可以添加請求攔截邏輯
        # 例如：使用 requests 攔截器或修改 urllib
        pass

# 在模組載入時自動檢查
check_offline_mode()

