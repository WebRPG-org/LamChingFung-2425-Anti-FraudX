import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Optional
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from scripts.real_dialogue_runner import RealDialogueRunner
from services.rag_service import query_db
from utils.logger import log

router = APIRouter()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
# Immediate stop flags
stop_flags: Dict[str, bool] = {}
heartbeat_tasks: Dict[str, asyncio.Task] = {}
event_buffers: Dict[str, list] = {}
event_seqs: Dict[str, int] = {}

def should_stop(simulation_id: str) -> bool:
    return stop_flags.get(simulation_id, False)

def classify_outcome(conversation_history) -> str:
    """已棄用：所有判定邏輯交由記錄人分析決定"""
    return "FAILURE"  # 預設為FAILURE，避免UNKNOWN

class SimulationRequest(BaseModel):
    victim_persona: Optional[str] = "average"
    scam_tactic: Optional[str] = "WhatsApp 對話詐騙"
    mode: Optional[str] = "fast"  # fast | demo

class SimulationResponse(BaseModel):
    simulation_id: str
    websocket_url: str

@router.post("/simulation/start", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest):
    """啟動一次新的模擬"""
    simulation_id = str(uuid.uuid4())
    websocket_url = f"/ws/simulation/{simulation_id}"
    
    log.info(f"Starting simulation {simulation_id} with victim_persona: {request.victim_persona}")
    
# Launch simulation in background
    asyncio.create_task(run_simulation_async(
        simulation_id,
        victim_persona=request.victim_persona,
        scam_tactic=request.scam_tactic,
        mode=request.mode or "fast",
    ))
    
    return SimulationResponse(
        simulation_id=simulation_id,
        websocket_url=websocket_url
    )

@router.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    """處理模擬的 WebSocket 連接"""
    await websocket.accept()
    active_connections[simulation_id] = websocket
# Replay a few recent events (avoid blank UI after reconnect)
    try:
        buf = event_buffers.get(simulation_id) or []
        # Only replay the last 10
        for evt in buf[-10:]:
            try:
                await websocket.send_json(evt)
            except Exception:
                break
    except Exception:
        pass
    # Start heartbeat to prevent idle disconnects mid-session
    async def _heartbeat(sim_id: str):
        try:
            while sim_id in active_connections:
                try:
                    await send_websocket_event(sim_id, "heartbeat", {"ts": datetime.now().isoformat()})
                except Exception:
                    break
                await asyncio.sleep(15)
        except Exception:
            pass
    try:
        # Cancel previous heartbeat if any
        old = heartbeat_tasks.get(simulation_id)
        if old and not old.done():
            old.cancel()
        heartbeat_tasks[simulation_id] = asyncio.create_task(_heartbeat(simulation_id))
    except Exception:
        pass
    
    log.info(f"WebSocket connected for simulation: {simulation_id}")
    
    try:
        # Send connection_success
        await websocket.send_json({
            "event_type": "connection_success",
            "payload": {"simulation_id": simulation_id}
        })
        
        # Keep connection open to handle control messages
        while True:
            msg = await websocket.receive_text()
            try:
                if msg.strip().lower() == 'stop_now':
                    stop_flags[simulation_id] = True
                    await websocket.send_json({"event_type": "ack", "payload": {"command": "stop_now", "ok": True}})
                else:
                    data = json.loads(msg)
                    cmd = isinstance(data, dict) and data.get('command')
                    if cmd == 'stop_now':
                        stop_flags[simulation_id] = True
                        await websocket.send_json({"event_type": "ack", "payload": {"command": "stop_now", "ok": True}})
                    elif cmd == 'replay':
                        # Replay recent events (up to 20)
                        buf = event_buffers.get(simulation_id) or []
                        for evt in buf[-20:]:
                            try:
                                await websocket.send_json(evt)
                            except Exception:
                                break
                        await websocket.send_json({"event_type": "ack", "payload": {"command": "replay", "ok": True}})
            except Exception:
                # Ignore unparseable messages
                pass
            
    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected for simulation: {simulation_id}")
        if simulation_id in active_connections:
            del active_connections[simulation_id]
        try:
            task = heartbeat_tasks.pop(simulation_id, None)
            if task and not task.done():
                task.cancel()
        except Exception:
            pass
    except Exception as e:
        log.error(f"WebSocket error for simulation {simulation_id}: {e}")
        if simulation_id in active_connections:
            del active_connections[simulation_id]
        try:
            task = heartbeat_tasks.pop(simulation_id, None)
            if task and not task.done():
                task.cancel()
        except Exception:
            pass

async def send_websocket_event(simulation_id: str, event_type: str, payload: dict):
    """Send a WebSocket event"""
    # Buffer events for reconnect replay
    try:
        seq = event_seqs.get(simulation_id, 0) + 1
        event_seqs[simulation_id] = seq
        evt = {"seq": seq, "event_type": event_type, "payload": payload}
        buf = event_buffers.get(simulation_id)
        if buf is None:
            buf = []
            event_buffers[simulation_id] = buf
        buf.append(evt)
        # Limit buffer size
        if len(buf) > 100:
            del buf[: len(buf) - 100]
    except Exception:
        pass
    if simulation_id in active_connections:
        try:
            # Yield to event loop to avoid idle disconnect on sync blocking
            await asyncio.sleep(0)
            await active_connections[simulation_id].send_json(evt)
        except Exception as e:
            log.error(f"Failed to send WebSocket event: {e}")

@router.get("/simulation/events/{simulation_id}")
async def get_simulation_events(simulation_id: str, since_seq: Optional[int] = None):
    buf = event_buffers.get(simulation_id) or []
    if since_seq is None:
        events = buf[-50:]  # avoid large one-shot payloads
    else:
        try:
            cutoff = int(since_seq)
        except Exception:
            cutoff = 0
        events = [e for e in buf if int(e.get('seq', 0)) > cutoff][-200:]
    next_seq = int(event_seqs.get(simulation_id, len(buf)))
    return {"events": events, "next_seq": next_seq}

async def run_simulation_async(simulation_id: str, victim_persona: str, scam_tactic: str, mode: str = "fast"):
    """在背景中運行模擬"""
    try:
        # Reset state to avoid leftovers from previous simulation
        try:
            stop_flags[simulation_id] = False
            event_buffers[simulation_id] = []
            event_seqs[simulation_id] = 0
        except Exception:
            pass
        # Use RealDialogueRunner (ADK + direct fallback)
        runner = RealDialogueRunner()
        ok = runner.initialize_agents(victim_persona=victim_persona)
        if not ok:
            raise RuntimeError("initialize_agents failed")

        # Wait for frontend WebSocket connect to avoid dropping events before connection
        for _ in range(50):  # wait up to 5 seconds
            if simulation_id in active_connections:
                break
            await asyncio.sleep(0.1)
        
        # Send simulation_start event
        await send_websocket_event(simulation_id, "simulation_start", {
            "simulation_id": simulation_id,
            "characters": [
                {"name": "專業騙徒", "persona_summary": "精通社會工程學的詐騙專家"},
                {"name": "受騙者", "persona_summary": f"角色類型: {victim_persona}"},
                {"name": "防騙專家", "persona_summary": "冷靜理性的防騙分析師"}
            ]
        })
        
        conversation_history = []
        max_turns = 8
    
        # Internal helper: enforce scammer stays in-character (rewrite if anti-scam/reveal wording is detected)
        async def _enforce_scammer_role(original_text: str, victim_turn_text: str | None = None, expert_turn_text: str | None = None) -> str:
            text = original_text or ""
            lower = text.lower()
            banned_core = ["詐騙", "騙局", "防騙", "舉報", "報警", "警方"]
            if any(k in text for k in banned_core) or any(k.replace(" ", "") in lower for k in ["唔好提供", "唔好輸入"]) or any(k in lower for k in ["don\'t", "do not"]):
                # Request rewrite with the same tactic; strictly forbid anti-scam/reveal wording
                rewrite_prompt = (
                    f"（請用廣東話）**你嘅回覆唔合格！** 你必須保持騙徒身份，嚴禁提醒對方防騙或揭露係騙局。\n"
                    f"**你嘅任務係呃錢，唔係幫人！**\n"
                    f"**受騙者剛才回應：** 『{victim_turn_text}』\n"
                    + (f"**防騙專家講咗：** 『{expert_turn_text}』\n" if expert_turn_text else "")
                    + f"**你要反駁專家，唔係附和佢！**\n"
                    f"請用『{scam_tactic}』手法重寫你嘅回覆，保持誘因/權威/緊急感，≤120字。"
                )
                rewritten = await runner.run_agent_with_adk(runner.scammer, rewrite_prompt, f"{simulation_id}_scammer_rewrite")
                return rewritten or original_text
            return original_text


        # Provide RAG hints in the initial turn to increase realism (not exposed to other agents)
        def _rag_bullets(query: str, n: int = 3) -> str:
            try:
                r = query_db(query, n_results=n)
                if not r or not r.get('documents'):
                    return ""
                docs = r['documents'][0]
                metas = r.get('metadatas', [[]])[0]
                lines = []
                for i, doc in enumerate(docs[:n]):
                    meta = metas[i] if i < len(metas) else {}
                    title = meta.get('title', 'N/A')
                    date = meta.get('date', 'N/A')
                    snippet = (doc or '')[:160]
                    lines.append(f"- {title}（{date}）：{snippet}")
                return "\n".join(lines)
            except Exception:
                return ""

        scammer_turn = await runner.run_agent_with_adk(
            runner.scammer,

            f"（請用廣東話）以『{scam_tactic}』為目標，自然地展開對話。"
            f"保持騙徒身份，但可以根據對方反應調整策略。"
            f"避免直接使用『詐騙』等敏感詞彙，但可以自然地建立信任關係。"
            f"根據不同騙案手法特點：愛情詐騙需要耐心建立關係，投資詐騙需要權威感，緊急詐騙需要緊迫感。",
            f"{simulation_id}_scammer_1"
        )
        scammer_turn = await _enforce_scammer_role(scammer_turn)
        conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn})
        
        await send_websocket_event(simulation_id, "agent_turn", {
            "character_name": "專業騙徒",
            "dialogue": scammer_turn
        })
        await send_websocket_event(simulation_id, "turn_progress", {
            "current_turn": 1,
            "max_turns": max_turns
        })
        await asyncio.sleep(0)
        if should_stop(simulation_id):

            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                save_dir = os.path.join(base_dir, 'training_data')
                os.makedirs(save_dir, exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                path = os.path.join(save_dir, filename)
                speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                outcome_now = "FAILURE"  # 早期停止，預設為失敗
                data_to_save = {
                    "analysis": {
                        "outcome": outcome_now,
                        "reason": "stopped_by_user",
                        "victim_persona": victim_persona,
                        "scam_tactic": scam_tactic,
                        "timestamp": datetime.now().isoformat(),
                        "total_turns": len(conversation_history),
                    },
                    "metadata": {
                        "simulation_id": simulation_id,
                        "mode": mode,
                        "source": "websocket_simulation_user_stop"
                    },
                    "conversation_history": conversation_history,
                    "dialogue": dialogue,
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            except Exception as se:
                log.error(f"save training data (user stop) failed: {se}")
                filename = None
            await send_websocket_event(simulation_id, "simulation_end", {
                "announcer": "用戶",
                "result_text": "立即停止",
                "outcome": outcome_now,
                "analysis": {"reason": "stopped_by_user"},
                "filename": locals().get('filename')
            })
            return
        if mode == "demo":
            await asyncio.sleep(random.uniform(3.0, 5.0))
        

        max_turns = 8
        for turn in range(2, max_turns + 1):

            if should_stop(simulation_id):
                break

            prompt_for_victim = (
                f"這是你剛收到的訊息：'{scammer_turn}'\n\n"
                "你只能以普通市民身份回覆，不可評論/總結/說教。包含情緒或猶疑點，可提出具體追問。"
            )
            victim_turn = await runner.run_agent_with_adk(runner.victim, prompt_for_victim, f"{simulation_id}_victim_{turn}")
            conversation_history.append({"speaker": "受騙者", "dialogue": victim_turn})

            await send_websocket_event(simulation_id, "agent_turn", {
                "character_name": "受騙者",
                "dialogue": victim_turn
            })
            await send_websocket_event(simulation_id, "turn_progress", {
                "current_turn": turn,
                "max_turns": max_turns
            })
            await asyncio.sleep(0)
            if should_stop(simulation_id):
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    save_dir = os.path.join(base_dir, 'training_data')
                    os.makedirs(save_dir, exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                    path = os.path.join(save_dir, filename)
                    speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                    dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                    outcome_now2 = "FAILURE"  # 早期停止，預設為失敗
                    data_to_save = {
                        "analysis": {
                            "outcome": outcome_now2,
                            "reason": "stopped_by_user",
                            "victim_persona": victim_persona,
                            "scam_tactic": scam_tactic,
                            "timestamp": datetime.now().isoformat(),
                            "total_turns": len(conversation_history),
                        },
                        "metadata": {
                            "simulation_id": simulation_id,
                            "mode": mode,
                            "source": "websocket_simulation_user_stop"
                        },
                        "conversation_history": conversation_history,
                        "dialogue": dialogue,
                    }
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                except Exception as se:
                    log.error(f"save training data (user stop) failed: {se}")
                    filename = None
                await send_websocket_event(simulation_id, "simulation_end", {
                    "announcer": "用戶",
                    "result_text": "立即停止",
                    "outcome": outcome_now2,
                    "analysis": {"reason": "stopped_by_user"},
                    "filename": locals().get('filename')
                })
                return
            if mode == "demo":
                await asyncio.sleep(random.uniform(3.0, 5.0))


            try:
                quick_check_prompt = (
                    "請僅以 JSON 回覆，不要額外文字。格式: "
                    + '{"stop":true|false,"outcome":"SUCCESS|FAILURE","reason":"..."}'
                    + "\n判斷規則：若不確定，預設為 FAILURE（風險優先）。\n"
                    + "若你認為受騙者已被說服/已提供敏感資料/已承諾轉帳，視為 FAILURE；"
                    + "若你認為已成功阻止受騙，視為 SUCCESS。\n"
                    + f"對話至今：\n{json.dumps(conversation_history, ensure_ascii=False)}"
                )
                decision_raw = await runner.run_agent_with_adk(
                    runner.recorder, quick_check_prompt, f"{simulation_id}_recorder_quick_{turn}_v"
                )
                decision = json.loads(decision_raw)
                if isinstance(decision, dict) and decision.get("stop") is True:
                    outcome = decision.get("outcome") or "FAILURE"  # 記錄人判定或預設失敗
                    try:
                        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                        save_dir = os.path.join(base_dir, 'training_data')
                        os.makedirs(save_dir, exist_ok=True)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                        path = os.path.join(save_dir, filename)
                        speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                        dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                        data_to_save = {
                            "analysis": {
                                "outcome": outcome,
                                "reason": decision.get("reason"),
                                "victim_persona": victim_persona,
                                "scam_tactic": scam_tactic,
                                "timestamp": datetime.now().isoformat(),
                                "total_turns": len(conversation_history),
                            },
                            "metadata": {
                                "simulation_id": simulation_id,
                                "mode": mode,
                                "source": "websocket_simulation_quick_stop"
                            },
                            "conversation_history": conversation_history,
                            "dialogue": dialogue,
                        }
                        with open(path, 'w', encoding='utf-8') as f:
                            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                    except Exception as se:
                        log.error(f"save training data (early stop) failed: {se}")
                        filename = None
                    # Emit end event and return
                    await send_websocket_event(simulation_id, "simulation_end", {
                        "announcer": "記錄人",
                        "result_text": "提早結束",
                        "outcome": outcome,
                        "analysis": decision,
                        "filename": locals().get('filename')
                    })
                    return
            except Exception:
                pass

            await send_websocket_event(simulation_id, "tool_use", {
                "character_name": "防騙專家",
                "action": "正在查詢防騙資料庫..."
            })
            if should_stop(simulation_id):
                break


            expert_rag = _rag_bullets(f"{scam_tactic} {scammer_turn} {victim_turn}", n=3)
            prompt_for_expert = (
                "目前的對話如下（隱去記錄人內容）：\n"
                f"騙徒: '{scammer_turn}'\n受騙者: '{victim_turn}'\n\n"
                + (f"參考官方資料（節錄）：\n{expert_rag}\n\n" if expert_rag else "")
                + "請以防騙專家身份輸出，嚴格120字內"
            )


            if should_stop(simulation_id):
                break
            expert_turn = await runner.run_agent_with_adk(runner.expert, prompt_for_expert, f"{simulation_id}_expert_{turn}")

            conversation_history.append({"speaker": "專家", "dialogue": expert_turn})
            await send_websocket_event(simulation_id, "agent_turn", {
                "character_name": "防騙專家",
                "dialogue": expert_turn
            })
            await send_websocket_event(simulation_id, "turn_progress", {
                "current_turn": turn,
                "max_turns": max_turns
            })
            await asyncio.sleep(0)
            if should_stop(simulation_id):
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    save_dir = os.path.join(base_dir, 'training_data')
                    os.makedirs(save_dir, exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                    path = os.path.join(save_dir, filename)
                    speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                    dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                    outcome_now3 = "FAILURE"  # 早期停止，預設為失敗
                    data_to_save = {
                        "analysis": {
                            "outcome": outcome_now3,
                            "reason": "stopped_by_user",
                            "victim_persona": victim_persona,
                            "scam_tactic": scam_tactic,
                            "timestamp": datetime.now().isoformat(),
                            "total_turns": len(conversation_history),
                        },
                        "metadata": {
                            "simulation_id": simulation_id,
                            "mode": mode,
                            "source": "websocket_simulation_user_stop"
                        },
                        "conversation_history": conversation_history,
                        "dialogue": dialogue,
                    }
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                except Exception as se:
                    log.error(f"save training data (user stop) failed: {se}")
                    filename = None
                await send_websocket_event(simulation_id, "simulation_end", {
                    "announcer": "用戶",
                    "result_text": "立即停止",
                    "outcome": outcome_now3,
                    "analysis": {"reason": "stopped_by_user"},
                    "filename": locals().get('filename')
                })
                return
            if mode == "demo":
                await asyncio.sleep(random.uniform(3.0, 5.0))

            try:
                quick_check_prompt2 = (
                    "請僅以 JSON 回覆，不要額外文字。格式: "
                    + '{"stop":true|false,"outcome":"SUCCESS|FAILURE","reason":"..."}'
                    + "\n根據最新對話判斷是否應提早結束；若不確定，預設為 FAILURE。\n"
                    + f"對話至今：\n{json.dumps(conversation_history, ensure_ascii=False)}"
                )
                decision_raw2 = await runner.run_agent_with_adk(
                    runner.recorder, quick_check_prompt2, f"{simulation_id}_recorder_quick_{turn}_s"
                )
                decision2 = json.loads(decision_raw2)
                if isinstance(decision2, dict) and decision2.get("stop") is True:
                    outcome2 = decision2.get("outcome") or "FAILURE"  # 記錄人判定或預設失敗
                    try:
                        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                        save_dir = os.path.join(base_dir, 'training_data')
                        os.makedirs(save_dir, exist_ok=True)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                        path = os.path.join(save_dir, filename)
                        speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                        dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                        data_to_save = {
                            "analysis": {
                                "outcome": outcome2,
                                "reason": decision2.get("reason"),
                                "victim_persona": victim_persona,
                                "scam_tactic": scam_tactic,
                                "timestamp": datetime.now().isoformat(),
                                "total_turns": len(conversation_history),
                            },
                            "metadata": {
                                "simulation_id": simulation_id,
                                "mode": mode,
                                "source": "websocket_simulation_quick_stop"
                            },
                            "conversation_history": conversation_history,
                            "dialogue": dialogue,
                        }
                        with open(path, 'w', encoding='utf-8') as f:
                            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                    except Exception as se:
                        log.error(f"save training data (early stop) failed: {se}")
                        filename = None
                    await send_websocket_event(simulation_id, "simulation_end", {
                        "announcer": "記錄人",
                        "result_text": "提早結束",
                        "outcome": outcome2,
                        "analysis": decision2,
                        "filename": locals().get('filename')
                    })
                    return
            except Exception:
                pass


            scammer_rag = _rag_bullets(f"{scam_tactic} {victim_turn}", n=2)
            if should_stop(simulation_id):
                break
            scammer_turn = await runner.run_agent_with_adk(
                runner.scammer,
                (
                    f"（請用廣東話）受騙者剛才回應：『{victim_turn}』。"
                    f"嚴禁更換手法；嚴禁揭露或否定行為；嚴禁使用『詐騙／騙局／防騙／舉報／報警／警方』等字眼；"
                    f"繼續沿用『{scam_tactic}』嘅套路推進；禁止研究/倫理/免責口吻；≤120字"
                    + (f"（內部提示：相似案例提要→\n{scammer_rag}）" if scammer_rag else "")
                ),
                f"{simulation_id}_scammer_{turn}"
            )
            scammer_turn = await _enforce_scammer_role(scammer_turn, victim_turn_text=victim_turn, expert_turn_text=None)
            conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn})
            await send_websocket_event(simulation_id, "agent_turn", {
                "character_name": "專業騙徒",
                "dialogue": scammer_turn
            })
            await send_websocket_event(simulation_id, "turn_progress", {
                "current_turn": turn,
                "max_turns": max_turns
            })
            await asyncio.sleep(0)
            if mode == "demo":
                await asyncio.sleep(random.uniform(3.0, 5.0))
            
            # Termination will be decided by the recorder (quick checks and final analysis).
        
        # If exited due to turn cap, send cap_reached
        try:
            await send_websocket_event(simulation_id, "cap_reached", {
                "max_turns": max_turns,
                "total_turns": len(conversation_history)
            })
        except Exception:
            pass

        await send_websocket_event(simulation_id, "tool_use", {
            "character_name": "記錄人",
            "action": "正在分析對話結果..."
        })
        
        conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
        # 記錄人完全負責所有判定邏輯
        analysis_prompt = (
            "請作為專業的AI模擬分析師，分析以下對話歷史並產出 JSON（不要額外文字）。\n"
            "格式：{\"outcome\":\"SUCCESS|FAILURE\",\"reason\":\"...\",\"improvement_suggestion\":\"...\"}\n"
            "分析要點：\n"
            "1. 受騙者是否表現出信任騙徒的跡象？\n"
            "2. 受騙者是否同意提供個人資料、金錢或敏感信息？\n"
            "3. 防騙專家的建議是否被採納？\n"
            "4. 騙徒是否成功建立信任關係？\n"
            "5. 受騙者是否表現出懷疑或拒絕的態度？\n"
            "SUCCESS = 受騙者保持警惕，沒有被騙，專家建議有效\n"
            "FAILURE = 受騙者被騙，提供個人資料、金錢或表現出信任騙徒\n"
            "規則：不允許 UNKNOWN；若不確定，一律視為 FAILURE（風險優先）。\n"
            f"對話歷史：\n{conversation_str}"
        )
        analysis_json_str = await runner.run_agent_with_adk(runner.recorder, analysis_prompt, f"{simulation_id}_recorder")
        log.info(f"Recorder raw output: {analysis_json_str}")
        
        # Clean up the JSON string by removing markdown code blocks
        cleaned_json = analysis_json_str.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]  # Remove ```json
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]  # Remove ```
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]  # Remove trailing ```
        cleaned_json = cleaned_json.strip()
        
        try:
            analysis = json.loads(cleaned_json)
            # Enforce SUCCESS/FAILURE only
            outcome = analysis.get("outcome", "FAILURE")
            if outcome not in ("SUCCESS", "FAILURE"):
                outcome = "FAILURE"
            
            # 所有判定邏輯交由記錄人分析決定，不再進行硬編碼檢測
            
            result_text = "模擬成功" if outcome == "SUCCESS" else "模擬失敗"

            # save training data to backend/training_data
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                save_dir = os.path.join(base_dir, 'training_data')
                log.info(f"Training data save directory: {save_dir}")
                os.makedirs(save_dir, exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                path = os.path.join(save_dir, filename)
                log.info(f"Saving training data to: {path}")

                # Generate flattened dialogue (for training/frontend)
                speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]

                data_to_save = {
                    "analysis": {
                        **analysis,
                        "victim_persona": victim_persona,
                        "scam_tactic": scam_tactic,
                        "timestamp": datetime.now().isoformat(),
                        "total_turns": len(conversation_history),
                    },
                    "metadata": {
                        "simulation_id": simulation_id,
                        "mode": mode,
                        "source": "websocket_simulation"
                    },
                    "conversation_history": conversation_history,
                    "dialogue": dialogue,
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                log.info(f"Training data saved successfully: {filename}")
            except Exception as se:
                log.error(f"save training data failed: {se}")
                filename = None

            await send_websocket_event(simulation_id, "simulation_end", {
                "announcer": "記錄人",
                "result_text": result_text,
                "outcome": outcome,
                "analysis": analysis,
                "filename": filename
            })
            
        except json.JSONDecodeError:
            # If JSON parsing fails, default to FAILURE (risk-first approach)
            # Still save training data even if analysis fails
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                save_dir = os.path.join(base_dir, 'training_data')
                os.makedirs(save_dir, exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"training_data_ws_{ts}_{simulation_id[:8]}_json_error.json"
                path = os.path.join(save_dir, filename)
                
                speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                
                data_to_save = {
                    "analysis": {
                        "outcome": "FAILURE",
                        "reason": "JSON解析失敗",
                        "improvement_suggestion": "檢查記錄人模型輸出",
                        "victim_persona": victim_persona,
                        "scam_tactic": scam_tactic,
                        "timestamp": datetime.now().isoformat(),
                        "total_turns": len(conversation_history),
                    },
                    "metadata": {
                        "simulation_id": simulation_id,
                        "mode": mode,
                        "source": "websocket_simulation_json_error"
                    },
                    "conversation_history": conversation_history,
                    "dialogue": dialogue,
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                log.info(f"Training data saved despite JSON error: {filename}")
            except Exception as se:
                log.error(f"save training data (json error) failed: {se}")
                filename = None
            
            await send_websocket_event(simulation_id, "simulation_end", {
                "announcer": "記錄人",
                "result_text": "模擬完成（分析失敗，預設為失敗）",
                "outcome": "FAILURE",
                "analysis": {"outcome": "FAILURE", "reason": "JSON解析失敗", "improvement_suggestion": "檢查記錄人模型輸出"},
                "filename": filename
            })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_type = type(e).__name__
        error_msg = str(e)
        
        log.error(f"Simulation {simulation_id} failed: {error_type}: {error_msg}")
        log.error(f"詳細錯誤追蹤:\n{error_detail}")
        
        # Try to save training data even if simulation failed
        filename = None
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            save_dir = os.path.join(base_dir, 'training_data')
            os.makedirs(save_dir, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"training_data_ws_{ts}_{simulation_id[:8]}_error.json"
            path = os.path.join(save_dir, filename)
            
            speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
            dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
            
            data_to_save = {
                "analysis": {
                    "outcome": "FAILURE",
                    "reason": f"模擬失敗: {error_type}: {error_msg}",
                    "error_type": error_type,
                    "error_detail": error_detail,
                    "improvement_suggestion": "檢查系統錯誤",
                    "victim_persona": victim_persona,
                    "scam_tactic": scam_tactic,
                    "timestamp": datetime.now().isoformat(),
                    "total_turns": len(conversation_history),
                },
                "metadata": {
                    "simulation_id": simulation_id,
                    "mode": mode,
                    "source": "websocket_simulation_error"
                },
                "conversation_history": conversation_history,
                "dialogue": dialogue,
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            log.info(f"Training data saved despite simulation error: {filename}")
        except Exception as se:
            log.error(f"save training data (simulation error) failed: {se}")
            filename = None
        
        await send_websocket_event(simulation_id, "simulation_end", {
            "announcer": "系統",
            "result_text": f"模擬失敗: {error_type}: {error_msg}",
            "error_type": error_type,
            "error_detail": error_detail,
            "outcome": "FAILURE",
            "filename": filename
        })
    finally:
        # Cleanup connection
        if simulation_id in active_connections:
            del active_connections[simulation_id]
