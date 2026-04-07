"""
性能指標追蹤 - 追蹤騙徒和專家的表現
整合舊版 performance_tracker.py 的性能評分系統
"""

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import log


@dataclass
class ScammerPerformance:
    """騙徒表現評分"""
    persuasiveness: int = 50        # 說服力 (0-100)
    credibility: int = 50           # 可信度 (0-100)
    pressure_effectiveness: int = 50  # 施壓有效性 (0-100)
    role_consistency: int = 100     # 角色一致性 (0-100)
    strategy_score: int = 50        # 策略得分 (0-100)
    
    successful_manipulations: int = 0  # 成功的操控次數
    exposed_lies: int = 0              # 被揭穿的謊言次數
    trust_gains: int = 0               # 獲得的信任增加次數
    trust_losses: int = 0              # 失去的信任次數
    
    history: List[Dict] = field(default_factory=list)
    
    def record_turn(self, turn_analysis: Dict):
        """記錄單輪表現"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            **turn_analysis
        })
        
        # 更新統計
        if turn_analysis.get("trust_change", 0) > 0:
            self.trust_gains += 1
        elif turn_analysis.get("trust_change", 0) < 0:
            self.trust_losses += 1
        
        if turn_analysis.get("exposed", False):
            self.exposed_lies += 1
        
        if turn_analysis.get("manipulation_success", False):
            self.successful_manipulations += 1
    
    def calculate_overall_score(self) -> int:
        """計算總體得分"""
        base_score = (
            self.persuasiveness * 0.3 +
            self.credibility * 0.2 +
            self.pressure_effectiveness * 0.2 +
            self.role_consistency * 0.15 +
            self.strategy_score * 0.15
        )
        
        # 根據成功/失敗調整
        success_bonus = self.successful_manipulations * 5
        failure_penalty = self.exposed_lies * 10
        
        final_score = max(0, min(100, base_score + success_bonus - failure_penalty))
        return int(final_score)
    
    def to_dict(self) -> Dict:
        return {
            "persuasiveness": self.persuasiveness,
            "credibility": self.credibility,
            "pressure_effectiveness": self.pressure_effectiveness,
            "role_consistency": self.role_consistency,
            "strategy_score": self.strategy_score,
            "overall_score": self.calculate_overall_score(),
            "successful_manipulations": self.successful_manipulations,
            "exposed_lies": self.exposed_lies,
            "trust_gains": self.trust_gains,
            "trust_losses": self.trust_losses
        }


@dataclass
class ExpertPerformance:
    """專家表現評分"""
    intervention_effectiveness: int = 50  # 干預有效性 (0-100)
    clarity: int = 50                     # 清晰度 (0-100)
    empathy: int = 50                     # 同理心 (0-100)
    actionability: int = 50               # 建議可執行性 (0-100)
    timing: int = 50                      # 時機把握 (0-100)
    
    successful_warnings: int = 0      # 成功的警告次數
    ignored_warnings: int = 0         # 被忽視的警告次數
    trust_gains: int = 0              # 獲得的信任增加次數
    trust_losses: int = 0             # 失去的信任次數
    
    history: List[Dict] = field(default_factory=list)
    
    def record_turn(self, turn_analysis: Dict):
        """記錄單輪表現"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            **turn_analysis
        })
        
        # 更新統計
        if turn_analysis.get("trust_change", 0) > 0:
            self.trust_gains += 1
        elif turn_analysis.get("trust_change", 0) < 0:
            self.trust_losses += 1
        
        if turn_analysis.get("warning_effective", False):
            self.successful_warnings += 1
        elif turn_analysis.get("warning_ignored", False):
            self.ignored_warnings += 1
    
    def calculate_overall_score(self) -> int:
        """計算總體得分"""
        base_score = (
            self.intervention_effectiveness * 0.3 +
            self.clarity * 0.2 +
            self.empathy * 0.2 +
            self.actionability * 0.15 +
            self.timing * 0.15
        )
        
        # 根據成功/失敗調整
        success_bonus = self.successful_warnings * 5
        failure_penalty = self.ignored_warnings * 3
        
        final_score = max(0, min(100, base_score + success_bonus - failure_penalty))
        return int(final_score)
    
    def to_dict(self) -> Dict:
        return {
            "intervention_effectiveness": self.intervention_effectiveness,
            "clarity": self.clarity,
            "empathy": self.empathy,
            "actionability": self.actionability,
            "timing": self.timing,
            "overall_score": self.calculate_overall_score(),
            "successful_warnings": self.successful_warnings,
            "ignored_warnings": self.ignored_warnings,
            "trust_gains": self.trust_gains,
            "trust_losses": self.trust_losses
        }


class PerformanceTracker:
    """性能追蹤器 - 追蹤騙徒和專家的表現"""
    
    def __init__(self):
        self.scammer_perf = ScammerPerformance()
        self.expert_perf = ExpertPerformance()
        self.key_moments = []
        self.turn_count = 0
    
    def record_scammer_turn(self, turn_analysis: Dict):
        """記錄騙徒單輪表現"""
        self.scammer_perf.record_turn(turn_analysis)
        self.turn_count += 1
    
    def record_expert_turn(self, turn_analysis: Dict):
        """記錄專家單輪表現"""
        self.expert_perf.record_turn(turn_analysis)
    
    def identify_key_moment(self, moment_type: str, description: str, 
                           victim_trust_state: Dict, turn: int):
        """識別關鍵時刻"""
        self.key_moments.append({
            "turn": turn,
            "type": moment_type,
            "description": description,
            "victim_trust_state": victim_trust_state,
            "timestamp": datetime.now().isoformat()
        })
        
        log.info(f"🔑 關鍵時刻 (第{turn}輪): {moment_type} - {description}")
    
    def get_current_performance(self) -> Dict:
        """獲取當前性能狀態"""
        return {
            "turn": self.turn_count,
            "scammer_performance": self.scammer_perf.to_dict(),
            "expert_performance": self.expert_perf.to_dict(),
            "key_moments_count": len(self.key_moments)
        }
    
    def generate_report(self) -> Dict:
        """生成性能報告"""
        scammer_score = self.scammer_perf.calculate_overall_score()
        expert_score = self.expert_perf.calculate_overall_score()
        
        return {
            "total_turns": self.turn_count,
            "scammer_performance": self.scammer_perf.to_dict(),
            "scammer_overall_score": scammer_score,
            "expert_performance": self.expert_perf.to_dict(),
            "expert_overall_score": expert_score,
            "key_moments": self.key_moments,
            "scammer_history": self.scammer_perf.history,
            "expert_history": self.expert_perf.history
        }

