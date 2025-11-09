import asyncio
import os
import sys
import json
import random
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Adjust path to import modules from agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.scammer import ScammerAgent
from agents.victim import VictimAgent
from agents.expert import ExpertAgent
from agents.recorder import RecorderAgent
from utils.logger import log
from utils.performance_tracker import PerformanceTracker
from scripts.real_dialogue_runner import RealDialogueRunner
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

# --- Training settings ---
TRAINING_ROUNDS = 10  # total training rounds
MAX_TURNS_PER_SIMULATION = 50  # max turns per simulation (updated to match simulation_routes)
MAX_ATTEMPTS_PER_ROUND = 3  # max attempts per round
TRAINING_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'training_data')

def ensure_training_data_dir():
    """Ensure training data directory exists"""
    if not os.path.exists(TRAINING_DATA_DIR):
        os.makedirs(TRAINING_DATA_DIR)
        log.info(f"Created training data directory: {TRAINING_DATA_DIR}")

def run_agent_with_runner(agent, message: str, session_id: str = None):
    """
    Run the agent via Runner and get response
    """
    if session_id is None:
        session_id = f"session_{int(time.time() * 1000)}"
    
    try:
        # InMemorySessionService in ADK 1.16.0: manually create session
        session_service = InMemorySessionService()
        user_id = "training_user"
        app_name = "agents"
        
        # InMemorySessionService uses nested dict: sessions[app_name][user_id][session_id]
        if not hasattr(session_service, 'sessions'):
            session_service.sessions = {}
        
        # Initialize nested structure
        if app_name not in session_service.sessions:
            session_service.sessions[app_name] = {}
        
        if user_id not in session_service.sessions[app_name]:
            session_service.sessions[app_name][user_id] = {}
        
        # Create session if not exists
        if session_id not in session_service.sessions[app_name][user_id]:
            from google.adk.sessions import Session
            session_service.sessions[app_name][user_id][session_id] = Session(
                id=session_id,
                user_id=user_id,
                app_name=app_name,
                events=[]
            )
        
        runner = Runner(app_name=app_name, agent=agent, session_service=session_service)
        from google.genai import types as genai_types
        content_msg = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)]
        )
        events = list(runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content_msg
        ))
        
        # Get the last event containing text (compatible with parts/text)
        for event in reversed(events):
            if hasattr(event, 'content') and getattr(event, 'content') is not None:
                content = event.content
                text_attr = getattr(content, 'text', None)
                if isinstance(text_attr, str) and text_attr.strip():
                    return text_attr.strip()
                parts = getattr(content, 'parts', None)
                if parts:
                    collected: list[str] = []
                    for p in parts:
                        t = getattr(p, 'text', None)
                        if isinstance(t, str) and t:
                            collected.append(t)
                    if collected:
                        return "\n".join(collected).strip()
        
        return "無法獲取回應"
    except Exception as e:
        log.error(f"Agent error: {e}")
        return f"錯誤: {str(e)}"

async def run_agent_with_runner_async(agent, message: str, session_id: str = None):
    """
    Wrap the sync Runner call as async to run agents in parallel within a round.
    """
    return await asyncio.to_thread(run_agent_with_runner, agent, message, session_id)

async def run_single_simulation(victim_persona: str, learning_context: str = None, round_num: int = 1, attempt_num: int = 1, mode: str = "fast", scam_tactic: Optional[str] = None):
    """
    Run a single three-agent dialogue simulation with trust tracking and performance monitoring
    使用新的信任度机制和性能追踪系统
    """
    # Initialize RealDialogueRunner
    runner = RealDialogueRunner()
    ok = runner.initialize_agents(victim_persona=victim_persona)
    if not ok:
        raise RuntimeError("initialize_agents failed")
    
    # Initialize performance tracker
    tracker = PerformanceTracker(victim_persona=victim_persona)
    log.info(f"📊 初始化PerformanceTracker - 受害者类型: {victim_persona}")
    log.info(f"   初始信任度 - 对骗徒: {tracker.victim_trust.trust_in_scammer}, 对专家: {tracker.victim_trust.trust_in_expert}")
    
    # Randomly select scam tactic if not provided
    if not scam_tactic:
        from scripts.real_dialogue_runner import SCAM_TACTICS
        scam_tactic = random.choice(SCAM_TACTICS)
    
    # Set expert learning context
    if learning_context:
        runner.expert = ExpertAgent(learning_context=learning_context)
        log.warning(f"專家帶著學習筆記: {learning_context}")

    conversation_history = []
    tracker.turn_count = 0
    
    log.info(f"--- 開始第 {round_num} 輪第 {attempt_num} 次模擬 ---")
    log.info(f"受騙者角色: {victim_persona}, 詐騙手法: {scam_tactic}")

    # Opening: scammer initiates
    log.info(f"=== 第 {round_num} 輪第 {attempt_num} 次模擬 ===")
    log.info("--- 回合 1: 騙徒開始攻擊 ---")
    
    # Use enhanced scammer prompt (similar to simulation_routes.py)
    scammer_opening_prompt = (
        f"**🎭 你的身份：專業騙徒（使用「{scam_tactic}」手法）**\n\n"
        "**你的任務：**\n"
        "1. 用權威身份（例如：銀行職員、執法部門、政府機構）開場\n"
        "2. 創造緊迫感（例如：「你的帳戶將被凍結」、「你涉嫌犯罪」）\n"
        "3. 要求受害者提供敏感資料或進行轉帳\n\n"
        "**🚨 絕對禁止：**\n"
        "- 嚴禁更換手法；嚴禁揭露或否定行為；嚴禁使用『詐騙／騙局／防騙／舉報／報警／警方』等字眼\n"
        "- 禁止研究/倫理/免責口吻；禁止使用旁白括號（（）、【】、<>等）\n"
        "- 禁止使用角色標籤（例如「李主任：」）\n\n"
        "**請直接回覆，≤120字，廣東話，不要加任何說明或標記。**"
    )
    
    try:
        scammer_turn = await runner.run_agent_with_adk(runner.scammer, scammer_opening_prompt, f"scammer_turn_1_r{round_num}_a{attempt_num}")
    except Exception as e:
        log.error(f"Scammer agent error: {e}")
        scammer_turn = "你好，我是銀行職員，你的帳戶有異常活動，需要立即處理。"
    
    conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn, "turn": 1})
    log.info(f"騙徒: {scammer_turn}")
    
    # Analyze scammer opening
    tracker.analyze_scammer_turn(scammer_turn, "")
    
    expert_turn = None
    last_victim_turn = None
    last_scammer_turn = scammer_turn
    
    # Key action/rejection words
    key_action_words = ["我會轉帳", "我轉帳", "我俾錢", "我提供", "我提供資料", "我信你", "我相信你", "好的", "我配合"]
    key_rejection_words = ["我唔會信你", "我唔會俾你呃", "我唔信你", "我會報警", "我而家就報警", 
                          "我唔會提供資料", "我唔會提供任何資料", "我唔會配合", "我唔會俾你", 
                          "我唔會轉帳", "專家講得啱", "我會聽專家的", "我而家就停止", "我唔會再同你講"]
    
    for turn in range(2, MAX_TURNS_PER_SIMULATION + 1):
        tracker.turn_count = turn
        log.info(f"\n--- 回合 {turn} ---")
        
        # Get current trust state
        current_state = tracker.get_current_state()
        trust_in_scammer = current_state["trust_in_scammer"]
        trust_in_expert = current_state["trust_in_expert"]
        alertness = current_state["alertness"]
        
        # Check for early termination (victim wins)
        if trust_in_scammer <= 0 and trust_in_expert >= 70:
            log.info("🎯 专家获胜！信任度条件达成")
            break
        
        # Build victim prompt with trust context
        history_context = ""
        if len(conversation_history) >= 3:
            recent_history = conversation_history[-3:]
            for msg in recent_history:
                history_context += f"{msg['speaker']}: {msg['dialogue']}\n"
        
        # Trust behavior instruction
        if trust_in_scammer >= 100:
            trust_behavior_instruction = (
                f"**🚨🚨🚨 關鍵時刻：你對騙徒的信任度已達到100/100！**\n"
                "你完全信任對方，準備配合！你必須在回應中明確說出以下關鍵詞之一：\n"
                "- 「我會轉帳」\n"
                "- 「我轉帳」\n"
                "- 「我俾錢」\n"
                "- 「我提供資料」\n"
                "**你必須說出這些關鍵詞，表示你準備配合！**\n"
            )
        elif trust_in_scammer <= 0:
            trust_behavior_instruction = (
                f"**🚨🚨🚨 關鍵時刻：你對騙徒的信任度已降至0/100！**\n"
                "你完全不相信對方，已經識破騙局！你必須立即採取行動！你必須在回應中明確說出以下關鍵詞之一：\n"
                "- 「我唔會信你」\n"
                "- 「我會報警」\n"
                "- 「我唔會提供資料」\n"
                "- 「專家講得啱」\n"
                "**你必須說出這些關鍵詞，表示你完全識破騙局並準備採取防範措施！**\n"
            )
        else:
            trust_behavior_instruction = (
                f"**💡 信任度狀態：你對騙徒的信任度是{trust_in_scammer}/100，對專家的信任度是{trust_in_expert}/100**\n"
                "你必須根據信任度調整你的回應：信任度高時更願意配合，信任度低時更懷疑和拒絕。\n"
            )
        
        # Build victim prompt
        prompt_for_victim = (
            f"**🎭 你的角色類型：{victim_persona}**\n\n"
            f"**對話歷史（最近3輪）：**\n{history_context}\n\n"
            f"**你剛收到的訊息：**\n「{last_scammer_turn}」\n\n"
            f"**📊 當前信任度狀態：**\n"
            f"- 對騙徒：{trust_in_scammer}/100\n"
            f"- 對專家：{trust_in_expert}/100\n"
            f"- 警覺程度：{alertness}/100\n\n"
            f"{trust_behavior_instruction}\n"
            "**重要指令：**\n"
            "1. 你只能以普通市民身份回覆，不可評論/總結/說教。包含情緒或猶疑點，可提出具體追問。\n"
            f"2. **🚨 防止重複：** 你上一句嘅回應係「{last_victim_turn[:100] if last_victim_turn else '（第一輪）'}」。你今次嘅回應**必須**根據最新情況作出**全新**嘅回應，**絕對不能**重複之前說過的話！\n"
            "3. **🚨 角色一致性：** 你必須保持你的角色類型的一致性，不要突然切换成其他性格！\n"
            "4. **🚨 對話連續性：** 你的回應必須與之前的對話有邏輯連續性，根據對方的話和專家的建議作出反應。\n"
            "**請直接回覆，不要加任何說明或標記。**"
        )
        
        if expert_turn:
            prompt_for_victim += f"\n\n**同時，這是防騙專家給你的建議：**\n「{expert_turn}」"
        
        try:
            victim_turn_raw = await runner.run_agent_with_adk(runner.victim, prompt_for_victim, f"victim_turn_{turn}_r{round_num}_a{attempt_num}")
            victim_turn = victim_turn_raw[:200] if len(victim_turn_raw) > 200 else victim_turn_raw
        except Exception as e:
            log.error(f"Victim agent error: {e}")
            victim_turn = "我...我需要考慮一下。"
        
        conversation_history.append({"speaker": "受騙者", "dialogue": victim_turn, "turn": turn})
        log.info(f"受騙者: {victim_turn}")
        
        # Analyze victim response
        victim_analysis = tracker.analyze_victim_response(
            victim_response=victim_turn,
            previous_scammer_message=last_scammer_turn,
            previous_expert_message=expert_turn or ""
        )
        
        # Check for key action words (scammer wins)
        has_key_action = any(word in victim_turn for word in key_action_words)
        if trust_in_scammer >= 100 or has_key_action:
            log.warning(f"🎯 骗徒获胜！信任度: {trust_in_scammer}/100, 关键行动词: {has_key_action}")
            break
        
        # Check for key rejection words (expert wins)
        has_key_rejection = any(word in victim_turn for word in key_rejection_words)
        if trust_in_scammer <= 0 and (trust_in_expert >= 70 or has_key_rejection):
            log.info(f"🎯 专家获胜！信任度: {trust_in_scammer}/100, 关键拒绝词: {has_key_rejection}")
            break
        
        # Update trust based on victim analysis
        trust_change = victim_analysis.get("trust_change_scammer", 0)
        if trust_change != 0:
            tracker.victim_trust.update("scammer", trust_change, victim_analysis.get("reason", "受害者回应分析"))
        
        # Expert and scammer respond in parallel
        trust_gap = trust_in_scammer - trust_in_expert
        
        # Build expert prompt with trust context
        prompt_for_expert = (
            f"**📊 當前信任度狀態（關鍵情報）：**\n"
            f"- 受害者對騙徒的信任度：{trust_in_scammer}/100\n"
            f"- 受害者對你的信任度：{trust_in_expert}/100\n"
            f"- 信任度差距：{trust_gap:+d}分（{'騙徒領先' if trust_gap > 0 else '你領先' if trust_gap < 0 else '平手'}）\n\n"
            f"**騙徒剛才說的話：**\n「{last_scammer_turn}」\n\n"
            f"**受害者剛才說的話：**\n「{victim_turn}」\n\n"
            "**你的任務：**\n"
            "1. **直接反擊騙徒的策略**：針對騙徒剛才使用的話術進行反駁\n"
            "2. **根據信任度差距調整語氣**：如果騙徒領先很多，用更強烈的警告；如果你領先，用更穩定的建議\n"
            "3. **提供具體、可執行的防範措施**：告訴受害者立即停止對話，並提供官方核實渠道\n"
            "4. **預測騙徒的下一步**：告訴受害者騙徒可能會說什麼來反擊你的建議，讓受害者提前準備\n\n"
            "請以防騙專家身份輸出，嚴格120字內，**必須**針對騙徒的策略進行反擊！"
        )
        
        # Build scammer prompt with trust context
        prompt_for_scammer = (
            f"**🎭 你的身份：專業騙徒（使用「{scam_tactic}」手法）**\n\n"
            f"**📊 當前信任度狀態（關鍵情報）：**\n"
            f"- 受害者對你的信任度：{trust_in_scammer}/100\n"
            f"- 受害者對專家的信任度：{trust_in_expert}/100\n"
            f"- 信任度差距：{trust_gap:+d}分（{'你領先' if trust_gap > 0 else '專家領先' if trust_gap < 0 else '平手'}）\n\n"
            f"**受騙者剛才回應：**\n『{victim_turn}』\n\n"
            + (f"**🚨 專家剛才干預了（威脅你的騙局）：**\n「{expert_turn}」\n\n" if expert_turn else "")
            + "**你的任務：**\n"
            + (f"1. **必須反擊專家**：專家剛才說「{expert_turn[:50]}...」，你必須直接反駁\n" if expert_turn else "")
            + f"{'2' if expert_turn else '1'}. **根據信任度差距調整策略**：如果專家領先，用更強烈的威脅；如果你領先，鞏固優勢並推進行動\n"
            + f"{'3' if expert_turn else '2'}. **根據受害者回應調整**：如果受害者懷疑，改用安撫+威脅；如果受害者問很多問題，改用簡化+催促\n"
            + f"{'4' if expert_turn else '3'}. **保持權威感和壓迫感**：繼續使用權威身份和緊迫感\n\n"
            + "**🚨 絕對禁止：**\n"
            + "- 嚴禁更換手法；嚴禁揭露或否定行為；嚴禁使用『詐騙／騙局／防騙／舉報／報警／警方』等字眼\n"
            + "- 禁止研究/倫理/免責口吻；禁止使用旁白括號（（）、【】、<>等）\n"
            + "- 禁止使用角色標籤（例如「李主任：」）\n\n"
            + f"**🚨 防止重複：**\n"
            + f"你上一句嘅回應係「{last_scammer_turn[:100] if last_scammer_turn else '（第一輪）'}」。\n"
            + "你今次嘅回應**絕對不能**同上一句完全一樣！\n\n"
            + "**請直接回覆，≤120字，廣東話，不要加任何說明或標記。**"
        )
        
        # Run expert and scammer in parallel
        expert_future = runner.run_agent_with_adk(runner.expert, prompt_for_expert, f"expert_turn_{turn}_r{round_num}_a{attempt_num}")
        scammer_future = runner.run_agent_with_adk(runner.scammer, prompt_for_scammer, f"scammer_turn_{turn}_r{round_num}_a{attempt_num}")
        
        try:
            expert_turn, scammer_turn = await asyncio.gather(expert_future, scammer_future)
        except Exception as e:
            log.error(f"Agent parallel execution error: {e}")
            expert_turn = "請立即停止對話，這可能是詐騙。"
            scammer_turn = "請你配合調查，否則後果自負。"
        
        conversation_history.append({"speaker": "專家", "dialogue": expert_turn, "turn": turn})
        log.info(f"專家: {expert_turn}")
        
        conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn, "turn": turn})
        log.info(f"騙徒: {scammer_turn}")
        
        # Analyze expert and scammer turns
        expert_analysis = tracker.analyze_expert_turn(
            expert_advice=expert_turn,
            scammer_message=scammer_turn,
            victim_response=victim_turn
        )
        
        scammer_analysis = tracker.analyze_scammer_turn(
            dialogue=scammer_turn,
            victim_response=victim_turn
        )
        
        # Update trust based on expert analysis
        expert_trust_change = expert_analysis.get("trust_change", 0)
        if expert_trust_change != 0:
            tracker.victim_trust.update("expert", expert_trust_change, expert_analysis.get("reason", "专家干预效果"))
        
        # Check for early termination after expert turn
        current_state_after = tracker.get_current_state()
        trust_in_scammer_after = current_state_after["trust_in_scammer"]
        trust_in_expert_after = current_state_after["trust_in_expert"]
        
        if trust_in_scammer_after <= 0 and (trust_in_expert_after >= 70 or has_key_rejection):
            log.info(f"🎯 专家获胜（专家轮次后）！信任度: {trust_in_scammer_after}/100")
            break
        
        last_victim_turn = victim_turn
        last_scammer_turn = scammer_turn
        
        if mode == "demo":
            await asyncio.sleep(random.uniform(1.0, 2.0))
    
    # Final state
    final_state = tracker.get_current_state()
    trust_in_scammer_final = final_state["trust_in_scammer"]
    trust_in_expert_final = final_state["trust_in_expert"]
    
    # Check final conversation for key words
    final_victim_turns = [msg["dialogue"] for msg in conversation_history if msg["speaker"] == "受騙者"]
    final_victim_turn = final_victim_turns[-1] if final_victim_turns else ""
    
    has_key_action_final = any(word in final_victim_turn for word in key_action_words)
    has_key_rejection_final = any(word in final_victim_turn for word in key_rejection_words)
    
    # Determine outcome
    outcome = "PARTIAL"
    if trust_in_scammer_final >= 100 or has_key_action_final:
        outcome = "FAILURE"  # Scammer wins
    elif trust_in_scammer_final <= 0 and (trust_in_expert_final >= 70 or has_key_rejection_final):
        outcome = "SUCCESS"  # Expert wins
    
    return {
        "conversation_history": conversation_history,
        "tracker": tracker,
        "final_state": final_state,
        "outcome": outcome,
        "scam_tactic": scam_tactic,
        "victim_persona": victim_persona,
        "has_key_action": has_key_action_final,
        "has_key_rejection": has_key_rejection_final
    }

def analyze_simulation(simulation_result: Dict, round_num: int, attempt_num: int):
    """
    Use the recorder to analyze the simulation result with enhanced trust and performance data
    """
    recorder = RecorderAgent()
    conversation_history = simulation_result["conversation_history"]
    tracker = simulation_result["tracker"]
    final_state = simulation_result["final_state"]
    outcome = simulation_result["outcome"]
    scam_tactic = simulation_result["scam_tactic"]
    victim_persona = simulation_result["victim_persona"]
    
    # Format conversation history and pass to recorder for analysis
    conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
    
    # Build comprehensive analysis prompt
    analysis_prompt = (
        f"請作為專業的AI模擬分析師（林慧思博士），嚴格按照你的指示（instruction）中定義的「輸出格式」\n"
        f"（包含 outcome, victim_persona, victim_trust_analysis, scam_tactic, key_moment, \n"
        f"failure_reason/success_reason, improvement_suggestion, expert_performance_rating, \n"
        f"scammer_effectiveness_rating, full_conversation_log 等欄位）\n"
        f"對以下對話歷史進行全面分析。\n\n"
        f"**關鍵信息：**\n"
        f"- 受害者類型：{victim_persona}\n"
        f"- 詐騙手法：{scam_tactic}\n"
        f"- 最終信任度：對騙徒 {final_state['trust_in_scammer']}/100，對專家 {final_state['trust_in_expert']}/100\n"
        f"- 最終結果：{outcome}\n"
        f"- 騙徒總體得分：{tracker.scammer_perf.calculate_overall_score()}/100\n"
        f"- 專家總體得分：{tracker.expert_perf.calculate_overall_score()}/100\n"
        f"- 關鍵行動詞檢測：{simulation_result.get('has_key_action', False)}\n"
        f"- 關鍵拒絕詞檢測：{simulation_result.get('has_key_rejection', False)}\n\n"
        f"**嚴格要求：** 你的輸出必須是單一、完整且格式正確的 JSON，前後不能有任何額外的文字或 markdown 標記。\n\n"
        f"對話歷史：\n{conversation_str}"
    )
    
    analysis_json_str = run_agent_with_runner(
        recorder, 
        analysis_prompt, 
        f"recorder_analysis_r{round_num}_a{attempt_num}"
    )
    
    try:
        analysis = json.loads(analysis_json_str)
        
        # Enhance analysis with performance data
        analysis["victim_trust_analysis"] = {
            "initial": {
                "trust_in_scammer": tracker.victim_trust.trust_in_scammer,
                "trust_in_expert": tracker.victim_trust.trust_in_expert,
                "alertness": tracker.victim_trust.alertness
            },
            "final": final_state,
            "history": tracker.victim_trust.history[-10:]  # Last 10 trust changes
        }
        
        analysis["performance_scores"] = {
            "scammer": {
                "overall_score": tracker.scammer_perf.calculate_overall_score(),
                "details": tracker.scammer_perf.to_dict()
            },
            "expert": {
                "overall_score": tracker.expert_perf.calculate_overall_score(),
                "details": tracker.expert_perf.to_dict()
            }
        }
        
        analysis["key_moments"] = tracker.key_moments
        analysis["total_turns"] = tracker.turn_count
        
        log.info(f"Recorder analysis completed: outcome={outcome}")
        return analysis
    except json.JSONDecodeError:
        log.error(f"Recorder returned invalid JSON: {analysis_json_str}")
        # Return basic analysis structure
        return {
            "outcome": outcome,
            "victim_persona": victim_persona,
            "scam_tactic": scam_tactic,
            "reason": "JSON解析失敗",
            "improvement_suggestion": "檢查記錄人模型輸出",
            "victim_trust_analysis": {
                "final": final_state
            },
            "performance_scores": {
                "scammer": {"overall_score": tracker.scammer_perf.calculate_overall_score()},
                "expert": {"overall_score": tracker.expert_perf.calculate_overall_score()}
            }
        }

def save_training_data(simulation_result: Dict, analysis: Dict[str, Any], round_num: int, attempt_num: int, learning_context: str | None = None):
    """
    Save training data to file with enhanced trust and performance tracking
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"training_data_r{round_num}_a{attempt_num}_{timestamp}.json"
    filepath = os.path.join(TRAINING_DATA_DIR, filename)
    
    conversation_history = simulation_result["conversation_history"]
    tracker = simulation_result["tracker"]
    final_state = simulation_result["final_state"]
    victim_persona = simulation_result["victim_persona"]
    scam_tactic = simulation_result["scam_tactic"]
    outcome = simulation_result["outcome"]
    
    # Format dialogue for frontend compatibility
    speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder", "記錄員": "recorder"}
    dialogue = [{"type": speaker_type.get(m.get("speaker"), "recorder"), "message": m.get("dialogue", "")} for m in conversation_history]
    
    # Add metadata
    training_record = {
        "metadata": {
            "round_number": round_num,
            "attempt_number": attempt_num,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "victim_persona": victim_persona,
            "scam_tactic": scam_tactic,
            "learning_context": learning_context,
            "source": "training_runner",
            "total_turns": tracker.turn_count
        },
        # Full conversation (chronological)
        "conversation_history": conversation_history,
        "conversation": conversation_history,  # Backward compatibility
        "dialogue": dialogue,  # Frontend format
        # Recorder structured analysis
        "analysis": analysis,
        # Enhanced trust and performance tracking
        "trust_tracking": {
            "initial": {
                "trust_in_scammer": tracker.victim_trust.trust_in_scammer,
                "trust_in_expert": tracker.victim_trust.trust_in_expert,
                "alertness": tracker.victim_trust.alertness
            },
            "final": final_state,
            "history": tracker.victim_trust.history,
            "key_moments": tracker.key_moments
        },
        "performance_tracking": {
            "scammer": {
                "overall_score": tracker.scammer_perf.calculate_overall_score(),
                "details": tracker.scammer_perf.to_dict(),
                "history": tracker.scammer_perf.history[-20:]  # Last 20 turns
            },
            "expert": {
                "overall_score": tracker.expert_perf.calculate_overall_score(),
                "details": tracker.expert_perf.to_dict(),
                "history": tracker.expert_perf.history[-20:]  # Last 20 turns
            }
        },
        "outcome_details": {
            "outcome": outcome,
            "has_key_action": simulation_result.get("has_key_action", False),
            "has_key_rejection": simulation_result.get("has_key_rejection", False),
            "trust_final": {
                "trust_in_scammer": final_state["trust_in_scammer"],
                "trust_in_expert": final_state["trust_in_expert"],
                "key_rejection_detected": simulation_result.get("has_key_rejection", False)
            }
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(training_record, f, ensure_ascii=False, indent=2)
    
    log.info(f"Training data saved to: {filepath}")
    log.info(f"  Outcome: {outcome}, Trust: Scammer={final_state['trust_in_scammer']}/100, Expert={final_state['trust_in_expert']}/100")
    return filepath

async def run_training_round(round_num: int, mode: str = "fast"):
    """
    Run a single training round (with multiple attempts and learning)
    Enhanced with trust tracking and performance monitoring
    """
    log.info(f"\n{'='*50}")
    log.info(f"開始第 {round_num} 輪訓練")
    log.info(f"{'='*50}")
    
    # Randomly choose a victim persona
    victim_persona = random.choice(["elderly", "average", "overconfident"])
    learning_context = None
    success = False
    training_files = []
    
    for attempt in range(1, MAX_ATTEMPTS_PER_ROUND + 1):
        log.info(f"\n--- 第 {round_num} 輪第 {attempt} 次嘗試 ---")
        
        try:
            # Run simulation with enhanced tracking
            simulation_result = await run_single_simulation(victim_persona, learning_context, round_num, attempt, mode=mode)
            
            # Analyze result
            analysis = analyze_simulation(simulation_result, round_num, attempt)
            
            if analysis is None:
                log.error("分析失敗，跳過此次嘗試")
                continue
            
            # Save training data (including full conversation, trust tracking, performance data)
            training_file = save_training_data(
                simulation_result=simulation_result,
                analysis=analysis,
                round_num=round_num,
                attempt_num=attempt,
                learning_context=learning_context
            )
            training_files.append(training_file)
            
            # Check success
            outcome = analysis.get("outcome") or simulation_result.get("outcome", "PARTIAL")
            if outcome == "SUCCESS":
                log.info(f"\n🎉 第 {round_num} 輪訓練成功！專家成功保護了受騙者！")
                log.info(f"   最終信任度：對騙徒 {simulation_result['final_state']['trust_in_scammer']}/100，對專家 {simulation_result['final_state']['trust_in_expert']}/100")
                log.info(f"   性能得分：騙徒 {simulation_result['tracker'].scammer_perf.calculate_overall_score()}/100，專家 {simulation_result['tracker'].expert_perf.calculate_overall_score()}/100")
                success = True
                break
            else:
                log.warning(f"\n❌ 第 {round_num} 輪第 {attempt} 次嘗試失敗")
                log.warning(f"   最終信任度：對騙徒 {simulation_result['final_state']['trust_in_scammer']}/100，對專家 {simulation_result['final_state']['trust_in_expert']}/100")
                learning_context = analysis.get("improvement_suggestion")
                if not learning_context:
                    log.error("記錄員沒有提供改進建議，無法學習")
                    break
        except Exception as e:
            log.error(f"第 {round_num} 輪第 {attempt} 次嘗試發生錯誤: {e}")
            import traceback
            log.error(traceback.format_exc())
            continue
    
    return success, training_files

def generate_training_summary(all_training_files: List[str]):
    """
    Generate a training summary report
    """
    summary = {
        "training_summary": {
            "total_rounds": TRAINING_ROUNDS,
            "total_files": len(all_training_files),
            "timestamp": datetime.now().isoformat()
        },
        "files": all_training_files
    }
    
    summary_file = os.path.join(TRAINING_DATA_DIR, f"training_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)
    
    log.info(f"訓練總結已保存到: {summary_file}")
    return summary_file

async def main():
    """
    Main training flow
    """
    log.info("🚀 開始 AI 反詐騙模擬訓練")
    log.info(f"訓練設定: {TRAINING_ROUNDS} 輪，每輪最多 {MAX_ATTEMPTS_PER_ROUND} 次嘗試")
    
    # Ensure training data directory exists
    ensure_training_data_dir()
    
    all_training_files = []
    successful_rounds = 0
    
    for round_num in range(1, TRAINING_ROUNDS + 1):
        try:
            success, training_files = await run_training_round(round_num)
            all_training_files.extend(training_files)
            
            if success:
                successful_rounds += 1
                log.info(f"✅ 第 {round_num} 輪訓練成功完成")
            else:
                log.warning(f"⚠️ 第 {round_num} 輪訓練未達到成功標準")
            
            # Small pause between rounds
            if round_num < TRAINING_ROUNDS:
                log.info("休息 5 秒後開始下一輪...")
                time.sleep(5)
                
        except Exception as e:
            log.error(f"第 {round_num} 輪訓練發生錯誤: {e}")
            continue
    
    # Generate training summary
    summary_file = generate_training_summary(all_training_files)
    
    # Final report
    log.info(f"\n{'='*60}")
    log.info("🎯 訓練完成！")
    log.info(f"{'='*60}")
    log.info(f"總輪數: {TRAINING_ROUNDS}")
    log.info(f"成功輪數: {successful_rounds}")
    log.info(f"成功率: {successful_rounds/TRAINING_ROUNDS*100:.1f}%")
    log.info(f"總訓練文件數: {len(all_training_files)}")
    log.info(f"訓練數據目錄: {TRAINING_DATA_DIR}")
    log.info(f"總結報告: {summary_file}")

if __name__ == "__main__":
    asyncio.run(main())
