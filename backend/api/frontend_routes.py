from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from typing import Dict, Any
from datetime import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

router = APIRouter()

@router.get("/")
async def serve_frontend():
    """提供RPG入口頁面作為主頁，禁用瀏覽器快取以確保 UI 立即更新。"""
    rpg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'RPG_platform', 'RPG_Project', 'index.html')
    if not os.path.exists(rpg_path):
        raise HTTPException(status_code=404, detail="RPG頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(rpg_path, headers=headers)

@router.get("/app")
async def serve_frontend_alias():
    """提供訓練控制頁面（別名路徑 /app），同樣禁用快取。"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'index_old.html')
    if not os.path.exists(frontend_path):
        raise HTTPException(status_code=404, detail="訓練頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(frontend_path, headers=headers)

@router.get("/simulation")
async def serve_simulation_page():
    """提供訓練控制頁面"""
    simulation_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'index_old.html')
    if not os.path.exists(simulation_path):
        raise HTTPException(status_code=404, detail="訓練頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(simulation_path, headers=headers)

@router.get("/personal_chat.html")
async def serve_personal_chat_page():
    """提供個人對話模式頁面"""
    chat_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'personal_chat.html')
    if not os.path.exists(chat_path):
        raise HTTPException(status_code=404, detail="對話頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(chat_path, headers=headers)

@router.get("/test")
async def serve_test_page():
    """提供WebSocket测试页面"""
    test_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'test.html')
    if not os.path.exists(test_path):
        raise HTTPException(status_code=404, detail="测试页面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(test_path, headers=headers)

@router.get("/rpg")
async def serve_rpg_page():
    """提供RPG游戏入口页面（与主页相同）"""
    rpg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'RPG_platform', 'RPG_Project', 'index.html')
    if not os.path.exists(rpg_path):
        raise HTTPException(status_code=404, detail="RPG页面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(rpg_path, headers=headers)

@router.get("/modes")
async def serve_modes_page():
    """提供原來的模式選擇頁面（如需要）"""
    modes_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'index.html')
    if not os.path.exists(modes_path):
        raise HTTPException(status_code=404, detail="模式選擇頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(modes_path, headers=headers)

@router.post("/api/training/single")
async def start_single_real_dialogue(request_data: Dict[str, Any] | None = None):
    """只使用真實 AI 對話，不回退模擬"""
    try:
        scam_tactic = (request_data or {}).get("scam_tactic", "WhatsApp 對話詐騙")
        victim_persona = (request_data or {}).get("victim_persona", "average")
        mode = (request_data or {}).get("mode", "fast")  # fast | demo

        from scripts.real_dialogue_runner import RealDialogueRunner
        runner = RealDialogueRunner()
        result = await runner.run_dialogue_simulation(scam_tactic, victim_persona, mode=mode)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result.get("error", "real dialogue failed"))

        result.update({
            "round_id": f"round_{int(datetime.now().timestamp())}",
            "success": result.get("outcome") == "SUCCESS",
            "mode": "real_ai"
        })

        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"對話失敗: {str(e)}")

@router.get("/api/options")
async def get_training_options():
    """提供選項（保留供前端選擇參數）"""
    return {
        "status": "success",
        "data": {
            "scam_tactics": [
                "WhatsApp 對話詐騙",
                "假短訊釣魚",
                "虛假投資應用程式",
                "假網站冒充銀行",
                "刷單騙案",
                "中獎詐騙",
                "假冒官員詐騙",
                "假網站冒充政府",
                "虛假購物平台",
                "愛情詐騙"
            ],
            "victim_personas": ["elderly", "average", "overconfident", "student"],
            "persona_descriptions": {
                "elderly": "長者（高風險）- 容易相信權威，對新科技不熟悉",
                "average": "一般市民（中等風險）- 有基本防騙意識，但可能被精心設計的騙局迷惑",
                "overconfident": "過度自信者（低風險但可能洩露資訊）- 認為自己不會被騙",
                "student": "年輕學生（中等風險）- 熟悉科技但缺乏社會經驗"
            }
        }
    }
