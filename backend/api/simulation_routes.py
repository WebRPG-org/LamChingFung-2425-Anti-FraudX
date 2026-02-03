import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket
from pydantic import BaseModel

from utils.logger import log
from api.websocket_manager import manager
from services.simulation_runner import run_simulation_async

router = APIRouter()

class SimulationRequest(BaseModel):
    victim_persona: Optional[str] = "average"
    scam_tactic: Optional[str] = "WhatsApp 對話詐騙"
    mode: Optional[str] = "fast"  # fast | demo
    auto_train: Optional[bool] = True  # 是否启用自动训练（默认启用）

class SimulationResponse(BaseModel):
    simulation_id: str
    websocket_url: str

@router.post("/simulation/start", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest):
    """啟動一次新的模擬"""
    simulation_id = str(uuid.uuid4())
    websocket_url = f"/ws/simulation/{simulation_id}"
    
    # 保存自动训练设置
    auto_train_enabled = request.auto_train if request.auto_train is not None else True
    
    log.info(f"Starting simulation {simulation_id} with victim_persona: {request.victim_persona}, auto_train: {auto_train_enabled}")
    
    # Launch simulation in background
    import asyncio
    asyncio.create_task(run_simulation_async(
        simulation_id,
        victim_persona=request.victim_persona,
        scam_tactic=request.scam_tactic,
        mode=request.mode or "fast",
        auto_train=auto_train_enabled,
        is_auto_round=False  # 用戶手動開始，清除停止標誌
    ))
    
    return SimulationResponse(
        simulation_id=simulation_id,
        websocket_url=websocket_url
    )

@router.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    """處理模擬的 WebSocket 連接"""
    await manager.connect(websocket, simulation_id)

@router.post("/simulation/stop/{simulation_id}")
async def stop_simulation(simulation_id: str):
    """停止所有正在運行的模擬"""
    log.info(f"🛑 Stopping all simulations (triggered by {simulation_id})")
    
    # 停止所有模擬
    manager.stop_all_simulations()
    
    # 發送停止事件給所有客戶端
    for sim_id in list(manager.active_connections.keys()):
        try:
            await manager.send_event(sim_id, "simulation_stopped", {
                "simulation_id": sim_id,
                "reason": "用戶手動停止所有模擬"
            })
        except Exception:
            pass
    
    # 斷開所有 WebSocket 連接
    for sim_id in list(manager.active_connections.keys()):
        manager.disconnect(sim_id)
    
    return {
        "success": True,
        "simulation_id": simulation_id,
        "message": "所有模擬已停止"
    }

@router.get("/simulation/events/{simulation_id}")
async def get_simulation_events(simulation_id: str, since_seq: Optional[int] = None):
    """獲取模擬事件歷史（用於輪詢或重連恢復）"""
    return manager.get_events(simulation_id, since_seq)
