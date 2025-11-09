"""
防詐騙遊戲 API 路由
整合到 AI-Agent 系統中
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
import requests
import json
import sqlite3
import os
from datetime import datetime
import uuid
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

router = APIRouter(prefix="/api/game", tags=["Game"])

# 配置
OLLAMA_API_URL = "http://localhost:11434/api/chat"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'anti_fraud_game.db')

# 數據模型
class ChatRequest(BaseModel):
    role: str
    message: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    reply: str
    success: bool = True

class GameStartRequest(BaseModel):
    persona_type: str

class GameStartResponse(BaseModel):
    session_id: str
    persona: Dict[str, Any]
    success: bool = True

from pydantic import field_validator

class GameMessageRequest(BaseModel):
    model_config = {"extra": "allow"}  # Pydantic v2 語法：允許接收額外的欄位
    
    session_id: str
    message: str
    target_ai: str = "AI-D"
    persona_type: str = "A"
    role: Optional[str] = None  # 支援前端傳入的 role 參數
    
    @field_validator('session_id', mode='before')
    @classmethod
    def convert_session_id_to_str(cls, v):
        """自動將 session_id 轉換為字串"""
        return str(v)

# 數據庫初始化
def init_database():
    """初始化數據庫"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 創建會話表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            persona_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # 創建對話表
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

# 初始化數據庫
init_database()

# Persona 定義
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

def get_ai_system_prompt(role: str, persona_type: str = "A") -> str:
    """根據角色獲取系統提示"""
    persona = PERSONAS.get(persona_type, PERSONAS["A"])
    
    prompts = {
        "AI-A": f"""你是 {persona['name']}，一個{persona['background']}。
你的特點：{', '.join(persona['characteristics'])}。
請以這個角色的身份回應，保持角色設定的一致性。
請用繁體中文回應。""",
        
        "AI-B": """你是防詐騙評分AI，負責分析對話中被騙人的防詐騙表現。
你需要：
1. 分析被騙人的警覺性
2. 評估其防騙技巧
3. 給出具體的改進建議
4. 提供0-100的評分
請用繁體中文回應，格式清晰。""",
        
        "AI-C": """你是防騙助手，負責在對話中提供即時的防詐騙建議。
當你看到詐騙跡象時：
1. 立即指出可疑之處
2. 提供應對建議
3. 教育用戶識別類似詐騙
保持友善、專業，用繁體中文回應。""",
        
        "AI-D": """你是詐騙者，試圖說服受害者。
你會使用常見的詐騙手法：
1. 建立信任
2. 製造緊迫感
3. 要求個人資訊或金錢
但要保持真實感，不要太過明顯。
用繁體中文對話。"""
    }
    
    return prompts.get(role, "你是一個AI助手，請用繁體中文回應。")

async def call_ollama(role: str, message: str, history: List[Dict] = None, persona_type: str = "A") -> str:
    """調用 Ollama API"""
    if history is None:
        history = []
    
    system_prompt = get_ai_system_prompt(role, persona_type)
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    payload = {
        "model": "gemma:2b",
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
    """發送遊戲訊息"""
    # 先讀取原始請求體進行調試
    body = await raw_request.body()
    print(f"🔍 原始請求體: {body.decode('utf-8')}")
    
    # 手動解析 JSON
    try:
        data = json.loads(body)
        print(f"📦 解析後的數據: {data}")
        print(f"📋 數據類型: {type(data)}")
        print(f"🔑 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    except Exception as e:
        print(f"❌ JSON 解析失敗: {str(e)}")
        raise HTTPException(status_code=400, detail=f"無效的 JSON: {str(e)}")
    
    # 嘗試用 Pydantic 驗證
    try:
        request = GameMessageRequest(**data)
        print(f"✅ Pydantic 驗證成功!")
    except ValidationError as e:
        print(f"❌ Pydantic 驗證失敗: {str(e)}")
        print(f"📝 驗證錯誤詳情: {e.errors()}")
        raise HTTPException(status_code=422, detail=f"驗證失敗: {e.errors()}")
    except Exception as e:
        print(f"❌ 未知錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"未知錯誤: {str(e)}")
    
    try:
        # 記錄接收到的請求
        print(f"📨 收到請求: session_id={request.session_id}, message={request.message[:50]}..., target_ai={request.target_ai}, persona_type={request.persona_type}")
        
        # 驗證必要欄位
        if not request.session_id:
            raise HTTPException(status_code=400, detail="缺少 session_id")
        if not request.message:
            raise HTTPException(status_code=400, detail="缺少 message")
        
        # 驗證 session
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 🔧 容錯處理:如果 session_id 是 "0",自動創建一個預設 session
        if request.session_id == "0":
            print(f"⚠️  檢測到 session_id=0,自動創建預設 session")
            # 檢查是否已有 id="0" 的 session
            cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", ("0",))
            result = cursor.fetchone()
            if not result:
                # 創建 id="0" 的 session
                cursor.execute(
                    "INSERT INTO sessions (id, persona_type, status) VALUES (?, ?, ?)",
                    ("0", request.persona_type or "A", 'active')
                )
                conn.commit()
                print(f"✅ 已創建預設 session: id=0, persona_type={request.persona_type or 'A'}")
                result = (request.persona_type or "A",)
        else:
            cursor.execute("SELECT persona_type FROM sessions WHERE id = ?", (request.session_id,))
            result = cursor.fetchone()
        
        if not result:
            conn.close()
            print(f"❌ 會話不存在: {request.session_id}")
            raise HTTPException(status_code=404, detail=f"會話不存在: {request.session_id}")
        
        # 使用請求中的 persona_type，如果沒有則使用 session 中的
        persona_type = request.persona_type or result[0]
        
        # 獲取歷史對話
        cursor.execute(
            "SELECT role, message FROM conversations WHERE session_id = ? ORDER BY timestamp",
            (request.session_id,)
        )
        history_rows = cursor.fetchall()
        history = [{"role": "user" if r[0] == "user" else "assistant", "content": r[1]} for r in history_rows]
        
        # 調用 AI
        ai_reply = await call_ollama(request.target_ai, request.message, history, persona_type)
        
        # 保存對話（使用前端傳入的 role 或預設為 "user"）
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
        
        return {"reply": ai_reply, "success": True}
    
    except HTTPException:
        raise
    except Exception as e:
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

@router.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 檢查 Ollama
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_status = "running" if response.status_code == 200 else "error"
    except:
        ollama_status = "not_running"
    
    # 檢查數據庫
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions")
        session_count = cursor.fetchone()[0]
        conn.close()
        db_status = "ok"
    except:
        session_count = 0
        db_status = "error"
    
    return {
        "status": "ok",
        "ollama": ollama_status,
        "database": db_status,
        "total_sessions": session_count
    }
