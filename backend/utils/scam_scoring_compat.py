"""
兼容層 - 新舊版本的無縫過渡
支持舊版 API 調用，內部使用新的混合系統
"""

from typing import Dict, List, Optional, Tuple
from utils.scam_scoring_hybrid import HybridScamScoring
from utils.logger import log


class ScamScoringCompatibility:
    """兼容層 - 支持舊版 API"""
    
    def __init__(self, victim_persona: str = "average"):
        """初始化兼容層"""
        self.hybrid_scorer = HybridScamScoring(victim_persona)
        self.victim_persona = victim_persona
    
    # ============================================================================
    # 舊版 API 兼容
    # ============================================================================
    
    def add_scammer_message(self, message: str, tactics: List[str]) -> Tuple[int, str]:
        """舊版 API - 添加騙徒消息"""
        return self.hybrid_scorer.add_scammer_message(message, tactics)
    
    def add_expert_message(self, message: str, defenses: List[str]) -> Tuple[int, str]:
        """舊版 API - 添加專家消息"""
        return self.hybrid_scorer.add_expert_message(message, defenses)
    
    def add_victim_response(self, message: str, response_type: str = "neutral") -> Dict:
        """舊版 API - 添加受害者反應"""
        return self.hybrid_scorer.add_victim_response(message)
    
    def get_scam_risk_level(self) -> str:
        """舊版 API - 獲取詐騙風險等級"""
        score = self.hybrid_scorer.scam_score
        if score < 20:
            return "極低"
        elif score < 40:
            return "低"
        elif score < 60:
            return "中"
        elif score < 80:
            return "高"
        else:
            return "極高"
    
    def get_defense_effectiveness(self) -> str:
        """舊版 API - 獲取防騙有效程度"""
        score = self.hybrid_scorer.defense_score
        if score < 20:
            return "無效"
        elif score < 40:
            return "低效"
        elif score < 60:
            return "中等"
        elif score < 80:
            return "高效"
        else:
            return "非常高效"
    
    def get_victim_status(self) -> str:
        """舊版 API - 獲取受害者狀態"""
        trust = self.hybrid_scorer.psychology.trust_state.trust_in_scammer
        if trust > 80:
            return "完全相信"
        elif trust > 60:
            return "傾向相信"
        elif trust > 40:
            return "猶豫"
        elif trust > 20:
            return "傾向懷疑"
        else:
            return "完全懷疑"
    
    def get_game_outcome(self) -> Dict:
        """舊版 API - 獲取遊戲結果"""
        return self.hybrid_scorer.get_game_outcome()
    
    def get_detailed_analysis(self) -> Dict:
        """舊版 API - 獲取詳細分析"""
        return self.hybrid_scorer.get_detailed_analysis()
    
    # ============================================================================
    # 新版 API 直通
    # ============================================================================
    
    def get_current_state(self) -> Dict:
        """新版 API - 獲取當前狀態"""
        return self.hybrid_scorer.get_current_state()
    
    def generate_final_report(self) -> Dict:
        """新版 API - 生成最終報告"""
        return self.hybrid_scorer.generate_final_report()
    
    # ============================================================================
    # 混合系統特有方法
    # ============================================================================
    
    def get_psychology_state(self) -> Dict:
        """獲取心理狀態"""
        return self.hybrid_scorer.psychology.get_current_state()
    
    def get_performance_metrics(self) -> Dict:
        """獲取性能指標"""
        return self.hybrid_scorer.performance_tracker.get_current_performance()
    
    def get_multiplier_analysis(self) -> Dict:
        """獲取乘數分析"""
        return {
            "recent_scammer_tactics": self.hybrid_scorer.multiplier_engine.recent_scammer_tactics,
            "recent_expert_approaches": self.hybrid_scorer.multiplier_engine.recent_expert_approaches
        }


# ============================================================================
# 全局實例（便於快速使用）
# ============================================================================

_global_scorer: Optional[ScamScoringCompatibility] = None


def initialize_scorer(victim_persona: str = "average") -> ScamScoringCompatibility:
    """初始化全局評分器"""
    global _global_scorer
    _global_scorer = ScamScoringCompatibility(victim_persona)
    log.info(f"✅ 全局評分器已初始化 (persona={victim_persona})")
    return _global_scorer


def get_scorer() -> ScamScoringCompatibility:
    """獲取全局評分器"""
    global _global_scorer
    if _global_scorer is None:
        _global_scorer = ScamScoringCompatibility()
    return _global_scorer

