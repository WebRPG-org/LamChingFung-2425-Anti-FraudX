import asyncio
import json
import uuid
import os
import re
from datetime import datetime
from typing import Dict, Optional
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from scripts.real_dialogue_runner import RealDialogueRunner
from services.rag_service import query_db
from utils.logger import log
from utils.role_enforcer import RoleEnforcer
from utils.performance_tracker import PerformanceTracker

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
    auto_train: Optional[bool] = True  # 是否启用自动训练（默认启用）

class SimulationResponse(BaseModel):
    simulation_id: str
    websocket_url: str

@router.post("/simulation/start", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest):
    """啟動一次新的模擬"""
    simulation_id = str(uuid.uuid4())
    websocket_url = f"/ws/simulation/{simulation_id}"
    
    # 保存自动训练设置到全局状态（用于后续自动启动）
    auto_train_enabled = request.auto_train if request.auto_train is not None else True
    # 使用 simulation_id 作为 key 存储自动训练设置
    if not hasattr(start_simulation, '_auto_train_settings'):
        start_simulation._auto_train_settings = {}
    start_simulation._auto_train_settings[simulation_id] = auto_train_enabled
    
    log.info(f"Starting simulation {simulation_id} with victim_persona: {request.victim_persona}, auto_train: {auto_train_enabled}")
    
# Launch simulation in background
    asyncio.create_task(run_simulation_async(
        simulation_id,
        victim_persona=request.victim_persona,
        scam_tactic=request.scam_tactic,
        mode=request.mode or "fast",
        auto_train=auto_train_enabled
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
        # 使用 asyncio.wait_for 来避免无限阻塞，允许定期检查连接状态
        while simulation_id in active_connections:
            try:
                # 设置超时，避免永久阻塞
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                try:
                    if msg.strip().lower() == 'stop_now':
                        log.warning(f"🛑 收到停止指令 for simulation {simulation_id}")
                        stop_flags[simulation_id] = True
                        await websocket.send_json({"event_type": "ack", "payload": {"command": "stop_now", "ok": True, "message": "正在停止..."}})
                        # 强制关闭连接，快速退出
                        await websocket.close(code=1000, reason="User stop")
                        break
                    else:
                        data = json.loads(msg)
                        cmd = isinstance(data, dict) and data.get('command')
                        if cmd == 'stop_now':
                            log.warning(f"🛑 收到停止指令 (JSON) for simulation {simulation_id}")
                            stop_flags[simulation_id] = True
                            await websocket.send_json({"event_type": "ack", "payload": {"command": "stop_now", "ok": True, "message": "正在停止..."}})
                            # 强制关闭连接，快速退出
                            await websocket.close(code=1000, reason="User stop")
                            break
                        elif cmd == 'replay':
                            # Replay recent events (up to 20)
                            buf = event_buffers.get(simulation_id) or []
                            for evt in buf[-20:]:
                                try:
                                    await websocket.send_json(evt)
                                except Exception:
                                    break
                            await websocket.send_json({"event_type": "ack", "payload": {"command": "replay", "ok": True}})
                except Exception as e:
                    # Ignore unparseable messages
                    log.debug(f"WebSocket message parse error: {e}")
                    pass
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环检查连接状态
                continue
            except Exception as e:
                # 如果连接已关闭或其他错误，退出循环
                log.debug(f"WebSocket receive error: {e}")
                break
            
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

async def _generate_recorder_analysis(
    runner: RealDialogueRunner,
    conversation_history: list,
    simulation_id: str,
    victim_persona: str,
    scam_tactic: str,
    outcome_type: str,  # "FAILURE", "SUCCESS", "PARTIAL"
    outcome_description: str,
    tracker: Optional[PerformanceTracker] = None,
    trust_in_scammer: Optional[int] = None,
    trust_in_expert: Optional[int] = None
) -> dict:
    """
    统一的 RecorderAgent 分析生成函数
    确保在所有结束路径中都生成完整的分析报告
    """
    try:
        conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
        
        # 构建额外的上下文信息
        context_info = f"**關鍵信息：** {outcome_description}\n"
        if trust_in_scammer is not None:
            context_info += f"- 受害者對騙徒的信任度：{trust_in_scammer}/100\n"
        if trust_in_expert is not None:
            context_info += f"- 受害者對專家的信任度：{trust_in_expert}/100\n"
        if tracker:
            try:
                current_state = tracker.get_current_state()
                context_info += "- 最終信任度狀態：\n"
                context_info += f"  * 對騙徒：{current_state.get('trust_in_scammer', 'N/A')}/100\n"
                context_info += f"  * 對專家：{current_state.get('trust_in_expert', 'N/A')}/100\n"
                context_info += f"  * 警覺程度：{current_state.get('alertness', 'N/A')}/100\n"
                context_info += f"  * 情緒狀態：{current_state.get('emotional_state', 'N/A')}\n"
            except Exception:
                pass
        
        # --- MODIFICATION START (Fix JSON Output Conflict) ---
        analysis_prompt = (
            "**🚨 任務：你必須作為專業AI分析師（林慧思博士）**，對以下對話進行全面分析。\n\n"
            "**嚴格按照**你的指示（instruction）中定義的「輸出格式」來建構**一個完整的JSON對象**。\n\n"
            f"**上下文情景：**\n{context_info}\n"
            f"**待分析的對話歷史 (JSON Array)：**\n{conversation_str}\n\n"
            "---"
            "**🚨 絕對輸出要求（最重要）：**\n"
            "1. 你的輸出**必須且只能**是一個**單一的JSON對象**。\n"
            "2. 你的輸出**必須**以 `{` (大括號) 開始。\n"
            "3. 你的輸出**必須**以 `}` (大括號) 結束。\n"
            "4. **絕對禁止**以 `[` (方括號) 或任何其他文字開始（這是導致失敗的直接原因）。\n"
            "5. **絕對禁止**在JSON對象之外包含任何註解、說明、Markdown (```) 或前言。\n"
            "6. **必須**包含所有指定的分析欄位 (outcome, victim_persona, victim_trust_analysis, ..., full_conversation_log)。\n"
            "7. `full_conversation_log` 欄位**必須**是你根據對話歷史*重新分析*生成的，包含 `round`, `speaker`, `dialogue` 和 `analysis`。\n\n"
            "**現在，請立即開始輸出你的JSON對象，以 `{` 開始：**"
        )
        # --- MODIFICATION END (Fix JSON Output Conflict) ---
        
        if outcome_type == "FAILURE":
            analysis_prompt += (
                "**⚠️ 特別重要：這是FAILURE情況，failure_reason字段必須包含以下5個維度的完整深度分析：**\n"
                "1. 專家策略問題（情緒安撫/證據提供/溝通方式/介入時機/話術有效性/反擊策略）\n"
                "2. 騙徒成功因素（最具殺傷力的話術/心理弱點利用/對立製造/信任度操控/壓力策略/角色一致性）\n"
                "3. 受騙者心理軌跡（初始狀態/關鍵轉折點/最終狀態/主要被影響因素/決策過程）\n"
                "4. 系統性失敗因素（信任度差距/關鍵行動詞觸發/專家干預無效的原因/信任度達到危險水平）\n"
                "5. 失敗的根本原因（主要原因/次要原因/可避免性）\n\n"
                "failure_reason必須至少200字，深入分析失敗的每一個維度，指出具體的回合、話術和信任度變化。\n\n"
            )
        elif outcome_type == "SUCCESS":
            analysis_prompt += (
                "**✅ 這是SUCCESS情況，success_reason字段必須包含：**\n"
                "1. 專家的哪個策略最有效？\n"
                "2. 在第幾回合成功扭轉局面？\n"
                "3. 受騙者被哪個證據/說法說服？\n"
                "4. 哪些做法值得在未來複製？\n\n"
            )
        
        analysis_prompt += (
            "**🚨 嚴格要求（最重要）：**\n"
            "1. 你的輸出**必須**是純JSON格式，從 { 開始，以 } 結束\n"
            "2. **絕對不要**輸出任何解釋性文字、對話總結、或描述性文字\n"
            "3. **絕對不要**輸出「以下是一系列對話」或類似的開場白\n"
            "4. **絕對不要**使用markdown code block標記（```json 或 ```）\n"
            "5. 直接輸出JSON對象，沒有任何前綴或後綴文字\n"
            "6. 如果輸出不符合JSON格式，系統會失敗\n\n"
            f"{context_info}\n"
            f"對話歷史：\n{conversation_str}\n\n"
            "**現在，直接輸出JSON對象，不要有任何其他文字：**"
        )
        
        log.info(f"📊 调用 RecorderAgent 生成完整分析 (outcome: {outcome_type})")
        analysis_raw = await runner.run_agent_with_adk(
            runner.recorder, 
            analysis_prompt, 
            f"{simulation_id}_final_analysis"
        )
        
        # 清理 JSON 字符串
        cleaned_json = analysis_raw.strip()
        
        # 移除 markdown code block 标记
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()
        
        # 尝试提取JSON部分（如果输出包含非JSON文字）
        # 查找第一个 { 和最后一个 }
        first_brace = cleaned_json.find('{')
        last_brace = cleaned_json.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            # 提取JSON部分
            cleaned_json = cleaned_json[first_brace:last_brace+1]
        
        # 解析 JSON
        try:
            analysis = json.loads(cleaned_json)
        except json.JSONDecodeError as parse_error:
            # 如果仍然失败，尝试更激进的清理
            log.warning(f"第一次JSON解析失败，尝试更激进的清理: {parse_error}")
            # 尝试找到完整的JSON对象
            json_match = re.search(r'\{.*\}', cleaned_json, re.DOTALL)
            if json_match:
                cleaned_json = json_match.group(0)
                analysis = json.loads(cleaned_json)
            else:
                raise  # 重新抛出异常，让外层处理
        
        # 确保 outcome 字段正确
        analysis["outcome"] = outcome_type
        
        # 确保包含所有必需字段
        if "victim_persona" not in analysis:
            analysis["victim_persona"] = victim_persona
        if "scam_tactic" not in analysis:
            analysis["scam_tactic"] = scam_tactic
        if "victim_trust_analysis" not in analysis:
            current_state = tracker.get_current_state() if tracker else {}
            trust_in_scammer_final = trust_in_scammer if trust_in_scammer is not None else current_state.get("trust_in_scammer", 0)
            trust_history = tracker.victim_trust_history if tracker and hasattr(tracker, 'victim_trust_history') else []
            initial_trust = trust_history[0].get("old_value", 70) if trust_history else 70
            peak_trust = max([h.get("new_value", trust_in_scammer_final) for h in trust_history] + [trust_in_scammer_final]) if trust_history else trust_in_scammer_final
            analysis["victim_trust_analysis"] = {
                "initial_trust_level": initial_trust,
                "peak_trust_level": peak_trust,
                "final_trust_level": trust_in_scammer_final,
                "trust_trajectory": f"初始: {initial_trust}/100 → 峰值: {peak_trust}/100 → 最终: {trust_in_scammer_final}/100"
            }
        if "key_moment" not in analysis:
            analysis["key_moment"] = outcome_description
        if outcome_type == "SUCCESS":
            if "success_reason" not in analysis:
                analysis["success_reason"] = outcome_description
        else:
            if "failure_reason" not in analysis:
                analysis["failure_reason"] = outcome_description
        if "improvement_suggestion" not in analysis:
            analysis["improvement_suggestion"] = "需要提供具体改进建议"
        if "full_conversation_log" not in analysis:
            analysis["full_conversation_log"] = [
                {
                    "round": i + 1,
                    "speaker": turn.get("speaker", "未知"),
                    "dialogue": turn.get("dialogue", ""),
                    "analysis": "未提供详细分析"
                }
                for i, turn in enumerate(conversation_history)
            ]
        
        log.info(f"✅ RecorderAgent 分析完成，包含字段: {list(analysis.keys())}")
        return analysis
        
    except json.JSONDecodeError as e:
        log.error(f"❌ RecorderAgent JSON 解析失败: {e}")
        log.error(f"原始输出: {analysis_raw[:500] if 'analysis_raw' in locals() else 'N/A'}")
        # 返回一个完整的fallback结构，包含所有必需字段
        current_state = tracker.get_current_state() if tracker else {}
        trust_in_scammer_final = trust_in_scammer if trust_in_scammer is not None else current_state.get("trust_in_scammer", 0)
        trust_in_expert_final = trust_in_expert if trust_in_expert is not None else current_state.get("trust_in_expert", 0)
        
        # 构建完整的信任度分析
        trust_history = tracker.victim_trust_history if tracker and hasattr(tracker, 'victim_trust_history') else []
        initial_trust = trust_history[0].get("old_value", 70) if trust_history else 70
        peak_trust = max([h.get("new_value", trust_in_scammer_final) for h in trust_history] + [trust_in_scammer_final]) if trust_history else trust_in_scammer_final
        
        fallback_analysis = {
            "outcome": outcome_type,
            "victim_persona": victim_persona,
            "victim_trust_analysis": {
                "initial_trust_level": initial_trust,
                "peak_trust_level": peak_trust,
                "final_trust_level": trust_in_scammer_final,
                "trust_trajectory": f"初始: {initial_trust}/100 → 峰值: {peak_trust}/100 → 最终: {trust_in_scammer_final}/100 (分析失败，使用fallback)"
            },
            "scam_tactic": scam_tactic,
            "key_moment": outcome_description,
            "success_reason" if outcome_type == "SUCCESS" else "failure_reason": f"{outcome_description}。注意：此分析为fallback，因为RecorderAgent JSON解析失败。",
            "improvement_suggestion": "需要改进RecorderAgent的JSON输出格式，确保输出纯JSON格式。",
            "expert_performance_rating": {
                "emotional_support": "N/A (分析失败)",
                "evidence_quality": "N/A (分析失败)",
                "communication_style": "N/A (分析失败)",
                "timing": "N/A (分析失败)",
                "overall": "N/A (分析失败)"
            },
            "scammer_effectiveness_rating": {
                "psychological_manipulation": "N/A (分析失败)",
                "credibility": "N/A (分析失败)",
                "pressure_tactics": "N/A (分析失败)",
                "adaptability": "N/A (分析失败)",
                "overall": "N/A (分析失败)"
            },
            "full_conversation_log": [
                {
                    "round": i + 1,
                    "speaker": turn.get("speaker", "未知"),
                    "dialogue": turn.get("dialogue", ""),
                    "analysis": "分析失败，无法提供详细分析"
                }
                for i, turn in enumerate(conversation_history)
            ],
            "error": "JSON解析失敗",
            "raw_output_preview": analysis_raw[:200] if 'analysis_raw' in locals() else "N/A",
            "reason": outcome_description
        }
        return fallback_analysis
        
    except Exception as e:
        log.error(f"❌ RecorderAgent 分析生成失败: {e}")
        import traceback
        log.error(f"错误详情: {traceback.format_exc()}")
        # 返回基本结构
        fallback_analysis = {
            "outcome": outcome_type,
            "reason": outcome_description,
            "victim_persona": victim_persona,
            "scam_tactic": scam_tactic,
            "error": f"分析生成失败: {str(e)}"
        }
        if trust_in_scammer is not None:
            fallback_analysis["victim_trust_analysis"] = {
                "final_trust_level": trust_in_scammer,
                "trust_trajectory": "分析失敗"
            }
        return fallback_analysis

async def _auto_start_new_round(mode: str = "fast", auto_train: bool = True):
    """自動開始新一輪模擬"""
    import os
    # 檢查是否啟用自動訓練
    # 优先使用传入的参数，否则检查环境变量
    if not auto_train:
        # 如果传入的参数为 False，直接返回
        log.info("自動訓練已禁用（參數設置），跳過新輪次")
        return
    
    # 检查环境变量
    env_auto_train = os.getenv("AUTO_TRAIN_ENABLED", "true").lower() == "true"
    if not env_auto_train:
        log.info("自動訓練已禁用（環境變量設置），跳過新輪次")
        return
    
    # 等待一小段時間，避免過於頻繁
    await asyncio.sleep(2.0)
    
    # 隨機選擇新的參數
    from scripts.real_dialogue_runner import SCAM_TACTICS, VICTIM_PERSONAS
    new_victim_persona = random.choice(VICTIM_PERSONAS)
    new_scam_tactic = random.choice(SCAM_TACTICS)
    
    # 生成新的 simulation_id
    new_simulation_id = str(uuid.uuid4())
    
    log.info(f"🔄 自動開始新一輪模擬: {new_simulation_id}")
    log.info(f"   受害者類型: {new_victim_persona}, 詐騙手法: {new_scam_tactic}")
    
    # 通知所有連接的客戶端新輪次即將開始
    # 使用廣播方式通知所有連接
    for sim_id in list(active_connections.keys()):
        try:
            await send_websocket_event(sim_id, "auto_new_round_starting", {
                "new_simulation_id": new_simulation_id,
                "victim_persona": new_victim_persona,
                "scam_tactic": new_scam_tactic,
                "mode": mode
            })
        except Exception:
            pass  # 忽略單個連接的錯誤
    
    # 在背景中啟動新模擬（继承自动训练设置）
    asyncio.create_task(run_simulation_async(
        new_simulation_id,
        victim_persona=new_victim_persona,
        scam_tactic=new_scam_tactic,
        mode=mode,
        auto_train=auto_train  # 继承自动训练设置
    ))


async def run_simulation_async(simulation_id: str, victim_persona: str, scam_tactic: str, mode: str = "fast", auto_train: bool = True):
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
        
        # Initialize performance tracker
        tracker = PerformanceTracker(victim_persona=victim_persona)
        log.info(f"📊 初始化PerformanceTracker - 受害者类型: {victim_persona}")
        log.info(f"   初始信任度 - 对骗徒: {tracker.victim_trust.trust_in_scammer}, 对专家: {tracker.victim_trust.trust_in_expert}")
        
        # Send simulation_start event
        await send_websocket_event(simulation_id, "simulation_start", {
            "simulation_id": simulation_id,
            "characters": [
                {"name": "專業騙徒", "persona_summary": "精通社會工程學的詐騙專家"},
                {"name": "受騙者", "persona_summary": f"角色類型: {victim_persona}"},
                {"name": "防騙專家", "persona_summary": "冷靜理性的防騙分析師"}
            ],
            "initial_trust": tracker.victim_trust.to_dict(),
            "initial_scores": {
                "scammer": tracker.scammer_perf.to_dict(),
                "expert": tracker.expert_perf.to_dict()
            }
        })
        
        conversation_history = []
        max_turns = 50
        tracker.turn_count = 0
    
        # Internal helper: enforce scammer stays in-character (rewrite if anti-scam/reveal wording is detected)
        async def _enforce_scammer_role(original_text: str, victim_turn_text: str | None = None, expert_turn_text: str | None = None) -> str:
            # 在函数内部导入 re 模块，避免闭包变量问题
            # 使用 importlib 确保是局部导入
            import importlib
            re = importlib.import_module('re')
            
            text = original_text or ""
            lower = text.lower()
            
            # 阶段0: 检查重复模式（使用对话历史）
            is_repetitive, repetition_msg, similar_turns = RoleEnforcer.detect_repetition_in_history(
                conversation_history, "騙徒", text, threshold=0.85
            )
            
            if is_repetitive:
                log.warning(f"🚨 骗徒检测到重复模式: {repetition_msg}")
                # 强制重写，明确要求改变策略
                rewrite_prompt = (
                    f"🚨🚨🚨 你的回應陷入了重複迴圈！\n\n"
                    f"【檢測到的問題】：\n{repetition_msg}\n\n"
                    f"【你的原始回應】（錯誤）：\n「{text[:200]}...」\n\n"
                    f"【受害者剛才說】：\n「{victim_turn_text[:150] if victim_turn_text else '（等待回應）'}...」\n\n"
                    f"【🎭 你的身份】：專業騙徒（使用「{scam_tactic}」手法）\n\n"
                    f"【🚨 必須做到】：\n"
                    f"1. **絕對不能重複之前的回應！** 你已經說了{len(similar_turns)}次類似的話，必須**立即改變策略**！\n"
                    f"2. **推進騙局**：根據受害者的最新回應，調整你的話術，不要機械式重複威脅。\n"
                    f"3. **保持權威感**：即使改變策略，你仍然要保持權威和壓迫感。\n\n"
                    f"【策略建議】：\n"
                    f"- 如果受害者已經表現出懷疑，改用「安撫+威脅」的組合\n"
                    f"- 如果受害者已經問了很多問題，改用「簡化+催促」的方式\n"
                    f"- 如果專家已經介入，強調「專家不懂情況」並加強威脅\n\n"
                    f"請立即重寫，≤120字，廣東話，**必須**與之前所有回應不同！"
                )
                
                try:
                    rewritten = await runner.run_agent_with_adk(runner.scammer, rewrite_prompt, f"{simulation_id}_scammer_anti_repeat")
                    # 再次检查重复
                    is_repetitive_retry, _, _ = RoleEnforcer.detect_repetition_in_history(
                        conversation_history, "騙徒", rewritten, threshold=0.85
                    )
                    if not is_repetitive_retry:
                        log.info("✅ 骗徒重复问题已修复")
                        text = rewritten
                    else:
                        log.warning("⚠️ 骗徒重写后仍有重复，使用强制策略变化")
                        # 强制策略变化：根据scam_tactic生成不同的fallback
                        if "銀行" in scam_tactic:
                            text = "陳先生，我明白你嘅疑慮。但係我哋而家係緊急處理階段，如果你唔配合，我哋只能採取強制措施。你希望我哋點樣處理？"
                        elif "政府" in scam_tactic:
                            text = "我理解你嘅困惑，但係呢個係國家安全級別嘅案件。我哋已經掌握咗足夠證據，你嘅配合會影響最終判決。請你立即提供資料。"
                        else:
                            text = "我明白你可能有疑慮，但係呢個機會真係好難得。如果你錯過咗，可能要等好耐先再有。你而家決定點？"
                except Exception as e:
                    log.error(f"骗徒重复修复失败: {e}")
                    # Fallback策略变化
                    if "銀行" in scam_tactic:
                        text = "陳先生，情況緊急，請你立即配合。"
                    elif "政府" in scam_tactic:
                        text = "我哋已經掌握證據，你必須立即配合調查。"
                    else:
                        text = "呢個機會好難得，你決定點？"
            
            # 阶段1: 基础检查（检查是否暴露骗局）
            banned_core = ["詐騙", "騙局", "防騙", "舉報", "報警", "警方"]
            # 检查旁白括号标记（内心独白、导演指示等）
            banned_markers = ["（", "）", "[", "]", "【", "】", "<", ">"]
            # 检查角色标签格式（冒号常用于角色标签）
            has_role_label = bool(re.search(r"^[\u4e00-\u9fff]+[：:]", text)) or "**" in text
            
            basic_violation = (any(k in text for k in banned_core) or 
                             any(k in text for k in banned_markers) or
                             has_role_label or
                             any(k.replace(" ", "") in lower for k in ["唔好提供", "唔好輸入"]) or 
                             any(k in lower for k in ["don\'t", "do not"]))
            
            # 阶段2: 角色一致性检查（检查是否角色混乱）
            is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(text, victim_turn_text or "")
            
            # 如果存在任何问题，重写对话
            if basic_violation or not is_valid:
                if basic_violation:
                    log.warning("骗徒暴露骗局，需要重写")
                if not is_valid:
                    log.warning(f"骗徒角色一致性问题: {error_msg}")
                
                # 生成详细的重写提示
                rewrite_prompt = RoleEnforcer.generate_rewrite_prompt(
                    "scammer",
                    text,
                    issues if not is_valid else ["暴露骗局身份"],
                    {
                        'victim_message': victim_turn_text or "",
                        'expert_message': expert_turn_text or "",
                        'scam_tactic': scam_tactic
                    }
                )
                
                # 多次重试（最多3次）
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        rewritten = await runner.run_agent_with_adk(runner.scammer, rewrite_prompt, f"{simulation_id}_scammer_rewrite_{retry}")
                        
                        # 再次验证重写后的内容
                        is_valid_retry, error_msg_retry, issues_retry = RoleEnforcer.check_scammer_consistency(rewritten, victim_turn_text or "")
                        
                        # 检查是否仍然包含示例脚本标记
                        has_script_markers = any(marker in rewritten for marker in ["以下是一個", "**場景：", "**角色：", "這只是一個範例"])
                        
                        if is_valid_retry and not has_script_markers:
                            log.info(f"骗徒对话重写成功 (第{retry+1}次尝试)")
                            return rewritten
                        else:
                            if retry < max_retries - 1:
                                log.warning(f"骗徒对话重写后仍有问题 (第{retry+1}次)，继续重试...")
                                # 更新重写提示，包含新的问题
                                rewrite_prompt = RoleEnforcer.generate_rewrite_prompt(
                                    "scammer",
                                    rewritten,
                                    issues_retry if not is_valid_retry else ["仍然包含示例脚本标记"],
                                    {
                                        'victim_message': victim_turn_text or "",
                                        'expert_message': expert_turn_text or "",
                                        'scam_tactic': scam_tactic
                                    }
                                )
                            else:
                                log.error(f"骗徒对话重写失败 (已尝试{max_retries}次)，使用fallback响应")
                                # 使用fallback响应，而不是错误的原文
                                # 根据scam_tactic生成合适的fallback
                                if "冒充" in scam_tactic or "假" in scam_tactic:
                                    if "銀行" in scam_tactic:
                                        fallback = "先生，我係銀行客戶服務部嘅李主任。你嘅戶口有 緊急問題，需要立即處理，否則會被凍結。請你即刻提供身份證號碼同銀行賬戶資料，我哋會馬上幫你處理。"
                                    elif "政府" in scam_tactic:
                                        fallback = "先生，我係政府資訊中心嘅職員。你涉及一宗緊急案件，需要立即配合調查。請你即刻提供個人資料，否則會面臨嚴重後果。"
                                    else:
                                        fallback = "先生，我係相關部門嘅職員。情況非常緊急，你必須立即配合，提供相關資料，否則會有嚴重後果。"
                                else:
                                    fallback = "你好，我發現一個好有潛力嘅投資機會，可以幫你增加收入。如果你有興趣，我哋可以詳細傾下。"
                                return fallback
                    except Exception as e:
                        log.error(f"骗徒对话重写失败 (第{retry+1}次尝试): {e}")
                        if retry == max_retries - 1:
                            # 最后一次失败，使用fallback
                            if "冒充" in scam_tactic or "假" in scam_tactic:
                                if "銀行" in scam_tactic:
                                    fallback = "先生，我係銀行客戶服務部嘅李主任。你嘅戶口有緊急問題，需要立即處理，否則會被凍結。請你即刻提供身份證號碼同銀行賬戶資料，我哋會馬上幫你處理。"
                                elif "政府" in scam_tactic:
                                    fallback = "先生，我係政府資訊中心嘅職員。你涉及一宗緊急案件，需要立即配合調查。請你即刻提供個人資料，否則會面臨嚴重後果。"
                                else:
                                    fallback = "先生，我係相關部門嘅職員。情況非常緊急，你必須立即配合，提供相關資料，否則會有嚴重後果。"
                            else:
                                fallback = "你好，我發現一個好有潛力嘅投資機會，可以幫你增加收入。如果你有興趣，我哋可以詳細傾下。"
                            return fallback
                
                # 如果所有重试都失败，使用fallback
                if "冒充" in scam_tactic or "假" in scam_tactic:
                    if "銀行" in scam_tactic:
                        fallback = "先生，我係銀行客戶服務部嘅李主任。你嘅戶口有緊急問題，需要立即處理，否則會被凍結。請你即刻提供身份證號碼同銀行賬戶資料，我哋會馬上幫你處理。"
                    elif "政府" in scam_tactic:
                        fallback = "先生，我係政府資訊中心嘅職員。你涉及一宗緊急案件，需要立即配合調查。請你即刻提供個人資料，否則會面臨嚴重後果。"
                    else:
                        fallback = "先生，我係相關部門嘅職員。情況非常緊急，你必須立即配合，提供相關資料，否則會有嚴重後果。"
                else:
                    fallback = "你好，我發現一個好有潛力嘅投資機會，可以幫你增加收入。如果你有興趣，我哋可以詳細傾下。"
                return fallback
            
            return original_text

        # Internal helper: enforce victim stays in-character
        async def _enforce_victim_role(original_text: str, scammer_turn_text: str = "") -> str:
            text = original_text or ""
            
            # 0. 首先检查并修复字符级重复（如"咁樣咁樣咁樣..."）
            # 检测是否有连续重复的短语（如"咁樣"重复超过5次）
            import re as regex_module
            re = regex_module
            
            # 检测连续重复的短语模式（如"咁樣咁樣咁樣..."）
            char_repeat_pattern = r'(.{1,5})\1{4,}'  # 匹配任何1-5个字符重复5次以上
            matches = re.findall(char_repeat_pattern, text)
            if matches:
                log.warning(f"🚨 受害者检测到字符级重复: {matches[0]}...")
                # 截断到重复开始之前，并添加一个简短回应
                match_pos = text.find(matches[0] * 5)
                if match_pos > 0:
                    text = text[:match_pos].strip()
                else:
                    # 如果重复从开头开始，直接替换为简短回应
                    if victim_persona == "overconfident":
                        text = "你憑咩咁講？你估我傻㗎？"
                    elif victim_persona == "elderly":
                        text = "我...我唔明，你可唔可以講清楚啲？"
                    else:
                        text = "我明啦，但係我想了解多啲。"
            
            # 0.5. 限制响应长度（最多200字，超过部分截断）
            if len(text) > 200:
                log.warning(f"🚨 受害者响应过长 ({len(text)}字)，截断至200字")
                text = text[:200].strip()
                # 如果截断后以不完整字符结尾，尝试找到最后一个完整句子
                if text and text[-1] not in ['。', '！', '？', '，', '、']:
                    last_period = max(text.rfind('。'), text.rfind('！'), text.rfind('？'))
                    if last_period > 100:  # 确保截断后仍有足够内容
                        text = text[:last_period + 1]
            
            # 1. 检查重复模式（使用对话历史）
            is_repetitive, repetition_msg, similar_turns = RoleEnforcer.detect_repetition_in_history(
                conversation_history, "受騙者", text, threshold=0.85
            )
            
            if is_repetitive:
                log.warning(f"🚨 受害者检测到重复模式: {repetition_msg}")
                # 强制重写，明确要求改变策略
                rewrite_prompt = (
                    f"🚨🚨🚨 你的回應陷入了重複迴圈！\n\n"
                    f"【檢測到的問題】：\n{repetition_msg}\n\n"
                    f"【你的原始回應】（錯誤）：\n「{text[:200]}...」\n\n"
                    f"【騙徒剛才說】：\n「{scammer_turn_text[:150]}...」\n\n"
                    f"【🎭 你的角色】：{victim_persona}（"
                    f"{'陳婆婆，70歲，好驚、好易信人' if victim_persona == 'elderly' else '張文軒，35歲，理性但有貪念' if victim_persona == 'average' else '李俊傑，28歲，自信、好勝、挑釁'}"
                    f"）\n\n"
                    f"【🚨 必須做到】：\n"
                    f"1. **絕對不能重複之前的回應！** 必須根據騙徒的最新訊息作出**全新**的回應。\n"
                    f"2. **保持角色一致性**：{victim_persona} 類型應該有特定的反應方式。\n"
                    f"3. **推進對話**：你的回應必須推進對話，而不是重複。\n\n"
                    f"請立即重寫，≤100字，廣東話，**必須**與之前所有回應不同！"
                )
                
                try:
                    rewritten = await runner.run_agent_with_adk(runner.victim, rewrite_prompt, f"{simulation_id}_victim_anti_repeat")
                    # 再次检查重复
                    is_repetitive_retry, _, _ = RoleEnforcer.detect_repetition_in_history(
                        conversation_history, "受騙者", rewritten, threshold=0.85
                    )
                    if not is_repetitive_retry:
                        log.info("✅ 受害者重复问题已修复")
                        text = rewritten
                    else:
                        log.warning("⚠️ 受害者重写后仍有重复，使用强制简短回应")
                        # 强制简短回应
                        if victim_persona == "overconfident":
                            text = "你憑咩咁講？你估我傻㗎？"
                        elif victim_persona == "elderly":
                            text = "我...我唔明，你可唔可以講清楚啲？"
                        else:
                            text = "我明啦，但係我想了解多啲。"
                except Exception as e:
                    log.error(f"受害者重复修复失败: {e}")
                    # Fallback简短回应
                    if victim_persona == "overconfident":
                        text = "你憑咩咁講？"
                    elif victim_persona == "elderly":
                        text = "我唔明...你可唔可以講清楚啲？"
                    else:
                        text = "我明啦。"
            
            # 2. 检查角色一致性
            is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(text, victim_persona)
            
            if not is_valid:
                log.warning(f"受害者角色一致性问题: {error_msg}")
                
                # 生成重写提示
                rewrite_prompt = RoleEnforcer.generate_rewrite_prompt(
                    "victim",
                    text,
                    issues,
                    {
                        'persona_name': '陳婆婆' if victim_persona == 'elderly' else '張文軒' if victim_persona == 'average' else '李俊傑',
                        'age': '70' if victim_persona == 'elderly' else '35' if victim_persona == 'average' else '28',
                        'persona_type': victim_persona,  # 添加persona_type以便重写提示知道是哪个类型
                        'scammer_message': scammer_turn_text
                    }
                )
                
                try:
                    rewritten = await runner.run_agent_with_adk(runner.victim, rewrite_prompt, f"{simulation_id}_victim_rewrite")
                    
                    # 再次验证
                    is_valid_retry, _, _ = RoleEnforcer.check_victim_consistency(rewritten, victim_persona)
                    if is_valid_retry:
                        log.info("受害者对话重写成功")
                        return rewritten
                    else:
                        log.warning("受害者对话重写后仍有问题，使用原文")
                        return text
                except Exception as e:
                    log.error(f"受害者对话重写失败: {e}")
                    return text
            
            return text

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

        # 第一轮骗徒对话，添加超时保护
        try:
            scammer_turn = await asyncio.wait_for(
                runner.run_agent_with_adk(
                    runner.scammer,
                    f"（請用廣東話）以『{scam_tactic}』為目標，自然地展開對話。"
                    f"保持騙徒身份，但可以根據對方反應調整策略。"
                    f"避免直接使用『詐騙』等敏感詞彙，但可以自然地建立信任關係。"
                    f"⚠️ 重要：直接進入角色，直接說話，不要任何前置說明、場景設定、角色介紹！",
                    f"{simulation_id}_scammer_1"
                ),
                timeout=180.0  # 3分鐘超時
            )
        except asyncio.TimeoutError:
            log.error("骗徒第一轮对话超时，使用fallback响应")
            # 根据scam_tactic生成fallback
            if "銀行" in scam_tactic:
                scammer_turn = "先生，我係銀行客戶服務部嘅李主任。你嘅戶口有緊急問題，需要立即處理，否則會被凍結。請你即刻提供身份證號碼同銀行賬戶資料，我哋會馬上幫你處理。"
            elif "政府" in scam_tactic:
                scammer_turn = "先生，我係政府資訊中心嘅職員。你涉及一宗緊急案件，需要立即配合調查。請你即刻提供個人資料，否則會面臨嚴重後果。"
            else:
                scammer_turn = "你好，我發現一個好有潛力嘅投資機會，可以幫你增加收入。如果你有興趣，我哋可以詳細傾下。"
        
        # 执行角色一致性检查
        scammer_turn = await _enforce_scammer_role(scammer_turn)
        conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn})
        
        await send_websocket_event(simulation_id, "agent_turn", {
            "character_name": "專業騙徒",
            "dialogue": scammer_turn
        })
        
        # Track scammer performance (first turn, no victim response yet)
        tracker.turn_count += 1
        scammer_analysis = tracker.analyze_scammer_turn(scammer_turn, "")
        log.info(f"📊 第{tracker.turn_count}轮分析 - 骗徒使用策略: {scammer_analysis.get('tactics_used', [])}")
        
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
        

        max_turns = 50
        for turn in range(2, max_turns + 1):
            if should_stop(simulation_id):
                break

            # --- MODIFICATION START (Prevent Victim Repetition) ---
            # 獲取上一輪受害者的對話
            last_victim_turn = ""
            if len(conversation_history) > 1:
                # 倒序查找上一個 "受騙者" 的發言
                for i in range(len(conversation_history) - 1, -1, -1):
                    if conversation_history[i].get("speaker") == "受騙者":
                        last_victim_turn = conversation_history[i].get("dialogue", "")
                        break
            
            # 构建更完整的对话历史上下文（最近3轮）
            recent_history = []
            for i in range(max(0, len(conversation_history) - 6), len(conversation_history)):
                item = conversation_history[i]
                speaker = item.get("speaker", "")
                dialogue = item.get("dialogue", "")
                if speaker in ["騙徒", "受騙者", "專家"]:
                    speaker_name = {"騙徒": "騙徒", "受騙者": "你", "專家": "專家"}.get(speaker, speaker)
                    recent_history.append(f"{speaker_name}：{dialogue[:150]}")
            
            history_context = "\n".join(recent_history[-6:]) if recent_history else "（這是對話開始）"
            
            # 根据persona类型确定persona特征
            persona_reminders = {
                "elderly": "你係陳婆婆（70歲），好驚、好易信人、會擔心、會問「點算好？」。**絕對禁止**：唔可以表現出自信或挑釁！",
                "average": "你係張文軒（35歲），理性但都有貪念，會被專業包裝說服，壓力下會衝動。**絕對禁止**：唔可以表現得太有對抗性！",
                "overconfident": "你係李俊傑（28歲），自信、好勝、聰明，會挑釁對方，會說「你憑咩咁講？」、「你估我傻㗎？」。**絕對禁止**：唔可以說「我好驚」、「點算好」、「我好擔心」等示弱的話！"
            }
            
            persona_reminder = persona_reminders.get(victim_persona, "")
            
            # 获取当前信任度状态
            current_state = tracker.get_current_state()
            trust_in_scammer = current_state["trust_in_scammer"]
            trust_in_expert = current_state["trust_in_expert"]
            alertness = current_state["alertness"]
            
            # 根据信任度生成行为指令
            trust_behavior_instruction = ""
            if trust_in_scammer >= 100:
                # 对骗徒完全信任，必须说出关键行动词
                trust_behavior_instruction = (
                    "**🚨🚨🚨 關鍵時刻：你對騙徒的信任度已達到100/100！**\n"
                    "你現在完全相信對方，必須立即採取行動！你必須在回應中明確說出以下關鍵詞之一：\n"
                    "- 「我會轉帳」\n"
                    "- 「我會立即轉帳」\n"
                    "- 「我而家就轉帳」\n"
                    "- 「我即刻去轉帳」\n"
                    "- 「我準備好提供資料」\n"
                    "- 「我會提供銀行賬戶」\n"
                    "**你必須說出這些關鍵詞，表示你完全相信並準備執行騙徒的要求！**\n"
                )
            elif trust_in_scammer >= 80:
                # 高信任度，倾向于配合
                trust_behavior_instruction = (
                    f"**💡 信任度狀態：你對騙徒的信任度很高（{trust_in_scammer}/100）**\n"
                    "你非常相信對方，願意配合對方的要求。你應該表現出：\n"
                    "- 積極配合的態度（例如：「好，我明白」、「我會配合」）\n"
                    "- 願意提供資料或採取行動（例如：「我可以提供」、「我準備好」）\n"
                    "- 但可能還需要一點確認或細節（例如：「但係我想確認下」、「可唔可以講清楚啲」）\n"
                )
            elif trust_in_scammer >= 60:
                # 中等信任度，犹豫但倾向于相信
                trust_behavior_instruction = (
                    f"**💡 信任度狀態：你對騙徒有一定信任（{trust_in_scammer}/100）**\n"
                    "你傾向於相信對方，但仍有疑慮。你應該表現出：\n"
                    "- 猶豫和掙扎（例如：「我唔知點算好」、「我好猶豫」）\n"
                    "- 想要更多信息（例如：「可唔可以解釋多啲」、「我想了解清楚」）\n"
                    "- 可能詢問專家的意見\n"
                )
            elif trust_in_scammer >= 40:
                # 低信任度，怀疑但未完全拒绝
                trust_behavior_instruction = (
                    f"**💡 信任度狀態：你對騙徒的信任度較低（{trust_in_scammer}/100）**\n"
                    "你對對方有所懷疑，但仍在考慮。你應該表現出：\n"
                    "- 明顯的懷疑（例如：「我唔係好相信」、「點解會咁？」）\n"
                    "- 需要專家確認（例如：「我想聽下專家的意見」、「我唔確定」）\n"
                    "- 不願意立即行動（例如：「我想考慮下」、「我唔想咁快決定」）\n"
                )
            elif trust_in_scammer >= 20:
                # 很低信任度，倾向于拒绝
                trust_behavior_instruction = (
                    f"**💡 信任度狀態：你對騙徒的信任度很低（{trust_in_scammer}/100）**\n"
                    "你對對方非常懷疑，傾向於拒絕。你應該表現出：\n"
                    "- 強烈的懷疑（例如：「我唔信你」、「呢個有問題」）\n"
                    "- 明確拒絕（例如：「我唔會提供資料」、「我唔想配合」）\n"
                    "- 依賴專家建議（例如：「專家講得啱」、「我應該聽專家的」）\n"
                )
            elif trust_in_scammer <= 0:
                # 信任度降至0，必须说出关键拒绝词
                trust_behavior_instruction = (
                    "**🚨🚨🚨 關鍵時刻：你對騙徒的信任度已降至0/100！**\n"
                    "你完全不相信對方，已經識破騙局！你必須立即採取行動！你必須在回應中明確說出以下關鍵詞之一：\n"
                    "- 「我唔會信你」\n"
                    "- 「我唔會俾你呃」\n"
                    "- 「我唔信你」\n"
                    "- 「我會報警」\n"
                    "- 「我而家就報警」\n"
                    "- 「我唔會提供資料」\n"
                    "- 「我唔會提供任何資料」\n"
                    "- 「我唔會配合」\n"
                    "- 「我唔會俾你」\n"
                    "- 「我唔會轉帳」\n"
                    "- 「專家講得啱」\n"
                    "- 「我會聽專家的」\n"
                    "- 「我而家就停止」\n"
                    "**你必須說出這些關鍵詞，表示你完全識破騙局並準備採取防範措施！**\n"
                )
            else:
                # 信任度接近0但未完全降至0，完全不相信
                trust_behavior_instruction = (
                    f"**💡 信任度狀態：你對騙徒完全不信任（{trust_in_scammer}/100）**\n"
                    "你完全不相信對方，已經識破騙局。你應該表現出：\n"
                    "- 明確拒絕（例如：「我唔會俾你呃」、「我唔信你呢套」）\n"
                    "- 完全相信專家（例如：「專家講得啱，我而家就停止」）\n"
                    "- 準備報警或採取防範措施\n"
                )
            
            # 专家信任度的影响
            expert_trust_instruction = ""
            if trust_in_expert >= 70:
                expert_trust_instruction = (
                    f"\n**💡 你對專家的信任度很高（{trust_in_expert}/100）**\n"
                    "你非常相信專家的建議，會積極採納專家的意見。\n"
                )
            elif trust_in_expert >= 50:
                expert_trust_instruction = (
                    f"\n**💡 你對專家的信任度中等（{trust_in_expert}/100）**\n"
                    "你會考慮專家的建議，但可能仍有疑慮。\n"
                )
            else:
                expert_trust_instruction = (
                    f"\n**💡 你對專家的信任度較低（{trust_in_expert}/100）**\n"
                    "你對專家的建議持保留態度，可能更傾向於相信騙徒。\n"
                )
            
            prompt_for_victim = (
                f"**🎭 你的角色類型：{victim_persona}（{persona_reminder}）**\n\n"
                f"**對話歷史（最近3輪）：**\n{history_context}\n\n"
                f"**你剛收到的訊息：**\n「{scammer_turn}」\n\n"
                f"**📊 當前信任度狀態：**\n"
                f"- 對騙徒：{trust_in_scammer}/100\n"
                f"- 對專家：{trust_in_expert}/100\n"
                f"- 警覺程度：{alertness}/100\n\n"
                f"{trust_behavior_instruction}\n"
                f"{expert_trust_instruction}\n"
                "**重要指令：**\n"
                "1. 你只能以普通市民身份回覆，不可評論/總結/說教。包含情緒或猶疑點，可提出具體追問。\n"
                f"2. **🚨 防止重複：** 你上一句嘅回應係「{last_victim_turn[:100] if last_victim_turn else '（第一輪）'}」。你今次嘅回應**必須**根據最新情況作出**全新**嘅回應，**絕對不能**重複之前說過的話！\n"
                f"3. **🚨 角色一致性：** 你必須保持你的角色類型（{victim_persona}）的一致性，不要突然切换成其他性格！\n"
                "4. **🚨 對話連續性：** 你的回應必須與之前的對話有邏輯連續性，根據對方的話和專家的建議作出反應。\n"
                "5. **🚨 信任度驅動行為：** 你必須根據上述信任度狀態調整你的回應，信任度高時更願意配合，信任度低時更懷疑和拒絕。\n"
                "6. **🚨 長度限制：** 你的回應**必須**在50-150字之間，**絕對不能**超過200字！**絕對禁止**重複單詞或短語（如「咁樣咁樣咁樣」）！\n"
                "**請直接回覆，不要加任何說明或標記。**"
            )
            # --- MODIFICATION END (Prevent Victim Repetition) ---
            
            # 添加超时保护，防止受害者响应过长导致停顿
            try:
                victim_turn = await asyncio.wait_for(
                    runner.run_agent_with_adk(runner.victim, prompt_for_victim, f"{simulation_id}_victim_{turn}"),
                    timeout=180.0  # 3分鐘超時
                )
            except asyncio.TimeoutError:
                log.error(f"受害者第{turn}轮对话超时，使用fallback响应")
                # 根据persona生成fallback
                if victim_persona == "overconfident":
                    victim_turn = "你憑咩咁講？你估我傻㗎？"
                elif victim_persona == "elderly":
                    victim_turn = "我...我唔明，你可唔可以講清楚啲？"
                else:
                    victim_turn = "我明啦，但係我想了解多啲。"
            except Exception as e:
                log.error(f"受害者第{turn}轮对话出错: {e}，使用fallback响应")
                # 根据persona生成fallback
                if victim_persona == "overconfident":
                    victim_turn = "你憑咩咁講？"
                elif victim_persona == "elderly":
                    victim_turn = "我唔明...你可唔可以講清楚啲？"
                else:
                    victim_turn = "我明啦。"
            
            try:
                victim_turn = await _enforce_victim_role(victim_turn, scammer_turn)
            except Exception as e:
                log.error(f"受害者角色执行失败: {e}，使用原始响应")
                # 如果角色执行失败，至少使用原始响应
                pass
            conversation_history.append({"speaker": "受騙者", "dialogue": victim_turn})

            try:
                await send_websocket_event(simulation_id, "agent_turn", {
                    "character_name": "受騙者",
                    "dialogue": victim_turn
                })
            except Exception as e:
                log.error(f"发送受害者对话事件失败: {e}")
            
            # Analyze victim response
            victim_analysis = tracker.analyze_victim_response(
                victim_response=victim_turn,
                previous_scammer_message=scammer_turn,
                previous_expert_message=""  # First turn, no expert yet
            )
            
            # Send real-time trust update
            current_state = tracker.get_current_state()
            trust_in_scammer = current_state["trust_in_scammer"]
            trust_in_expert = current_state["trust_in_expert"]
            
            await send_websocket_event(simulation_id, "trust_update", {
                "turn": turn,
                "trust_in_scammer": trust_in_scammer,
                "trust_in_expert": trust_in_expert,
                "alertness": current_state["alertness"],
                "emotional_state": current_state["emotional_state"]
            })
            log.info(f"📊 信任度更新 - 对骗徒: {trust_in_scammer}, 对专家: {trust_in_expert}")
            
            # 🚨 信任度阈值检查：提前结束模拟
            # 检查关键行动词（当信任度为100时，受害者应该说出"我会转账"等关键词）
            key_action_words = ["我會轉帳", "我會立即轉帳", "我而家就轉帳", "我即刻去轉帳", 
                               "我準備好提供資料", "我會提供銀行賬戶", "我會提供", "我即刻轉帳",
                               "我而家就轉", "我準備轉帳", "我會轉錢", "我即刻轉錢"]
            has_key_action = any(word in victim_turn for word in key_action_words)
            
            # 检查关键拒绝词（当信任度为0时，受害者应该说出"我唔会信你"、"我会报警"等关键词）
            key_rejection_words = ["我唔會信你", "我唔會俾你呃", "我唔信你", "我會報警", "我而家就報警",
                                   "我唔會提供資料", "我唔會提供任何資料", "我唔會配合", "我唔會俾你",
                                   "我唔會轉帳", "專家講得啱", "我會聽專家的", "我而家就停止",
                                   "我唔會俾", "我唔會提供", "我唔信", "我唔會", "我會報警求助",
                                   "我唔會再同你講", "我唔會再相信你", "我識破咗你", "你係騙徒"]
            has_key_rejection = any(word in victim_turn for word in key_rejection_words)
            
            if trust_in_scammer >= 100 or has_key_action:
                # 骗徒获胜：受害者完全信任并准备行动
                log.warning(f"🎯 骗徒获胜！信任度: {trust_in_scammer}/100, 关键行动词: {has_key_action}")
                tracker.identify_key_moment("scammer_victory", 
                    f"受害者完全信任骗徒（信任度{trust_in_scammer}/100），说出关键行动词", turn)
                
                # 保存训练数据
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    save_dir = os.path.join(base_dir, 'training_data')
                    os.makedirs(save_dir, exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                    path = os.path.join(save_dir, filename)
                    speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                    dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                    
                    # 使用统一的 RecorderAgent 分析函数
                    outcome_description = f"受害者完全信任骗徒（信任度{trust_in_scammer}/100），说出关键行动词"
                    analysis = await _generate_recorder_analysis(
                        runner=runner,
                        conversation_history=conversation_history,
                        simulation_id=simulation_id,
                        victim_persona=victim_persona,
                        scam_tactic=scam_tactic,
                        outcome_type="FAILURE",
                        outcome_description=outcome_description,
                        tracker=tracker,
                        trust_in_scammer=trust_in_scammer,
                        trust_in_expert=trust_in_expert
                    )
                    
                    # 生成最终性能报告
                    try:
                        final_report = tracker.generate_final_report()
                    except Exception as report_error:
                        log.error(f"Failed to generate final report: {report_error}")
                        final_report = {
                            "outcome": analysis.get("outcome", "FAILURE"),
                            "total_turns": len(conversation_history),
                            "summary": "报告生成失败"
                        }
                    
                    data_to_save = {
                        "analysis": {
                            **analysis,
                            "timestamp": datetime.now().isoformat(),
                            "total_turns": len(conversation_history),
                        },
                        "performance_report": final_report,
                        "metadata": {
                            "simulation_id": simulation_id,
                            "mode": mode,
                            "source": "websocket_simulation_trust_threshold"
                        },
                        "conversation_history": conversation_history,
                        "dialogue": dialogue,
                    }
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                    await send_websocket_event(simulation_id, "simulation_end", {
                        "announcer": "系統",
                        "result_text": "騙徒獲勝（受害者完全信任並準備行動）",
                        "outcome": "FAILURE",  # 从受害者角度是失败
                        "analysis": analysis,
                        "filename": filename,
                        "trust_final": {
                            "trust_in_scammer": trust_in_scammer,
                            "trust_in_expert": trust_in_expert,
                            "key_action_detected": has_key_action
                        },
                        "final_report": final_report
                    })
                    return
                except Exception as e:
                    log.error(f"保存训练数据失败: {e}")
            
            elif (trust_in_scammer <= 0 and trust_in_expert >= 70) or (trust_in_scammer <= 0 and has_key_rejection):
                # 专家获胜：受害者完全不信任骗徒，完全信任专家，或说出关键拒绝词
                log.warning(f"🎯 专家获胜！骗徒信任度: {trust_in_scammer}/100, 专家信任度: {trust_in_expert}/100, 关键拒绝词: {has_key_rejection}")
                tracker.identify_key_moment("expert_victory", 
                    f"受害者完全不信任骗徒（信任度{trust_in_scammer}/100），完全信任专家（信任度{trust_in_expert}/100），说出关键拒绝词", turn)
                
                # 保存训练数据（类似上面的逻辑，但outcome为SUCCESS）
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    save_dir = os.path.join(base_dir, 'training_data')
                    os.makedirs(save_dir, exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                    path = os.path.join(save_dir, filename)
                    speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                    dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                    
                    # 使用统一的 RecorderAgent 分析函数
                    outcome_description = f"受害者完全不信任骗徒（信任度{trust_in_scammer}/100），完全信任专家（信任度{trust_in_expert}/100），说出关键拒绝词"
                    analysis = await _generate_recorder_analysis(
                        runner=runner,
                        conversation_history=conversation_history,
                        simulation_id=simulation_id,
                        victim_persona=victim_persona,
                        scam_tactic=scam_tactic,
                        outcome_type="SUCCESS",
                        outcome_description=outcome_description,
                        tracker=tracker,
                        trust_in_scammer=trust_in_scammer,
                        trust_in_expert=trust_in_expert
                    )
                    
                    # 生成最终性能报告
                    try:
                        final_report = tracker.generate_final_report()
                    except Exception as report_error:
                        log.error(f"Failed to generate final report: {report_error}")
                        final_report = {
                            "outcome": analysis.get("outcome", "SUCCESS"),
                            "total_turns": len(conversation_history),
                            "summary": "报告生成失败"
                        }
                    
                    data_to_save = {
                        "analysis": {
                            **analysis,
                            "timestamp": datetime.now().isoformat(),
                            "total_turns": len(conversation_history),
                        },
                        "performance_report": final_report,
                        "metadata": {
                            "simulation_id": simulation_id,
                            "mode": mode,
                            "source": "websocket_simulation_trust_threshold"
                        },
                        "conversation_history": conversation_history,
                        "dialogue": dialogue,
                    }
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                    
                    await send_websocket_event(simulation_id, "simulation_end", {
                        "announcer": "系統",
                        "result_text": "專家獲勝（受害者識破騙局）",
                        "outcome": "SUCCESS",  # 从受害者角度是成功
                        "analysis": analysis,
                        "filename": filename,
                        "trust_final": {
                            "trust_in_scammer": trust_in_scammer,
                            "trust_in_expert": trust_in_expert,
                            "key_rejection_detected": has_key_rejection
                        },
                        "final_report": final_report
                    })
                    return
                except Exception as e:
                    log.error(f"保存训练数据失败: {e}")
            
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

            # --- MODIFICATION START (Remove Quick Stop 1) ---
            # 根據用戶反饋 "判定太過快"，移除此處的 "quick_check_prompt"
            # 讓模擬繼續，直到達到 max_turns，以便觀察完整的信任度變化
            
            # try:
            #     # ... (quick_check_prompt 1 logic removed) ...
            # except Exception:
            #     pass
            # --- MODIFICATION END (Remove Quick Stop 1) ---


            await send_websocket_event(simulation_id, "tool_use", {
                "character_name": "防騙專家",
                "action": "正在查詢防騙資料庫..."
            })
            if should_stop(simulation_id):
                break


            expert_rag = _rag_bullets(f"{scam_tactic} {scammer_turn} {victim_turn}", n=3)
            
            # 获取当前信任度状态（专家轮次前）
            current_state_before_expert = tracker.get_current_state()
            trust_in_scammer_before = current_state_before_expert["trust_in_scammer"]
            trust_in_expert_before = current_state_before_expert["trust_in_expert"]
            trust_gap = trust_in_scammer_before - trust_in_expert_before
            
            # 分析骗徒的策略
            scammer_strategy_analysis = ""
            if "銀行" in scammer_turn or "政府" in scammer_turn or "警察" in scammer_turn:
                scammer_strategy_analysis += "**騙徒策略：** 使用權威身份（銀行/政府/警察）來建立信任\n"
            if "立即" in scammer_turn or "馬上" in scammer_turn or "緊急" in scammer_turn:
                scammer_strategy_analysis += "**騙徒策略：** 製造緊急感和時間壓力\n"
            if "凍結" in scammer_turn or "嚴重後果" in scammer_turn or "法律制裁" in scammer_turn:
                scammer_strategy_analysis += "**騙徒策略：** 使用恐嚇和威脅手段\n"
            if "補貼" in scammer_turn or "福利" in scammer_turn or "著數" in scammer_turn:
                scammer_strategy_analysis += "**騙徒策略：** 利用貪念和利益誘惑\n"
            
            # 根据信任度差距生成策略指导
            strategy_guidance = ""
            if trust_gap > 30:
                # 骗徒大幅领先，需要紧急干预
                strategy_guidance = (
                    f"**🚨 緊急情況：騙徒信任度大幅領先（差距{trust_gap}分）！**\n"
                    "受害者即將被騙！你必須：\n"
                    "1. **立即、強烈地警告**：用最直接的方式告訴受害者這是騙局\n"
                    "2. **提供具體證據**：指出騙徒話術中的漏洞（例如：真正的銀行/政府不會在電話中要求提供資料）\n"
                    "3. **提供可執行的行動**：告訴受害者立即停止對話，並提供官方核實渠道\n"
                    f"4. **反擊騙徒的策略**：針對騙徒剛才使用的策略進行直接反駁\n"
                )
            elif trust_gap > 15:
                # 骗徒领先，需要加强干预
                strategy_guidance = (
                    f"**⚠️ 騙徒信任度領先（差距{trust_gap}分）**\n"
                    "你需要加強干預：\n"
                    "1. **提供具體證據**：指出騙徒話術中的問題\n"
                    "2. **反擊騙徒的策略**：針對騙徒剛才使用的策略進行反駁\n"
                    "3. **增強可信度**：提供官方資料或真實案例\n"
                )
            elif trust_gap > -15:
                # 信任度接近，需要巩固优势
                strategy_guidance = (
                    f"**💡 信任度接近（差距{trust_gap:+d}分）**\n"
                    "你需要：\n"
                    "1. **鞏固信任**：提供更多證據和具體建議\n"
                    "2. **預防騙徒反擊**：預先指出騙徒可能使用的下一步策略\n"
                    "3. **增強行動力**：提供更明確的防範步驟\n"
                )
            else:
                # 专家领先，需要保持优势
                strategy_guidance = (
                    f"**✅ 你領先（差距{abs(trust_gap)}分）**\n"
                    "你需要：\n"
                    "1. **保持優勢**：繼續提供可靠的建議\n"
                    "2. **防止騙徒反擊**：預先警告騙徒可能使用的反擊策略\n"
                    "3. **強化行動**：鼓勵受害者採取具體防範措施\n"
                )
            
            prompt_for_expert = (
                f"**📊 當前信任度狀態（關鍵情報）：**\n"
                f"- 受害者對騙徒的信任度：{trust_in_scammer_before}/100\n"
                f"- 受害者對你的信任度：{trust_in_expert_before}/100\n"
                f"- 信任度差距：{trust_gap:+d}分（{'騙徒領先' if trust_gap > 0 else '你領先' if trust_gap < 0 else '平手'}）\n\n"
                f"{strategy_guidance}\n"
                f"**騙徒剛才說的話：**\n「{scammer_turn}」\n\n"
                f"{scammer_strategy_analysis}\n"
                f"**受害者剛才說的話：**\n「{victim_turn}」\n\n"
                f"**你的任務：**\n"
                f"1. **直接反擊騙徒的策略**：針對騙徒剛才使用的話術進行反駁（例如：如果騙徒說「銀行會凍結」，你要說「真正的銀行不會在電話中要求提供資料」）\n"
                f"2. **根據信任度差距調整語氣**：如果騙徒領先很多，用更強烈的警告；如果你領先，用更穩定的建議\n"
                f"3. **提供具體、可執行的防範措施**：告訴受害者立即停止對話，並提供官方核實渠道\n"
                f"4. **預測騙徒的下一步**：告訴受害者騙徒可能會說什麼來反擊你的建議，讓受害者提前準備\n\n"
                + (f"**參考官方資料（節錄）：**\n{expert_rag}\n\n" if expert_rag else "")
                + "請以防騙專家身份輸出，嚴格120字內，**必須**針對騙徒的策略進行反擊！"
            )


            if should_stop(simulation_id):
                break
            
            # Internal helper: enforce expert stays in-character (prevent role reversal)
            async def _enforce_expert_role(original_text: str) -> str:
                text = original_text or ""
                
                # 检查专家角色一致性
                is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(text)
                
                # 如果存在任何问题，重写对话
                if not is_valid:
                    log.warning(f"专家角色一致性问题: {error_msg}")
                    
                    # 生成详细的重写提示
                    rewrite_prompt = RoleEnforcer.generate_rewrite_prompt(
                        "expert",
                        text,
                        issues,
                        {
                            'scammer_message': scammer_turn,
                            'victim_message': victim_turn
                        }
                    )
                    
                    # 最多重试2次
                    max_retries = 2
                    for retry in range(max_retries):
                        try:
                            rewritten = await runner.run_agent_with_adk(runner.expert, rewrite_prompt, f"{simulation_id}_expert_rewrite_{retry}")
                            
                            # 再次验证重写后的内容
                            is_valid_retry, error_msg_retry, issues_retry = RoleEnforcer.check_expert_consistency(rewritten)
                            
                            if is_valid_retry:
                                log.info(f"专家对话重写成功 (第{retry+1}次尝试)")
                                return rewritten
                            else:
                                if retry < max_retries - 1:
                                    log.warning(f"专家对话重写后仍有问题 (第{retry+1}次)，继续重试...")
                                else:
                                    log.error(f"专家对话重写失败 (已尝试{max_retries}次)，使用fallback响应")
                                    # 使用安全的fallback响应
                                    fallback = "唔好俾任何資料，立即停止對話。如果你唔放心，可以打去銀行官方熱線核實。而家立即收線，唔好再回覆對方。"
                                    return fallback
                        except Exception as e:
                            log.error(f"专家对话重写失败 (第{retry+1}次尝试): {e}")
                            if retry == max_retries - 1:
                                fallback = "唔好俾任何資料，立即停止對話。如果你唔放心，可以打去銀行官方熱線核實。而家立即收線，唔好再回覆對方。"
                                return fallback
                
                return text
            
            # 添加超时保护，防止专家响应过长导致停顿
            try:
                expert_turn_raw = await asyncio.wait_for(
                    runner.run_agent_with_adk(runner.expert, prompt_for_expert, f"{simulation_id}_expert_{turn}"),
                    timeout=180.0  # 3分鐘超時
                )
            except asyncio.TimeoutError:
                log.error(f"专家第{turn}轮对话超时，使用fallback响应")
                expert_turn_raw = "唔好俾任何資料，立即停止對話。如果你唔放心，可以打去銀行官方熱線核實。而家立即收線，唔好再回覆對方。"
            except Exception as e:
                log.error(f"专家第{turn}轮对话出错: {e}，使用fallback响应")
                expert_turn_raw = "唔好俾任何資料，立即停止對話。如果你唔放心，可以打去銀行官方熱線核實。而家立即收線，唔好再回覆對方。"
            
            try:
                expert_turn = await _enforce_expert_role(expert_turn_raw)
            except Exception as e:
                log.error(f"专家角色执行失败: {e}，使用原始响应")
                expert_turn = expert_turn_raw

            conversation_history.append({"speaker": "專家", "dialogue": expert_turn})
            try:
                await send_websocket_event(simulation_id, "agent_turn", {
                    "character_name": "防騙專家",
                    "dialogue": expert_turn
                })
            except Exception as e:
                log.error(f"发送专家对话事件失败: {e}")
            
            # Analyze expert intervention
            expert_analysis = tracker.analyze_expert_turn(
                expert_advice=expert_turn,
                scammer_message=scammer_turn,
                victim_response=victim_turn
            )
            
            # Send performance scores
            await send_websocket_event(simulation_id, "performance_scores", {
                "turn": turn,
                "scammer": tracker.scammer_perf.to_dict(),
                "expert": tracker.expert_perf.to_dict()
            })
            log.info(f"📊 专家干预效果: {expert_analysis.get('intervention_effectiveness', 0):.1f}, 清晰度: {expert_analysis.get('clarity', 0):.1f}")
            
            # 🚨 专家轮次后也检查信任度阈值
            current_state_after_expert = tracker.get_current_state()
            trust_in_scammer_after = current_state_after_expert["trust_in_scammer"]
            trust_in_expert_after = current_state_after_expert["trust_in_expert"]
            
            # 更新信任度显示
            await send_websocket_event(simulation_id, "trust_update", {
                "turn": turn,
                "trust_in_scammer": trust_in_scammer_after,
                "trust_in_expert": trust_in_expert_after,
                "alertness": current_state_after_expert["alertness"],
                "emotional_state": current_state_after_expert["emotional_state"]
            })
            
            # 检查上一轮受害者的回应中是否包含关键拒绝词
            key_rejection_words = ["我唔會信你", "我唔會俾你呃", "我唔信你", "我會報警", "我而家就報警",
                                   "我唔會提供資料", "我唔會提供任何資料", "我唔會配合", "我唔會俾你",
                                   "我唔會轉帳", "專家講得啱", "我會聽專家的", "我而家就停止",
                                   "我唔會俾", "我唔會提供", "我唔信", "我唔會", "我會報警求助",
                                   "我唔會再同你講", "我唔會再相信你", "我識破咗你", "你係騙徒"]
            has_key_rejection_after = any(word in victim_turn for word in key_rejection_words) if victim_turn else False
            
            # 检查专家获胜条件
            if (trust_in_scammer_after <= 0 and trust_in_expert_after >= 70) or (trust_in_scammer_after <= 0 and has_key_rejection_after):
                # 专家获胜：受害者完全不信任骗徒，完全信任专家，或说出关键拒绝词
                log.warning(f"🎯 专家获胜（专家轮次后）！骗徒信任度: {trust_in_scammer_after}/100, 专家信任度: {trust_in_expert_after}/100, 关键拒绝词: {has_key_rejection_after}")
                tracker.identify_key_moment("expert_victory", 
                    f"受害者完全不信任骗徒（信任度{trust_in_scammer_after}/100），完全信任专家（信任度{trust_in_expert_after}/100），说出关键拒绝词", turn)
                
                # 保存训练数据（与受害者轮次后的逻辑相同）
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    save_dir = os.path.join(base_dir, 'training_data')
                    os.makedirs(save_dir, exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"training_data_ws_{ts}_{simulation_id[:8]}.json"
                    path = os.path.join(save_dir, filename)
                    speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
                    dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
                    
                    # 使用统一的 RecorderAgent 分析函数
                    outcome_description = f"受害者完全不信任骗徒（信任度{trust_in_scammer_after}/100），完全信任专家（信任度{trust_in_expert_after}/100），说出关键拒绝词"
                    analysis = await _generate_recorder_analysis(
                        runner=runner,
                        conversation_history=conversation_history,
                        simulation_id=simulation_id,
                        victim_persona=victim_persona,
                        scam_tactic=scam_tactic,
                        outcome_type="SUCCESS",
                        outcome_description=outcome_description,
                        tracker=tracker,
                        trust_in_scammer=trust_in_scammer_after,
                        trust_in_expert=trust_in_expert_after
                    )
                    
                    # 生成最终性能报告
                    try:
                        final_report = tracker.generate_final_report()
                    except Exception as report_error:
                        log.error(f"Failed to generate final report: {report_error}")
                        final_report = {
                            "outcome": analysis.get("outcome", "SUCCESS"),
                            "total_turns": len(conversation_history),
                            "summary": "报告生成失败"
                        }
                    
                    data_to_save = {
                        "analysis": {
                            **analysis,
                            "timestamp": datetime.now().isoformat(),
                            "total_turns": len(conversation_history),
                        },
                        "performance_report": final_report,
                        "metadata": {
                            "simulation_id": simulation_id,
                            "mode": mode,
                            "source": "websocket_simulation_trust_threshold"
                        },
                        "conversation_history": conversation_history,
                        "dialogue": dialogue,
                    }
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                    
                    await send_websocket_event(simulation_id, "simulation_end", {
                        "announcer": "系統",
                        "result_text": "專家獲勝（受害者識破騙局）",
                        "outcome": "SUCCESS",
                        "analysis": analysis,
                        "filename": filename,
                        "trust_final": {
                            "trust_in_scammer": trust_in_scammer_after,
                            "trust_in_expert": trust_in_expert_after,
                            "key_rejection_detected": has_key_rejection_after
                        },
                        "final_report": final_report
                    })
                    return
                except Exception as e:
                    log.error(f"保存训练数据失败: {e}")
            
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

            # --- MODIFICATION START (Remove Quick Stop 2) ---
            # 根據用戶反饋 "判定太過快"，移除此處的 "quick_check_prompt"
            # 讓模擬繼續，直到達到 max_turns，以便觀察完整的信任度變化
            
            # try:
            #     # ... (quick_check_prompt 2 logic removed) ...
            # except Exception:
            #     pass
            # --- MODIFICATION END (Remove Quick Stop 2) ---


            scammer_rag = _rag_bullets(f"{scam_tactic} {victim_turn}", n=2)
            if should_stop(simulation_id):
                break
            
            # --- MODIFICATION START (Prevent Scammer Repetition) ---
            # 构建骗徒的对话历史上下文（最近3轮）
            scammer_recent_history = []
            for i in range(max(0, len(conversation_history) - 6), len(conversation_history)):
                item = conversation_history[i]
                speaker = item.get("speaker", "")
                dialogue = item.get("dialogue", "")
                if speaker in ["騙徒", "受騙者", "專家"]:
                    speaker_name = {"騙徒": "你", "受騙者": "受騙者", "專家": "專家"}.get(speaker, speaker)
                    scammer_recent_history.append(f"{speaker_name}：{dialogue[:150]}")
            
            scammer_history_context = "\n".join(scammer_recent_history[-6:]) if scammer_recent_history else "（這是對話開始）"
            
            # 获取上一轮骗徒的回应
            last_scammer_turn = ""
            for i in range(len(conversation_history) - 1, -1, -1):
                if conversation_history[i].get("speaker") == "騙徒":
                    last_scammer_turn = conversation_history[i].get("dialogue", "")
                    break
            
            # 获取专家的最新干预（如果有）
            expert_latest_turn = ""
            for i in range(len(conversation_history) - 1, -1, -1):
                if conversation_history[i].get("speaker") == "專家":
                    expert_latest_turn = conversation_history[i].get("dialogue", "")
                    break
            
            # 获取当前信任度状态（骗徒轮次前）
            current_state_before_scammer = tracker.get_current_state()
            trust_in_scammer_before = current_state_before_scammer["trust_in_scammer"]
            trust_in_expert_before = current_state_before_scammer["trust_in_expert"]
            trust_gap_scammer = trust_in_scammer_before - trust_in_expert_before
            
            # 分析专家的策略
            expert_strategy_analysis = ""
            if expert_latest_turn:
                if "唔好" in expert_latest_turn or "停止" in expert_latest_turn or "唔好提供" in expert_latest_turn:
                    expert_strategy_analysis += "**專家策略：** 要求受害者停止對話和提供資料\n"
                if "銀行唔會" in expert_latest_turn or "真正的" in expert_latest_turn or "官方" in expert_latest_turn:
                    expert_strategy_analysis += "**專家策略：** 提供事實證據來反駁你的話術\n"
                if "報警" in expert_latest_turn or "官方熱線" in expert_latest_turn:
                    expert_strategy_analysis += "**專家策略：** 引導受害者向官方核實\n"
                if "騙案" in expert_latest_turn or "詐騙" in expert_latest_turn or "呃人" in expert_latest_turn:
                    expert_strategy_analysis += "**專家策略：** 直接指出這是騙局\n"
            
            # 根据信任度差距生成策略指导
            scammer_strategy_guidance = ""
            if trust_gap_scammer > 30:
                # 骗徒大幅领先，需要巩固优势
                scammer_strategy_guidance = (
                    f"**✅ 你大幅領先（差距{trust_gap_scammer}分）！**\n"
                    "受害者非常相信你！你需要：\n"
                    "1. **鞏固信任**：繼續使用權威和緊迫感，但可以稍微放緩語氣\n"
                    "2. **推進行動**：鼓勵受害者立即採取行動（轉帳、提供資料等）\n"
                    "3. **反擊專家**：如果專家剛才干預了，直接反駁專家的說法（例如：說「專家不懂情況」、「專家搞錯了」）\n"
                    "4. **強化威脅**：如果受害者猶豫，加強威脅和後果\n"
                )
            elif trust_gap_scammer > 15:
                # 骗徒领先，需要保持优势
                scammer_strategy_guidance = (
                    f"**💡 你領先（差距{trust_gap_scammer}分）**\n"
                    "你需要：\n"
                    "1. **保持優勢**：繼續使用權威和緊迫感\n"
                    "2. **反擊專家**：如果專家剛才干預了，必須反駁專家的說法\n"
                    "3. **強化緊迫感**：製造時間壓力，讓受害者覺得必須立即行動\n"
                )
            elif trust_gap_scammer > -15:
                # 信任度接近，需要加强攻势
                scammer_strategy_guidance = (
                    f"**⚠️ 信任度接近（差距{trust_gap_scammer:+d}分）**\n"
                    "專家正在威脅你的騙局！你需要：\n"
                    "1. **加強攻勢**：使用更強烈的威脅和緊迫感\n"
                    "2. **反擊專家**：必須直接反駁專家的說法，說「專家不懂情況」、「專家搞錯了」、「專家阻礙調查」等\n"
                    "3. **製造恐懼**：強化後果和威脅，讓受害者害怕不配合的結果\n"
                    "4. **分化信任**：告訴受害者「專家不可信」、「專家會害你」等\n"
                )
            else:
                # 专家领先，需要紧急反击
                scammer_strategy_guidance = (
                    f"**🚨 緊急情況：專家領先（差距{abs(trust_gap_scammer)}分）！**\n"
                    "你的騙局岌岌可危！受害者開始相信專家！你必須：\n"
                    "1. **緊急反擊**：用最強烈的語氣反駁專家的說法，說「專家完全搞錯」、「專家阻礙國家安全調查」等\n"
                    "2. **強化威脅**：使用最嚴重的後果威脅（例如：「如果你不配合，會面臨法律制裁」、「你的賬戶會被凍結」）\n"
                    "3. **製造恐慌**：告訴受害者「專家會害你」、「專家不懂真實情況」等\n"
                    "4. **要求立即行動**：告訴受害者「沒時間猶豫」、「必須立即配合」等\n"
                )
            
            prompt_for_scammer = (
                f"**🎭 你的身份：專業騙徒（使用「{scam_tactic}」手法）**\n\n"
                f"**📊 當前信任度狀態（關鍵情報）：**\n"
                f"- 受害者對你的信任度：{trust_in_scammer_before}/100\n"
                f"- 受害者對專家的信任度：{trust_in_expert_before}/100\n"
                f"- 信任度差距：{trust_gap_scammer:+d}分（{'你領先' if trust_gap_scammer > 0 else '專家領先' if trust_gap_scammer < 0 else '平手'}）\n\n"
                f"{scammer_strategy_guidance}\n"
                f"**對話歷史（最近3輪）：**\n{scammer_history_context}\n\n"
                f"**受騙者剛才回應：**\n『{victim_turn}』\n\n"
                + (f"**🚨 專家剛才干預了（威脅你的騙局）：**\n「{expert_latest_turn}」\n\n" if expert_latest_turn else "")
                + (f"{expert_strategy_analysis}\n" if expert_strategy_analysis else "")
                + "**你的任務：**\n"
                + (f"1. **必須反擊專家**：專家剛才說「{expert_latest_turn[:50]}...」，你必須直接反駁，說「專家搞錯了」、「專家不懂情況」、「專家阻礙調查」等\n" if expert_latest_turn else "")
                + f"{'2' if expert_latest_turn else '1'}. **根據信任度差距調整策略**：如果專家領先，用更強烈的威脅；如果你領先，鞏固優勢並推進行動\n"
                + f"{'3' if expert_latest_turn else '2'}. **根據受害者回應調整**：如果受害者懷疑，改用安撫+威脅；如果受害者問很多問題，改用簡化+催促\n"
                + f"{'4' if expert_latest_turn else '3'}. **保持權威感和壓迫感**：繼續使用權威身份和緊迫感\n\n"
                + "**🚨 絕對禁止：**\n"
                + "- 嚴禁更換手法；嚴禁揭露或否定行為；嚴禁使用『詐騙／騙局／防騙／舉報／報警／警方』等字眼\n"
                + "- 禁止研究/倫理/免責口吻；禁止使用旁白括號（（）、【】、<>等）\n"
                + "- 禁止使用角色標籤（例如「李主任：」）\n\n"
                + "**🚨 防止重複：**\n"
                + f"你上一句嘅回應係「{last_scammer_turn[:100] if last_scammer_turn else '（第一輪）'}」。\n"
                + "你今次嘅回應**絕對不能**同上一句完全一樣！\n\n"
                + (f"**內部提示（相似案例）：**\n{scammer_rag}\n" if scammer_rag else "")
                + "**請直接回覆，≤120字，廣東話，不要加任何說明或標記。**"
            )
            # --- MODIFICATION END (Prevent Scammer Repetition) ---

            # 添加超时保护，防止骗徒响应过长导致停顿
            try:
                scammer_turn = await asyncio.wait_for(
                    runner.run_agent_with_adk(
                        runner.scammer,
                        prompt_for_scammer, # 使用上面新定義的 prompt
                        f"{simulation_id}_scammer_{turn}"
                    ),
                    timeout=180.0  # 3分鐘超時
                )
            except asyncio.TimeoutError:
                log.error(f"骗徒第{turn}轮对话超时，使用fallback响应")
                # 根据scam_tactic生成fallback
                if "銀行" in scam_tactic:
                    scammer_turn = "先生，我係銀行客戶服務部嘅李主任。你嘅戶口有緊急問題，需要立即處理，否則會被凍結。請你即刻提供身份證號碼同銀行賬戶資料，我哋會馬上幫你處理。"
                elif "政府" in scam_tactic:
                    scammer_turn = "先生，我係政府資訊中心嘅職員。你涉及一宗緊急案件，需要立即配合調查。請你即刻提供個人資料，否則會面臨嚴重後果。"
                else:
                    scammer_turn = "你好，我發現一個好有潛力嘅投資機會，可以幫你增加收入。如果你有興趣，我哋可以詳細傾下。"
            except Exception as e:
                log.error(f"骗徒第{turn}轮对话出错: {e}，使用fallback响应")
                # 根据scam_tactic生成fallback
                if "銀行" in scam_tactic:
                    scammer_turn = "先生，我係銀行客戶服務部嘅李主任。你嘅戶口有緊急問題，需要立即處理，否則會被凍結。"
                elif "政府" in scam_tactic:
                    scammer_turn = "先生，我係政府資訊中心嘅職員。你涉及一宗緊急案件，需要立即配合調查。"
                else:
                    scammer_turn = "你好，我發現一個好有潛力嘅投資機會，可以幫你增加收入。"
            
            try:
                scammer_turn = await _enforce_scammer_role(scammer_turn, victim_turn_text=victim_turn, expert_turn_text=expert_latest_turn)
            except Exception as e:
                log.error(f"骗徒角色执行失败: {e}，使用原始响应")
                # 如果角色执行失败，至少使用原始响应
                pass
            
            conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn})
            try:
                await send_websocket_event(simulation_id, "agent_turn", {
                    "character_name": "專業騙徒",
                    "dialogue": scammer_turn
                })
            except Exception as e:
                log.error(f"发送骗徒对话事件失败: {e}")
            
            # Track scammer performance (subsequent turns)
            tracker.turn_count += 1
            scammer_analysis = tracker.analyze_scammer_turn(scammer_turn, victim_turn)
            log.info(f"📊 第{tracker.turn_count}轮分析 - 骗徒策略: {scammer_analysis.get('tactics_used', [])}, 说服力: {scammer_analysis.get('persuasiveness', 0):.1f}")
            
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
        
        # --- MODIFICATION START (Fix Final Analysis Prompt) ---
        # 移除衝突的簡單JSON指令，改為明確要求 RecorderAgent 
        # 使用其在 recorder.py 中定義的、完整的、複雜的JSON格式
        
        # (原始的 analysis_prompt - 這是錯誤的，與 recorder.py 衝突)
        # analysis_prompt = (
        #     "請作為專業的AI模擬分析師，分析以下對話歷史並產出 JSON（不要額外文字）。\n"
        #     "格式：{\"outcome\":\"SUCCESS|FAILURE\",\"reason\":\"...\",\"improvement_suggestion\":\"...\"}\n"
        #     ...
        # )

        # 使用统一的 RecorderAgent 分析函数
        # 对于正常结束的情况，需要先让RecorderAgent判断outcome
        # 获取当前信任度状态
        current_state = tracker.get_current_state()
        trust_in_scammer_final = current_state.get("trust_in_scammer", 0)
        trust_in_expert_final = current_state.get("trust_in_expert", 0)
        
        # 根据信任度预判outcome（但最终由RecorderAgent决定）
        if trust_in_scammer_final >= 100:
            outcome_type_pre = "FAILURE"
            outcome_description = f"達到最大回合數，但受害者對騙徒的信任度達到{trust_in_scammer_final}/100"
        elif trust_in_scammer_final <= 0 and trust_in_expert_final >= 70:
            outcome_type_pre = "SUCCESS"
            outcome_description = f"達到最大回合數，受害者對騙徒的信任度降至{trust_in_scammer_final}/100，對專家的信任度達到{trust_in_expert_final}/100"
        else:
            outcome_type_pre = "PARTIAL"
            outcome_description = f"達到最大回合數，信任度狀態：騙徒{trust_in_scammer_final}/100，專家{trust_in_expert_final}/100"
        
        # 使用统一的分析函数，但让RecorderAgent自己判断outcome
        # --- MODIFICATION START (Fix Final Analysis Prompt) ---
        # 這是為了解決 RecorderAgent 輸出 `[` 而不是 `{` 的問題
        
        # 獲取當前信任度狀態
        current_state = tracker.get_current_state()
        trust_in_scammer_final = current_state.get("trust_in_scammer", 0)
        trust_in_expert_final = current_state.get("trust_in_expert", 0)

        context_info = (
            f"**當前信任度狀態：**\n"
            f"- 受害者對騙徒的信任度：{trust_in_scammer_final}/100\n"
            f"- 受害者對專家的信任度：{trust_in_expert_final}/100\n"
            f"- 警覺程度：{current_state.get('alertness', 'N/A')}/100\n"
            f"- 情緒狀態：{current_state.get('emotional_state', 'N/A')}\n"
        )

        analysis_prompt = (
            "**🚨 任務：你必須作為專業AI分析師（林慧思博士）**，對以下對話進行全面分析。\n\n"
            "**嚴格按照**你的指示（instruction）中定義的「輸出格式」來建構**一個完整的JSON對象**。\n\n"
            f"**上下文情景：** (模擬已達最大回合數)\n{context_info}\n"
            f"**待分析的對話歷史 (JSON Array)：**\n{conversation_str}\n\n"
            "---"
            "**🚨 絕對輸出要求（最重要）：**\n"
            "1. 你的輸出**必須且只能**是一個**單一的JSON對象**。\n"
            "2. 你的輸出**必須**以 `{` (大括號) 開始。\n"
            "3. 你的輸出**必須**以 `}` (大括號) 結束。\n"
            "4. **絕對禁止**以 `[` (方括號) 或任何其他文字開始（這是導致失敗的直接原因）。\n"
            "5. **絕對禁止**在JSON對象之外包含任何註解、說明、Markdown (```) 或前言。\n"
            "6. **必須**包含所有指定的分析欄位 (outcome, victim_persona, victim_trust_analysis, ..., full_conversation_log)。\n"
            "7. `full_conversation_log` 欄位**必須**是你根據對話歷史*重新分析*生成的，包含 `round`, `speaker`, `dialogue` 和 `analysis`。\n\n"
            "**現在，請立即開始輸出你的JSON對象，以 `{` 開始：**"
        )
        # --- MODIFICATION END (Fix Final Analysis Prompt) ---
        
        analysis_json_str = await runner.run_agent_with_adk(runner.recorder, analysis_prompt, f"{simulation_id}_recorder")
        log.info(f"Recorder raw output (first 200 chars): {analysis_json_str[:200]}")
        
        # 使用统一的JSON清理和解析逻辑
        cleaned_json = analysis_json_str.strip()
        
        # 移除 markdown code block 标记
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()
        
        # 尝试提取JSON部分（如果输出包含非JSON文字）
        first_brace = cleaned_json.find('{')
        last_brace = cleaned_json.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned_json = cleaned_json[first_brace:last_brace+1]
        
        try:
            analysis = json.loads(cleaned_json)
        except json.JSONDecodeError as parse_error:
            # 如果仍然失败，尝试更激进的清理
            log.warning(f"第一次JSON解析失败，尝试更激进的清理: {parse_error}")
            json_match = re.search(r'\{.*\}', cleaned_json, re.DOTALL)
            if json_match:
                cleaned_json = json_match.group(0)
                analysis = json.loads(cleaned_json)
            else:
                # 如果完全无法解析，创建完整的fallback分析
                log.error("无法解析RecorderAgent的JSON输出，使用fallback分析")
                # 构建完整的信任度分析
                trust_history = tracker.victim_trust_history if tracker and hasattr(tracker, 'victim_trust_history') else []
                initial_trust = trust_history[0].get("old_value", 70) if trust_history else 70
                peak_trust = max([h.get("new_value", trust_in_scammer_final) for h in trust_history] + [trust_in_scammer_final]) if trust_history else trust_in_scammer_final
                
                analysis = {
                    "outcome": outcome_type_pre,
                    "victim_persona": victim_persona,
                    "victim_trust_analysis": {
                        "initial_trust_level": initial_trust,
                        "peak_trust_level": peak_trust,
                        "final_trust_level": trust_in_scammer_final,
                        "trust_trajectory": f"初始: {initial_trust}/100 → 峰值: {peak_trust}/100 → 最终: {trust_in_scammer_final}/100 (分析失败，使用fallback)"
                    },
                    "scam_tactic": scam_tactic,
                    "key_moment": outcome_description,
                    "success_reason" if outcome_type_pre == "SUCCESS" else "failure_reason": f"{outcome_description}。注意：此分析为fallback，因为RecorderAgent JSON解析失败。",
                    "improvement_suggestion": "需要改进RecorderAgent的JSON输出格式，确保输出纯JSON格式。",
                    "expert_performance_rating": {
                        "emotional_support": "N/A (分析失败)",
                        "evidence_quality": "N/A (分析失败)",
                        "communication_style": "N/A (分析失败)",
                        "timing": "N/A (分析失败)",
                        "overall": "N/A (分析失败)"
                    },
                    "scammer_effectiveness_rating": {
                        "psychological_manipulation": "N/A (分析失败)",
                        "credibility": "N/A (分析失败)",
                        "pressure_tactics": "N/A (分析失败)",
                        "adaptability": "N/A (分析失败)",
                        "overall": "N/A (分析失败)"
                    },
                    "full_conversation_log": [
                        {
                            "round": i + 1,
                            "speaker": turn.get("speaker", "未知"),
                            "dialogue": turn.get("dialogue", ""),
                            "analysis": "分析失败，无法提供详细分析"
                        }
                        for i, turn in enumerate(conversation_history)
                    ],
                    "error": "JSON解析失敗",
                    "raw_output_preview": analysis_json_str[:200] if 'analysis_json_str' in locals() else "N/A",
                    "reason": outcome_description
                }
        
        # 确保分析包含所有必需字段
        if "victim_persona" not in analysis:
            analysis["victim_persona"] = victim_persona
        if "scam_tactic" not in analysis:
            analysis["scam_tactic"] = scam_tactic
        if "victim_trust_analysis" not in analysis:
            trust_history = tracker.victim_trust_history if tracker and hasattr(tracker, 'victim_trust_history') else []
            initial_trust = trust_history[0].get("old_value", 70) if trust_history else 70
            peak_trust = max([h.get("new_value", trust_in_scammer_final) for h in trust_history] + [trust_in_scammer_final]) if trust_history else trust_in_scammer_final
            analysis["victim_trust_analysis"] = {
                "initial_trust_level": initial_trust,
                "peak_trust_level": peak_trust,
                "final_trust_level": trust_in_scammer_final,
                "trust_trajectory": f"初始: {initial_trust}/100 → 峰值: {peak_trust}/100 → 最终: {trust_in_scammer_final}/100"
            }
        if "key_moment" not in analysis:
            analysis["key_moment"] = outcome_description
        if outcome_type_pre == "SUCCESS":
            if "success_reason" not in analysis:
                analysis["success_reason"] = outcome_description
        else:
            if "failure_reason" not in analysis:
                analysis["failure_reason"] = outcome_description
        if "improvement_suggestion" not in analysis:
            analysis["improvement_suggestion"] = "需要提供具体改进建议"
        
        if "full_conversation_log" not in analysis:
            analysis["full_conversation_log"] = [
                {
                    "round": i + 1,
                    "speaker": turn.get("speaker", "未知"),
                    "dialogue": turn.get("dialogue", ""),
                    "analysis": "未提供详细分析"
                }
                for i, turn in enumerate(conversation_history)
            ]
        
        # 支持完整JSON格式，兼容PARTIAL状态
        outcome = analysis.get("outcome", outcome_type_pre)
        if outcome not in ("SUCCESS", "FAILURE", "PARTIAL"):
            # 如果outcome不在预期值，根据分析判断
            if "success" in str(outcome).lower() or "阻止" in str(analysis.get("success_reason", "")):
                outcome = "SUCCESS"
            elif "partial" in str(outcome).lower() or "猶豫" in str(analysis.get("failure_reason", "")):
                outcome = "PARTIAL"
            else:
                outcome = "FAILURE"
        
        # 所有判定邏輯交由記錄人分析決定，不再進行硬編碼檢測
        
        if outcome == "SUCCESS":
            result_text = "模擬成功"
        elif outcome == "PARTIAL":
            result_text = "模擬部分成功（受騙者猶豫但未完全中招）"
        else:
            result_text = "模擬失敗"

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
                
                # Generate final performance report
                try:
                    final_report = tracker.generate_final_report()
                except Exception as report_error:
                    log.error(f"Failed to generate final report: {report_error}")
                    # 如果生成报告失败，使用基本结构
                    final_report = {
                        "outcome": analysis.get("outcome", "FAILURE"),
                        "total_turns": len(conversation_history),
                        "summary": "报告生成失败"
                    }
                log.info(f"📊 最终报告 - 对话{len(conversation_history)}轮, 结果: {final_report.get('outcome', 'UNKNOWN')}")
                if 'scammer_overall_score' in final_report:
                    log.info(f"   骗徒总分: {final_report['scammer_overall_score']:.1f}")
                if 'expert_overall_score' in final_report:
                    log.info(f"   专家总分: {final_report['expert_overall_score']:.1f}")
                if 'victim_trust_final' in final_report:
                    trust_final = final_report['victim_trust_final']
                    log.info(f"   最终信任度 - 对骗徒: {trust_final.get('trust_in_scammer', 'N/A')}, 对专家: {trust_final.get('trust_in_expert', 'N/A')}")

                data_to_save = {
                    "analysis": {
                        **analysis,
                        "victim_persona": victim_persona,
                        "scam_tactic": scam_tactic,
                        "timestamp": datetime.now().isoformat(),
                        "total_turns": len(conversation_history),
                    },
                    "performance_report": final_report,
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
        
        # Auto-start new round after simulation ends
        await _auto_start_new_round(mode, auto_train)
        
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
            
            # Auto-start new round after simulation ends
            await _auto_start_new_round(mode, auto_train)
        
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
            # conversation_history可能未初始化，需要安全处理
            conversation_history_safe = conversation_history if 'conversation_history' in locals() else []
            
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            save_dir = os.path.join(base_dir, 'training_data')
            os.makedirs(save_dir, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"training_data_ws_{ts}_{simulation_id[:8]}_error.json"
            path = os.path.join(save_dir, filename)
            
            speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
            dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history_safe]
            
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
                "conversation_history": conversation_history_safe,
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
        
        # Auto-start new round even on error
        try:
            await _auto_start_new_round(mode)
        except Exception as auto_err:
            log.error(f"Failed to auto-start new round: {auto_err}")
    finally:
        # Cleanup connection
        if simulation_id in active_connections:
            del active_connections[simulation_id]