"""
RPGv2 三方對話 API 路由
支持玩家與騙徒、防詐專家的三方實時對話
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.agent_service import AgentService
from utils.logger import log
from utils.scam_scoring_hybrid import HybridScamScoring

router = APIRouter(prefix="/api/rpgv2", tags=["RPGv2"])

# 會話存儲
rpg_sessions = {}

# 數據模型
class StartBattleRequest(BaseModel):
    scam_type: str          # 騙案類型 ID
    player_role: str        # 玩家角色 (victim/observer)
    victim_persona: str     # 受害者人設 (elderly/average/overconfident)

class StartBattleResponse(BaseModel):
    session_id: str
    scam_type: str
    player_role: str
    opening_message: str    # 騙徒開場白
    success: bool = True

class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    speaker: str            # 'player' | 'scammer' | 'expert'

class SendMessageResponse(BaseModel):
    session_id: str
    replies: List[Dict[str, str]]  # [{ speaker: 'scammer', message: '...' }, ...]
    trust_data: Optional[Dict] = None
    success: bool = True

class GetAnalysisRequest(BaseModel):
    session_id: str

@router.post("/battle/start", response_model=StartBattleResponse)
async def start_battle(request: StartBattleRequest):
    """
    開始三方對話戰鬥
    
    玩家扮演受害者，與騙徒和防詐專家進行三方對話
    """
    try:
        session_id = str(uuid.uuid4())
        
        # 初始化 AgentService
        agent_service = AgentService(
            persona_type=request.victim_persona,
            enable_tracking=True
        )
        
        # 創建會話（使用混合評分系統）
        hybrid_scorer = HybridScamScoring(victim_persona=request.victim_persona)
        
        rpg_sessions[session_id] = {
            "scam_type": request.scam_type,
            "player_role": request.player_role,
            "victim_persona": request.victim_persona,
            "agent_service": agent_service,
            "hybrid_scorer": hybrid_scorer,
            "conversation_history": [],
            "round_count": 0,
            "trust_in_scammer": 50,
            "trust_in_expert": 50,
            "alertness": 50
        }
        
        log.info(f"[RPGv2] 新戰鬥會話 {session_id} - 騙案: {request.scam_type}, 角色: {request.player_role}")
        
        # 生成騙徒開場白
        scam_context = f"騙案類型：{request.scam_type}\n開始對話，引誘受害者。"
        
        scammer_response = await agent_service.generate_response(
            agent_type="scammer",
            message=scam_context,
            conversation_history=[],
            check_consistency=False,
            track_performance=True
        )
        
        opening_message = scammer_response.get("reply", "你好，我有一個很好的機會想跟你分享...")
        
        # 記錄開場白
        rpg_sessions[session_id]["conversation_history"].append({
            "role": "scammer",
            "content": opening_message
        })
        
        return StartBattleResponse(
            session_id=session_id,
            scam_type=request.scam_type,
            player_role=request.player_role,
            opening_message=opening_message,
            success=True
        )
        
    except Exception as e:
        log.error(f"[RPGv2] 啟動戰鬥失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動失敗: {str(e)}")

@router.post("/battle/message", response_model=SendMessageResponse)
async def send_battle_message(request: SendMessageRequest):
    """
    發送消息並獲取其他角色的回應
    
    流程：
    1. 玩家發送消息
    2. 騙徒回應
    3. 防詐專家分析並給出建議
    4. 更新信任度數據
    """
    try:
        if request.session_id not in rpg_sessions:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        session = rpg_sessions[request.session_id]
        agent_service = session["agent_service"]
        history = session["conversation_history"]
        
        # 記錄玩家消息
        history.append({
            "role": "player",
            "content": request.message
        })
        
        session["round_count"] += 1
        
        log.info(f"[RPGv2] {request.session_id} - 回合 {session['round_count']} - 玩家: {request.message[:50]}...")
        
        replies = []
        
        # 1. 騙徒回應
        scammer_context = f"騙案類型：{session['scam_type']}\n受害者說：{request.message}"
        
        scammer_response = await agent_service.generate_response(
            agent_type="scammer",
            message=scammer_context,
            conversation_history=history,
            check_consistency=True,
            track_performance=True
        )
        
        scammer_reply = scammer_response.get("reply", "讓我想想...")
        
        history.append({
            "role": "scammer",
            "content": scammer_reply
        })
        
        replies.append({
            "speaker": "scammer",
            "message": scammer_reply
        })
        
        log.info(f"[RPGv2] {request.session_id} - 騙徒: {scammer_reply[:50]}...")
        
        # 2. 防詐專家分析
        expert_context = f"騙案類型：{session['scam_type']}\n受害者說：{request.message}\n騙徒回應：{scammer_reply}\n請分析並給出建議。"
        
        expert_response = await agent_service.generate_response(
            agent_type="expert",
            message=expert_context,
            conversation_history=history,
            check_consistency=True,
            track_performance=True
        )
        
        expert_reply = expert_response.get("reply", "小心這可能是詐騙...")
        
        history.append({
            "role": "expert",
            "content": expert_reply
        })
        
        replies.append({
            "speaker": "expert",
            "message": expert_reply
        })
        
        log.info(f"[RPGv2] {request.session_id} - 專家: {expert_reply[:50]}...")
        
        # 3. 更新信任度（基於回應內容和回合數）
        trust_data = update_trust_levels(
            session,
            request.message,
            scammer_reply,
            expert_reply
        )
        
        return SendMessageResponse(
            session_id=request.session_id,
            replies=replies,
            trust_data=trust_data,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 發送消息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"發送消息失敗: {str(e)}")

def update_trust_levels(session: Dict, player_msg: str, scammer_msg: str, expert_msg: str) -> Dict:
    """
    更新信任度數據（使用混合評分系統）
    
    基於混合評分系統的動態乘數計算信任度變化
    """
    hybrid_scorer = session["hybrid_scorer"]
    
    # 使用混合評分系統分析騙徒消息
    scammer_tactics = detect_tactics(scammer_msg)
    
    # 只有檢測到策略才調用混合評分系統
    if scammer_tactics:
        score, status = hybrid_scorer.add_scammer_message(scammer_msg, scammer_tactics)
        
        # 檢查是否即時勝負
        if status == "scammer_win":
            session["trust_in_scammer"] = 100
            log.info(f"[RPGv2] 騙徒即時贏！")
            return get_trust_data(session)
    
    # 使用混合評分系統分析專家消息
    expert_defenses = detect_defenses(expert_msg)
    
    # 只有檢測到防騙方法才調用混合評分系統
    if expert_defenses:
        score, status = hybrid_scorer.add_expert_message(expert_msg, expert_defenses)
        
        # 檢查是否即時勝負
        if status == "expert_win":
            session["trust_in_scammer"] = 0
            session["trust_in_expert"] = 100
            log.info(f"[RPGv2] 專家即時贏！")
            return get_trust_data(session)
    
    # 分析玩家反應
    hybrid_scorer.add_victim_response(player_msg)
    
    # 從混合評分系統獲取當前狀態
    state = hybrid_scorer.get_current_state()
    
    # 更新會話信任度
    session["trust_in_scammer"] = state["trust_in_scammer"]
    session["trust_in_expert"] = state["trust_in_expert"]
    session["alertness"] = state["alertness"]
    
    log.info(f"[RPGv2] 信任度更新 - 騙徒: {session['trust_in_scammer']}, 專家: {session['trust_in_expert']}, 警覺: {session['alertness']}")
    
    return get_trust_data(session)

def detect_tactics(message: str) -> List[str]:
    """檢測騙徒使用的策略"""
    tactics = []
    message_lower = message.lower()
    
    # 只檢測明確的策略詞，避免誤判
    if any(word in message_lower for word in ["銀行", "政府", "警察", "官方", "執法"]):
        tactics.append("authority")
    if any(word in message_lower for word in ["立即", "馬上", "緊急", "嚴重", "急"]):
        tactics.append("urgency")
    if any(word in message_lower for word in ["補貼", "福利", "回贈", "優惠", "獎勵", "獲利"]):
        tactics.append("benefits")
    if any(word in message_lower for word in ["凍結", "損失", "危險", "後果", "風險", "虧損"]):
        tactics.append("fear")
    if any(word in message_lower for word in ["唔信", "唔係咁", "你以為", "不信", "不相信"]):
        tactics.append("challenge")
    
    # 如果沒有檢測到任何策略，返回空列表（不使用默認值）
    return tactics

def detect_defenses(message: str) -> List[str]:
    """檢測專家使用的防騙方法"""
    defenses = []
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["唔好驚", "冷靜", "理解", "明白"]):
        defenses.append("empathy")
    if any(word in message_lower for word in ["銀行唔會", "騙案手法", "真正", "官方"]):
        defenses.append("evidence")
    if any(word in message_lower for word in ["打去", "聯絡", "報警", "掛斷"]):
        defenses.append("actionable")
    if len(message) < 100 and "。" in message:
        defenses.append("clarity")
    
    return defenses if defenses else ["evidence"]  # 默認證據方法

def get_trust_data(session: Dict) -> Dict:
    """獲取信任度數據"""
    return {
        "trust_in_scammer": session["trust_in_scammer"],
        "trust_in_expert": session["trust_in_expert"],
        "alertness": session["alertness"],
        "round_count": session["round_count"]
    }

@router.post("/battle/analysis")
async def get_battle_analysis(request: GetAnalysisRequest):
    """
    獲取戰鬥結束後的詳細分析
    """
    try:
        if request.session_id not in rpg_sessions:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        session = rpg_sessions[request.session_id]
        agent_service = session["agent_service"]
        history = session["conversation_history"]
        
        log.info(f"[RPGv2] 生成分析報告 {request.session_id}")
        
        # 使用 RecorderAgent 生成最終分析
        analysis = await agent_service.generate_final_analysis(
            conversation_history=history,
            outcome_description=f"RPGv2 戰鬥會話結束 - 回合數: {session['round_count']}"
        )
        
        # 判斷結果
        trust_in_scammer = session["trust_in_scammer"]
        trust_in_expert = session["trust_in_expert"]
        alertness = session["alertness"]
        
        if trust_in_scammer > 70:
            outcome = "scammer_win"
            outcome_text = "你被騙了！騙徒成功獲取了你的信任。"
        elif alertness > 70 or trust_in_expert > 70:
            outcome = "expert_win"
            outcome_text = "成功識破騙局！你保護了自己。"
        else:
            outcome = "draw"
            outcome_text = "對話結束，結果未明。"
        
        return {
            "success": True,
            "session_id": request.session_id,
            "outcome": outcome,
            "outcome_text": outcome_text,
            "trust_data": {
                "trust_in_scammer": trust_in_scammer,
                "trust_in_expert": trust_in_expert,
                "alertness": alertness
            },
            "round_count": session["round_count"],
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 生成分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成分析失敗: {str(e)}")

@router.delete("/battle/session/{session_id}")
async def end_battle_session(session_id: str):
    """
    結束戰鬥會話
    """
    if session_id in rpg_sessions:
        del rpg_sessions[session_id]
        log.info(f"[RPGv2] 戰鬥會話 {session_id} 已結束")
        return {"success": True, "message": "會話已結束"}
    else:
        raise HTTPException(status_code=404, detail="會話不存在")

@router.get("/battle/health")
async def battle_health_check():
    """
    健康檢查
    """
    return {
        "status": "ok",
        "active_sessions": len(rpg_sessions),
        "features": [
            "ThreeWayConversation",
            "RealTimeAI",
            "TrustSystem",
            "DynamicAnalysis"
        ]
    }
