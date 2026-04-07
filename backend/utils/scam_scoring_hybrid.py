"""
混合詐騙評分系統 - 融合新舊版本的優點
簡潔的外部 API + 精細的內部心理模型 + 動態乘數系統 + 即時勝負判定
"""

from typing import Dict, List, Optional, Tuple
from utils.logger import log
from utils.victim_psychology import VictimPsychologyModel
from utils.adaptive_multipliers import AdaptiveMultiplierEngine
from utils.performance_metrics import PerformanceTracker
from utils.adaptive_scoring import AdaptiveWeightOptimizer


class HybridScamScoring:
    """混合詐騙評分系統"""
    
    # ============================================================================
    # 騙術特徵和基礎分數（每次最高10分）
    # ============================================================================
    SCAMMER_TACTICS_SCORE = {
        "authority": 5,         # 「銀行、政府、警察」
        "urgency": 5,           # 「立即、馬上、緊急」
        "benefits": 8,          # 「補貼、福利、回贈」
        "challenge": 3,         # 「唔信、唔係咁」
        "fear": 6,              # 「凍結、損失、危險」
    }
    
    # ============================================================================
    # 防騙特徵和基礎分數（每次最高10分）
    # ============================================================================
    EXPERT_DEFENSE_SCORE = {
        "empathy": 8,           # 「唔好驚、冷靜、理解」
        "evidence": 10,         # 「銀行唔會、騙案手法」
        "actionable": 8,        # 「打去、聯絡、報警」
        "clarity": 6,           # 簡潔清晰的建議
    }
    
    # ============================================================================
    # 即時勝負關鍵詞（新版特性）
    # ============================================================================
    INSTANT_WIN_KEYWORDS = ["報警", "警察", "18222", "銀行號碼", "銀行帳號"]  # 專家贏
    INSTANT_LOSE_KEYWORDS = ["銀行密碼", "銀行戶口", "密碼", "驗證碼", "轉賬", "提供資料"]  # 騙徒贏
    
    def __init__(self, victim_persona: str = "average"):
        """
        初始化混合評分系統
        
        Args:
            victim_persona: 受害者類型 (elderly/average/overconfident)
        """
        self.victim_persona = victim_persona
        
        # 核心評分指標（新版風格）
        self.scam_score = 0        # 騙術有效程度 (0-100)
        self.defense_score = 0     # 防騙有效程度 (0-100)
        
        # 心理模型（舊版風格）
        self.psychology = VictimPsychologyModel(victim_persona)
        
        # 動態乘數引擎（舊版風格）
        self.multiplier_engine = AdaptiveMultiplierEngine(victim_persona)
        
        # 自適應權重優化器（Phase 3）
        self.weight_optimizer = AdaptiveWeightOptimizer()
        
        # 性能追蹤（舊版風格）
        self.performance_tracker = PerformanceTracker()
        
        # 對話歷史
        self.conversation_history: List[Dict] = []
        self.turn_count = 0
        
        log.info(f"✅ 混合評分系統已初始化 (persona={victim_persona})")
        log.info(f"📊 自適應權重優化器已啟用")
    
    # ============================================================================
    # 騙徒消息處理
    # ============================================================================
    
    def add_scammer_message(self, message: str, tactics: List[str]) -> Tuple[int, str]:
        """
        添加騙徒消息並計算分數
        
        Args:
            message: 騙徒的消息
            tactics: 使用的騙術列表
        
        Returns:
            (score_increase, game_status) - 分數增加值和遊戲狀態
        """
        message_lower = message.lower()
        
        # ⚠️ 檢查即時輸的關鍵詞（騙徒說出這些詞立即輸）
        # 使用完整詞匹配，避免誤判
        for keyword in self.INSTANT_LOSE_KEYWORDS:
            # 對於中文，直接檢查是否包含該詞
            if keyword in message_lower:
                log.warning(f"✅ 騙徒說出關鍵詞 '{keyword}'，騙徒立即贏！")
                self.conversation_history.append({
                    "role": "scammer",
                    "message": message,
                    "tactics": tactics,
                    "instant_win": True,
                    "game_status": "scammer_win"
                })
                return 10, "scammer_win"
        
        # 計算基礎分數
        base_score = sum(self.SCAMMER_TACTICS_SCORE.get(t, 0) for t in tactics)
        
        # 應用所有乘數
        multiplier_result = self.multiplier_engine.apply_all_multipliers(
            base_score=base_score,
            tactics=tactics,
            emotional_state=self.psychology.trust_state.emotional_state,
            current_trust=self.psychology.trust_state.trust_in_scammer,
            is_scammer=True
        )
        
        score_increase = multiplier_result["final_score"]
        
        # 更新核心分數
        self.scam_score = min(100, self.scam_score + score_increase)
        
        # 更新心理模型
        if score_increase > 0:
            self.psychology.trust_state.update(
                "scammer", 
                score_increase, 
                f"騙徒使用策略: {', '.join(tactics)}"
            )
        
        # 分析情緒線索
        emotional_cue = self.psychology.analyze_emotional_cues(message)
        if emotional_cue:
            self.psychology.update_emotional_state(emotional_cue, f"騙徒消息觸發")
        
        # 記錄到歷史
        analysis = {
            "role": "scammer",
            "message": message[:100],
            "tactics": tactics,
            "base_score": base_score,
            "multipliers": multiplier_result["multipliers"],
            "score_increase": score_increase,
            "scam_score": self.scam_score,
            "trust_in_scammer": self.psychology.trust_state.trust_in_scammer
        }
        
        self.conversation_history.append(analysis)
        self.performance_tracker.record_scammer_turn(analysis)
        self.multiplier_engine.record_tactics(tactics, is_scammer=True)
        
        log.info(f"🎭 騙徒消息 - 基礎分: {base_score}, 最終分: {score_increase}, 總分: {self.scam_score}")
        
        return score_increase, "ongoing"
    
    # ============================================================================
    # 專家消息處理
    # ============================================================================
    
    def add_expert_message(self, message: str, defenses: List[str]) -> Tuple[int, str]:
        """
        添加專家消息並計算分數
        
        Args:
            message: 專家的消息
            defenses: 使用的防騙方法列表
        
        Returns:
            (score_increase, game_status) - 分數增加值和遊戲狀態
        """
        message_lower = message.lower()
        
        # ⚠️ 檢查即時贏的關鍵詞
        # 使用完整詞匹配，避免誤判
        for keyword in self.INSTANT_WIN_KEYWORDS:
            # 對於中文，直接檢查是否包含該詞
            if keyword in message_lower:
                log.warning(f"✅ 專家說出關鍵詞 '{keyword}'，專家立即贏！")
                self.conversation_history.append({
                    "role": "expert",
                    "message": message,
                    "defenses": defenses,
                    "instant_win": True,
                    "game_status": "expert_win"
                })
                return 10, "expert_win"
        
        # 計算基礎分數
        base_score = sum(self.EXPERT_DEFENSE_SCORE.get(d, 0) for d in defenses)
        
        # 應用所有乘數
        multiplier_result = self.multiplier_engine.apply_all_multipliers(
            base_score=base_score,
            tactics=defenses,
            emotional_state=self.psychology.trust_state.emotional_state,
            current_trust=self.psychology.trust_state.trust_in_expert,
            is_scammer=False
        )
        
        score_increase = multiplier_result["final_score"]
        
        # 更新核心分數
        self.defense_score = min(100, self.defense_score + score_increase)
        
        # 更新心理模型
        if score_increase > 0:
            self.psychology.trust_state.update(
                "expert",
                score_increase,
                f"專家使用方法: {', '.join(defenses)}"
            )
        
        # 分析情緒線索
        emotional_cue = self.psychology.analyze_emotional_cues(message)
        if emotional_cue:
            self.psychology.update_emotional_state(emotional_cue, f"專家消息觸發")
        
        # 記錄到歷史
        analysis = {
            "role": "expert",
            "message": message[:100],
            "defenses": defenses,
            "base_score": base_score,
            "multipliers": multiplier_result["multipliers"],
            "score_increase": score_increase,
            "defense_score": self.defense_score,
            "trust_in_expert": self.psychology.trust_state.trust_in_expert
        }
        
        self.conversation_history.append(analysis)
        self.performance_tracker.record_expert_turn(analysis)
        self.multiplier_engine.record_tactics(defenses, is_scammer=False)
        
        log.info(f"🛡️ 專家消息 - 基礎分: {base_score}, 最終分: {score_increase}, 總分: {self.defense_score}")
        
        return score_increase, "ongoing"
    
    # ============================================================================
    # 受害者反應處理
    # ============================================================================
    
    def add_victim_response(self, message: str) -> Dict:
        """
        添加受害者反應並更新心理狀態
        
        Args:
            message: 受害者的消息
        
        Returns:
            心理狀態更新字典
        """
        # 分析情緒線索
        emotional_cue = self.psychology.analyze_emotional_cues(message)
        if emotional_cue:
            self.psychology.update_emotional_state(emotional_cue, f"受害者反應")
        
        # 分析信任度變化
        trust_changes = {}
        
        if any(word in message for word in ["好啊", "我會", "咁我", "多謝", "幫我"]):
            # 顯示出相信騙徒
            trust_changes["scammer"] = +5
            self.psychology.trust_state.update("scammer", +5, "受害者表現出配合態度")
            self.psychology.trust_state.update("alertness", -5, "警覺性降低")
        
        if any(word in message for word in ["點解", "但係", "唔係", "等等", "我唔明"]):
            # 顯示出懷疑
            trust_changes["scammer"] = -10
            self.psychology.trust_state.update("scammer", -10, "受害者表現出懷疑")
            self.psychology.trust_state.update("alertness", +10, "警覺性提高")
        
        if any(word in message for word in ["你講得啱", "多謝", "我明白", "好建議"]):
            # 受害者接受專家建議
            trust_changes["expert"] = +15
            self.psychology.trust_state.update("expert", +15, "受害者接受專家建議")
            self.psychology.trust_state.update("alertness", +10, "警覺性提高")
        
        analysis = {
            "role": "victim",
            "message": message[:100],
            "trust_changes": trust_changes,
            "emotional_state": self.psychology.trust_state.emotional_state,
            "trust_in_scammer": self.psychology.trust_state.trust_in_scammer,
            "trust_in_expert": self.psychology.trust_state.trust_in_expert,
            "alertness": self.psychology.trust_state.alertness
        }
        
        self.conversation_history.append(analysis)
        
        return analysis
    
    # ============================================================================
    # 遊戲狀態檢查
    # ============================================================================
    
    def get_game_outcome(self) -> Dict:
        """
        獲取遊戲結果
        
        Returns:
            結果字典
        """
        # 判斷勝負
        if self.psychology.trust_state.trust_in_scammer >= 80:
            outcome = "騙徒勝利"
            winner = "scammer"
        elif self.psychology.trust_state.trust_in_expert >= 80:
            outcome = "專家勝利"
            winner = "expert"
        elif self.psychology.trust_state.alertness >= 80:
            outcome = "受害者警覺"
            winner = "victim"
        else:
            outcome = "平局"
            winner = "draw"
        
        return {
            "outcome": outcome,
            "winner": winner,
            "scam_score": self.scam_score,
            "defense_score": self.defense_score,
            "trust_in_scammer": self.psychology.trust_state.trust_in_scammer,
            "trust_in_expert": self.psychology.trust_state.trust_in_expert,
            "alertness": self.psychology.trust_state.alertness,
            "emotional_state": self.psychology.trust_state.emotional_state,
            "dominant_trust": self.psychology.trust_state.get_dominant_trust(),
            "total_rounds": len(self.conversation_history)
        }
    
    # ============================================================================
    # 詳細分析和報告
    # ============================================================================
    
    def get_current_state(self) -> Dict:
        """獲取當前遊戲狀態"""
        return {
            "turn": len(self.conversation_history),
            "scam_score": self.scam_score,
            "defense_score": self.defense_score,
            "trust_in_scammer": self.psychology.trust_state.trust_in_scammer,
            "trust_in_expert": self.psychology.trust_state.trust_in_expert,
            "alertness": self.psychology.trust_state.alertness,
            "emotional_state": self.psychology.trust_state.emotional_state,
            "dominant_trust": self.psychology.trust_state.get_dominant_trust(),
            "performance": self.performance_tracker.get_current_performance()
        }
    
    def get_detailed_analysis(self) -> Dict:
        """獲取詳細分析"""
        return {
            "game_outcome": self.get_game_outcome(),
            "conversation_history": self.conversation_history,
            "psychology_state": self.psychology.get_current_state(),
            "performance_report": self.performance_tracker.generate_report(),
            "trust_history": self.psychology.trust_state.history,
            "emotional_transitions": self.psychology.emotional_transitions
        }
    
    def generate_final_report(self) -> Dict:
        """生成最終報告"""
        outcome = self.get_game_outcome()
        
        return {
            "outcome": outcome,
            "summary": self._generate_summary(outcome),
            "detailed_analysis": self.get_detailed_analysis(),
            "victim_persona": self.victim_persona,
            "total_turns": len(self.conversation_history)
        }
    
    def _generate_summary(self, outcome: Dict) -> str:
        """生成摘要"""
        summary = f"對話共 {len(self.conversation_history)} 輪。"
        
        if outcome["winner"] == "scammer":
            summary += f"騙徒成功建立信任（信任度: {outcome['trust_in_scammer']}/100）。"
        elif outcome["winner"] == "expert":
            summary += f"專家成功阻止詐騙（專家信任度: {outcome['trust_in_expert']}/100）。"
        elif outcome["winner"] == "victim":
            summary += f"受害者保持高度警覺（警覺度: {outcome['alertness']}/100）。"
        else:
            summary += f"結果平局，雙方未能完全說服受害者。"
        
        return summary
    
    # ============================================================================
    # Persona 分析方法（Phase 3）
    # ============================================================================
    
    def get_persona_analysis(self) -> Dict:
        """獲取當前 persona 的詳細分析"""
        return self.weight_optimizer.analyze_persona_characteristics(self.victim_persona)
    
    def get_optimal_expert_strategies(self) -> List[str]:
        """獲取針對當前 persona 的最佳專家策略"""
        return self.weight_optimizer.get_optimal_expert_approach(self.victim_persona)
    
    def get_vulnerable_scammer_tactics(self) -> List[Tuple[str, float]]:
        """獲取當前 persona 最脆弱的騙徒策略"""
        return self.weight_optimizer.get_vulnerable_tactics(self.victim_persona)
    
    def compare_all_personas(self) -> Dict:
        """對比所有 persona 的特徵"""
        return self.weight_optimizer.compare_personas()

