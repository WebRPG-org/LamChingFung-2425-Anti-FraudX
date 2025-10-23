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
    """提供前端頁面，禁用瀏覽器快取以確保 UI 立即更新。"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'index.html')
    if not os.path.exists(frontend_path):
        raise HTTPException(status_code=404, detail="前端頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(frontend_path, headers=headers)

@router.get("/app")
async def serve_frontend_alias():
    """提供前端頁面（別名路徑 /app），同樣禁用快取。"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'index.html')
    if not os.path.exists(frontend_path):
        raise HTTPException(status_code=404, detail="前端頁面未找到")
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(frontend_path, headers=headers)

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
            "victim_personas": ["elderly", "average", "overconfident"],
            "persona_descriptions": {
                "elderly": "長者（高風險）- 容易相信權威，對新科技不熟悉",
                "average": "一般市民（中等風險）- 有基本防騙意識，但可能被精心設計的騙局迷惑",
                "overconfident": "過度自信者（低風險但可能洩露資訊）- 認為自己不會被騙"
            }
        }
    }
