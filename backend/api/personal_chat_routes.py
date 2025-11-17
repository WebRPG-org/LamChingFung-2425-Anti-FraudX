"""
個人對話模式 API 路由
允許用戶選擇與助手或騙徒進行一對一對話
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.agent_service import AgentService
from utils.logger import log

router = APIRouter(tags=["PersonalChat"])

# 會話存儲（實際應用中應使用數據庫）
sessions = {}

# Agent 實例緩存
agent_instances = {}

def remove_emotion_markers(text: str) -> str:
    """
    移除文字中括號內的語氣描述
    例如：(笑)、(自信地說)、（微笑）等
    """
    # 移除中文括號和英文括號中的內容
    text = re.sub(r'\([^)]*\)', '', text)  # 英文括號 ()
    text = re.sub(r'（[^）]*）', '', text)  # 中文括號 （）
    text = re.sub(r'\[[^\]]*\]', '', text)  # 方括號 []
    text = re.sub(r'【[^】]*】', '', text)  # 中文方括號 【】
    
    # 移除多餘的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# 數據模型
class StartChatRequest(BaseModel):
    mode: str  # "assistant" 或 "scammer"
    scam_type: Optional[str] = None  # 騙局類型，僅在scammer模式使用

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: Optional[str] = None
    reply: str
    mode: str
    history: List[Dict[str, str]] = []
    success: bool = True

@router.post("/api/personal-chat/start", response_model=ChatResponse)
async def start_personal_chat(request: StartChatRequest):
    """
    開始個人對話會話
    mode: "assistant" (防詐助手) 或 "scammer" (騙徒)
    """
    try:
        session_id = str(uuid.uuid4())
        
        # 初始化 AgentService
        agent_service = AgentService(persona_type="average", enable_tracking=False)
        
        if request.mode == "assistant":
            welcome_message = "你好！我係黃sir，退休警察，專門處理詐騙案30年。有咩可以幫到你？如果你懷疑遇到騙案，隨時可以同我傾傾。"
            agent_type = "expert"
            
        elif request.mode == "scammer":
            scam_type = request.scam_type or "WhatsApp 對話詐騙"
            # 根據騙局類型給出開場白
            welcome_messages = {
                "WhatsApp 對話詐騙": "Hi，我係你朋友介紹嘅投資專家，有個機會可以幫你賺快錢，加我WhatsApp詳談？",
                "假短訊釣魚": "【銀行通知】你嘅賬戶出現可疑活動，請立即點擊以下連結驗證身份，否則將被凍結。",
                "虛假投資應用程式": "你好！我哋係正規投資平台，註冊即送$100體驗金，保證每日收益5%以上！",
                "假網站冒充銀行": "你好！我係XX銀行客服，你嘅網上銀行需要升級，請點擊連結進行驗證。",
                "刷單騙案": "你好！我哋請緊兼職刷單員，每單賺$50-200，日結工資，在家工作，有興趣嗎？",
                "中獎詐騙": "恭喜你！你中咗我哋電視台嘅頭獎，獎金港幣50萬，請盡快聯絡我哋領獎。",
                "假冒官員詐騙": "喂，你好，我係香港警務處嘅探員，你嘅身份證涉及一宗嚴重案件，需要立即處理。",
                "假網站冒充政府": "你好，我係政府部門職員，你有資格申請$10,000援助金，請提供個人資料以便處理。",
                "虛假購物平台": "你好！我哋係官方授權代理，名牌手袋8折優惠，只限今日，先到先得！",
                "愛情詐騙": "Hi～我覺得你個profile好有趣，想同你做個朋友，方便交換聯絡方式嗎？",
            }
            welcome_message = welcome_messages.get(scam_type, "你好，有咩可以幫到你？")
            agent_type = "scammer"
            
        else:
            raise HTTPException(status_code=400, detail="無效的模式，請選擇 'assistant' 或 'scammer'")
        
        # 存儲會話
        sessions[session_id] = {
            "mode": request.mode,
            "agent_service": agent_service,
            "agent_type": agent_type,
            "history": [],
            "scam_type": request.scam_type if request.mode == "scammer" else None
        }
        
        log.info(f"[個人對話] 新會話 {session_id} - 模式: {request.mode}")
        
        return ChatResponse(
            session_id=session_id,
            reply=welcome_message,
            mode=request.mode,
            history=[],
            success=True
        )
        
    except Exception as e:
        log.error(f"[個人對話] 啟動失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動對話失敗: {str(e)}")

@router.post("/api/personal-chat/message", response_model=ChatResponse)
async def send_message(request: ChatMessageRequest):
    """
    發送消息到個人對話會話
    """
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        session = sessions[request.session_id]
        agent_service = session["agent_service"]
        agent_type = session["agent_type"]
        mode = session["mode"]
        
        # 添加用戶消息到歷史
        session["history"].append({
            "role": "user",
            "content": request.message
        })
        
        log.info(f"[個人對話] {request.session_id} - 用戶: {request.message}")
        
        # 構建上下文消息
        if mode == "scammer":
            scam_type = session.get("scam_type", "投資理財詐騙")
            context_message = f"騙局類型：{scam_type}\n對方回應：{request.message}"
        else:
            context_message = request.message
        
        # 使用 AgentService 生成回應
        response = await agent_service.generate_response(
            agent_type=agent_type,
            message=context_message,
            conversation_history=session["history"],
            check_consistency=False,
            track_performance=False
        )
        
        reply = response.get("reply", "抱歉，我無法回應。")
        
        # 移除語氣描述括號
        reply = remove_emotion_markers(reply)
        
        # 添加AI回應到歷史
        session["history"].append({
            "role": "assistant",
            "content": reply
        })
        
        log.info(f"[個人對話] {request.session_id} - AI: {reply[:50]}...")
        
        return ChatResponse(
            session_id=request.session_id,
            reply=reply,
            mode=mode,
            history=session["history"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[個人對話] 發送消息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"發送消息失敗: {str(e)}")

@router.get("/api/personal-chat/session/{session_id}")
async def get_session(session_id: str):
    """
    獲取會話信息
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "mode": session["mode"],
        "history": session["history"],
        "scam_type": session.get("scam_type")
    }

@router.delete("/api/personal-chat/session/{session_id}")
async def end_session(session_id: str):
    """
    結束會話
    """
    if session_id in sessions:
        del sessions[session_id]
        log.info(f"[個人對話] 會話 {session_id} 已結束")
        return {"success": True, "message": "會話已結束"}
    else:
        raise HTTPException(status_code=404, detail="會話不存在")

@router.get("/api/personal-chat/modes")
async def get_available_modes():
    """
    獲取可用的對話模式
    """
    return {
        "modes": [
            {
                "id": "assistant",
                "name": "防詐助手",
                "description": "退休警察黃sir，專門處理詐騙案30年",
                "icon": "🛡️"
            },
            {
                "id": "scammer",
                "name": "騙徒模擬",
                "description": "職業騙徒林志強，體驗詐騙手法",
                "icon": "🎭"
            }
        ],
        "scam_types": [
            "投資理財詐騙",
            "冒充政府機關詐騙",
            "網購退款詐騙",
            "假冒親友詐騙",
            "網路交友詐騙",
            "假冒客服詐騙",
            "虛假中獎詐騙",
            "求職詐騙"
        ]
    }
