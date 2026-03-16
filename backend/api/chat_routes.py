"""
通用 AI 聊天 API 路由
用於 RPG Maker 插件和其他客戶端
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import requests
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

router = APIRouter(tags=["Chat"])

# 配置
OLLAMA_API_URL = "http://localhost:11434/api/chat"

# 數據模型
class ChatRequest(BaseModel):
    role: str
    message: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    reply: str
    success: bool = True

async def call_ollama(role: str, message: str, history: List[Dict] = None) -> str:
    """調用 Ollama API"""
    if history is None:
        history = []
    
    system_prompt = f"{role}\n請用繁體中文回應。"
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    # 使用環境變量或默認模型
    model_name = os.getenv("AGENT_MODEL", "gemma3:4b")
    
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        return result.get("message", {}).get("content", "抱歉，我無法回應。")
    except Exception as e:
        return f"AI 服務錯誤: {str(e)}"

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    通用 AI 聊天端點
    用於 RPG Maker 插件和其他需要簡單對話的客戶端
    """
    reply = await call_ollama(request.role, request.message, request.history)
    return ChatResponse(reply=reply, success=True)

@router.post("/api/chat/send", response_model=ChatResponse)
async def chat_send(request: ChatRequest):
    """
    替代聊天端點（向後兼容）
    """
    reply = await call_ollama(request.role, request.message, request.history)
    return ChatResponse(reply=reply, success=True)

@router.get("/chat/health")
async def chat_health():
    """聊天服務健康檢查"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return {"status": "ok", "ollama": "running"}
        else:
            return {"status": "degraded", "ollama": "error"}
    except:
        return {"status": "error", "ollama": "not_running"}


