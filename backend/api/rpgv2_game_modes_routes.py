"""
RPGv2 完整遊戲模式 API 路由
支持騙徒模式、專家模式、自動模式
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal, Any
import asyncio
import uuid
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.agent_service import AgentService
from utils.rpgv2_game_mode_manager import game_mode_manager, GameMode
from utils.logger import log
from utils.scam_scoring_hybrid import HybridScamScoring

router = APIRouter(prefix="/api/rpgv2", tags=["RPGv2-GameModes"])

# 每個遊戲會話對應一個混合評分器（PROJECT_COMPLETION_REPORT 判定邏輯實際應用）
_hybrid_scorers: Dict[str, HybridScamScoring] = {}

SUPPORTED_LANGUAGES = {"zh-HK", "zh-CN", "en-US", "ja-JP"}


def _normalize_language(language: Optional[str]) -> str:
    if not language:
        return "zh-HK"
    value = language.strip()
    return value if value in SUPPORTED_LANGUAGES else "zh-HK"


def _language_instruction(language: str) -> str:
    if language == "zh-CN":
        return "请使用简体中文对话；可理解繁体中文输入并用简体中文回复。"
    if language == "en-US":
        return "IMPORTANT: You MUST reply in English only. Do not use Chinese or any other language. All responses must be in natural English."
    if language == "ja-JP":
        return "重要：必ず日本語で返答してください。中国語や他の言語を使わないでください。すべての返答を自然な日本語で行ってください。"
    return "請使用繁體中文（香港粵語語境）回覆；可理解簡體中文輸入。"


class StartGameRequest(BaseModel):
    mode: GameMode  # "victim" | "expert" | "scammer" | "auto"
    scam_type: str
    victim_persona: str = "average"
    difficulty: Optional[str] = "normal"  # easy/normal/hard
    language: str = "zh-HK"  # zh-HK | zh-CN | en-US | ja-JP

class StartGameResponse(BaseModel):
    session_id: str
    mode: str
    mode_info: Dict
    opening_messages: List[Dict]  # [{ role: str, content: str }]
    game_state: Dict
    success: bool = True

class PlayerActionRequest(BaseModel):
    session_id: str
    message: str
    action_type: Optional[str] = "message"  # message/hint/skip
    language: Optional[str] = None

class PlayerActionResponse(BaseModel):
    session_id: str
    ai_responses: List[Dict]
    game_state: Dict
    score_update: Dict
    game_status: Dict
    success: bool = True

class GetGameStateRequest(BaseModel):
    session_id: str

class AutoPlayRequest(BaseModel):
    session_id: str
    rounds: int = 1  # 自動進行的回合數

class SwitchRoleRequest(BaseModel):
    session_id: str
    new_mode: GameMode  # 切換到的新模式
    language: Optional[str] = None


# ==================== API 端點 ====================

@router.post("/game/start", response_model=StartGameResponse)
async def start_game(request: StartGameRequest):
    """
    開始遊戲
    
    支持四種模式：
    - victim: 玩家扮演受害人（與騙徒和專家對話）
    - expert: 玩家扮演防詐專家（與騙徒和受害人對話）
    - scammer: 玩家扮演騙徒（與受害人和專家對話）
    - auto: 自動模式（觀察AI對話）
    """
    try:
        session_id = str(uuid.uuid4())
        
        normalized_language = _normalize_language(request.language)

        # 創建遊戲會話
        session = game_mode_manager.create_session(
            session_id=session_id,
            mode=request.mode,
            scam_type=request.scam_type,
            victim_persona=request.victim_persona,
            language=normalized_language
        )
        
        # 初始化 AgentService
        agent_service = AgentService(
            persona_type=request.victim_persona,
            enable_tracking=True,
            scam_type=request.scam_type
        )

        # 初始化混合評分器（把 PROJECT_COMPLETION_REPORT 的判定邏輯接入主流程）
        hybrid_scorer = HybridScamScoring(victim_persona=request.victim_persona)
        _hybrid_scorers[session_id] = hybrid_scorer
        
        # 獲取模式信息
        mode_info = game_mode_manager.get_mode_info(request.mode)
        
        log.info(
            f"[RPGv2] 開始遊戲 - 會話={session_id}, "
            f"模式={request.mode}, 騙案={request.scam_type}, 語言={normalized_language}"
        )
        
        # 根據模式生成開場消息
        opening_messages = await generate_opening_messages(
            mode=request.mode,
            scam_type=request.scam_type,
            agent_service=agent_service,
            session=session
        )
        
        # 記錄開場消息到會話
        for msg in opening_messages:
            session.conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 構建遊戲狀態
        game_state = {
            "round_count": session.round_count,
            "trust_in_scammer": session.trust_in_scammer,
            "trust_in_expert": session.trust_in_expert,
            "alertness": session.alertness,
            "player_score": session.player_score,
            "ai_score": session.ai_score,
            "mode": request.mode,
            "language": normalized_language
        }
        
        return StartGameResponse(
            session_id=session_id,
            mode=request.mode,
            mode_info=mode_info,
            opening_messages=opening_messages,
            game_state=game_state,
            success=True
        )
        
    except Exception as e:
        log.error(f"[RPGv2] 開始遊戲失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"開始遊戲失敗: {str(e)}")


@router.post("/game/action", response_model=PlayerActionResponse)
async def player_action(request: PlayerActionRequest):
    """
    玩家行動
    
    根據不同模式處理玩家輸入：
    - victim模式: 玩家回應騙徒和專家的對話
    - expert模式: 玩家發送防詐建議，AI騙徒和受害者回應
    - scammer模式: 玩家發送詐騙消息，AI受害者和專家回應
    - auto模式: 不需要玩家輸入，自動進行
    """
    try:
        session = game_mode_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        if request.language:
            session.language = _normalize_language(request.language)

        # 初始化 AgentService
        agent_service = AgentService(
            persona_type=session.victim_persona,
            enable_tracking=True,
            scam_type=session.scam_type
        )
        
        log.info(
            f"[RPGv2] 玩家行動 - 會話={request.session_id}, "
            f"模式={session.mode}, 回合={session.round_count + 1}, 語言={session.language}"
        )
        
        # 根據模式處理行動
        if session.mode == "victim":
            ai_responses, trust_changes = await handle_victim_mode(
                session=session,
                player_message=request.message,
                agent_service=agent_service
            )
        elif session.mode == "expert":
            ai_responses, trust_changes = await handle_expert_mode(
                session=session,
                player_message=request.message,
                agent_service=agent_service
            )
        elif session.mode == "scammer":
            ai_responses, trust_changes = await handle_scammer_mode(
                session=session,
                player_message=request.message,
                agent_service=agent_service
            )
        else:  # auto
            raise HTTPException(
                status_code=400,
                detail="自動模式不需要玩家輸入，請使用 /game/auto-play"
            )
        
        # 🔥 修復：不要在這裡設置 game_over，讓 update_session 內部處理
        # 檢查即時勝負（如果trust_changes中有instant_win）
        if trust_changes.get("instant_win"):
            instant_result = trust_changes["instant_win"]
            
            log.info(
                f"[RPGv2] 即時勝負判定 - 會話={request.session_id}, "
                f"勝者={instant_result['winner']}, 原因={instant_result['reason']}"
            )
        
        # 更新會話（內部會處理即時勝負的情況）
        update_result = game_mode_manager.update_session(
            session_id=request.session_id,
            player_message=request.message,
            ai_responses=ai_responses,
            trust_changes=trust_changes
        )
        
        # 🔥 修復：從 update_result 中獲取更新後的 session
        updated_session = update_result["session"]
        
        # 構建回應（使用更新後的數據）
        game_state = {
            "round_count": updated_session.round_count,
            "trust_in_scammer": updated_session.trust_in_scammer,
            "trust_in_expert": updated_session.trust_in_expert,
            "alertness": updated_session.alertness,
            "player_score": updated_session.player_score,
            "ai_score": updated_session.ai_score,
            "language": updated_session.language
        }
        
        log.info(
            f"[RPGv2] 回應前端 - 回合={updated_session.round_count}, "
            f"騙徒={updated_session.trust_in_scammer:.1f}, "
            f"專家={updated_session.trust_in_expert:.1f}, "
            f"警覺性={updated_session.alertness:.1f}"
        )
        
        return PlayerActionResponse(
            session_id=request.session_id,
            ai_responses=ai_responses,
            game_state=game_state,
            score_update=update_result["score_update"],
            game_status=update_result["game_status"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 玩家行動失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"玩家行動失敗: {str(e)}")


@router.post("/game/auto-play")
async def auto_play(request: AutoPlayRequest):
    """
    自動模式播放
    
    讓AI騙徒和AI受害者自動對話指定回合數
    """
    try:
        session = game_mode_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        if session.mode != "auto":
            raise HTTPException(
                status_code=400,
                detail="只有自動模式支持此功能"
            )
        
        # 初始化 AgentService
        agent_service = AgentService(
            persona_type=session.victim_persona,
            enable_tracking=True,
            scam_type=session.scam_type
        )
        
        log.info(
            f"[RPGv2] 自動播放 - 會話={request.session_id}, "
            f"回合數={request.rounds}"
        )
        
        all_messages = []
        
        for round_num in range(request.rounds):
            # 騙徒發言
            scammer_context = f"騙案類型：{session.scam_type}\n繼續對話。"
            
            scammer_response = await agent_service.generate_response(
                agent_type="scammer",
                message=scammer_context,
                conversation_history=session.conversation_history,
                check_consistency=True,
                track_performance=True
            )
            
            scammer_msg = {
                "role": "scammer",
                "content": scammer_response.get("reply", "...")
            }
            
            session.conversation_history.append(scammer_msg)
            all_messages.append(scammer_msg)
            
            # 受害者回應
            victim_context = f"騙徒說：{scammer_msg['content']}"
            
            victim_response = await agent_service.generate_response(
                agent_type="victim",
                message=victim_context,
                conversation_history=session.conversation_history,
                check_consistency=True,
                track_performance=True
            )
            
            victim_msg = {
                "role": "victim",
                "content": victim_response.get("reply", "...")
            }
            
            session.conversation_history.append(victim_msg)
            all_messages.append(victim_msg)
            
            # 更新信任度（混合評分系統）
            scorer = _hybrid_scorers.get(request.session_id)
            if scorer:
                scammer_tactics = detect_tactics(scammer_msg["content"])
                scorer.add_scammer_message(scammer_msg["content"], scammer_tactics)
                scorer.add_victim_response(victim_msg["content"])

                hybrid_state = scorer.get_current_state()
                session.trust_in_scammer = hybrid_state.get("trust_in_scammer", session.trust_in_scammer)
                session.trust_in_expert = hybrid_state.get("trust_in_expert", session.trust_in_expert)
                session.alertness = hybrid_state.get("alertness", session.alertness)
            else:
                trust_changes = calculate_auto_trust_changes(
                    scammer_msg["content"],
                    victim_msg["content"]
                )
                session.trust_in_scammer += trust_changes["scammer"]
                session.alertness += trust_changes["alertness"]

            session.round_count += 1
        
        # 檢查遊戲狀態
        game_status = game_mode_manager._check_win_condition(session)
        
        game_state = {
            "round_count": session.round_count,
            "trust_in_scammer": session.trust_in_scammer,
            "trust_in_expert": session.trust_in_expert,
            "alertness": session.alertness,
            "player_score": session.player_score,
            "ai_score": session.ai_score
        }
        
        return {
            "success": True,
            "session_id": request.session_id,
            "messages": all_messages,
            "game_state": game_state,
            "game_status": game_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 自動播放失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"自動播放失敗: {str(e)}")


@router.get("/game/state/{session_id}")
async def get_game_state(session_id: str):
    """獲取遊戲狀態"""
    try:
        stats = game_mode_manager.get_session_stats(session_id)
        scorer = _hybrid_scorers.get(session_id)
        if scorer:
            stats["hybrid"] = _build_hybrid_snapshot(session_id, scorer)
        return {
            "success": True,
            **stats
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"[RPGv2] 獲取遊戲狀態失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/hybrid-analysis/{session_id}")
async def get_hybrid_analysis(session_id: str):
    """輸出 PROJECT_COMPLETION_REPORT 對應的完整 Hybrid 分析"""
    try:
        scorer = _get_hybrid_scorer_or_404(session_id)
        return {
            "success": True,
            "hybrid": _build_hybrid_snapshot(session_id, scorer)
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 獲取 Hybrid 分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/modes")
async def get_game_modes():
    """獲取所有遊戲模式信息"""
    try:
        modes = game_mode_manager.get_all_modes()
        return {
            "success": True,
            "modes": modes
        }
    except Exception as e:
        log.error(f"[RPGv2] 獲取模式信息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/game/session/{session_id}")
async def end_game_session(session_id: str):
    """結束遊戲會話"""
    try:
        success = game_mode_manager.delete_session(session_id)
        _hybrid_scorers.pop(session_id, None)
        if success:
            return {"success": True, "message": "會話已結束"}
        else:
            raise HTTPException(status_code=404, detail="會話不存在")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 結束會話失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/stats")
async def get_performance_stats(session_id: Optional[str] = None):
    """
    獲取性能統計

    - 若提供 session_id，輸出該會話的 Hybrid 性能與分析
    - 若未提供，輸出所有活躍會話的 Hybrid 摘要
    """
    try:
        if session_id:
            scorer = _get_hybrid_scorer_or_404(session_id)
            return {
                "success": True,
                "session_id": session_id,
                "data": {
                    "current_state": scorer.get_current_state(),
                    "detailed_analysis": scorer.get_detailed_analysis(),
                    "final_report": scorer.generate_final_report(),
                }
            }

        all_sessions = {
            sid: {
                "current_state": scorer.get_current_state(),
                "game_outcome": scorer.get_game_outcome(),
            }
            for sid, scorer in _hybrid_scorers.items()
        }

        return {
            "success": True,
            "total_active_sessions": len(_hybrid_scorers),
            "data": all_sessions
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 獲取性能統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/clear-cache")
async def clear_performance_cache():
    """清空 Hybrid 評分器緩存"""
    try:
        _hybrid_scorers.clear()
        return {
            "success": True,
            "message": "Hybrid 緩存已清空"
        }
    except Exception as e:
        log.error(f"[RPGv2] 清空緩存失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/game/switch-role")
async def switch_role(request: SwitchRoleRequest):
    """
    切換角色模式
    
    允許玩家在遊戲中切換角色：
    - victim (按鍵1): 受害人模式
    - expert (按鍵2): 專家模式  
    - scammer (按鍵3): 騙徒模式
    """
    try:
        session = game_mode_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        old_mode = session.mode

        if request.language:
            session.language = _normalize_language(request.language)
        
        # 不允許切換到自動模式
        if request.new_mode == "auto":
            raise HTTPException(
                status_code=400,
                detail="不能切換到自動模式"
            )
        
        # 更新模式
        session.mode = request.new_mode
        
        log.info(
            f"[RPGv2] 角色切換 - 會話={request.session_id}, "
            f"{old_mode} -> {request.new_mode}, 語言={session.language}"
        )
        
        # 獲取新模式信息
        mode_info = game_mode_manager.get_mode_info(request.new_mode)
        
        return {
            "success": True,
            "session_id": request.session_id,
            "old_mode": old_mode,
            "new_mode": request.new_mode,
            "mode_info": mode_info,
            "language": session.language,
            "message": f"已切換到{mode_info['name']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[RPGv2] 角色切換失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"角色切換失敗: {str(e)}")


# ==================== 輔助函數 ====================

async def generate_opening_messages(
    mode: GameMode,
    scam_type: str,
    agent_service: AgentService,
    session
) -> List[Dict]:
    """生成開場消息"""
    import re
    
    def clean_role_prefix(text: str) -> str:
        """清理角色前綴和語氣描述"""
        # 移除角色前綴
        role_prefixes = [
            r'^scammer:\s*',
            r'^expert:\s*',
            r'^victim:\s*',
            r'^騙徒:\s*',
            r'^騙徒：\s*',
            r'^專家:\s*',
            r'^專家：\s*',
            r'^受害者:\s*',
            r'^受害者：\s*',
        ]
        
        for prefix_pattern in role_prefixes:
            text = re.sub(prefix_pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # 移除語氣描述，如 (語氣沉穩、帶著一點急切)
        text = re.sub(r'^\(.*?\)\s*', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    lang_instruction = _language_instruction(session.language)
    lang = session.language
    messages = []

    if mode == "victim":
        # 受害人模式：只顯示騙徒開場白，專家在玩家首次發言後才介入
        if lang == 'en-US':
            scammer_context = (
                f"Scam type: {scam_type}\n"
                f"{lang_instruction}\n"
                f"Start the scam conversation with one sentence to attract the victim's interest (within 50 words)."
            )
        elif lang == 'ja-JP':
            scammer_context = (
                f"詐欺の種類：{scam_type}\n"
                f"{lang_instruction}\n"
                f"詐欺の会話を始めて、一文で被害者の興味を引いてください（50字以内）。"
            )
        elif lang == 'zh-CN':
            scammer_context = (
                f"诈骗类型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"开始诈骗对话，用一句话引起受害者兴趣（50字内）。"
            )
        else:
            scammer_context = (
                f"騙案類型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"開始詐騙對話，用一句話引起受害者興趣（50字內）。"
            )
        
        scammer_response = await agent_service.generate_response(
            agent_type="scammer",
            message=scammer_context,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        scammer_content = clean_role_prefix(scammer_response.get("reply", "你好，我是..."))
        
        messages.append({
            "role": "scammer",
            "content": scammer_content
        })
        
        log.info(f"[開場] 騙徒: {scammer_content[:50]}...")
        # 注意：專家不在開場出現，等玩家首次發言後再介入
    
    elif mode == "scammer":
        # 騙徒模式：AI先代騙徒（玩家）生成開場白，然後受害者和專家回應，最後輪到玩家輸入
        lang = session.language
        if lang == 'en-US':
            scammer_context = (
                f"Scam type: {scam_type}\n"
                f"{lang_instruction}\n"
                f"You are the scammer. Generate a natural opening line to approach the victim (within 60 words)."
            )
            victim_ctx_tmpl = "The scammer said: {scammer}\n{lang}\nAs the victim, respond naturally (within 40 words)."
            expert_ctx_tmpl = "Scam type: {scam_type}\n{lang}\nThe scammer said: {scammer}\nThe victim said: {victim}\nAs an anti-scam expert, warn the victim briefly that this may be a scam (within 40 words)."
        elif lang == 'ja-JP':
            scammer_context = (
                f"詐欺の種類：{scam_type}\n"
                f"{lang_instruction}\n"
                f"あなたは詐欺師です。被害者に自然な日本語で話しかけてください（60字以内）。"
            )
            victim_ctx_tmpl = "詐欺師が言いました：{scammer}\n{lang}\n被害者として自然に返答してください（40字以内）。"
            expert_ctx_tmpl = "詐欺の種類：{scam_type}\n{lang}\n詐欺師が言いました：{scammer}\n被害者が言いました：{victim}\n防詐欺の専門家として、被害者にこれが詐欺かもしれないと簡潔に警告してください（40字以内）。"
        elif lang == 'zh-CN':
            scammer_context = (
                f"诈骗类型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"你是骗徒，根据诈骗类型生成一句自然的开场白接触受害者（60字内）。"
            )
            victim_ctx_tmpl = "骗徒说：{scammer}\n{lang}\n你是受害者，自然地回应骗徒（40字内）。"
            expert_ctx_tmpl = "诈骗类型：{scam_type}\n{lang}\n骗徒说：{scammer}\n受害者说：{victim}\n你是防诈专家，简短警告受害者这可能是诈骗（40字内）。"
        else:  # zh-HK
            scammer_context = (
                f"騙案類型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"你是騙徒，根據騙案類型生成一句真實的開場白來接觸受害者（60字內，自然口語化）。"
            )
            victim_ctx_tmpl = "騙徒說：{scammer}\n{lang}\n你是受害者，自然地回應騙徒（40字內）。"
            expert_ctx_tmpl = "騙案類型：{scam_type}\n{lang}\n騙徒說：{scammer}\n受害者說：{victim}\n你是防詐專家，向受害者提出簡短警告，提醒他這可能是詐騙（旁白口吻，40字內）。"

        scammer_response = await agent_service.generate_response(
            agent_type="scammer",
            message=scammer_context,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )

        scammer_content = clean_role_prefix(scammer_response.get("reply", "你好，我有個重要事項想告訴你..."))

        messages.append({
            "role": "scammer",
            "content": scammer_content
        })

        log.info(f"[開場-騙徒模式] 騙徒開場: {scammer_content[:50]}...")

        # 受害者初步回應
        victim_context = victim_ctx_tmpl.format(
            scammer=scammer_content, lang=lang_instruction, scam_type=scam_type, victim=""
        )

        victim_response = await agent_service.generate_response(
            agent_type="victim",
            message=victim_context,
            conversation_history=messages,
            check_consistency=False,
            track_performance=False
        )

        victim_content = clean_role_prefix(victim_response.get("reply", "係咩事？"))

        messages.append({
            "role": "victim",
            "content": victim_content
        })

        log.info(f"[開場-騙徒模式] 受害者回應: {victim_content[:50]}...")

        # 專家向受害者提出警告
        expert_context = expert_ctx_tmpl.format(
            scammer=scammer_content, victim=victim_content,
            lang=lang_instruction, scam_type=scam_type
        )

        expert_response = await agent_service.generate_response(
            agent_type="expert",
            message=expert_context,
            conversation_history=messages,
            check_consistency=False,
            track_performance=False
        )

        expert_content = clean_role_prefix(expert_response.get("reply", "注意！這可能是詐騙！"))

        messages.append({
            "role": "expert",
            "content": expert_content
        })

        log.info(f"[開場-騙徒模式] 專家旁白: {expert_content[:50]}...")
        
    elif mode == "expert":
        # 專家模式：騙徒先發起詐騙
        if lang == 'en-US':
            scammer_context = (
                f"Scam type: {scam_type}\n"
                f"{lang_instruction}\n"
                f"Start the scam conversation."
            )
            victim_ctx = f"The scammer said: {'{scammer_content}'}\n{lang_instruction}\nAs the victim, respond naturally."
        elif lang == 'ja-JP':
            scammer_context = (
                f"詐欺の種類：{scam_type}\n"
                f"{lang_instruction}\n"
                f"詐欺の会話を始めてください。"
            )
            victim_ctx = f"詐欺師が言いました：{{scammer_content}}\n{lang_instruction}\n被害者として自然に返答してください。"
        elif lang == 'zh-CN':
            scammer_context = (
                f"诈骗类型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"开始诈骗对话。"
            )
            victim_ctx = f"骗徒说：{{scammer_content}}\n{lang_instruction}\n你是受害者，自然地回应。"
        else:
            scammer_context = (
                f"騙案類型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"開始詐騙對話。"
            )
            victim_ctx = f"騙徒說：{{scammer_content}}\n{lang_instruction}"

        scammer_response = await agent_service.generate_response(
            agent_type="scammer",
            message=scammer_context,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        scammer_content = clean_role_prefix(scammer_response.get("reply", "你好，我是..."))
        
        messages.append({
            "role": "scammer",
            "content": scammer_content
        })
        
        log.info(f"[開場] 騙徒: {scammer_content[:50]}...")
        
        # 受害者初步回應
        victim_context = victim_ctx.format(scammer_content=scammer_content)
        
        victim_response = await agent_service.generate_response(
            agent_type="victim",
            message=victim_context,
            conversation_history=messages,
            check_consistency=False,
            track_performance=False
        )
        
        victim_content = clean_role_prefix(victim_response.get("reply", "什麼事？"))
        
        messages.append({
            "role": "victim",
            "content": victim_content
        })
        
        log.info(f"[開場] 受害者: {victim_content[:50]}...")
        
    elif mode == "auto":
        # 自動模式：騙徒開場
        if lang == 'en-US':
            scammer_context = (
                f"Scam type: {scam_type}\n"
                f"{lang_instruction}\n"
                f"Start the scam conversation."
            )
        elif lang == 'ja-JP':
            scammer_context = (
                f"詐欺の種類：{scam_type}\n"
                f"{lang_instruction}\n"
                f"詐欺の会話を始めてください。"
            )
        elif lang == 'zh-CN':
            scammer_context = (
                f"诈骗类型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"开始诈骗对话。"
            )
        else:
            scammer_context = (
                f"騙案類型：{scam_type}\n"
                f"{lang_instruction}\n"
                f"開始詐騙對話。"
            )
        
        scammer_response = await agent_service.generate_response(
            agent_type="scammer",
            message=scammer_context,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        scammer_content = clean_role_prefix(scammer_response.get("reply", "你好..."))
        
        messages.append({
            "role": "scammer",
            "content": scammer_content
        })
        
        log.info(f"[開場] 騙徒: {scammer_content[:50]}...")
    
    return messages


def detect_tactics(message: str) -> List[str]:
    """從訊息抽取騙徒策略標籤（對應 HybridScamScoring）"""
    text = (message or "")
    tactics: List[str] = []

    if any(k in text for k in ["銀行", "警察", "政府", "官方", "客服", "職員"]):
        tactics.append("authority")
    if any(k in text for k in ["立即", "馬上", "緊急", "即刻", "限時", "最後機會"]):
        tactics.append("urgency")
    if any(k in text for k in ["回贈", "獎金", "福利", "高回報", "賺錢", "補貼"]):
        tactics.append("benefits")
    if any(k in text for k in ["你唔敢", "你不敢", "唔信", "敢唔敢", "挑戰"]):
        tactics.append("challenge")
    if any(k in text for k in ["凍結", "封鎖", "風險", "會出事", "損失", "追究"]):
        tactics.append("fear")

    return tactics


def detect_defenses(message: str) -> List[str]:
    """從訊息抽取專家防騙標籤（對應 HybridScamScoring）"""
    text = (message or "")
    defenses: List[str] = []

    if any(k in text for k in ["唔好驚", "冷靜", "放心", "我明白", "先冷靜"]):
        defenses.append("empathy")
    if any(k in text for k in ["銀行唔會", "這是詐騙", "常見手法", "官方不會"]):
        defenses.append("evidence")
    if any(k in text for k in ["報警", "打去銀行", "18222", "核實", "聯絡官方"]):
        defenses.append("actionable")
    if any(k in text for k in ["重點", "總結", "簡單講", "一句話"]):
        defenses.append("clarity")

    return defenses


def _apply_hybrid_scorer(
    session_id: str,
    mode: str,
    player_msg: str,
    scammer_msg: str,
    expert_msg: str,
    victim_msg: Optional[str] = None,
) -> Dict[str, float]:
    """把 PROJECT_COMPLETION_REPORT 的混合判定實際套用到主流程信任變化"""
    scorer = _hybrid_scorers.get(session_id)
    if not scorer:
        return {}

    scammer_tactics = detect_tactics(scammer_msg)
    expert_defenses = detect_defenses(expert_msg)

    _, scammer_status = scorer.add_scammer_message(scammer_msg, scammer_tactics)
    _, expert_status = scorer.add_expert_message(expert_msg, expert_defenses)

    victim_input = victim_msg if victim_msg is not None else player_msg
    scorer.add_victim_response(victim_input)

    # 依報告中的即時勝負規則，映射到現有 winner 表示
    if scammer_status == "scammer_win":
        winner = "player" if mode == "scammer" else "ai"
        return {
            "instant_win": {
                "instant_win": True,
                "winner": winner,
                "reason": "即時判定：騙徒勝利"
            },
            "scammer": 100,
            "expert": -100,
            "alertness": -100
        }

    if expert_status == "expert_win":
        winner = "player" if mode in ["victim", "expert"] else "ai"
        return {
            "instant_win": {
                "instant_win": True,
                "winner": winner,
                "reason": "即時判定：專家勝利"
            },
            "scammer": -100,
            "expert": 100,
            "alertness": 100
        }

    state = scorer.get_current_state()
    return {
        "scammer": state.get("trust_in_scammer", 50) - 50,
        "expert": state.get("trust_in_expert", 50) - 50,
        "alertness": state.get("alertness", 50) - 50,
    }


def _get_hybrid_scorer_or_404(session_id: str) -> HybridScamScoring:
    scorer = _hybrid_scorers.get(session_id)
    if not scorer:
        raise HTTPException(status_code=404, detail="Hybrid 評分器不存在，請先開始遊戲")
    return scorer


def _build_hybrid_snapshot(session_id: str, scorer: HybridScamScoring) -> Dict[str, Any]:
    """彙整 PROJECT_COMPLETION_REPORT 中所有核心輸出"""
    return {
        "session_id": session_id,
        "current_state": scorer.get_current_state(),
        "game_outcome": scorer.get_game_outcome(),
        "detailed_analysis": scorer.get_detailed_analysis(),
        "persona_analysis": scorer.get_persona_analysis(),
        "optimal_expert_strategies": scorer.get_optimal_expert_strategies(),
        "vulnerable_scammer_tactics": scorer.get_vulnerable_scammer_tactics(),
        "all_personas_comparison": scorer.compare_all_personas(),
    }


async def handle_victim_mode(
    session,
    player_message: str,
    agent_service: AgentService
) -> tuple[List[Dict], Dict]:
    """
    處理受害人模式（並行優化版）

    玩家扮演受害者，AI 騙徒和 AI 專家並行生成回應
    🔥 使用 asyncio.gather 並行生成，速度提升約 50%
    """
    # 構建對話歷史，將玩家消息標記為 victim
    conversation_with_player = session.conversation_history + [{
        "role": "victim",
        "content": player_message
    }]

    lang_instruction = _language_instruction(session.language)
    lang = session.language

    if lang == 'en-US':
        scammer_context = (
            f"Scam type: {session.scam_type}\n"
            f"{lang_instruction}\n"
            f"The victim said: {player_message}\n"
            f"Continue the scam conversation, respond briefly and persuasively (within 80 words)."
        )
        expert_context = (
            f"{lang_instruction}\n"
            f"The victim said: {player_message}\n"
            f"As an anti-scam expert, give brief advice to protect the victim (within 80 words)."
        )
    elif lang == 'ja-JP':
        scammer_context = (
            f"詐欺の種類：{session.scam_type}\n"
            f"{lang_instruction}\n"
            f"被害者が言いました：{player_message}\n"
            f"詐欺の会話を続けて、簡潔かつ説得力のある返答をしてください（80字以内）。"
        )
        expert_context = (
            f"{lang_instruction}\n"
            f"被害者が言いました：{player_message}\n"
            f"防詐欺の専門家として、被害者を守るための簡潔なアドバイスをしてください（80字以内）。"
        )
    elif lang == 'zh-CN':
        scammer_context = (
            f"诈骗类型：{session.scam_type}\n"
            f"{lang_instruction}\n"
            f"受害者说：{player_message}\n"
            f"继续诈骗对话，回应要简短有力（80字内）。"
        )
        expert_context = (
            f"{lang_instruction}\n"
            f"受害者说：{player_message}\n"
            f"请向受害者提供简短防诈建议（80字内）。"
        )
    else:  # zh-HK default
        scammer_context = (
            f"騙案類型：{session.scam_type}\n"
            f"{lang_instruction}\n"
            f"受害者說：{player_message}\n"
            f"繼續詐騙對話，回應要簡短有力（100字內）。"
        )
        expert_context = (
            f"{lang_instruction}\n"
            f"受害者說：{player_message}\n"
            f"請向受害者提供簡短防詐建議（100字內）。"
        )

    # 🔥 並行生成騙徒和專家回應
    log.info(f"[RPGv2] 並行生成騙徒+專家回應...")
    scammer_task = agent_service.generate_response(
        agent_type="scammer",
        message=scammer_context,
        conversation_history=conversation_with_player,
        check_consistency=True,
        track_performance=True
    )
    expert_task = agent_service.generate_response(
        agent_type="expert",
        message=expert_context,
        conversation_history=conversation_with_player,
        check_consistency=True,
        track_performance=True
    )

    scammer_response, expert_response = await asyncio.gather(
        scammer_task, expert_task
    )

    scammer_reply = scammer_response.get("reply", "...")
    expert_reply = expert_response.get("reply", "...")

    ai_responses = [
        {"role": "scammer", "content": scammer_reply},
        {"role": "expert",   "content": expert_reply},
    ]

    log.info(f"[RPGv2] 騙徒: {scammer_reply[:80]}...")
    log.info(f"[RPGv2] 專家: {expert_reply[:80]}...")
    log.info(f"[RPGv2] ai_responses 數量: {len(ai_responses)}")
    
    # 計算信任度變化（使用AI語意判定 + HybridScamScoring 實際判定）
    trust_changes = await calculate_victim_trust_changes(
        player_message,
        scammer_reply,
        expert_reply,
        agent_service,
        conversation_with_player
    )
    hybrid_changes = _apply_hybrid_scorer(
        session.session_id,
        session.mode,
        player_message,
        scammer_reply,
        expert_reply,
        victim_msg=player_message,
    )
    if hybrid_changes:
        has_instant_win = bool(hybrid_changes.get("instant_win"))
        has_numeric_signal = any(
            abs(float(hybrid_changes.get(k, 0))) > 1e-6
            for k in ("scammer", "expert", "alertness")
        )

        if has_instant_win:
            trust_changes["instant_win"] = hybrid_changes["instant_win"]

        # Hybrid 沒有實質變化時，不覆蓋 AI 分析結果（避免長期卡 50/50/50）
        if has_numeric_signal:
            trust_changes.update({
                "scammer": hybrid_changes.get("scammer", trust_changes.get("scammer", 0)),
                "expert": hybrid_changes.get("expert", trust_changes.get("expert", 0)),
                "alertness": hybrid_changes.get("alertness", trust_changes.get("alertness", 0)),
            })    
    log.info(
        f"[受害人模式] 信任度變化計算完成 - "
        f"scammer={trust_changes.get('scammer', 0):+.1f}, "
        f"expert={trust_changes.get('expert', 0):+.1f}, "
        f"alertness={trust_changes.get('alertness', 0):+.1f}"
    )
    
    return ai_responses, trust_changes


async def handle_scammer_mode(
    session,
    player_message: str,
    agent_service: AgentService
) -> tuple[List[Dict], Dict]:
    """
    處理騙徒模式（並行優化版）

    玩家扮演騙徒，AI 受害者和 AI 專家並行生成
    🔥 使用 asyncio.gather 並行生成
    """
    conversation_with_player = session.conversation_history + [{
        "role": "scammer",
        "content": player_message
    }]

    lang_instruction = _language_instruction(session.language)
    lang = session.language

    if lang == 'en-US':
        expert_context = (
            f"{lang_instruction}\n"
            f"The scammer said to the victim: {player_message}\n"
            f"As an anti-scam expert, warn the victim briefly (within 80 words)."
        )
        victim_context = (
            f"{lang_instruction}\n"
            f"The scammer said: {player_message}\n"
            f"As the victim, respond briefly (within 80 words)."
        )
    elif lang == 'ja-JP':
        expert_context = (
            f"{lang_instruction}\n"
            f"詐欺師が被害者に言いました：{player_message}\n"
            f"防詐欺の専門家として、被害者に簡潔に警告してください（80字以内）。"
        )
        victim_context = (
            f"{lang_instruction}\n"
            f"詐欺師が言いました：{player_message}\n"
            f"被害者として、簡潔に返答してください（80字以内）。"
        )
    elif lang == 'zh-CN':
        expert_context = (
            f"{lang_instruction}\n"
            f"骗徒对受害者说：{player_message}\n"
            f"作为防诈专家，请简短警告受害者（80字内）。"
        )
        victim_context = (
            f"{lang_instruction}\n"
            f"骗徒说：{player_message}\n"
            f"作为受害者，请简短回应（80字内）。"
        )
    else:  # zh-HK default
        expert_context = (
            f"{lang_instruction}\n"
            f"騙徒對受害者說：{player_message}\n"
            f"請用粵語簡短警告受害者（80字內）。"
        )
        victim_context = (
            f"{lang_instruction}\n"
            f"騙徒說：{player_message}\n"
            f"你作為受害者，如何簡短回應（80字內）？"
        )

    # 🔥 並行生成
    log.info(f"[RPGv2] 並行生成受害者+專家回應...")
    expert_task = agent_service.generate_response(
        agent_type="expert",
        message=expert_context,
        conversation_history=conversation_with_player,
        check_consistency=True,
        track_performance=True
    )
    victim_task = agent_service.generate_response(
        agent_type="victim",
        message=victim_context,
        conversation_history=conversation_with_player,
        check_consistency=True,
        track_performance=True
    )

    expert_response, victim_response = await asyncio.gather(
        expert_task, victim_task
    )

    expert_reply = expert_response.get("reply", "...")
    victim_reply = victim_response.get("reply", "...")

    ai_responses = [
        {"role": "expert",  "content": expert_reply},
        {"role": "victim",  "content": victim_reply},
    ]

    log.info(f"[RPGv2] 專家: {expert_reply[:80]}...")
    log.info(f"[RPGv2] 受害者: {victim_reply[:80]}...")
    log.info(f"[RPGv2] ai_responses 數量: {len(ai_responses)}")
    
    # 計算信任度變化（使用AI語意判定 + HybridScamScoring 實際判定）
    trust_changes = await calculate_scammer_trust_changes(
        player_message,
        victim_reply,
        expert_reply,
        agent_service,
        conversation_with_player
    )
    hybrid_changes = _apply_hybrid_scorer(
        session.session_id,
        session.mode,
        player_message,
        scammer_msg=player_message,
        expert_msg=expert_reply,
        victim_msg=victim_reply,
    )
    if hybrid_changes:
        has_instant_win = bool(hybrid_changes.get("instant_win"))
        has_numeric_signal = any(
            abs(float(hybrid_changes.get(k, 0))) > 1e-6
            for k in ("scammer", "expert", "alertness")
        )

        if has_instant_win:
            trust_changes["instant_win"] = hybrid_changes["instant_win"]

        # Hybrid 沒有實質變化時，不覆蓋 AI 分析結果（避免長期卡 50/50/50）
        if has_numeric_signal:
            trust_changes.update({
                "scammer": hybrid_changes.get("scammer", trust_changes.get("scammer", 0)),
                "expert": hybrid_changes.get("expert", trust_changes.get("expert", 0)),
                "alertness": hybrid_changes.get("alertness", trust_changes.get("alertness", 0)),
            })    
    log.info(
        f"[騙徒模式] 信任度變化計算完成 - "
        f"scammer={trust_changes.get('scammer', 0):+.1f}, "
        f"expert={trust_changes.get('expert', 0):+.1f}, "
        f"alertness={trust_changes.get('alertness', 0):+.1f}"
    )
    
    return ai_responses, trust_changes


async def handle_expert_mode(
    session,
    player_message: str,
    agent_service: AgentService
) -> tuple[List[Dict], Dict]:
    """
    處理專家模式（並行優化版）

    玩家扮演防詐專家，AI 受害者和 AI 騙徒並行生成
    🔥 使用 asyncio.gather 並行生成
    """
    conversation_with_player = session.conversation_history + [{
        "role": "expert",
        "content": player_message
    }]

    lang_instruction = _language_instruction(session.language)
    lang = session.language

    if lang == 'en-US':
        victim_context = (
            f"{lang_instruction}\n"
            f"Expert advice: {player_message}\n"
            f"As the victim, respond briefly (within 80 words)."
        )
        scammer_context = (
            f"Scam type: {session.scam_type}\n"
            f"{lang_instruction}\n"
            f"The expert said to the victim: {player_message}\n"
            f"Continue the scam and counter the expert (within 80 words)."
        )
    elif lang == 'ja-JP':
        victim_context = (
            f"{lang_instruction}\n"
            f"専門家のアドバイス：{player_message}\n"
            f"被害者として、簡潔に返答してください（80字以内）。"
        )
        scammer_context = (
            f"詐欺の種類：{session.scam_type}\n"
            f"{lang_instruction}\n"
            f"専門家が被害者に言いました：{player_message}\n"
            f"詐欺を続けて専門家に反論してください（80字以内）。"
        )
    elif lang == 'zh-CN':
        victim_context = (
            f"{lang_instruction}\n"
            f"专家建议：{player_message}\n"
            f"作为受害者，请简短回应（80字内）。"
        )
        scammer_context = (
            f"诈骗类型：{session.scam_type}\n"
            f"{lang_instruction}\n"
            f"专家对受害者说：{player_message}\n"
            f"继续诈骗并反击专家（80字内）。"
        )
    else:  # zh-HK default
        victim_context = (
            f"{lang_instruction}\n"
            f"專家建議：{player_message}\n"
            f"你作為受害者，如何簡短回應（100字內）？"
        )
        scammer_context = (
            f"騙案類型：{session.scam_type}\n"
            f"{lang_instruction}\n"
            f"專家對受害者說：{player_message}\n"
            f"繼續詐騙並反擊專家（100字內）。"
        )

    # 🔥 並行生成
    log.info(f"[RPGv2] 並行生成受害者+騙徒回應...")
    victim_task = agent_service.generate_response(
        agent_type="victim",
        message=victim_context,
        conversation_history=conversation_with_player,
        check_consistency=True,
        track_performance=True
    )
    scammer_task = agent_service.generate_response(
        agent_type="scammer",
        message=scammer_context,
        conversation_history=conversation_with_player,
        check_consistency=True,
        track_performance=True
    )

    victim_response, scammer_response = await asyncio.gather(
        victim_task, scammer_task
    )

    victim_reply = victim_response.get("reply", "...")
    scammer_reply = scammer_response.get("reply", "...")

    ai_responses = [
        {"role": "victim",  "content": victim_reply},
        {"role": "scammer", "content": scammer_reply},
    ]

    log.info(f"[RPGv2] 受害者: {victim_reply[:80]}...")
    log.info(f"[RPGv2] 騙徒: {scammer_reply[:80]}...")
    log.info(f"[RPGv2] ai_responses 數量: {len(ai_responses)}")
    
    # 計算信任度變化（使用AI語意判定 + HybridScamScoring 實際判定）
    trust_changes = await calculate_expert_trust_changes(
        player_message,
        scammer_reply,
        victim_reply,
        agent_service,
        conversation_with_player
    )
    hybrid_changes = _apply_hybrid_scorer(
        session.session_id,
        session.mode,
        player_message,
        scammer_msg=scammer_reply,
        expert_msg=player_message,
        victim_msg=victim_reply,
    )
    if hybrid_changes:
        has_instant_win = bool(hybrid_changes.get("instant_win"))
        has_numeric_signal = any(
            abs(float(hybrid_changes.get(k, 0))) > 1e-6
            for k in ("scammer", "expert", "alertness")
        )

        if has_instant_win:
            trust_changes["instant_win"] = hybrid_changes["instant_win"]

        # Hybrid 沒有實質變化時，不覆蓋 AI 分析結果（避免長期卡 50/50/50）
        if has_numeric_signal:
            trust_changes.update({
                "scammer": hybrid_changes.get("scammer", trust_changes.get("scammer", 0)),
                "expert": hybrid_changes.get("expert", trust_changes.get("expert", 0)),
                "alertness": hybrid_changes.get("alertness", trust_changes.get("alertness", 0)),
            })    
    log.info(
        f"[專家模式] 信任度變化計算完成 - "
        f"scammer={trust_changes.get('scammer', 0):+.1f}, "
        f"expert={trust_changes.get('expert', 0):+.1f}, "
        f"alertness={trust_changes.get('alertness', 0):+.1f}"
    )
    
    return ai_responses, trust_changes


async def check_instant_win_by_recorder(
    message: str, 
    role: str, 
    mode: str,
    agent_service: AgentService,
    conversation_history: List[Dict]
) -> Optional[Dict]:
    """
    使用 Recorder Agent 進行即時勝負判定（取代 ai_judgment_optimizer）
    
    Recorder 負責：
    1. 快速路徑判定（明確關鍵詞）
    2. AI 語意判定（模糊表達）
    3. 信任度變化分析
    4. 性能評分
    
    Args:
        message: 消息內容
        role: 角色 (player/victim)
        mode: 遊戲模式
        agent_service: AI服務
        conversation_history: 對話歷史
    
    Returns:
        Dict with instant_win, winner, reason
    """
    try:
        # 🔥 修復：短寒暄（如 hi / hello）不應觸發即時勝負
        if _is_short_greeting(message):
            return {
                "instant_win": False,
                "winner": None,
                "reason": ""
            }

        # 構建簡化的判定 prompt（只要求即時勝負判定）
        judge_prompt = f"""請快速判定以下對話是否達到即時勝負條件。

遊戲模式: {mode}
角色: {role}
消息: 「{message}」

請只回答以下格式的 JSON（不要有任何額外文字）：
{{
  "instant_win": true/false,
  "winner": "player"/"ai"/null,
  "reason": "原因說明"
}}

各模式勝負規則（必須嚴格遵守）：

【victim 模式 - 玩家扮演受害人】
- 玩家說「同意/好/可以/提供資料/給錢/轉帳」等配合騙徒 → instant_win=true, winner="ai"（玩家被騙，AI騙徒勝）
- 玩家說「拒絕/報警/識破/不信/掛線」等 → instant_win=true, winner="player"（玩家識破，玩家勝）
- 態度不明確 → instant_win=false

【scammer 模式 - 玩家扮演騙徒】
- AI受害者說「同意/好/可以/提供資料/給錢」等被騙 → instant_win=true, winner="player"（玩家騙徒勝）
- AI受害者說「拒絕/報警/識破」等 → instant_win=true, winner="ai"（防詐成功，AI勝）
- 態度不明確 → instant_win=false

【expert 模式 - 玩家扮演專家】
- AI受害者說「明白/聽你/拒絕騙徒/報警」等聽從建議 → instant_win=true, winner="player"（玩家專家勝）
- AI受害者說「同意騙徒/提供資料/給錢」等不聽建議 → instant_win=true, winner="ai"（防詐失敗，AI勝）
- 態度不明確 → instant_win=false

⚠️ 注意：單字「好」在 victim 模式下 = 同意騙徒 → winner="ai"

請直接輸出 JSON："""
        
        # 調用 Recorder（使用 expert agent 作為判定器）
        judge_response = await agent_service.generate_response(
            agent_type="expert",
            message=judge_prompt,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        response_text = judge_response.get("reply", "").strip()
        
        # 清理可能的 markdown 標記
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # 修復被截斷的 JSON（找到最後一個完整的 } 位置）
        import json
        # 嘗試直接解析，失敗則嘗試截取到最後一個 }
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # 找到最後一個 } 並截取
            last_brace = response_text.rfind('}')
            if last_brace != -1:
                response_text = response_text[:last_brace + 1]
            result = json.loads(response_text)
        
        if result.get("instant_win"):
            log.info(
                f"[Recorder判定] 模式={mode}, 消息={message[:50]}..., "
                f"判定結果={result['winner']}勝出, 原因={result['reason']}"
            )
        
        return result
        
    except json.JSONDecodeError as e:
        log.error(f"[Recorder判定] JSON 解析失敗: {e}")
        log.error(f"原始回應: {response_text[:200]}...")
        # 降級：返回繼續遊戲
        return {
            "instant_win": False,
            "winner": None,
            "reason": ""
        }
    except Exception as e:
        log.error(f"[Recorder判定] 錯誤: {str(e)}")
        # 降級：返回繼續遊戲
        return {
            "instant_win": False,
            "winner": None,
            "reason": ""
        }


async def check_instant_win_condition_by_ai(
    message: str, 
    role: str, 
    mode: str,
    agent_service: AgentService,
    conversation_history: List[Dict]
) -> Dict:
    """
    舊版 AI 判定函數（已被 check_instant_win_by_recorder 取代）
    保留作為降級備用
    """
    # 直接調用新版 Recorder 判定
    result = await check_instant_win_by_recorder(
        message, role, mode, agent_service, conversation_history
    )
    return result or {
        "instant_win": False,
        "winner": None,
        "reason": ""
    }


def check_instant_win_condition(message: str, role: str, mode: str) -> Dict:
    """
    檢查即時勝負條件
    
    Args:
        message: 消息內容
        role: 角色 (player/victim)
        mode: 遊戲模式
    
    Returns:
        Dict with instant_win, winner, reason
    """
    result = {
        "instant_win": False,
        "winner": None,
        "reason": ""
    }
    
    # 🔥 受害人模式：檢查玩家（受害人）的回應
    if mode == "victim" and role == "player":
        # 玩家勝出條件：識破騙局並報警
        victim_win_keywords = [
            # 報警（普通話）
            "報警", "報案", "打999", "打110", "報警察",
            "我要報警", "我會報警", "去報警",
            # 報警（廣東話）
            "報警啦", "報差", "報差佬", "打999", "打去報警",
            "去報警", "去報案", "搵警察", "搵差人",
            # 識破騙局（普通話）
            "這是騙局", "你是騙子", "我不相信", "這是詐騙",
            # 識破騙局（廣東話）
            "你呃人", "你呃我", "呃人", "騙子", "騙徒",
            "呢個係騙局", "係呃人", "唔信你", "唔會信你"
        ]
        
        if any(keyword in message for keyword in victim_win_keywords):
            result["instant_win"] = True
            result["winner"] = "player"
            result["reason"] = "成功識破騙局！玩家拒絕被騙並報警"
            return result
        
        # 玩家失敗條件：同意提供資料或金錢
        victim_fail_keywords = [
            # 提供資料（普通話）
            "會提供資料", "提供資料", "給你資料",
            # 提供資料（廣東話）
            "俾資料", "俾資料你", "俾你資料", "畀資料", "畀你資料",
            # 金錢交易（普通話）
            "會俾錢", "俾錢", "轉帳", "匯款", "付款", "給錢",
            "會轉帳", "會匯款", "會付款",
            # 金錢交易（廣東話）
            "俾錢你", "畀錢", "畀錢你", "過數", "過數俾你", "轉數", "轉數俾你",
            "入數", "入錢", "俾現金", "畀現金",
            # 敏感資料
            "銀行帳號", "信用卡號", "密碼", "驗證碼",
            "我的帳號", "我的密碼", "我的卡號"
        ]
        
        if any(keyword in message for keyword in victim_fail_keywords):
            result["instant_win"] = True
            result["winner"] = "ai"
            result["reason"] = "被騙成功！玩家同意提供資料或金錢"
            return result
    
    # 騙徒模式：檢查AI受害者的回應
    elif mode == "scammer" and role == "victim":
        # 騙徒勝出條件：受害者同意提供資料或金錢
        scam_success_keywords = [
            # 提供資料（普通話）
            "會提供資料", "提供資料", "給你資料",
            # 提供資料（廣東話）
            "俾資料", "俾資料你", "俾你資料", "畀資料", "畀你資料",
            # 金錢交易（普通話）
            "會俾錢", "俾錢", "轉帳", "匯款", "付款", "給錢",
            "會轉帳", "會匯款", "會付款",
            # 金錢交易（廣東話）
            "俾錢你", "畀錢", "畀錢你", "過數", "過數俾你", "轉數", "轉數俾你",
            "入數", "入錢", "俾現金", "畀現金",
            # 敏感資料
            "銀行帳號", "信用卡號", "密碼", "驗證碼",
            "我的帳號", "我的密碼", "我的卡號",
            # 廣東話確認
            "得", "得啦", "冇問題", "好呀", "可以呀", "聽你講"
        ]
        
        if any(keyword in message for keyword in scam_success_keywords):
            result["instant_win"] = True
            result["winner"] = "player"
            result["reason"] = "騙徒成功！受害者同意提供資料或金錢"
            return result
        
        # 防詐成功條件：受害者拒絕並報警
        anti_scam_success_keywords = [
            # 拒絕提供資料（普通話）
            "不會提供資料", "不提供資料", "不給資料",
            # 拒絕提供資料（廣東話）
            "唔俾資料", "唔會俾資料", "唔畀資料", "唔會畀資料",
            "唔提供資料", "唔會提供資料", "唔俾你資料",
            # 拒絕金錢（普通話）
            "不會俾錢", "不俾錢", "不會轉帳", "不會匯款", "不會付款",
            # 拒絕金錢（廣東話）
            "唔俾錢", "唔會俾錢", "唔畀錢", "唔會畀錢",
            "唔過數", "唔會過數", "唔轉數", "唔會轉數",
            "唔入數", "唔會入數", "唔俾錢你", "唔畀錢你",
            # 報警（普通話）
            "報警", "報案", "打999", "打110", "報警察",
            "我要報警", "我會報警", "去報警",
            # 報警（廣東話）
            "報警啦", "報差", "報差佬", "打999", "打去報警",
            "去報警", "去報案", "搵警察", "搵差人",
            # 識破騙局（普通話）
            "相信專家", "聽專家", "專家說", "這是騙局", "你是騙子",
            # 識破騙局（廣東話）
            "你呃人", "你呃我", "呃人", "騙子", "騙徒",
            "呢個係騙局", "係呃人", "唔信你", "唔會信你",
            "信專家", "聽專家講", "專家講得啱"
        ]
        
        if any(keyword in message for keyword in anti_scam_success_keywords):
            result["instant_win"] = True
            result["winner"] = "ai"
            result["reason"] = "防詐成功！受害者識破騙局並拒絕配合"
            return result
    
    # 專家模式：檢查AI受害者的回應
    elif mode == "expert" and role == "victim":
        # 防詐成功條件：受害者聽從專家建議
        expert_success_keywords = [
            # 相信專家（普通話）
            "相信專家", "聽專家", "專家說得對", "謝謝專家",
            # 相信專家（廣東話）
            "信專家", "聽專家講", "專家講得啱", "多謝專家",
            "專家啱", "聽你講", "信你", "跟你講",
            # 拒絕提供資料（普通話）
            "不會提供資料", "不提供資料", "不給資料",
            # 拒絕提供資料（廣東話）
            "唔俾資料", "唔會俾資料", "唔畀資料", "唔會畀資料",
            "唔提供資料", "唔會提供資料",
            # 拒絕金錢（普通話）
            "不會俾錢", "不俾錢", "不會轉帳", "不會匯款",
            # 拒絕金錢（廣東話）
            "唔俾錢", "唔會俾錢", "唔畀錢", "唔會畀錢",
            "唔過數", "唔會過數", "唔轉數", "唔會轉數",
            # 報警（普通話）
            "報警", "報案", "打999", "打110",
            # 報警（廣東話）
            "報警啦", "報差", "報差佬", "搵警察", "搵差人",
            # 識破騙局（普通話）
            "我明白了", "我知道是騙局", "這是詐騙",
            # 識破騙局（廣東話）
            "我明白", "我知道係騙局", "呢個係騙局", "係呃人",
            "知道啦", "明白啦", "唔會信佢", "唔信佢"
        ]
        
        if any(keyword in message for keyword in expert_success_keywords):
            result["instant_win"] = True
            result["winner"] = "player"
            result["reason"] = "防詐成功！受害者聽從專家建議，拒絕被騙"
            return result
        
        # 防詐失敗條件：受害者被騙
        expert_fail_keywords = [
            # 提供資料（普通話）
            "會提供資料", "提供資料", "給你資料",
            # 提供資料（廣東話）
            "俾資料", "俾資料你", "俾你資料", "畀資料", "畀你資料",
            # 金錢交易（普通話）
            "會俾錢", "俾錢", "轉帳", "匯款", "付款",
            # 金錢交易（廣東話）
            "俾錢你", "畀錢", "畀錢你", "過數", "過數俾你",
            "轉數", "轉數俾你", "入數", "入錢",
            # 敏感資料
            "銀行帳號", "信用卡號", "密碼", "驗證碼",
            # 不相信專家（普通話）
            "不相信專家", "專家錯了", "我相信他",
            # 不相信專家（廣東話）
            "唔信專家", "唔相信專家", "專家錯", "專家講錯",
            "我信佢", "信佢", "聽佢講", "跟佢講"
        ]
        
        if any(keyword in message for keyword in expert_fail_keywords):
            result["instant_win"] = True
            result["winner"] = "ai"
            result["reason"] = "防詐失敗！受害者不聽勸告，被騙成功"
            return result
    
    return result


def _is_refusal_of_sensitive_info(message: str) -> bool:
    """判斷是否在拒絕提供敏感資料（避免被 '密碼' 等字眼誤判）"""
    text = (message or "").lower().strip()

    # 常見字形/用字正規化
    normalized = (
        text.replace("给", "給")
            .replace("比", "俾")
            .replace("戶口", "帳號")
            .replace("账号", "帳號")
    )

    refusal_markers = [
        "不會", "不会", "不", "唔", "唔會", "拒絕", "拒绝", "不要", "唔好", "唔會俾", "不會俾", "不會給", "不會畀"
    ]
    sensitive_markers = [
        "資料", "信息", "帳號", "账号", "銀行", "密碼", "密码", "驗證碼", "验证码", "卡號", "信用卡"
    ]

    has_refusal = any(k in normalized for k in refusal_markers)
    has_sensitive = any(k in normalized for k in sensitive_markers)
    return has_refusal and has_sensitive


def _is_short_greeting(message: str) -> bool:
    """判斷是否為過短寒暄語（避免被誤判成勝負）"""
    text = (message or "").strip().lower()
    if not text:
        return True

    normalized = ''.join(ch for ch in text if ch.isalnum())
    short_greetings = {
        "hi", "hey", "hello", "yo", "ok", "okay",
        "哈囉", "你好", "嗨", "安", "在嗎", "喂", "hello"
    }

    return len(normalized) <= 3 or normalized in short_greetings


def _extract_last_int(segment: str) -> int:
    """從一段文字中提取最後一個整數（避免抓到 1. 2. 這類編號）"""
    import re

    numbers = re.findall(r'-?\d+', segment)
    if not numbers:
        raise ValueError(f"無法從段落提取數字: {segment}")
    return int(numbers[-1])


async def calculate_victim_trust_changes(
    victim_msg: str,
    scammer_msg: str,
    expert_msg: str,
    agent_service: AgentService,
    conversation_history: List[Dict]
) -> Dict:
    """計算受害人模式的信任度變化（使用 Recorder AI 判定）"""
    changes = {
        "scammer": 0,
        "expert": 0,
        "alertness": 0,
        "instant_win": None
    }
    
    # 🔥 優先使用關鍵詞快速判定（更可靠）
    # 修復：先檢查「拒絕提供敏感資料」語義，避免被 "密碼/銀行" 字眼反向誤判
    if _is_refusal_of_sensitive_info(victim_msg):
        changes["instant_win"] = {
            "instant_win": True,
            "winner": "player",
            "reason": "受害者明確拒絕提供敏感資料"
        }
        changes["alertness"] += 100
        changes["scammer"] -= 100
        changes["expert"] += 50
        log.info(f"[即時勝負-受害人模式] 拒絕敏感資料命中: {victim_msg[:50]}...")
        return changes

    instant_result = check_instant_win_condition(victim_msg, "player", "victim")
    
    # 如果關鍵詞沒有命中，再使用 AI 判定
    # 🔥 修復：短寒暄（如 hi / hello）不觸發即時勝負 AI 判定
    if not instant_result.get("instant_win") and not _is_short_greeting(victim_msg):
        instant_result = await check_instant_win_by_recorder(
            victim_msg, 
            "player", 
            "victim",
            agent_service,
            conversation_history
        )
    
    if instant_result and instant_result.get("instant_win"):
        changes["instant_win"] = instant_result
        # 如果受害人識破騙局
        if instant_result["winner"] == "player":
            changes["alertness"] += 100
            changes["scammer"] -= 100
            changes["expert"] += 50
        # 如果受害人被騙
        else:
            changes["alertness"] -= 100
            changes["scammer"] += 100
            changes["expert"] -= 50
        
        log.info(
            f"[即時勝負-受害人模式] 玩家說: {victim_msg[:50]}... | "
            f"勝者={instant_result['winner']}, 原因={instant_result['reason']}"
        )
        return changes
    
    # 使用AI分析受害人的判斷
    analysis_prompt = f"""
你是防詐騙分析專家，請分析以下三方對話中受害人的判斷。

受害人說：「{victim_msg}」
騙徒說：「{scammer_msg}」
專家建議：「{expert_msg}」

請評估（從騙徒的角度）：
1. 受害人是否聽從專家建議（-10到+10，正數=聽從專家，負數=不聽專家）
2. 騙徒的成功程度（-10到+10，正數=騙徒成功，負數=騙徒失敗）
3. 專家的影響力（-10到+10，正數=專家有效，負數=專家無效）
4. 受害人的警覺性變化（-10到+10，正數=更警覺，負數=更輕信）

只需回答四個數字，格式：聽從專家,騙徒成功度,專家影響力,警覺性
例如：-8,7,-5,-6（受害者不聽專家，騙徒很成功，專家無效，警覺性下降）
例如：9,-8,8,10（受害者聽專家，騙徒失敗，專家有效，警覺性提升）
"""
    
    try:
        analysis_response = await agent_service.generate_response(
            agent_type="expert",
            message=analysis_prompt,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        analysis = analysis_response.get("reply", "0,0,0,0").strip()
        
        # 🔥 修復：提取第一行的數字（忽略後續說明文字）
        first_line = analysis.split('\n')[0].strip()
        parts = first_line.split(",")
        
        if len(parts) >= 4:
            follow_expert = _extract_last_int(parts[0].strip())
            scammer_success = _extract_last_int(parts[1].strip())
            expert_influence = _extract_last_int(parts[2].strip())
            alertness_change = _extract_last_int(parts[3].strip())
            
            # 🔥 修復：直接使用「騙徒成功度」作為騙徒評分變化
            changes["scammer"] = scammer_success
            changes["expert"] = expert_influence
            changes["alertness"] = alertness_change
            
            log.info(
                f"[AI分析-受害人模式] 受害人說: {victim_msg[:50]}... | "
                f"聽從專家={follow_expert}, 騙徒成功度={scammer_success}, "
                f"專家影響={expert_influence}, 警覺性={alertness_change} | "
                f"最終變化: scammer={changes['scammer']}, expert={changes['expert']}, alertness={changes['alertness']}"
            )
    except Exception as e:
        log.error(f"[AI分析] 錯誤: {str(e)}")
        # 降級到簡單規則
        # 🔥 修復：當受害者說「會提供資料」等，應該增加騙徒評分
        if any(kw in victim_msg for kw in ["會提供資料", "提供資料", "俾資料", "畀資料", 
                                            "會俾錢", "俾錢", "畀錢", "轉帳", "匯款", "過數",
                                            "好的", "可以", "明白", "同意", "得", "冇問題"]):
            changes["scammer"] += 8  # 騙徒成功
            changes["alertness"] -= 5
            changes["expert"] -= 3
        elif any(kw in victim_msg for kw in ["不相信", "懷疑", "報警", "拒絕", "唔信", "唔俾"]):
            changes["alertness"] += 10
            changes["scammer"] -= 8  # 騙徒失敗
            changes["expert"] += 5
    
    return changes


async def calculate_scammer_trust_changes(
    player_msg: str, 
    victim_reply: str,
    expert_reply: str,
    agent_service: AgentService,
    conversation_history: List[Dict]
) -> Dict:
    """計算騙徒模式的信任度變化（使用 Recorder AI 判定）"""
    changes = {
        "scammer": 0,
        "expert": 0,
        "alertness": 0,
        "instant_win": None
    }
    
    # 🔥 優先使用關鍵詞快速判定（更可靠）
    instant_result = check_instant_win_condition(victim_reply, "victim", "scammer")
    
    # 如果關鍵詞沒有命中，再使用 AI 判定
    if not instant_result.get("instant_win"):
        instant_result = await check_instant_win_by_recorder(
            victim_reply, 
            "victim", 
            "scammer",
            agent_service,
            conversation_history
        )
    
    if instant_result and instant_result.get("instant_win"):
        changes["instant_win"] = instant_result
        # 如果騙徒勝出，大幅提升信任度
        if instant_result["winner"] == "player":
            changes["scammer"] += 100
            changes["alertness"] -= 50
        # 如果防詐成功，大幅降低信任度
        else:
            changes["scammer"] -= 100
            changes["alertness"] += 100
        
        log.info(
            f"[即時勝負-騙徒模式] AI受害者說: {victim_reply[:50]}... | "
            f"勝者={instant_result['winner']}, 原因={instant_result['reason']}"
        )
        return changes
    
    # 使用AI分析玩家策略和信任度變化（考慮專家介入）
    analysis_prompt = f"""
你是防詐騙分析專家，請分析以下對話中騙徒的策略效果。

騙徒說：「{player_msg}」
受害者回應：「{victim_reply}」
專家建議：「{expert_reply}」

請評估：
1. 騙徒使用了什麼策略？（權威/緊急/情感/利益）
2. 受害者的信任度變化（-10到+10）
3. 受害者的警覺性變化（-10到+10）
4. 專家建議的影響（-10到+10）

只需回答四個數字，格式：策略得分,信任度變化,警覺性變化,專家影響
例如：8,5,-3,-4
"""
    
    try:
        analysis_response = await agent_service.generate_response(
            agent_type="expert",
            message=analysis_prompt,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        analysis = analysis_response.get("reply", "0,0,0,0").strip()
        
        # 🔥 修復：提取第一行的數字（忽略後續說明文字）
        first_line = analysis.split('\n')[0].strip()
        parts = first_line.split(",")
        
        if len(parts) >= 4:
            strategy_score = _extract_last_int(parts[0].strip())
            trust_change = _extract_last_int(parts[1].strip())
            alertness_change = _extract_last_int(parts[2].strip())
            expert_impact = _extract_last_int(parts[3].strip())
            
            # 🔥 修復邏輯：
            # trust_change: AI分析的受害者對騙徒的信任變化（-10到+10）
            # expert_impact: 專家建議的影響（負數=有效降低騙徒效果，正數=無效）
            # 
            # 正確邏輯：trust_change 已經是騙徒的基礎效果
            # expert_impact 是負數時（如-4），表示專家有效，應該進一步降低騙徒信任度
            # expert_impact 是正數時（如+2），表示專家無效，騙徒效果不受影響或增強
            #
            # 所以應該：changes["scammer"] = trust_change + expert_impact
            # 例如：trust_change=+5（騙徒有效）, expert_impact=-4（專家有效）
            #       最終 = 5 + (-4) = +1（騙徒效果被專家削弱）
            
            changes["scammer"] = trust_change + expert_impact
            changes["alertness"] = alertness_change - expert_impact  # 專家影響越負，警覺性越高
            
            log.info(
                f"[AI分析-騙徒模式] 玩家說: {player_msg[:50]}... | "
                f"策略={strategy_score}, 信任變化={trust_change}, "
                f"警覺變化={alertness_change}, 專家影響={expert_impact} | "
                f"最終變化: scammer={changes['scammer']}, alertness={changes['alertness']}"
            )
    except Exception as e:
        log.error(f"[AI分析] 錯誤: {str(e)}")
        # 降級到簡單規則
        if any(kw in player_msg for kw in ["警察", "銀行", "政府", "官方"]):
            changes["scammer"] += 8
            changes["alertness"] -= 5
        if any(kw in player_msg for kw in ["立即", "馬上", "緊急", "快"]):
            changes["scammer"] += 5
            changes["alertness"] -= 3
        # 專家的警告會降低騙徒效果
        if any(kw in expert_reply for kw in ["小心", "詐騙", "騙局", "不要"]):
            changes["scammer"] -= 3
            changes["alertness"] += 5
    
    return changes


async def calculate_expert_trust_changes(
    expert_msg: str, 
    scammer_msg: str, 
    victim_reply: str,
    agent_service: AgentService,
    conversation_history: List[Dict]
) -> Dict:
    """計算專家模式的信任度變化（使用 Recorder AI 判定）"""
    changes = {
        "scammer": 0,
        "expert": 0,
        "alertness": 0,
        "instant_win": None
    }
    
    # 🔥 優先使用關鍵詞快速判定（更可靠）
    instant_result = check_instant_win_condition(victim_reply, "victim", "expert")
    
    # 如果關鍵詞沒有命中，再使用 AI 判定
    if not instant_result.get("instant_win"):
        instant_result = await check_instant_win_by_recorder(
            victim_reply, 
            "victim", 
            "expert",
            agent_service,
            conversation_history
        )
    
    if instant_result and instant_result.get("instant_win"):
        changes["instant_win"] = instant_result
        # 如果防詐成功，大幅提升警覺性
        if instant_result["winner"] == "player":
            changes["expert"] += 100
            changes["alertness"] += 100
            changes["scammer"] -= 100
        # 如果防詐失敗，大幅降低警覺性
        else:
            changes["expert"] -= 100
            changes["alertness"] -= 100
            changes["scammer"] += 100
        
        log.info(
            f"[即時勝負-專家模式] AI受害者說: {victim_reply[:50]}... | "
            f"勝者={instant_result['winner']}, 原因={instant_result['reason']}"
        )
        return changes
    
    # 使用AI分析專家建議效果
    analysis_prompt = f"""
你是防詐騙分析專家，請分析以下三方對話的效果。

專家建議：「{expert_msg}」
騙徒說：「{scammer_msg}」
受害者回應：「{victim_reply}」

請評估：
1. 專家建議的有效性（-10到+10）
2. 受害者對專家的信任變化（-10到+10）
3. 受害者對騙徒的信任變化（-10到+10）
4. 受害者的警覺性變化（-10到+10）

只需回答四個數字，格式：專家有效性,對專家信任,對騙徒信任,警覺性
例如：8,7,-5,10
"""
    
    try:
        analysis_response = await agent_service.generate_response(
            agent_type="expert",
            message=analysis_prompt,
            conversation_history=[],
            check_consistency=False,
            track_performance=False
        )
        
        analysis = analysis_response.get("reply", "0,0,0,0").strip()
        
        # 🔥 修復：提取第一行的數字（忽略後續說明文字）
        first_line = analysis.split('\n')[0].strip()
        parts = first_line.split(",")
        
        if len(parts) >= 4:
            expert_effectiveness = _extract_last_int(parts[0].strip())
            expert_trust = _extract_last_int(parts[1].strip())
            scammer_trust = _extract_last_int(parts[2].strip())
            alertness_change = _extract_last_int(parts[3].strip())
            
            changes["expert"] = expert_trust
            changes["scammer"] = scammer_trust
            changes["alertness"] = alertness_change
            
            log.info(
                f"[AI分析-專家模式] 玩家說: {expert_msg[:50]}... | "
                f"專家有效性={parts[0].strip()}, 對專家信任={changes['expert']}, "
                f"對騙徒信任={changes['scammer']}, 警覺性={changes['alertness']}"
            )
    except Exception as e:
        log.error(f"[AI分析] 錯誤: {str(e)}")
        # 降級到簡單規則
        if any(kw in expert_msg for kw in ["詐騙", "騙局", "小心", "不要"]):
            changes["expert"] += 8
            changes["alertness"] += 10
            changes["scammer"] -= 5
        if any(kw in victim_reply for kw in ["明白", "謝謝", "我知道"]):
            changes["expert"] += 10
            changes["alertness"] += 8
            changes["scammer"] -= 5
    
    return changes


def calculate_auto_trust_changes(scammer_msg: str, victim_reply: str) -> Dict:
    """計算自動模式的信任度變化"""
    changes = {
        "scammer": 0,
        "alertness": 0
    }
    
    # 分析受害者的正面回應
    positive_keywords = ["好", "可以", "是", "對", "沒問題", "明白", "知道"]
    if any(keyword in victim_reply for keyword in positive_keywords):
        changes["scammer"] += 5
        changes["alertness"] -= 3
    
    # 分析受害者的懷疑態度
    suspicious_keywords = ["不", "懷疑", "為什麼", "怎麼", "真的嗎", "確定"]
    if any(keyword in victim_reply for keyword in suspicious_keywords):
        changes["scammer"] -= 5
        changes["alertness"] += 5
    
    # 分析騙徒使用的策略
    scammer_tactics = ["警察", "銀行", "政府", "緊急", "立即", "馬上"]
    if any(keyword in scammer_msg for keyword in scammer_tactics):
        changes["scammer"] += 3
        changes["alertness"] -= 2
    
    return changes
