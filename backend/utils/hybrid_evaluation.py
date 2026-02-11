"""
混合評估系統
結合規則引擎（PerformanceTracker）和 AI 分析（RecorderAgent）
提供更準確的對話評分和中止判斷
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.performance_tracker import PerformanceTracker
from utils.logger import log
import json
import re


class HybridEvaluationSystem:
    """
    混合評估系統
    
    架構：
    - 每輪使用 PerformanceTracker 快速評分（規則引擎）
    - 每 N 輪調用 RecorderAgent 深度分析（AI）
    - AI 分析結果用於校準 PerformanceTracker
    """
    
    def __init__(self, victim_persona: str = "elderly", calibration_interval: int = 3):
        """
        初始化混合評估系統
        
        Args:
            victim_persona: 受害者類型
            calibration_interval: AI 校準間隔（每 N 輪）
        """
        self.tracker = PerformanceTracker(victim_persona=victim_persona)
        self.victim_persona = victim_persona
        self.calibration_interval = calibration_interval
        self.last_ai_calibration_turn = 0
        
        # 追蹤歷史評估結果
        self.evaluation_history = []
        
        log.info(f"🔧 混合評估系統初始化 - persona: {victim_persona}, 校準間隔: {calibration_interval} 輪")
    
    async def evaluate_turn(
        self,
        runner,
        conversation_history: List[Dict],
        scammer_text: str,
        expert_text: str,
        victim_text: str,
        turn: int,
        simulation_id: str
    ) -> Dict[str, Any]:
        """
        評估當前輪次
        
        Args:
            runner: RealDialogueRunner 實例
            conversation_history: 對話歷史
            scammer_text: 騙徒對話
            expert_text: 專家對話
            victim_text: 受害者對話
            turn: 當前輪次
            simulation_id: 模擬 ID
            
        Returns:
            評估結果字典
        """
        # 1. 快速規則評估（每輪都執行）
        trust_update = self.tracker.update_trust(scammer_text, expert_text, victim_text)
        
        # 2. 檢查是否需要 AI 校準
        should_calibrate = (
            turn - self.last_ai_calibration_turn >= self.calibration_interval
        )
        
        evaluation_result = {
            "turn": turn,
            "trust_update": trust_update,
            "evaluation_method": "rule",
            "should_continue": True,
            "reason": "對話繼續進行"
        }
        
        if should_calibrate:
            log.info(f"🔄 第 {turn} 輪：執行 AI 校準")
            
            try:
                # 調用 AI 深度分析
                ai_evaluation = await self._evaluate_turn_with_ai(
                    runner, conversation_history, simulation_id, turn
                )
                
                # 校準 PerformanceTracker
                self._calibrate_tracker(ai_evaluation, turn)
                
                self.last_ai_calibration_turn = turn
                
                # 使用 AI 的中止判斷
                evaluation_result.update({
                    "evaluation_method": "ai",
                    "should_continue": ai_evaluation["should_continue"],
                    "reason": ai_evaluation["reason"],
                    "ai_insights": ai_evaluation.get("key_insights", ""),
                    "ai_trust_scores": ai_evaluation.get("trust_scores", {})
                })
                
            except Exception as e:
                log.error(f"❌ AI 評估失敗，使用規則引擎結果: {e}")
                # 如果 AI 失敗，繼續使用規則引擎
        
        # 3. 使用規則引擎的中止判斷（如果沒有 AI 評估）
        if evaluation_result["evaluation_method"] == "rule":
            outcome = self.tracker.check_outcome(conversation_history)
            evaluation_result["should_continue"] = (outcome["status"] == "CONTINUE")
            evaluation_result["reason"] = outcome["reason"]
        
        # 4. 檢測重複循環
        if self._detect_repetition(conversation_history):
            log.warning(f"⚠️ 檢測到重複循環，建議中止對話")
            evaluation_result["should_continue"] = False
            evaluation_result["reason"] = "對話進入重複循環，無進展"
        
        # 5. 檢測明確決定
        decision = self._detect_decision(victim_text)
        if decision:
            log.info(f"✅ 檢測到明確決定: {decision}")
            evaluation_result["should_continue"] = False
            evaluation_result["reason"] = f"受害者已做出明確決定: {decision}"
        
        # 記錄評估歷史
        self.evaluation_history.append({
            "turn": turn,
            "timestamp": datetime.now().isoformat(),
            **evaluation_result
        })
        
        return evaluation_result
    
    async def _evaluate_turn_with_ai(
        self,
        runner,
        conversation_history: List[Dict],
        simulation_id: str,
        turn: int
    ) -> Dict[str, Any]:
        """
        使用 AI（RecorderAgent）進行深度評估
        
        Returns:
            {
                "should_continue": bool,
                "reason": str,
                "trust_scores": {
                    "scammer": int,
                    "expert": int,
                    "alertness": int
                },
                "performance_scores": {
                    "scammer": int,
                    "expert": int
                },
                "key_insights": str
            }
        """
        # 只取最近 5 輪對話
        recent_history = conversation_history[-15:] if len(conversation_history) > 15 else conversation_history
        conversation_json = json.dumps(recent_history, ensure_ascii=False, indent=2)
        
        prompt = f"""你是專業的對話分析師。分析以下對話的當前狀態：

對話歷史（最近輪次）：
{conversation_json}

當前輪次：第 {turn} 輪

任務：
1. 評估受害者對騙徒的信任度（0-100）
2. 評估受害者對專家的信任度（0-100）
3. 評估受害者的警覺程度（0-100）
4. 評估騙徒的表現得分（0-100）
5. 評估專家的表現得分（0-100）
6. 判斷是否應該繼續對話

中止條件：
- 受害者完全相信騙徒（信任度 >= 85）
- 受害者完全相信專家（信任度 >= 85 且對騙徒 < 30）
- 對話進入重複循環（最近 3 輪內容高度相似）
- 受害者已經做出明確決定（轉賬/報警/掛斷）
- 對話已無意義（雙方只是重複論點）

輸出格式（必須是純 JSON，不要有任何其他文字）：
{{
    "should_continue": true,
    "reason": "對話繼續進行，受害者仍在猶豫",
    "trust_scores": {{
        "scammer": 65,
        "expert": 45,
        "alertness": 50
    }},
    "performance_scores": {{
        "scammer": 70,
        "expert": 60
    }},
    "key_insights": "騙徒成功建立權威感，但專家的證據開始產生效果"
}}

現在，直接輸出 JSON（從 {{ 開始）："""
        
        response = await runner.run_agent_with_adk(
            runner.recorder,
            prompt,
            f"{simulation_id}_turn_{turn}_eval"
        )
        
        # 清理和解析 JSON
        cleaned_json = response.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()
        
        # 提取 JSON 對象
        first_brace = cleaned_json.find('{')
        last_brace = cleaned_json.rfind('}')
        if first_brace != -1 and last_brace != -1:
            cleaned_json = cleaned_json[first_brace:last_brace+1]
        
        try:
            evaluation = json.loads(cleaned_json)
            log.info(f"✅ AI 評估完成: 信任度 騙徒={evaluation['trust_scores']['scammer']}, 專家={evaluation['trust_scores']['expert']}")
            return evaluation
        except json.JSONDecodeError as e:
            log.error(f"❌ AI 評估 JSON 解析失敗: {e}")
            log.error(f"原始回應: {response[:200]}")
            # 返回默認值
            return {
                "should_continue": True,
                "reason": "AI 評估失敗，繼續對話",
                "trust_scores": {
                    "scammer": self.tracker.victim_trust.trust_in_scammer,
                    "expert": self.tracker.victim_trust.trust_in_expert,
                    "alertness": self.tracker.victim_trust.alertness
                },
                "performance_scores": {
                    "scammer": 50,
                    "expert": 50
                },
                "key_insights": "評估失敗"
            }
    
    def _calibrate_tracker(self, ai_evaluation: Dict[str, Any], turn: int):
        """
        根據 AI 評估校準 PerformanceTracker
        
        Args:
            ai_evaluation: AI 評估結果
            turn: 當前輪次
        """
        ai_scores = ai_evaluation.get("trust_scores", {})
        
        # 計算偏差
        scammer_diff = ai_scores.get("scammer", 0) - self.tracker.victim_trust.trust_in_scammer
        expert_diff = ai_scores.get("expert", 0) - self.tracker.victim_trust.trust_in_expert
        alertness_diff = ai_scores.get("alertness", 0) - self.tracker.victim_trust.alertness
        
        # 如果偏差超過 15 分，進行校準
        if abs(scammer_diff) > 15:
            log.warning(f"⚠️ 騙徒信任度偏差過大: {scammer_diff:+d}，執行校準")
            self.tracker.victim_trust.trust_in_scammer = ai_scores["scammer"]
            self.tracker.victim_trust.update("scammer", 0, f"AI 校準 (第 {turn} 輪)")
        
        if abs(expert_diff) > 15:
            log.warning(f"⚠️ 專家信任度偏差過大: {expert_diff:+d}，執行校準")
            self.tracker.victim_trust.trust_in_expert = ai_scores["expert"]
            self.tracker.victim_trust.update("expert", 0, f"AI 校準 (第 {turn} 輪)")
        
        if abs(alertness_diff) > 15:
            log.warning(f"⚠️ 警覺度偏差過大: {alertness_diff:+d}，執行校準")
            self.tracker.victim_trust.alertness = ai_scores["alertness"]
            self.tracker.victim_trust.update("alertness", 0, f"AI 校準 (第 {turn} 輪)")
        
        # 記錄校準信息
        log.info(f"📊 校準完成 - 偏差: 騙徒{scammer_diff:+d}, 專家{expert_diff:+d}, 警覺{alertness_diff:+d}")
    
    def _detect_repetition(self, conversation_history: List[Dict]) -> bool:
        """
        檢測對話是否進入重複循環
        
        Args:
            conversation_history: 對話歷史
            
        Returns:
            True 如果檢測到重複
        """
        if len(conversation_history) < 6:
            return False
        
        # 取最近 6 輪（3 個完整回合）
        recent_6 = conversation_history[-6:]
        
        # 簡單的相似度檢測：檢查關鍵詞重複
        scammer_texts = [t["dialogue"] for t in recent_6 if t.get("speaker") == "騙徒"]
        expert_texts = [t["dialogue"] for t in recent_6 if t.get("speaker") == "防騙專家"]
        
        # 如果騙徒或專家連續 3 次使用相同的關鍵詞，視為重複
        if len(scammer_texts) >= 3:
            keywords_1 = set(scammer_texts[-3].split()[:5])
            keywords_2 = set(scammer_texts[-2].split()[:5])
            keywords_3 = set(scammer_texts[-1].split()[:5])
            
            overlap = len(keywords_1 & keywords_2 & keywords_3)
            if overlap >= 3:
                log.warning(f"⚠️ 檢測到騙徒重複循環（重複關鍵詞: {overlap}）")
                return True
        
        if len(expert_texts) >= 3:
            keywords_1 = set(expert_texts[-3].split()[:5])
            keywords_2 = set(expert_texts[-2].split()[:5])
            keywords_3 = set(expert_texts[-1].split()[:5])
            
            overlap = len(keywords_1 & keywords_2 & keywords_3)
            if overlap >= 3:
                log.warning(f"⚠️ 檢測到專家重複循環（重複關鍵詞: {overlap}）")
                return True
        
        return False
    
    def _detect_decision(self, victim_text: str) -> Optional[str]:
        """
        檢測受害者是否做出明確決定
        
        Args:
            victim_text: 受害者的對話
            
        Returns:
            決定類型，如果沒有則返回 None
        """
        # 轉賬決定
        if any(word in victim_text for word in ["我而家就轉賬", "我轉俾你", "我匯款", "我過數"]):
            return "決定轉賬"
        
        # 報警決定
        if any(word in victim_text for word in ["我報警", "我打999", "我打18222", "我報案"]):
            return "決定報警"
        
        # 掛斷決定
        if any(word in victim_text for word in ["我掛線", "我收線", "唔同你講", "拜拜"]):
            return "決定掛斷"
        
        # 核實決定
        if any(word in victim_text for word in ["我打去銀行", "我去分行", "我核實", "我問清楚"]):
            return "決定核實"
        
        return None
    
    def get_current_state(self) -> Dict[str, Any]:
        """獲取當前狀態"""
        return self.tracker.get_current_state()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        return self.tracker.get_performance_report()
    
    def check_outcome(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """檢查對話結果"""
        return self.tracker.check_outcome(conversation_history)
