"""
防詐騙遊戲 API 路由 v2
使用完整的 Agent 服務層（AgentService）
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
import json
import sqlite3
import os
import uuid
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

router = APIRouter(prefix="/api/game/v2", tags=["Game V2"])

# 配置
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'anti_fraud_game.db')

# 數據模型
class GameStartRequest(BaseModel):
    persona_type: str

class GameStartResponse(BaseModel):
    session_id: str
    persona: Dict[str, Any]
    success: bool = True

class GameMessageRequest(BaseModel):
    model_config = {"extra": "allow"}
    
    session_id: str
    message: str
    target_ai: str = "AI-D"
    persona_type: str = "A"
    role: Optional[str] = None
    
    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id_to_str(cls, v):
        return str(v)

# 緩存 AgentService 實例
_agent_services = {}

def get_agent_service(persona_type: str):
    """獲取或創建 AgentService"""
    # 映射 RPG Maker 的 persona_type 到 backend 的 persona_type
    persona_mapping = {
        "A": "elderly",       # 陳老伯（長者）
        "B": "average",       # 林小姐（一般市民）
        "C": "overconfident", # 王先生（過度自信者）
        "D": "average"        # 自訂角色
    }
    backend_persona = persona_mapping.get(persona_type, "average")
    
    if backend_persona not in _agent_services:
        from services.agent_service import AgentService
        _agent_services[backend_persona] = AgentService(
            persona_type=backend_persona,
            enable_tracking=True  # 啟用性能追踪
        )
    
    return _agent_services[backend_persona]

# Persona 定義（保持與 v1 相同）
PERSONAS = {
    "A": {
        "name": "陳老伯（長者）",
        "age": 75,
        "background": "退休教師，對新科技不熟悉，容易相信權威",
        "vulnerability": "高",
        "characteristics": ["信任權威", "不熟悉科技", "善良單純"]
    },
    "B": {
        "name": "林小姐（一般市民）",
        "age": 35,
        "background": "上班族，有基本防騙意識",
        "vulnerability": "中",
        "characteristics": ["有基本警覺", "忙碌", "可能被精心設計的騙局迷惑"]
    },
    "C": {
        "name": "王先生（過度自信者）",
        "age": 45,
        "background": "企業主管，認為自己不會被騙",
        "vulnerability": "中低",
        "characteristics": ["過度自信", "可能洩露資訊", "輕視風險"]
    },
    "D": {
        "name": "自訂角色",
        "age": 0,
        "background": "根據用戶輸入自訂",
        "vulnerability": "未知",
        "characteristics": []
    }
}

# 數據庫初始化（與 v1 相同）
def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            persona_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

# API 路由

@router.post("/start", response_model=GameStartResponse)
async def start_game(request: GameStartRequest):
    """開始新遊戲"""
    persona_type = request.persona_type.upper()
    
    if persona_type not in PERSONAS:
        raise HTTPException(status_code=400, detail="無效的角色類型")
    
    session_id = str(uuid.uuid4())
    
    # 保存到數據庫
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, persona_type, status) VALUES (?, ?, ?)",
        (session_id, persona_type, 'active')
    )
    conn.commit()
    conn.close()
    
    return GameStartResponse(
        session_id=session_id,
        persona=PERSONAS[persona_type],
        success=True
    )

@router.post("/message")
async def send_message(raw_request: Request):
    """
    發送遊戲訊息 - 使用完整 Agent 系統
    
    與 v1 接口完全兼容，但內部使用 AgentService
    """
    # 解析請求
    body = await raw_request.body()
    data = json.loads(body)
    request = GameMessageRequest(**data)
    
    try:
        # 驗證 session
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 容錯處理：session_id=0 自動創建
        if request.session_id == "0":
            cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", ("0",))
            result = cursor.fetchone()
            if not result:
                cursor.execute(
                    "INSERT INTO sessions (id, persona_type, status) VALUES (?, ?, ?)",
                    ("0", request.persona_type or "A", 'active')
                )
                conn.commit()
                result = (request.persona_type or "A",)
        else:
            cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", (request.session_id,))
            result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"會話不存在: {request.session_id}")
        
        persona_type = request.persona_type or result[0]
        
        # 獲取歷史對話
        cursor.execute(
            "SELECT role, message FROM conversations WHERE session_id = ? ORDER BY timestamp",
            (request.session_id,)
        )
        history_rows = cursor.fetchall()
        history = [
            {"role": "user" if r[0] == "user" else "assistant", "content": r[1]}
            for r in history_rows
        ]
        
        # 🔥 使用 AgentService 生成響應
        agent_type_mapping = {
            "AI-A": "victim",     # 受騙者
            "AI-D": "scammer",    # 騙徒
            "AI-C": "expert",     # 防騙助手
        }
        agent_type = agent_type_mapping.get(request.target_ai)
        
        if agent_type:
            # 獲取 AgentService
            service = get_agent_service(persona_type)
            
            # 生成響應
            result = await service.generate_response(
                agent_type=agent_type,
                message=request.message,
                conversation_history=history,
                check_consistency=True,   # 啟用一致性檢查
                track_performance=True    # 啟用性能追踪
            )
            
            ai_reply = result["reply"]
            
            # 記錄 metrics（可選）
            if result.get("metrics"):
                from utils.logger import log
                log.info(f"📊 Agent {agent_type} metrics: {result['metrics']}")
        else:
            # 回退到簡單模式（評分 AI）
            ai_reply = "評分 AI 暫不支持，請使用 RecorderAgent"
        
        # 保存對話
        user_role = request.role if request.role else "user"
        cursor.execute(
            "INSERT INTO conversations (session_id, role, message) VALUES (?, ?, ?)",
            (request.session_id, user_role, request.message)
        )
        cursor.execute(
            "INSERT INTO conversations (session_id, role, message) VALUES (?, ?, ?)",
            (request.session_id, request.target_ai, ai_reply)
        )
        conn.commit()
        conn.close()
        
        # 返回響應（與 v1 兼容，但新增可選字段）
        response = {
            "reply": ai_reply,
            "success": True
        }
        
        # 新增：信任度數據（如果可用）
        if result.get("trust_in_scammer") is not None:
            response["trust_in_scammer"] = result["trust_in_scammer"]
        if result.get("trust_in_expert") is not None:
            response["trust_in_expert"] = result["trust_in_expert"]
        
        # 新增：性能指標（如果可用）
        if result.get("metrics"):
            response["metrics"] = result["metrics"]
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        from utils.logger import log
        log.error(f"❌ 消息處理失敗: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "reply": "系統錯誤，請稍後再試"}
        )

@router.post("/end")
async def end_game(session_id: str):
    """結束遊戲"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET status = ? WHERE id = ?", ('completed', session_id))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "遊戲已結束"}

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """獲取會話資訊"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="會話不存在")
    
    cursor.execute(
        "SELECT role, message, timestamp FROM conversations WHERE session_id = ? ORDER BY timestamp",
        (session_id,)
    )
    conversations = cursor.fetchall()
    
    conn.close()
    
    return {
        "session_id": session[0],
        "persona_type": session[1],
        "created_at": session[2],
        "status": session[3],
        "conversations": [
            {"role": c[0], "message": c[1], "timestamp": c[2]}
            for c in conversations
        ]
    }

class AnalyzeRequest(BaseModel):
    session_id: str

@router.post("/analyze")
async def analyze_session(request: AnalyzeRequest):
    """
    使用 RecorderAgent 分析會話並生成詳細評分
    
    這是遊戲結束時的最終分析端點
    """
    session_id = request.session_id
    try:
        # 獲取會話對話歷史
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            raise HTTPException(status_code=404, detail="會話不存在")
        
        persona_type = session[1]
        
        # 獲取完整對話歷史
        cursor.execute(
            "SELECT role, message FROM conversations WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        history_rows = cursor.fetchall()
        conn.close()
        
        # 構建對話歷史
        conversation_history = []
        for row in history_rows:
            conversation_history.append({
                "role": row[0],
                "content": row[1]
            })
        
        if not conversation_history:
            raise HTTPException(status_code=400, detail="沒有對話記錄可供分析")
        
        # 獲取 AgentService
        service = get_agent_service(persona_type)
        
        # 生成最終分析
        from utils.logger import log
        log.info(f"📊 開始分析會話 {session_id}")
        
        analysis = await service.generate_final_analysis(
            conversation_history=conversation_history,
            outcome_description=f"RPG 遊戲會話 {session_id} 結束"
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "analysis": analysis,
            "conversation_count": len(conversation_history)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        from utils.logger import log
        log.error(f"❌ 會話分析失敗: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "分析失敗，請稍後再試"
            }
        )

@router.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "ok",
        "version": "v2",
        "features": [
            "AgentService",
            "PerformanceTracking",
            "RoleConsistencyCheck",
            "TrustSystem",
            "RecorderAnalysis"  # 新增
        ]
    }

