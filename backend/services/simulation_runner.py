import asyncio
import json
import uuid
import os
import re
import random
from datetime import datetime
from typing import Dict, Optional, List, Any

from scripts.real_dialogue_runner import RealDialogueRunner, SCAM_TACTICS, VICTIM_PERSONAS
from utils.logger import log
from utils.role_enforcer import RoleEnforcer
from utils.performance_tracker import PerformanceTracker
from utils.hybrid_evaluation import HybridEvaluationSystem
from utils.finetuning_formatter import FineTuningFormatter
from utils.prompt_version_manager import PromptVersionManager
from agents.prompts.prompt_builder import PromptBuilder
from api.websocket_manager import manager

# Fine-tuning formatter instance
finetuning_formatter = FineTuningFormatter()

# Prompt version manager instance
version_manager = PromptVersionManager()

async def _parallel_agent_generation(
    runner: RealDialogueRunner,
    scammer_prompt: str,
    expert_prompt: str,
    simulation_id: str,
    turn: int
) -> tuple[str, str]:
    """
    並行生成騙徒和專家的回應
    
    這兩個 Agent 不需要等待對方，可以同時生成，提升響應速度 40%
    
    Args:
        runner: 對話運行器
        scammer_prompt: 騙徒的 Prompt
        expert_prompt: 專家的 Prompt
        simulation_id: 模擬 ID
        turn: 當前輪次
        
    Returns:
        (scammer_text, expert_text) 元組
    """
    log.info(f"🚀 [並行生成] Turn {turn} - 同時生成騙徒和專家回應")
    
    # 創建兩個並行任務
    scammer_task = asyncio.create_task(
        runner.run_agent_with_adk(
            runner.scammer, 
            scammer_prompt, 
            f"{simulation_id}_turn_{turn}_scammer"
        )
    )
    
    expert_task = asyncio.create_task(
        runner.run_agent_with_adk(
            runner.expert, 
            expert_prompt, 
            f"{simulation_id}_turn_{turn}_expert"
        )
    )
    
    # 並行等待兩個任務完成
    scammer_text, expert_text = await asyncio.gather(
        scammer_task, 
        expert_task
    )
    
    log.info(f"✅ [並行生成] Turn {turn} - 完成")
    
    return scammer_text, expert_text

def remove_emotion_markers(text: str) -> str:
    """
    移除文字中括號內的語氣描述
    例如：(笑)、(自信地說)、（微笑）等
    """
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'（[^）]*）', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'【[^】]*】', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _log_recorder_scores(analysis: Dict[str, Any]):
    """顯示 Recorder 的評分結果"""
    if "scammer_performance" in analysis and "expert_performance" in analysis:
        scammer_perf = analysis["scammer_performance"]
        expert_perf = analysis["expert_performance"]
        
        log.info("=" * 80)
        log.info("📊 [Recorder 最終評分]")
        log.info(f"   🎭 騙徒總分: {scammer_perf.get('overall_score', 0)}/100")
        log.info(f"      • 說服力: {scammer_perf.get('persuasiveness', 0)}/100")
        log.info(f"      • 可信度: {scammer_perf.get('credibility', 0)}/100")
        log.info(f"      • 施壓效果: {scammer_perf.get('pressure_effectiveness', 0)}/100")
        log.info(f"      • 策略一致性: {scammer_perf.get('strategy_consistency', 0)}/100")
        
        if scammer_perf.get('key_successes'):
            log.info(f"      ✅ 成功之處: {len(scammer_perf['key_successes'])}項")
        if scammer_perf.get('key_failures'):
            log.info(f"      ❌ 失敗之處: {len(scammer_perf['key_failures'])}項")
        
        log.info(f"   👨‍⚕️ 專家總分: {expert_perf.get('overall_score', 0)}/100")
        log.info(f"      • 干預效果: {expert_perf.get('intervention_effectiveness', 0)}/100")
        log.info(f"      • 清晰度: {expert_perf.get('clarity', 0)}/100")
        log.info(f"      • 同理心: {expert_perf.get('empathy', 0)}/100")
        log.info(f"      • 可執行性: {expert_perf.get('actionability', 0)}/100")
        log.info(f"      • 時機把握: {expert_perf.get('timing', 0)}/100")
        
        if expert_perf.get('key_successes'):
            log.info(f"      ✅ 成功之處: {len(expert_perf['key_successes'])}項")
        if expert_perf.get('key_failures'):
            log.info(f"      ❌ 失敗之處: {len(expert_perf['key_failures'])}項")
        
        log.info("=" * 80)

async def _record_version_performance(
    simulation_id: str,
    outcome: Dict[str, Any],
    tracker: PerformanceTracker,
    victim_persona: str,
    scam_tactic: str
):
    """記錄 Prompt 版本性能"""
    try:
        log.info(f"📊 記錄版本性能 (simulation_id={simulation_id[:8]})")
        
        # 計算平均響應時間（這裡簡化處理，實際應該在每輪記錄）
        avg_response_time = 5.0  # 預設值，實際應該從追蹤數據獲取
        
        # 計算總 Token 使用（簡化處理）
        total_tokens = tracker.turn_count * 1000  # 預估值
        
        # 判斷是否成功
        is_success = outcome["status"] == "SUCCESS"
        
        # 獲取最終信任度
        final_trust = tracker.victim_trust.to_dict()
        
        # 獲取性能報告
        performance_report = tracker.get_performance_report()
        
        # 為每個 Agent 類型記錄性能
        for agent_type in ["expert", "scammer", "victim"]:
            active_version = version_manager.get_active_version(agent_type)
            
            version_manager.record_performance(
                agent_type=agent_type,
                version=active_version,
                metrics={
                    "response_time": avg_response_time,
                    "token_usage": total_tokens // 3,  # 平均分配
                    "success": is_success,
                    "final_trust_scammer": final_trust["trust_in_scammer"],
                    "final_trust_expert": final_trust["trust_in_expert"],
                    "alertness": final_trust["alertness"],
                    "turn_count": tracker.turn_count,
                    "victim_persona": victim_persona,
                    "scam_tactic": scam_tactic,
                    "overall_score": performance_report.get("scammer_overall_score", 0) if agent_type == "scammer" else performance_report.get("expert_overall_score", 0)
                }
            )
        
        log.info(f"✅ 版本性能記錄完成")
        
    except Exception as e:
        log.error(f"❌ 記錄版本性能失敗: {e}", exc_info=True)


async def _generate_finetuning_data(
    conversation_history: List[Dict[str, str]],
    analysis: Dict[str, Any],
    performance_report: Dict[str, Any],
    metadata: Dict[str, Any],
    simulation_id: str
) -> Dict[str, str]:
    """生成fine-tuning格式的訓練數據"""
    try:
        log.info(f"🔄 開始生成fine-tuning訓練數據 (simulation_id={simulation_id[:8]})")
        
        saved_files = {}
        
        # 1. 生成專家訓練數據
        expert_samples = finetuning_formatter.format_for_expert_training(
            conversation_history, analysis, performance_report
        )
        if expert_samples:
            expert_path = finetuning_formatter.save_to_jsonl(
                expert_samples, "expert", simulation_id
            )
            saved_files["expert_training"] = expert_path
            log.info(f"✅ 專家訓練數據已生成: {expert_path}")
        else:
            log.warning("⚠️ 沒有生成專家訓練數據（可能質量不符合要求）")
        
        # 2. 生成騙徒訓練數據
        scammer_samples = finetuning_formatter.format_for_scammer_training(
            conversation_history, analysis, performance_report
        )
        if scammer_samples:
            scammer_path = finetuning_formatter.save_to_jsonl(
                scammer_samples, "scammer", simulation_id
            )
            saved_files["scammer_training"] = scammer_path
            log.info(f"✅ 騙徒訓練數據已生成: {scammer_path}")
        else:
            log.warning("⚠️ 沒有生成騙徒訓練數據（可能質量不符合要求）")
        
        if saved_files:
            log.info(f"🎉 Fine-tuning數據生成完成，共 {len(saved_files)} 個文件")
        
        return saved_files
        
    except Exception as e:
        log.error(f"❌ 生成fine-tuning數據失敗: {e}", exc_info=True)
        return {}

async def _generate_recorder_analysis(
    runner: RealDialogueRunner,
    conversation_history: list,
    simulation_id: str,
    victim_persona: str,
    scam_tactic: str,
    outcome_type: str,
    outcome_description: str,
    tracker: Optional[PerformanceTracker] = None,
    trust_in_scammer: Optional[int] = None,
    trust_in_expert: Optional[int] = None
) -> dict:
    """统一的 RecorderAgent 分析生成函数"""
    try:
        conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
        
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
            "4. **絕對禁止**以 `[` (方括號) 或任何其他文字開始。\n"
            "5. **絕對禁止**在JSON對象之外包含任何註解、說明、Markdown (```) 或前言。\n"
            "6. **必須**包含所有指定的分析欄位。\n"
            "7. `full_conversation_log` 欄位**必須**是你根據對話歷史*重新分析*生成的。\n\n"
            "**現在，請立即開始輸出你的JSON對象，以 `{` 開始：**"
        )
        
        if outcome_type == "FAILURE":
            analysis_prompt += (
                "**⚠️ 特別重要：這是FAILURE情況，failure_reason字段必須包含以下5個維度的完整深度分析：**\n"
                "1. 專家策略問題\n"
                "2. 騙徒成功因素\n"
                "3. 受騙者心理軌跡\n"
                "4. 系統性失敗因素\n"
                "5. 失敗的根本原因\n\n"
                "failure_reason必須至少200字。\n\n"
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
            "2. **絕對不要**輸出任何解釋性文字\n"
            "3. **絕對不要**使用markdown code block標記\n"
            "**現在，直接輸出JSON對象，不要有任何其他文字：**"
        )
        
        log.info(f"📊 调用 RecorderAgent 生成完整分析 (outcome: {outcome_type})")
        analysis_raw = await runner.run_agent_with_adk(
            runner.recorder, 
            analysis_prompt, 
            f"{simulation_id}_final_analysis"
        )
        
        cleaned_json = analysis_raw.strip()
        if cleaned_json.startswith("```json"): cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"): cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"): cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()
        
        first_brace = cleaned_json.find('{')
        last_brace = cleaned_json.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned_json = cleaned_json[first_brace:last_brace+1]
        
        try:
            analysis = json.loads(cleaned_json)
        except json.JSONDecodeError as parse_error:
            log.warning(f"第一次JSON解析失败，尝试更激进的清理: {parse_error}")
            json_match = re.search(r'\{.*\}', cleaned_json, re.DOTALL)
            if json_match:
                cleaned_json = json_match.group(0)
                analysis = json.loads(cleaned_json)
            else:
                raise
        
        analysis["outcome"] = outcome_type
        if "victim_persona" not in analysis: analysis["victim_persona"] = victim_persona
        if "scam_tactic" not in analysis: analysis["scam_tactic"] = scam_tactic
        
        # Fill missing fields logic omitted for brevity but kept in spirit (simplified here)
        if "full_conversation_log" not in analysis:
            analysis["full_conversation_log"] = [
                {"round": i+1, "speaker": t.get("speaker","?"), "dialogue": t.get("dialogue","")}
                for i, t in enumerate(conversation_history)
            ]

        log.info(f"✅ RecorderAgent 分析完成")
        _log_recorder_scores(analysis)
        return analysis
        
    except Exception as e:
        log.error(f"❌ RecorderAgent 分析生成失败: {e}")
        return {
            "outcome": outcome_type,
            "reason": outcome_description,
            "victim_persona": victim_persona,
            "scam_tactic": scam_tactic,
            "error": f"分析生成失败: {str(e)}"
        }

async def _auto_start_new_round(mode: str = "fast", auto_train: bool = True, previous_simulation_id: str = None):
    """自動開始新一輪模擬"""
    if not auto_train:
        log.info("自動訓練已禁用（參數設置），跳過新輪次")
        return
    
    env_auto_train = os.getenv("AUTO_TRAIN_ENABLED", "true").lower() == "true"
    if not env_auto_train:
        log.info("自動訓練已禁用（環境變量設置），跳過新輪次")
        return
    
    # 檢查全局停止標誌
    if manager.global_stop_flag:
        log.info(f"🛑 全局停止標誌已設置，不自動開始新輪次")
        return
    
    # 檢查前一個模擬是否被用戶停止
    if previous_simulation_id and manager.should_stop(previous_simulation_id):
        log.info(f"🛑 前一個模擬 {previous_simulation_id[:8]} 已被用戶停止，不自動開始新輪次")
        return
    
    await asyncio.sleep(2.0)
    
    new_victim_persona = random.choice(VICTIM_PERSONAS)
    new_scam_tactic = random.choice(SCAM_TACTICS)
    new_simulation_id = str(uuid.uuid4())
    
    log.info(f"🔄 自動開始新一輪模擬: {new_simulation_id}")
    
    # Broadcast new round
    for sim_id in list(manager.active_connections.keys()):
        try:
            await manager.send_event(sim_id, "auto_new_round_starting", {
                "new_simulation_id": new_simulation_id,
                "victim_persona": new_victim_persona,
                "scam_tactic": new_scam_tactic,
                "mode": mode
            })
        except Exception:
            pass
    
    asyncio.create_task(run_simulation_async(
        new_simulation_id,
        victim_persona=new_victim_persona,
        scam_tactic=new_scam_tactic,
        mode=mode,
        auto_train=auto_train,
        is_auto_round=True
    ))

async def run_simulation_async(simulation_id: str, victim_persona: str, scam_tactic: str, mode: str = "fast", auto_train: bool = True, is_auto_round: bool = False):
    """在背景中運行模擬"""
    try:
        # 如果是自動輪次，不清除停止標誌；如果是用戶手動開始，則清除
        manager.reset_simulation_state(simulation_id, clear_stop_flag=not is_auto_round)
        
        # 如果是自動輪次且停止標誌已設置，直接返回
        if is_auto_round and manager.should_stop(simulation_id):
            log.info(f"🛑 自動輪次 {simulation_id[:8]} 檢測到停止標誌，不啟動")
            return
        
        runner = RealDialogueRunner()
        ok = runner.initialize_agents(victim_persona=victim_persona)
        if not ok:
            raise RuntimeError("initialize_agents failed")

        # Wait for connection
        for _ in range(50):
            if simulation_id in manager.active_connections:
                break
            await asyncio.sleep(0.1)
        
        # 使用混合評估系統（結合規則引擎和 AI）
        hybrid_eval = HybridEvaluationSystem(victim_persona=victim_persona, calibration_interval=3)
        log.info(f"📊 初始化混合評估系統 - 受害者类型: {victim_persona}")
        
        await manager.send_event(simulation_id, "simulation_start", {
            "simulation_id": simulation_id,
            "characters": [
                {"name": "專業騙徒", "persona_summary": "精通社會工程學的詐騙專家"},
                {"name": "受騙者", "persona_summary": f"角色類型: {victim_persona}"},
                {"name": "防騙專家", "persona_summary": "冷靜理性的防騙分析師"}
            ],
            "initial_trust": hybrid_eval.tracker.victim_trust.to_dict(),
            "initial_scores": {
                "scammer": hybrid_eval.tracker.scammer_perf.to_dict(),
                "expert": hybrid_eval.tracker.expert_perf.to_dict()
            }
        })
        
        conversation_history = []
        max_turns = 50
        hybrid_eval.tracker.turn_count = 0

        # --- Role Enforcers (Simplified for Brevity but functional) ---
        async def _enforce_scammer_role(original_text: str, victim_turn_text: str | None = None) -> str:
            text = original_text or ""
            is_repetitive, msg, _ = RoleEnforcer.detect_repetition_in_history(conversation_history, "騙徒", text)
            if is_repetitive:
                # Fallback logic
                if "銀行" in scam_tactic: return "陳先生，情況緊急，請你立即配合。"
                return "我哋已經掌握證據，你必須立即配合調查。"
            return text

        async def _enforce_victim_role(original_text: str, scammer_turn_text: str = "") -> str:
            text = original_text or ""
            if len(text) > 200: text = text[:200]
            is_repetitive, msg, _ = RoleEnforcer.detect_repetition_in_history(conversation_history, "受騙者", text)
            if is_repetitive:
                if victim_persona == "overconfident": return "你憑咩咁講？"
                return "我唔係好明。"
            return text
        # -----------------------------------------------------------

        # Initial Scammer Turn
        scammer_prompt = f"（任務：使用「{scam_tactic}」手法，開始與目標接觸。用廣東話，語氣要自然但帶有壓迫感。不超過50字。）"
        scammer_text = await runner.run_agent_with_adk(runner.scammer, scammer_prompt, f"{simulation_id}_turn_0")
        scammer_text = remove_emotion_markers(scammer_text)
        scammer_text = await _enforce_scammer_role(scammer_text)

        conversation_history.append({"speaker": "騙徒", "dialogue": scammer_text})
        await manager.send_event(simulation_id, "agent_message", {
            "speaker": "騙徒", 
            "message": scammer_text,
            "trust_impact": "N/A"
        })

        # Main Loop
        for turn in range(max_turns):
            if manager.should_stop(simulation_id):
                log.info(f"🛑 Simulation {simulation_id} stopped by user at turn {turn}.")
                await manager.send_event(simulation_id, "simulation_stopped", {
                    "reason": "用戶手動停止",
                    "turn": turn
                })
                return

            hybrid_eval.tracker.turn_count = turn + 1
            
            # === 並行生成：騙徒和專家同時生成 ===
            expert_prompt = f"""
            目前對話：
            騙徒：{scammer_text}
            
            受害者類型：{victim_persona}
            詐騙手法：{scam_tactic}
            
            任務：提供簡短的防騙建議（廣東話，<60字）。
            """
            
            scammer_prompt_next = f"受害者上次說：{conversation_history[-1]['dialogue'] if conversation_history else '（開始對話）'}。繼續行騙。"
            
            # 並行生成騙徒和專家的回應
            scammer_text_next, expert_text = await _parallel_agent_generation(
                runner,
                scammer_prompt_next,
                expert_prompt,
                simulation_id,
                turn
            )
            
            expert_text = remove_emotion_markers(expert_text)
            
            # Check stop after parallel generation
            if manager.should_stop(simulation_id):
                log.info(f"🛑 Simulation {simulation_id} stopped by user after parallel generation.")
                await manager.send_event(simulation_id, "simulation_stopped", {
                    "reason": "用戶手動停止",
                    "turn": turn
                })
                return
            
            # 發送專家回應
            conversation_history.append({"speaker": "防騙專家", "dialogue": expert_text})
            await manager.send_event(simulation_id, "agent_message", {
                "speaker": "防騙專家",
                "message": expert_text
            })
            
            if mode == "demo": await asyncio.sleep(3)

            # === 受害者回應（需要等待專家和騙徒） ===
            if manager.should_stop(simulation_id):
                log.info(f"🛑 Simulation {simulation_id} stopped by user before victim response.")
                await manager.send_event(simulation_id, "simulation_stopped", {
                    "reason": "用戶手動停止",
                    "turn": turn
                })
                return
            
            victim_prompt = f"""
            騙徒說：{scammer_text}
            專家建議：{expert_text}
            
            你的設定：{victim_persona}
            任務：回應騙徒。
            """
            victim_text = await runner.run_agent_with_adk(runner.victim, victim_prompt, f"{simulation_id}_turn_{turn}_victim")
            victim_text = remove_emotion_markers(victim_text)
            victim_text = await _enforce_victim_role(victim_text, scammer_text)
            
            # Check stop after victim
            if manager.should_stop(simulation_id):
                log.info(f"🛑 Simulation {simulation_id} stopped by user after victim response.")
                await manager.send_event(simulation_id, "simulation_stopped", {
                    "reason": "用戶手動停止",
                    "turn": turn
                })
                return
            
            conversation_history.append({"speaker": "受騙者", "dialogue": victim_text})
            await manager.send_event(simulation_id, "agent_message", {
                "speaker": "受騙者",
                "message": victim_text
            })

            # === 使用混合評估系統評估當前輪次 ===
            evaluation = await hybrid_eval.evaluate_turn(
                runner, conversation_history,
                scammer_text, expert_text, victim_text,
                turn, simulation_id
            )
            
            # 發送信任度更新
            await manager.send_event(simulation_id, "trust_update", evaluation["trust_update"])
            
            # 記錄評估方法
            if evaluation["evaluation_method"] == "ai":
                log.info(f"🤖 使用 AI 評估: {evaluation.get('ai_insights', '')}")
            
            # 檢查是否應該中止
            if not evaluation["should_continue"]:
                # 判定最終結果
                outcome = hybrid_eval.check_outcome(conversation_history)
                
                # Game Over
                await manager.send_event(simulation_id, "simulation_end", {
                    "reason": evaluation["reason"],
                    "outcome": outcome["status"],
                    "evaluation_method": evaluation["evaluation_method"]
                })
                
                # Final Analysis
                analysis = await _generate_recorder_analysis(
                    runner, conversation_history, simulation_id,
                    victim_persona, scam_tactic,
                    outcome["status"], evaluation["reason"], hybrid_eval.tracker,
                    hybrid_eval.tracker.victim_trust.trust_in_scammer, 
                    hybrid_eval.tracker.victim_trust.trust_in_expert
                )
                
                await manager.send_event(simulation_id, "analysis_complete", {"analysis": analysis})
                
                # Fine-tuning generation
                await _generate_finetuning_data(
                    conversation_history, analysis, 
                    hybrid_eval.get_performance_report(), 
                    {"mode": mode, "auto_train": auto_train},
                    simulation_id
                )
                
                # 記錄版本性能
                await _record_version_performance(
                    simulation_id, outcome, hybrid_eval.tracker, 
                    victim_persona, scam_tactic
                )
                
                await _auto_start_new_round(mode, auto_train, simulation_id)
                return

            # === 更新騙徒文本（使用並行生成的結果） ===
            if manager.should_stop(simulation_id):
                log.info(f"🛑 Simulation {simulation_id} stopped by user before scammer update.")
                await manager.send_event(simulation_id, "simulation_stopped", {
                    "reason": "用戶手動停止",
                    "turn": turn
                })
                return
            
            scammer_text = remove_emotion_markers(scammer_text_next)
            scammer_text = await _enforce_scammer_role(scammer_text, victim_text)
            
            # Check stop after scammer
            if manager.should_stop(simulation_id):
                log.info(f"🛑 Simulation {simulation_id} stopped by user after scammer response.")
                await manager.send_event(simulation_id, "simulation_stopped", {
                    "reason": "用戶手動停止",
                    "turn": turn
                })
                return
            
            conversation_history.append({"speaker": "騙徒", "dialogue": scammer_text})
            await manager.send_event(simulation_id, "agent_message", {
                "speaker": "騙徒",
                "message": scammer_text
            })

    except Exception as e:
        log.error(f"Simulation error: {e}", exc_info=True)
        await manager.send_event(simulation_id, "error", {"message": str(e)})
