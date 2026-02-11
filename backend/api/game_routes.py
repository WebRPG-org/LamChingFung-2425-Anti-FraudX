"""
防詐騙遊戲 API 路由 - 完全基於 simulation_routes.py
作為 RPG Maker 和 simulation_routes.py 之間的轻量级代理层
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import httpx

router = APIRouter(prefix="/api/game", tags=["Game"])

# 配置
SIMULATION_API_BASE = "http://localhost:8000"

# ==================== 數據模型 ====================

class SimulationStartRequest(BaseModel):
    """啟動模擬請求 - 支持 RPG Maker 格式"""
    persona_type: Optional[str] = "average"
    scam_tactic: Optional[str] = "冒充銀行客服詐騙"
    mode: Optional[str] = "fast"
    auto_train: Optional[bool] = False

class SimulationStartResponse(BaseModel):
    """啟動模擬響應"""
    success: bool
    simulation_id: str
    websocket_url: str
    victim_persona: str
    scam_tactic: str
    mode: str

# ==================== Persona 映射 ====================

PERSONA_MAPPING = {
    "A": "elderly",
    "B": "average",
    "C": "overconfident",
    "D": "average",
    "elderly": "elderly",
    "average": "average",
    "overconfident": "overconfident"
}

PERSONA_DISPLAY_NAMES = {
    "elderly": "長者（高風險）",
    "average": "一般市民",
    "overconfident": "過度自信者"
}

# ==================== 詐騙手法列表 ====================

DEFAULT_SCAM_TACTICS = [
    "冒充銀行客服詐騙",
    "冒充政府機關詐騙",
    "投資理財詐騙",
    "網購退款詐騙",
    "假冒親友詐騙",
    "求職詐騙",
    "中獎詐騙",
    "愛情交友詐騙"
]

# ==================== API 端點 ====================

@router.post("/simulation/start", response_model=SimulationStartResponse)
async def start_simulation(request: SimulationStartRequest):
    """啟動模擬 - 完全基於 simulation_routes.py"""
    try:
        persona_type = request.persona_type.upper() if request.persona_type else "AVERAGE"
        victim_persona = PERSONA_MAPPING.get(persona_type, "average")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SIMULATION_API_BASE}/simulation/start",
                json={
                    "victim_persona": victim_persona,
                    "scam_tactic": request.scam_tactic,
                    "mode": request.mode,
                    "auto_train": request.auto_train
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return SimulationStartResponse(
                    success=True,
                    simulation_id=data["simulation_id"],
                    websocket_url=data["websocket_url"],
                    victim_persona=victim_persona,
                    scam_tactic=request.scam_tactic,
                    mode=request.mode
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"模擬啟動失敗: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="連接模擬服務超時"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"無法連接到模擬服務: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"啟動模擬時發生錯誤: {str(e)}"
        )

@router.get("/simulation/tactics")
async def get_scam_tactics():
    """獲取可用的詐騙手法列表"""
    try:
        from scripts.real_dialogue_runner import SCAM_TACTICS
        return {
            "success": True,
            "tactics": SCAM_TACTICS
        }
    except Exception:
        return {
            "success": True,
            "tactics": DEFAULT_SCAM_TACTICS
        }

@router.get("/simulation/personas")
async def get_victim_personas():
    """獲取可用的受害者類型列表"""
    try:
        from scripts.real_dialogue_runner import VICTIM_PERSONAS
        personas = VICTIM_PERSONAS
    except Exception:
        personas = ["elderly", "average", "overconfident"]
    
    return {
        "success": True,
        "personas": personas,
        "display_names": PERSONA_DISPLAY_NAMES,
        "rpg_mapping": {
            "A": "elderly",
            "B": "average",
            "C": "overconfident",
            "D": "average"
        }
    }

@router.get("/simulation/events/{simulation_id}")
async def get_simulation_events(simulation_id: str, since_seq: Optional[int] = None):
    """獲取模擬事件（HTTP 輪詢方式）"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {}
            if since_seq is not None:
                params["since_seq"] = since_seq
            
            response = await client.get(
                f"{SIMULATION_API_BASE}/simulation/events/{simulation_id}",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"獲取事件失敗: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="獲取事件超時"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"無法連接到模擬服務: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"獲取事件時發生錯誤: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """健康檢查 - 檢查各個服務的狀態"""
    health_status = {
        "status": "ok",
        "game_api": "ok",
        "simulation_api": "unknown",
        "ollama": "unknown"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SIMULATION_API_BASE}/docs")
            health_status["simulation_api"] = "ok" if response.status_code == 200 else "error"
    except Exception:
        health_status["simulation_api"] = "not_running"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            health_status["ollama"] = "running" if response.status_code == 200 else "error"
    except Exception:
        health_status["ollama"] = "not_running"
    
    if health_status["simulation_api"] != "ok" or health_status["ollama"] != "running":
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/info")
async def get_api_info():
    """獲取 API 信息"""
    return {
        "name": "Anti-Fraud Game API",
        "version": "2.0.0",
        "description": "完全基於 simulation_routes.py 的 RPG Maker 遊戲 API",
        "features": [
            "完整的三方對話模擬（騙徒、受害者、專家）",
            "實時信任度追蹤",
            "性能評分系統",
            "自動訓練循環",
            "WebSocket 即時通信",
            "訓練數據自動保存",
            "Fine-tuning 數據生成",
            "RecorderAgent 專業分析"
        ],
        "endpoints": {
            "start_simulation": "POST /api/game/simulation/start",
            "get_tactics": "GET /api/game/simulation/tactics",
            "get_personas": "GET /api/game/simulation/personas",
            "get_events": "GET /api/game/simulation/events/{simulation_id}",
            "health_check": "GET /api/game/health",
            "info": "GET /api/game/info"
        },
        "websocket": {
            "url": "ws://localhost:8000/ws/simulation/{simulation_id}",
            "description": "連接到此 WebSocket 接收即時模擬事件"
        },
        "migration": {
            "from": "RotatingScamSystem.js (simple AI chat)",
            "to": "simulation_routes.py based (complete simulation)",
            "compatible_plugin": "SimulationTraining_Compatible.js"
        }
    }

# ==================== 向後兼容（已棄用） ====================

@router.post("/start")
async def deprecated_start_game(request: Request):
    """[已棄用] 舊的遊戲啟動接口"""
    return JSONResponse(
        status_code=410,
        content={
            "error": "此接口已棄用",
            "message": "請使用新的 /api/game/simulation/start 接口",
            "migration_guide": "參考 RPG_Maker_兼容版本_使用指南.md",
            "deprecated_since": "2025-11-11"
        }
    )

@router.post("/message")
async def deprecated_send_message(request: Request):
    """[已棄用] 舊的訊息發送接口"""
    return JSONResponse(
        status_code=410,
        content={
            "error": "此接口已棄用",
            "message": "新系統使用 WebSocket 即時通信",
            "websocket_url": "ws://localhost:8000/ws/simulation/{simulation_id}",
            "migration_guide": "參考 RPG_Maker_兼容版本_使用指南.md",
            "deprecated_since": "2025-11-11"
        }
    )

@router.post("/end")
async def deprecated_end_game(request: Request):
    """[已棄用] 舊的遊戲結束接口"""
    return JSONResponse(
        status_code=410,
        content={
            "error": "此接口已棄用",
            "message": "新系統自動管理模擬生命週期",
            "migration_guide": "參考 RPG_Maker_兼容版本_使用指南.md",
            "deprecated_since": "2025-11-11"
        }
    )

@router.get("/session/{session_id}")
async def deprecated_get_session(session_id: str):
    """[已棄用] 舊的會話查詢接口"""
    return JSONResponse(
        status_code=410,
        content={
            "error": "此接口已棄用",
            "message": "請使用 /api/game/simulation/events/{simulation_id}",
            "migration_guide": "參考 RPG_Maker_兼容版本_使用指南.md",
            "deprecated_since": "2025-11-11"
        }
    )
