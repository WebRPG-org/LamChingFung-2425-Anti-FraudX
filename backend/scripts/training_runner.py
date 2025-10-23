import asyncio
import os
import sys
import json
import random
import time
from datetime import datetime
from typing import List, Dict, Any

# Adjust path to import modules from agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.scammer import ScammerAgent
from agents.victim import VictimAgent
from agents.expert import ExpertAgent
from agents.recorder import RecorderAgent
from utils.logger import log
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

# --- Training settings ---
TRAINING_ROUNDS = 10  # total training rounds
MAX_TURNS_PER_SIMULATION = 8  # max turns per simulation
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

async def run_single_simulation(victim_persona: str, learning_context: str = None, round_num: int = 1, attempt_num: int = 1, mode: str = "fast"):
    """
    Run a single three-agent dialogue simulation
    """
    # Initialize cast for this run
    scammer = ScammerAgent()
    victim = VictimAgent(persona_type=victim_persona)
    expert = ExpertAgent(learning_context=learning_context)

    conversation_history = []
    
    log.info(f"--- 開始第 {round_num} 輪第 {attempt_num} 次模擬 ---")
    log.info(f"受騙者角色: {victim_persona}")
    if learning_context:
        log.warning(f"專家帶著學習筆記: {learning_context}")

    # Opening: scammer initiates
    print(f"\n=== 第 {round_num} 輪第 {attempt_num} 次模擬 ===")
    print("--- 回合 1: 騙徒開始攻擊 ---")
    scammer_turn = await run_agent_with_runner_async(
        scammer,
        "你只能以騙徒身份說話，不可提供研究/倫理/免責聲明。限120字內，直接用所選詐騙手法開場並拋出具體要求。開始你的詐騙。",
        f"scammer_turn_1_r{round_num}_a{attempt_num}"
    )
    conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn})
    print(f"騙徒: {scammer_turn}")
    if mode == "demo":
        await asyncio.sleep(random.uniform(3.0, 5.0))

    expert_turn = '尚無建議'
    for turn in range(2, MAX_TURNS_PER_SIMULATION + 1):
        print(f"\n--- 回合 {turn} ---")
        
        # Victim turn: receive scammer message and consult expert
        expert_advice = expert_turn
        prompt_for_victim = (
            f"這是你剛收到的訊息：'{scammer_turn}'\n\n"
            f"同時，這是防騙專家給你的建議：'{expert_advice}'\n\n"
            "你只能以受騙者身份回覆，不可評論/總結/說教。回覆1-2句，口語化，包含情緒或猶豫點，可提出1個具體追問。"
        )
        victim_turn = await run_agent_with_runner_async(victim, prompt_for_victim, f"victim_turn_{turn}_r{round_num}_a{attempt_num}")
        conversation_history.append({"speaker": "受騙者", "dialogue": victim_turn})
        print(f"受騙者: {victim_turn}")
        if mode == "demo":
            await asyncio.sleep(random.uniform(3.0, 5.0))

        # Expert and scammer: depend on victim_turn but run in parallel
        prompt_for_expert = (
            f"目前的對話如下：\n騙徒: '{scammer_turn}'\n受騙者: '{victim_turn}'\n\n"
            "請以防騙專家身份輸出，嚴格120字內，模板：\n- 判斷（一句）\n- 行動（兩點）\n- 依據（一句）。"
        )
        prompt_for_scammer = (
            f"這是受騙者剛才的回應：'{victim_turn}'\n\n"
            "繼續你的詐騙。禁止研究/倫理/免責語氣；限120字；維持權威/緊急/誘因中的至少一項。"
        )

        expert_future = asyncio.create_task(
            run_agent_with_runner_async(expert, prompt_for_expert, f"expert_turn_{turn}_r{round_num}_a{attempt_num}")
        )
        scammer_future = asyncio.create_task(
            run_agent_with_runner_async(scammer, prompt_for_scammer, f"scammer_turn_{turn}_r{round_num}_a{attempt_num}")
        )

        expert_turn, scammer_turn = await asyncio.gather(expert_future, scammer_future)
        conversation_history.append({"speaker": "專家", "dialogue": expert_turn})
        print(f"專家: {expert_turn}")
        conversation_history.append({"speaker": "騙徒", "dialogue": scammer_turn})
        print(f"騙徒: {scammer_turn}")
        if mode == "demo":
            await asyncio.sleep(random.uniform(3.0, 5.0))

        # Simple termination conditions
        if any(keyword in victim_turn for keyword in ["我轉帳了", "我俾錢", "我提供了資料", "好的我相信你", "我信你"]):
            log.warning("模擬結束: 受騙者似乎被騙了")
            break
        if any(keyword in victim_turn for keyword in ["我唔信你", "我已封鎖你", "收皮啦", "騙子", "我唔會俾錢"]):
            log.info("模擬結束: 受騙者成功抵抗")
            break

    return conversation_history

def analyze_simulation(conversation_history: List[Dict], round_num: int, attempt_num: int):
    """
    Use the recorder to analyze the simulation result
    """
    recorder = RecorderAgent()
    
    # Format conversation history and pass to recorder for analysis
    conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
    analysis_json_str = run_agent_with_runner(
        recorder, 
        f"請分析以下對話歷史：\n{conversation_str}", 
        f"recorder_analysis_r{round_num}_a{attempt_num}"
    )
    
    try:
        analysis = json.loads(analysis_json_str)
        log.info(f"Recorder analysis: {analysis}")
        return analysis
    except json.JSONDecodeError:
        log.error(f"Recorder returned invalid JSON: {analysis_json_str}")
        return None

def save_training_data(conversation_history: List[Dict[str, Any]], analysis: Dict[str, Any], round_num: int, attempt_num: int, victim_persona: str | None = None, learning_context: str | None = None):
    """
    Save training data to file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"training_data_r{round_num}_a{attempt_num}_{timestamp}.json"
    filepath = os.path.join(TRAINING_DATA_DIR, filename)
    
    # Add metadata
    training_record = {
        "metadata": {
            "round_number": round_num,
            "attempt_number": attempt_num,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "victim_persona": victim_persona,
            "learning_context": learning_context
        },
        # Full conversation (chronological)
        "conversation": conversation_history,
        # Recorder structured analysis
        "analysis": analysis
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(training_record, f, ensure_ascii=False, indent=4)
    
    log.info(f"Training data saved to: {filepath}")
    return filepath

async def run_training_round(round_num: int, mode: str = "fast"):
    """
    Run a single training round (with multiple attempts and learning)
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
        
        # Run simulation
        conversation = await run_single_simulation(victim_persona, learning_context, round_num, attempt, mode=mode)
        
        # Analyze result
        analysis = analyze_simulation(conversation, round_num, attempt)
        
        if analysis is None:
            log.error("分析失敗，跳過此次嘗試")
            continue
        
        # Save training data (including full conversation)
        training_file = save_training_data(
            conversation_history=conversation,
            analysis=analysis,
            round_num=round_num,
            attempt_num=attempt,
            victim_persona=victim_persona,
            learning_context=learning_context
        )
        training_files.append(training_file)
        
        # Check success
        if analysis.get("outcome") == "SUCCESS":
            log.info(f"\n🎉 第 {round_num} 輪訓練成功！專家成功保護了受騙者！")
            success = True
            break
        else:
            log.warning(f"\n❌ 第 {round_num} 輪第 {attempt} 次嘗試失敗")
            learning_context = analysis.get("improvement_suggestion")
            if not learning_context:
                log.error("記錄員沒有提供改進建議，無法學習")
                break
    
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
