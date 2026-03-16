"""
防詐騙遊戲 API 路由 v2
使用完整的 Agent 服務層（AgentService）
支持騙案類型系統
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
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 導入日誌
try:
    from utils.logger import log
except Exception as e:
    log = logging.getLogger(__name__)
    log.warning(f"Failed to import custom logger: {e}")

router = APIRouter(prefix="/api/rpgv2/game", tags=["Game V2"])

# 配置
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'anti_fraud_game.db')

# 騙案類型定義（與前端 ScamTypes.ts 保持一致）
SCAM_TYPES = {
    "investment": {"name_zh": "虛假投資詐騙", "icon": "💰", "danger_level": 5, "tactic": "investment"},
    "phishing": {"name_zh": "釣魚短訊詐騙", "icon": "📱", "danger_level": 4, "tactic": "phishing"},
    "romance": {"name_zh": "愛情詐騙", "icon": "💕", "danger_level": 5, "tactic": "romance"},
    "impersonation": {"name_zh": "假冒官員詐騙", "icon": "👮", "danger_level": 5, "tactic": "impersonation"},
    "shopping": {"name_zh": "虛假購物詐騙", "icon": "🛒", "danger_level": 3, "tactic": "shopping"},
    "job": {"name_zh": "求職詐騙", "icon": "💼", "danger_level": 3, "tactic": "job"},
    "prize": {"name_zh": "中獎詐騙", "icon": "🎁", "danger_level": 3, "tactic": "prize"},
    "whatsapp": {"name_zh": "WhatsApp 詐騙", "icon": "💬", "danger_level": 4, "tactic": "whatsapp"},
    "banking": {"name_zh": "假冒銀行詐騙", "icon": "🏦", "danger_level": 5, "tactic": "banking"},
    "crypto": {"name_zh": "加密貨幣詐騙", "icon": "₿", "danger_level": 5, "tactic": "crypto"},
    "rental": {"name_zh": "租屋詐騙", "icon": "🏠", "danger_level": 3, "tactic": "rental"},
    "tech_support": {"name_zh": "技術支援詐騙", "icon": "💻", "danger_level": 4, "tactic": "tech_support"},
    "charity": {"name_zh": "虛假慈善詐騙", "icon": "❤️", "danger_level": 2, "tactic": "charity"}
}

# 數據模型
class GameStartRequest(BaseModel):
    persona_type: Optional[str] = None
    scam_type: Optional[str] = None
    mode: Optional[str] = None
    victim_persona: Optional[str] = None
    difficulty: Optional[str] = None

class GameStartResponse(BaseModel):
    session_id: str
    persona: Optional[Dict[str, Any]] = None
    scam_type: Optional[Dict[str, Any]] = None
    mode: Optional[str] = None
    opening_messages: Optional[List[Dict[str, str]]] = None
    game_state: Optional[Dict[str, Any]] = None
    success: bool = True

class GameMessageRequest(BaseModel):
    model_config = {"extra": "allow"}
    
    session_id: str
    message: str
    target_ai: str = "AI-D"
    persona_type: str = "A"
    role: Optional[str] = None
    scam_type: Optional[str] = None  # 新增：騙案類型
    
    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id_to_str(cls, v):
        return str(v)

# 緩存 AgentService 實例
_agent_services = {}

def get_agent_service(persona_type: str, scam_tactic: Optional[str] = None):
    """獲取或創建 AgentService，支持指定騙案類型"""
    # 映射 RPG Maker 的 persona_type 到 backend 的 persona_type
    persona_mapping = {
        "A": "elderly",       # 陳老伯（長者）
        "B": "average",       # 林小姐（一般市民）
        "C": "overconfident", # 王先生（過度自信者）
        "D": "average"        # 自訂角色
    }
    backend_persona = persona_mapping.get(persona_type, "average")
    
    # 如果指定了騙案類型，創建專門的 AgentService
    cache_key = f"{backend_persona}_{scam_tactic}" if scam_tactic else backend_persona
    
    if cache_key not in _agent_services:
        from services.agent_service import AgentService
        
        # 創建 AgentService，如果有騙案類型則傳遞給 ScammerAgent
        service_kwargs = {
            "persona_type": backend_persona,
            "enable_tracking": True  # 啟用性能追踪
        }
        
        # 注意：AgentService 目前不直接支持 scam_tactic 參數
        # 需要在 ScammerAgent 層面處理，這裡先創建基礎服務
        _agent_services[cache_key] = AgentService(**service_kwargs)
    
    return _agent_services[cache_key]

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
    """開始新遊戲 - 騙徒直接開始騙局"""
    # 映射前端的 victim_persona 到內部 persona_type
    persona_mapping = {
        "elderly": "A",
        "average": "B",
        "overconfident": "C"
    }
    
    # 優先使用 persona_type，其次使用 victim_persona
    persona_type = request.persona_type
    if not persona_type and request.victim_persona:
        persona_type = persona_mapping.get(request.victim_persona, "B")
    if not persona_type:
        persona_type = "B"  # 默認
    
    persona_type = persona_type.upper()
    
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
    
    # 🔥 **新流程：騙徒直接開始騙局**
    try:
        from services.agent_service import AgentService
        
        # 獲取 AgentService
        service = get_agent_service(persona_type)
        
        # 騙徒開始騙局（第一句話）
        scammer_opening = await service.generate_response(
            agent_type="scammer",
            message="",  # 空消息，讓騙徒自己開始
            session_id=session_id,
            check_consistency=False,
            track_performance=False
        )
        
        opening_message = scammer_opening["reply"]
        
        logging.info(f"🎭 騙徒開始騙局: {opening_message[:50]}...")
        
        return GameStartResponse(
            session_id=session_id,
            persona=PERSONAS[persona_type],
            mode=request.mode or "scammer",
            opening_messages=[
                {
                    "role": "scammer",
                    "content": opening_message
                }
            ],
            game_state={
                "round_count": 1,
                "player_score": 0,
                "ai_score": 0,
                "trust_in_scammer": 50,
                "trust_in_expert": 50,
                "alertness": 50
            },
            success=True
        )
    except Exception as e:
        from utils.logger import log
        log.error(f"❌ 遊戲開始失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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
        # 🔥 **先檢查玩家消息中的關鍵詞**
        message_lower = request.message.lower()
        INSTANT_SCAMMER_WIN = ["銀行密碼", "銀行戶口", "密碼", "驗證碼", "轉賬", "提供資料"]
        INSTANT_EXPERT_WIN = ["報警", "警察", "18222", "銀行號碼", "銀行帳號"]
        
        logging.info(f"🔍 玩家消息檢查 - message: '{request.message}', message_lower: '{message_lower}'")
        
        for keyword in INSTANT_SCAMMER_WIN:
            if keyword in message_lower:
                logging.warning(f"✅ 玩家說出關鍵詞 '{keyword}'，騙徒立即贏！")
                return {
                    "reply": f"遊戲結束！你說出了 '{keyword}'，騙徒贏了！",
                    "success": True,
                    "game_status": {
                        "game_over": True,
                        "winner": "scammer",
                        "reason": f"玩家說出關鍵詞：{keyword}"
                    },
                    "trust_in_scammer": 100,
                    "trust_in_expert": 0
                }
        
        for keyword in INSTANT_EXPERT_WIN:
            if keyword in message_lower:
                logging.warning(f"✅ 玩家說出關鍵詞 '{keyword}'，專家立即贏！")
                return {
                    "reply": f"遊戲結束！你說出了 '{keyword}'，專家贏了！",
                    "success": True,
                    "game_status": {
                        "game_over": True,
                        "winner": "expert",
                        "reason": f"玩家說出關鍵詞：{keyword}"
                    },
                    "trust_in_scammer": 0,
                    "trust_in_expert": 100
                }
        
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
            
            # 生成響應（使用 session_id，不需要傳 conversation_history）
            result = await service.generate_response(
                agent_type=agent_type,
                message=request.message,
                session_id=request.session_id,
                check_consistency=True,   # 啟用一致性檢查
                track_performance=True    # 啟用性能追踪
            )
            
            ai_reply = result["reply"]
            
            # 記錄 metrics（可選）
            if result.get("metrics"):
                logging.info(f"📊 Agent {agent_type} metrics: {result['metrics']}")
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
        
        # 新增：遊戲狀態（用於結算畫面）
        if result.get("game_status"):
            response["game_status"] = result["game_status"]
            response["game_over"] = result["game_status"] is not None
        
        # 新增：性能指標（如果可用）
        if result.get("metrics"):
            response["metrics"] = result["metrics"]
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ 消息處理失敗: {e}", exc_info=True)
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
        logging.info(f"📊 開始分析會話 {session_id}")
        
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
        logging.error(f"❌ 會話分析失敗: {e}", exc_info=True)
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
            "RecorderAnalysis",
            "ScamTypeSupport"  # 新增
        ]
    }

@router.get("/scam-types")
async def get_scam_types():
    """
    獲取所有騙案類型列表
    
    返回前端可用的所有騙案類型資訊
    """
    scam_types_list = []
    for scam_id, scam_info in SCAM_TYPES.items():
        scam_types_list.append({
            "id": scam_id,
            "name_zh": scam_info["name_zh"],
            "icon": scam_info["icon"],
            "danger_level": scam_info["danger_level"],
            "tactic": scam_info["tactic"]
        })
    
    return {
        "success": True,
        "scam_types": scam_types_list,
        "total": len(scam_types_list)
    }

@router.get("/scam-types/{scam_id}")
async def get_scam_type_detail(scam_id: str):
    """
    獲取特定騙案類型的詳細資訊
    """
    if scam_id not in SCAM_TYPES:
        raise HTTPException(status_code=404, detail=f"騙案類型不存在: {scam_id}")
    
    scam_info = SCAM_TYPES[scam_id]
    return {
        "success": True,
        "scam_type": {
            "id": scam_id,
            "name_zh": scam_info["name_zh"],
            "icon": scam_info["icon"],
            "danger_level": scam_info["danger_level"],
            "tactic": scam_info["tactic"]
        }
    }

# 新增：遊戲模式端點（用於 RPGv2 前端）
@router.get("/modes")
async def get_game_modes():
    """
    獲取可用的遊戲模式
    """
    modes = [
        {
            "id": "scammer",
            "name": "騙徒模式",
            "description": "扮演騙徒，嘗試詐騙受害者",
            "icon": "🎭",
            "difficulty": "medium"
        },
        {
            "id": "expert",
            "name": "專家模式",
            "description": "扮演防詐專家，保護受害者",
            "icon": "🛡️",
            "difficulty": "medium"
        },
        {
            "id": "auto",
            "name": "自動模式",
            "description": "觀看AI對話，學習防詐技巧",
            "icon": "🤖",
            "difficulty": "easy"
        }
    ]
    
    return {
        "success": True,
        "modes": modes
    }

@router.post("/action")
async def game_action(raw_request: Request):
    """
    處理遊戲動作 - 同時生成騙徒和專家的回應
    """
    body = await raw_request.body()
    data = json.loads(body)
    
    session_id = data.get("session_id")
    message = data.get("message")
    
    if not session_id or not message:
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    try:
        # 🔥 **先檢查玩家消息中的關鍵詞**
        message_lower = message.lower()
        INSTANT_SCAMMER_WIN = ["銀行密碼", "銀行戶口", "密碼", "驗證碼", "轉賬", "提供資料"]
        INSTANT_EXPERT_WIN = ["報警", "警察", "18222", "銀行號碼", "銀行帳號"]
        
        logging.info(f"🔍 玩家消息檢查 - message: '{message}', message_lower: '{message_lower}'")
        
        for keyword in INSTANT_SCAMMER_WIN:
            if keyword in message_lower:
                logging.warning(f"✅ 玩家說出關鍵詞 '{keyword}'，騙徒立即贏！")
                return {
                    "success": True,
                    "ai_responses": [
                        {"role": "scammer", "content": f"遊戲結束！你說出了 '{keyword}'，騙徒贏了！"},
                        {"role": "expert", "content": f"遊戲結束！你說出了 '{keyword}'，騙徒贏了！"}
                    ],
                    "game_state": {
                        "round_count": 0,
                        "player_score": 0,
                        "ai_score": 100,
                        "trust_in_scammer": 100,
                        "trust_in_expert": 0,
                        "alertness": 0
                    },
                    "game_status": {
                        "game_over": True,
                        "winner": "scammer",
                        "reason": f"玩家說出關鍵詞：{keyword}，騙徒贏了"
                    }
                }
        
        for keyword in INSTANT_EXPERT_WIN:
            if keyword in message_lower:
                logging.warning(f"✅ 玩家說出關鍵詞 '{keyword}'，專家立即贏！")
                return {
                    "success": True,
                    "ai_responses": [
                        {"role": "scammer", "content": f"遊戲結束！你說出了 '{keyword}'，專家贏了！"},
                        {"role": "expert", "content": f"遊戲結束！你說出了 '{keyword}'，專家贏了！"}
                    ],
                    "game_state": {
                        "round_count": 0,
                        "player_score": 0,
                        "ai_score": 100,
                        "trust_in_scammer": 0,
                        "trust_in_expert": 100,
                        "alertness": 100
                    },
                    "game_status": {
                        "game_over": True,
                        "winner": "expert",
                        "reason": f"玩家說出關鍵詞：{keyword}，專家贏了"
                    }
                }
        
        # 獲取會話信息
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="會話不存在")
        
        persona_type = result[0]
        
        # 使用 AgentService 生成響應
        service = get_agent_service(persona_type)
        
        # 🔥 **同時生成騙徒和專家的回應**
        scammer_result = await service.generate_response(
            agent_type="scammer",
            message=message,
            session_id=session_id,
            check_consistency=True,
            track_performance=True
        )
        
        expert_result = await service.generate_response(
            agent_type="expert",
            message=message,
            session_id=session_id,
            check_consistency=True,
            track_performance=True
        )
        
        scammer_reply = scammer_result["reply"]
        expert_reply = expert_result["reply"]
        
        # 保存對話
        cursor.execute(
            "INSERT INTO conversations (session_id, role, message) VALUES (?, ?, ?)",
            (session_id, "player", message)
        )
        cursor.execute(
            "INSERT INTO conversations (session_id, role, message) VALUES (?, ?, ?)",
            (session_id, "scammer", scammer_reply)
        )
        cursor.execute(
            "INSERT INTO conversations (session_id, role, message) VALUES (?, ?, ?)",
            (session_id, "expert", expert_reply)
        )
        conn.commit()
        
        # 計算遊戲狀態
        round_count = len(list(cursor.execute(
            "SELECT * FROM conversations WHERE session_id = ?", (session_id,)
        ))) // 3
        
        trust_in_scammer = scammer_result.get("trust_in_scammer", 50)
        trust_in_expert = expert_result.get("trust_in_expert", 50)
        
        # 檢查遊戲是否結束
        game_over = False
        winner = None
        reason = None
        
        if scammer_result.get("game_status") == "scammer_win":
            game_over = True
            winner = "scammer"
            reason = "騙徒信任度達到100"
        elif expert_result.get("game_status") == "expert_win":
            game_over = True
            winner = "expert"
            reason = "專家信任度達到100"
        
        conn.close()
        
        return {
            "success": True,
            "ai_responses": [
                {"role": "scammer", "content": scammer_reply},
                {"role": "expert", "content": expert_reply}
            ],
            "game_state": {
                "round_count": round_count,
                "player_score": 0,
                "ai_score": 0,
                "trust_in_scammer": trust_in_scammer,
                "trust_in_expert": trust_in_expert,
                "alertness": 100 - trust_in_scammer
            },
            "score_update": {
                "player": 0,
                "ai": 0
            },
            "game_status": {
                "game_over": game_over,
                "winner": winner,
                "reason": reason
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ 遊戲動作處理失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-play")
async def auto_play(raw_request: Request):
    """
    自動播放模式
    """
    body = await raw_request.body()
    data = json.loads(body)
    
    session_id = data.get("session_id")
    rounds = data.get("rounds", 3)
    
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="會話不存在")
        
        persona_type = result[0]
        service = get_agent_service(persona_type)
        
        messages = []
        
        # 模擬多輪對話
        for i in range(rounds):
            # 騙徒發言
            scammer_result = await service.generate_response(
                agent_type="scammer",
                message="",
                session_id=session_id,
                check_consistency=False,
                track_performance=False
            )
            
            messages.append({
                "role": "scammer",
                "content": scammer_result["reply"]
            })
            
            # 受害者回應
            victim_result = await service.generate_response(
                agent_type="victim",
                message=scammer_result["reply"],
                session_id=session_id,
                check_consistency=False,
                track_performance=False
            )
            
            messages.append({
                "role": "victim",
                "content": victim_result["reply"]
            })
        
        conn.close()
        
        return {
            "success": True,
            "messages": messages,
            "game_state": {
                "round_count": rounds,
                "player_score": 0,
                "ai_score": 0,
                "trust_in_scammer": 50,
                "trust_in_expert": 50,
                "alertness": 50
            },
            "game_status": {
                "game_over": False
            }
        }
    
    except Exception as e:
        logging.error(f"❌ 自動播放失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state/{session_id}")
async def get_game_state(session_id: str):
    """
    獲取遊戲狀態
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            raise HTTPException(status_code=404, detail="會話不存在")
        
        cursor.execute(
            "SELECT COUNT(*) FROM conversations WHERE session_id = ?",
            (session_id,)
        )
        message_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "player_score": 0,
            "ai_score": 0,
            "round_count": message_count // 2,
            "trust_data": {
                "trust_in_scammer": 50,
                "trust_in_expert": 50,
                "alertness": 50
            }
        }
    
    except Exception as e:
        logging.error(f"❌ 獲取遊戲狀態失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    刪除會話
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "會話已刪除"
        }
    
    except Exception as e:
        logging.error(f"❌ 刪除會話失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
