"""
三方表现追踪系统
实时追踪骗徒、受害者、专家的表现和互动效果
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import log


@dataclass
class VictimTrustState:
    """受害者信任状态"""
    trust_in_scammer: int = 50  # 对骗徒的信任度 (0-100)
    trust_in_expert: int = 50   # 对专家的信任度 (0-100)
    alertness: int = 50         # 警觉程度 (0-100)
    emotional_state: str = "neutral"  # calm/anxious/panicked/suspicious
    history: List[Dict] = field(default_factory=list)
    
    def update(self, change_type: str, change_value: int, reason: str):
        """更新信任度"""
        if change_type == "scammer":
            old_value = self.trust_in_scammer
            self.trust_in_scammer = max(0, min(100, self.trust_in_scammer + change_value))
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "scammer_trust",
                "old_value": old_value,
                "new_value": self.trust_in_scammer,
                "change": change_value,
                "reason": reason
            })
        elif change_type == "expert":
            old_value = self.trust_in_expert
            self.trust_in_expert = max(0, min(100, self.trust_in_expert + change_value))
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "expert_trust",
                "old_value": old_value,
                "new_value": self.trust_in_expert,
                "change": change_value,
                "reason": reason
            })
        elif change_type == "alertness":
            old_value = self.alertness
            self.alertness = max(0, min(100, self.alertness + change_value))
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "alertness",
                "old_value": old_value,
                "new_value": self.alertness,
                "change": change_value,
                "reason": reason
            })
    
    def get_dominant_trust(self) -> str:
        """返回主导的信任对象"""
        if self.trust_in_scammer > self.trust_in_expert + 20:
            return "scammer"
        elif self.trust_in_expert > self.trust_in_scammer + 20:
            return "expert"
        else:
            return "conflicted"
    
    def to_dict(self) -> Dict:
        return {
            "trust_in_scammer": self.trust_in_scammer,
            "trust_in_expert": self.trust_in_expert,
            "alertness": self.alertness,
            "emotional_state": self.emotional_state,
            "dominant_trust": self.get_dominant_trust()
        }


@dataclass
class ScammerPerformance:
    """骗徒表现评分"""
    persuasiveness: int = 50        # 说服力 (0-100)
    credibility: int = 50           # 可信度 (0-100)
    pressure_effectiveness: int = 50  # 施压有效性 (0-100)
    role_consistency: int = 100     # 角色一致性 (0-100)
    strategy_score: int = 50        # 策略得分 (0-100)
    
    successful_manipulations: int = 0  # 成功的操控次数
    exposed_lies: int = 0              # 被揭穿的谎言次数
    trust_gains: int = 0               # 获得的信任增加次数
    trust_losses: int = 0              # 失去的信任次数
    
    history: List[Dict] = field(default_factory=list)
    
    def record_turn(self, turn_analysis: Dict):
        """记录单轮表现"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            **turn_analysis
        })
        
        # 更新统计
        if turn_analysis.get("trust_change", 0) > 0:
            self.trust_gains += 1
        elif turn_analysis.get("trust_change", 0) < 0:
            self.trust_losses += 1
        
        if turn_analysis.get("exposed", False):
            self.exposed_lies += 1
        
        if turn_analysis.get("manipulation_success", False):
            self.successful_manipulations += 1
    
    def calculate_overall_score(self) -> int:
        """计算总体得分"""
        base_score = (
            self.persuasiveness * 0.3 +
            self.credibility * 0.2 +
            self.pressure_effectiveness * 0.2 +
            self.role_consistency * 0.15 +
            self.strategy_score * 0.15
        )
        
        # 根据成功/失败调整
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
    """专家表现评分"""
    intervention_effectiveness: int = 50  # 干预有效性 (0-100)
    clarity: int = 50                     # 清晰度 (0-100)
    empathy: int = 50                     # 同理心 (0-100)
    actionability: int = 50               # 建议可执行性 (0-100)
    timing: int = 50                      # 时机把握 (0-100)
    
    successful_warnings: int = 0      # 成功的警告次数
    ignored_warnings: int = 0         # 被忽视的警告次数
    trust_gains: int = 0              # 获得的信任增加次数
    trust_losses: int = 0             # 失去的信任次数
    
    history: List[Dict] = field(default_factory=list)
    
    def record_turn(self, turn_analysis: Dict):
        """记录单轮表现"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            **turn_analysis
        })
        
        # 更新统计
        if turn_analysis.get("trust_change", 0) > 0:
            self.trust_gains += 1
        elif turn_analysis.get("trust_change", 0) < 0:
            self.trust_losses += 1
        
        if turn_analysis.get("warning_effective", False):
            self.successful_warnings += 1
        elif turn_analysis.get("warning_ignored", False):
            self.ignored_warnings += 1
    
    def calculate_overall_score(self) -> int:
        """计算总体得分"""
        base_score = (
            self.intervention_effectiveness * 0.3 +
            self.clarity * 0.2 +
            self.empathy * 0.2 +
            self.actionability * 0.15 +
            self.timing * 0.15
        )
        
        # 根据成功/失败调整
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
    """三方表现追踪器"""
    
    def __init__(self, victim_persona: str = "elderly"):
        self.victim_persona = victim_persona
        self.victim_trust = VictimTrustState()
        self.scammer_perf = ScammerPerformance()
        self.expert_perf = ExpertPerformance()
        
        self.turn_count = 0
        self.key_moments = []
        
        # ⚠️ 新增：追踪最近使用的策略（用于策略疲劳效应）
        self.recent_scammer_tactics = []  # 最近3轮的策略
        self.recent_expert_approaches = []  # 最近3轮的专家方法
        
        # 根据persona设置初始信任度
        if victim_persona == "elderly":
            self.victim_trust.trust_in_scammer = 70  # 长者更容易信任权威
            self.victim_trust.trust_in_expert = 50
            self.victim_trust.alertness = 30
        elif victim_persona == "average":
            self.victim_trust.trust_in_scammer = 50
            self.victim_trust.trust_in_expert = 60
            self.victim_trust.alertness = 50
        elif victim_persona == "overconfident":
            self.victim_trust.trust_in_scammer = 30  # 过度自信者不容易相信
            self.victim_trust.trust_in_expert = 40   # 也不太信专家
            self.victim_trust.alertness = 70
    
    def _get_max_trust_change_per_turn(self) -> int:
        """根据victim.py获取每轮最大信任度变化"""
        if self.victim_persona == "elderly":
            return 12  # victim.py: 每轮最多改变 ±12 分
        elif self.victim_persona == "average":
            return 15  # victim.py: 每轮最多改变 ±15 分
        elif self.victim_persona == "overconfident":
            return 20  # overconfident 变化更激进
        else:
            return 15  # 默认值
    
    def _calculate_inertia_multiplier(self, current_trust: int, change: int) -> float:
        """
        计算心理惯性乘数（认知失调理论）
        信任度很高/很低时，改变更困难
        
        Args:
            current_trust: 当前信任度
            change: 即将发生的变化
        
        Returns:
            乘数 (0.5-1.0)
        """
        if change > 0:
            # 正向变化：信任度越高，增加越难
            if current_trust >= 80:
                return 0.6  # 高信任度，增加困难（-40%）
            elif current_trust >= 60:
                return 0.8  # 中高信任度，稍微困难（-20%）
        else:
            # 负向变化：信任度越高，降低越难（更容易找借口）
            if current_trust >= 80:
                return 0.5  # 高信任度，降低很困难（-50%）
            elif current_trust >= 60:
                return 0.7  # 中高信任度，降低较困难（-30%）
            # 低信任度时降低更容易（默认1.0）
        
        return 1.0  # 默认不调整
    
    def _calculate_fatigue_multiplier(self, tactics: List[str], recent_tactics: List[List[str]]) -> float:
        """
        计算策略疲劳乘数
        重复使用同一策略，效果递减
        
        Args:
            tactics: 本轮使用的策略
            recent_tactics: 最近3轮的策略列表
        
        Returns:
            乘数 (0.5-1.0)
        """
        if not tactics or not recent_tactics:
            return 1.0
        
        # 检查每个策略在最近几轮中使用的次数
        fatigue_penalties = []
        for tactic in tactics:
            count = sum(1 for recent in recent_tactics if tactic in recent)
            if count >= 3:
                fatigue_penalties.append(0.5)  # 连续3轮以上，效果减半
            elif count >= 2:
                fatigue_penalties.append(0.7)  # 连续2轮，效果-30%
            elif count >= 1:
                fatigue_penalties.append(0.9)  # 上一轮用过，效果-10%
        
        if fatigue_penalties:
            return min(fatigue_penalties)  # 取最严重的惩罚
        return 1.0
    
    def _calculate_emotional_multiplier(self, change: int, is_scammer: bool) -> float:
        """
        计算情绪状态乘数
        不同情绪状态对信任度变化的影响
        
        Args:
            change: 即将发生的变化
            is_scammer: True=骗徒的影响, False=专家的影响
        
        Returns:
            乘数 (0.5-1.5)
        """
        emotional_state = self.victim_trust.emotional_state
        
        if emotional_state == "anxious":
            # 焦虑状态：更容易被骗徒影响，专家影响减弱
            return 1.3 if is_scammer and change > 0 else 0.8
        elif emotional_state == "calm":
            # 冷静状态：骗徒影响减弱，专家影响增强
            return 0.8 if is_scammer and change > 0 else 1.2
        elif emotional_state == "suspicious":
            # 怀疑状态：骗徒影响大幅减弱，专家影响增强
            return 0.5 if is_scammer and change > 0 else 1.3
        elif emotional_state == "panicked":
            # 恐慌状态：极易被骗徒操控
            return 1.5 if is_scammer and change > 0 else 0.7
        
        return 1.0  # 中性状态
    
    def _calculate_persona_multiplier(self, tactic: str) -> float:
        """
        根据persona调整不同策略的效果
        
        Args:
            tactic: 策略类型
        
        Returns:
            乘数 (0.5-1.5)
        """
        if self.victim_persona == "elderly":
            # 长者：对权威和福利特别敏感
            if tactic == "authority":
                return 1.5
            elif tactic == "benefits":
                return 1.3
            elif tactic == "urgency":
                return 1.2
        elif self.victim_persona == "average":
            # 普通人：对专业包装和证据敏感
            if tactic == "authority":
                return 1.1
            elif tactic == "evidence":
                return 1.3
            elif tactic == "urgency":
                return 1.0
        elif self.victim_persona == "overconfident":
            # 过度自信：对激将法敏感，对权威不敏感
            if tactic == "authority":
                return 0.5
            elif tactic == "challenge":
                return 1.5
            elif tactic == "urgency":
                return 0.8
        
        return 1.0  # 默认
    
    def _calculate_combination_bonus(self, tactics: List[str]) -> int:
        """
        计算组合策略加成
        多个策略同时使用有协同效果
        
        Args:
            tactics: 本轮使用的策略列表
        
        Returns:
            额外加成分数
        """
        bonus = 0
        
        # 权威+紧急：经典组合
        if "authority" in tactics and "urgency" in tactics:
            bonus += 3
            log.info("🎯 组合策略：权威+紧急 (+3)")
        
        # 权威+福利：吸引力组合
        if "authority" in tactics and "benefits" in tactics:
            bonus += 2
            log.info("🎯 组合策略：权威+福利 (+2)")
        
        # 紧急+福利：FOMO组合
        if "urgency" in tactics and "benefits" in tactics:
            bonus += 2
            log.info("🎯 组合策略：紧急+福利 (+2)")
        
        # 三重组合：超级有效
        if len(tactics) >= 3:
            bonus += 3
            log.info("🎯 三重组合策略 (+3)")
        
        return bonus
    
    def analyze_scammer_turn(self, dialogue: str, victim_response: str) -> Dict:
        """分析骗徒单轮表现（使用改进的信任度机制）"""
        analysis = {
            "turn": self.turn_count,
            "dialogue": dialogue[:100],
            "trust_change": 0,
            "manipulation_success": False,
            "exposed": False,
            "tactics_used": []
        }
        
        # 检测使用的策略（根据victim.py的数值）
        base_changes = {}  # 记录每个策略的基础变化
        
        if any(word in dialogue for word in ["銀行", "政府", "警察", "警方", "官方"]):
            analysis["tactics_used"].append("authority")
            base_changes["authority"] = 5  # victim.py: +5
            self.scammer_perf.credibility = min(100, self.scammer_perf.credibility + 5)
        
        if any(word in dialogue for word in ["立即", "馬上", "緊急", "嚴重"]):
            analysis["tactics_used"].append("urgency")
            base_changes["urgency"] = 5  # victim.py: +5
            self.scammer_perf.pressure_effectiveness = min(100, self.scammer_perf.pressure_effectiveness + 5)
        
        if any(word in dialogue for word in ["補貼", "福利", "回贈", "優惠", "著數"]):
            analysis["tactics_used"].append("benefits")
            base_changes["benefits"] = 8  # victim.py: +8
            self.scammer_perf.persuasiveness = min(100, self.scammer_perf.persuasiveness + 5)
        
        # 计算基础信任度变化
        for tactic, base_value in base_changes.items():
            # ⚠️ 应用persona乘数
            persona_mult = self._calculate_persona_multiplier(tactic)
            adjusted_value = base_value * persona_mult
            analysis["trust_change"] += adjusted_value
            
            if persona_mult != 1.0:
                log.info(f"📊 {tactic}策略persona调整: {base_value} x {persona_mult:.2f} = {adjusted_value:.1f}")
        
        # ⚠️ 添加组合策略加成
        if len(analysis["tactics_used"]) >= 2:
            combo_bonus = self._calculate_combination_bonus(analysis["tactics_used"])
            analysis["trust_change"] += combo_bonus
            analysis["combo_bonus"] = combo_bonus
        
        # ⚠️ 应用策略疲劳惩罚
        fatigue_mult = self._calculate_fatigue_multiplier(
            analysis["tactics_used"], 
            self.recent_scammer_tactics
        )
        if fatigue_mult < 1.0:
            log.info(f"📊 策略疲劳: 效果 x {fatigue_mult:.2f}")
            analysis["trust_change"] *= fatigue_mult
            analysis["fatigue_multiplier"] = fatigue_mult
        
        # ⚠️ 应用情绪状态乘数
        emotional_mult = self._calculate_emotional_multiplier(
            analysis["trust_change"], 
            is_scammer=True
        )
        if emotional_mult != 1.0:
            log.info(f"📊 情绪状态({self.victim_trust.emotional_state}): 效果 x {emotional_mult:.2f}")
            analysis["trust_change"] *= emotional_mult
            analysis["emotional_multiplier"] = emotional_mult
        
        # ⚠️ 应用心理惯性乘数
        if analysis["trust_change"] != 0:
            inertia_mult = self._calculate_inertia_multiplier(
                self.victim_trust.trust_in_scammer,
                analysis["trust_change"]
            )
            if inertia_mult != 1.0:
                log.info(f"📊 心理惯性(当前信任{self.victim_trust.trust_in_scammer}): 效果 x {inertia_mult:.2f}")
                analysis["trust_change"] *= inertia_mult
                analysis["inertia_multiplier"] = inertia_mult
        
        # 四舍五入
        analysis["trust_change"] = round(analysis["trust_change"])
        
        # 检测受害者的回应
        if any(word in victim_response for word in ["好啊", "我會", "咁我", "多謝", "幫我"]):
            analysis["manipulation_success"] = True
            self.scammer_perf.persuasiveness = min(100, self.scammer_perf.persuasiveness + 3)
        
        if any(word in victim_response for word in ["唔信", "奇怪", "點解", "有問題"]):
            analysis["exposed"] = True
            self.scammer_perf.credibility = max(0, self.scammer_perf.credibility - 10)
            # victim.py: 对方回应模糊或避重就轻：-8
            analysis["trust_change"] = -8
        
        # ⚠️ 应用每轮最大变化限制（根据victim.py）
        max_change_per_turn = self._get_max_trust_change_per_turn()
        if analysis["trust_change"] > max_change_per_turn:
            log.info(f"📊 信任度变化被限制: {analysis['trust_change']} -> {max_change_per_turn}")
            analysis["trust_change"] = max_change_per_turn
        elif analysis["trust_change"] < -max_change_per_turn:
            log.info(f"📊 信任度变化被限制: {analysis['trust_change']} -> {-max_change_per_turn}")
            analysis["trust_change"] = -max_change_per_turn
        
        # 记录策略到历史（保留最近3轮）
        self.recent_scammer_tactics.append(analysis["tactics_used"])
        if len(self.recent_scammer_tactics) > 3:
            self.recent_scammer_tactics.pop(0)
        
        # 更新受害者信任度
        if analysis["trust_change"] != 0:
            self.victim_trust.update("scammer", analysis["trust_change"], 
                                    f"骗徒使用策略: {', '.join(analysis['tactics_used'])}")
        
        # 记录表现
        self.scammer_perf.record_turn(analysis)
        
        # 將累積評分添加到返回字典中（便於日誌和調試）
        analysis["persuasiveness"] = self.scammer_perf.persuasiveness
        analysis["credibility"] = self.scammer_perf.credibility
        analysis["pressure_effectiveness"] = self.scammer_perf.pressure_effectiveness
        analysis["role_consistency"] = self.scammer_perf.role_consistency
        analysis["strategy_score"] = self.scammer_perf.strategy_score
        
        return analysis
    
    def analyze_expert_turn(self, expert_advice: str, victim_response: str, scammer_message: str = "") -> Dict:
        """分析专家单轮表现
        
        Args:
            expert_advice: 专家的建议/对话
            victim_response: 受害者的回应
            scammer_message: 骗徒的消息（可选，用于分析专家是否针对性地回应）
        """
        analysis = {
            "turn": self.turn_count,
            "dialogue": expert_advice[:100],
            "trust_change": 0,
            "warning_effective": False,
            "warning_ignored": False,
            "approach": []
        }
        
        # 检测专家的方法（根据victim.py的设定）
        base_changes = {}  # 记录每个方法的基础变化
        
        has_empathy = any(word in expert_advice for word in ["唔好驚", "冷靜", "理解", "明白你"])
        has_evidence = any(word in expert_advice for word in ["銀行唔會", "騙案手法", "真正嘅", "官方"])
        has_action = any(word in expert_advice for word in ["打去", "聯絡", "報警", "掛斷"])
        
        # 如果提供了scammer_message，可以分析专家是否针对性地回应
        if scammer_message:
            # 检测专家是否直接回应了骗徒的威胁/压力
            if any(word in expert_advice for word in ["騙", "詐", "假", "唔信", "唔好"]):
                analysis["approach"].append("direct_counter")
                base_changes["direct_counter"] = 5
        
        if has_empathy:
            analysis["approach"].append("empathy")
            base_changes["empathy"] = 8  # victim.py: +8
            self.expert_perf.empathy = min(100, self.expert_perf.empathy + 5)
        else:
            # victim.py: 专家冷静分析但无安抚情绪：-3
            analysis["trust_change"] -= 3
        
        if has_evidence:
            analysis["approach"].append("evidence")
            base_changes["evidence"] = 10  # victim.py: +10
            self.expert_perf.clarity = min(100, self.expert_perf.clarity + 5)
        
        if has_action:
            analysis["approach"].append("actionable")
            base_changes["actionable"] = 8
            self.expert_perf.actionability = min(100, self.expert_perf.actionability + 5)
        
        # 计算基础信任度变化
        for approach, base_value in base_changes.items():
            # ⚠️ 应用persona乘数
            persona_mult = self._calculate_persona_multiplier(approach)
            adjusted_value = base_value * persona_mult
            analysis["trust_change"] += adjusted_value
            
            if persona_mult != 1.0:
                log.info(f"📊 {approach}方法persona调整: {base_value} x {persona_mult:.2f} = {adjusted_value:.1f}")
        
        # ⚠️ 应用策略疲劳惩罚
        fatigue_mult = self._calculate_fatigue_multiplier(
            analysis["approach"], 
            self.recent_expert_approaches
        )
        if fatigue_mult < 1.0:
            log.info(f"📊 专家方法疲劳: 效果 x {fatigue_mult:.2f}")
            analysis["trust_change"] *= fatigue_mult
            analysis["fatigue_multiplier"] = fatigue_mult
        
        # ⚠️ 应用情绪状态乘数
        emotional_mult = self._calculate_emotional_multiplier(
            analysis["trust_change"], 
            is_scammer=False
        )
        if emotional_mult != 1.0:
            log.info(f"📊 专家-情绪状态({self.victim_trust.emotional_state}): 效果 x {emotional_mult:.2f}")
            analysis["trust_change"] *= emotional_mult
            analysis["emotional_multiplier"] = emotional_mult
        
        # ⚠️ 应用心理惯性乘数
        if analysis["trust_change"] != 0:
            inertia_mult = self._calculate_inertia_multiplier(
                self.victim_trust.trust_in_expert,
                analysis["trust_change"]
            )
            if inertia_mult != 1.0:
                log.info(f"📊 专家-心理惯性(当前信任{self.victim_trust.trust_in_expert}): 效果 x {inertia_mult:.2f}")
                analysis["trust_change"] *= inertia_mult
                analysis["inertia_multiplier"] = inertia_mult
        
        # 四舍五入
        analysis["trust_change"] = round(analysis["trust_change"])
        
        # 检测受害者的回应
        if any(word in victim_response for word in ["你講得啱", "我明白", "我而家就", "好嘅"]):
            analysis["warning_effective"] = True
            self.expert_perf.intervention_effectiveness = min(100, self.expert_perf.intervention_effectiveness + 5)
            # 降低对骗徒的信任（应用限制）
            scammer_trust_change = -min(12, self._get_max_trust_change_per_turn())
            self.victim_trust.update("scammer", scammer_trust_change, "专家成功警告")
        elif any(word in victim_response for word in ["但係", "唔係", "我覺得"]):
            analysis["warning_ignored"] = True
            self.expert_perf.intervention_effectiveness = max(0, self.expert_perf.intervention_effectiveness - 3)
        
        # ⚠️ 应用每轮最大变化限制（根据victim.py）
        max_change_per_turn = self._get_max_trust_change_per_turn()
        if analysis["trust_change"] > max_change_per_turn:
            log.info(f"📊 专家信任度变化被限制: {analysis['trust_change']} -> {max_change_per_turn}")
            analysis["trust_change"] = max_change_per_turn
        elif analysis["trust_change"] < -max_change_per_turn:
            log.info(f"📊 专家信任度变化被限制: {analysis['trust_change']} -> {-max_change_per_turn}")
            analysis["trust_change"] = -max_change_per_turn
        
        # 记录策略到历史（保留最近3轮）
        self.recent_expert_approaches.append(analysis["approach"])
        if len(self.recent_expert_approaches) > 3:
            self.recent_expert_approaches.pop(0)
        
        # 更新受害者对专家的信任度
        if analysis["trust_change"] != 0:
            self.victim_trust.update("expert", analysis["trust_change"],
                                    f"专家使用方法: {', '.join(analysis['approach'])}")
        
        # 记录表现
        self.expert_perf.record_turn(analysis)
        
        # 將累積評分添加到返回字典中（便於日誌和調試）
        analysis["intervention_effectiveness"] = self.expert_perf.intervention_effectiveness
        analysis["clarity"] = self.expert_perf.clarity
        analysis["empathy"] = self.expert_perf.empathy
        analysis["actionability"] = self.expert_perf.actionability
        analysis["timing"] = self.expert_perf.timing
        
        return analysis
    
    def analyze_victim_response(self, victim_response: str, previous_scammer_message: str, previous_expert_message: str = "") -> Dict:
        """分析受害者回应，更新信任度和情绪状态"""
        analysis = {
            "turn": self.turn_count,
            "victim_response": victim_response[:100],
            "trust_changes": {},
            "alertness_change": 0,
            "emotional_shift": None
        }
        
        # 分析受害者对骗徒的态度
        if any(word in victim_response for word in ["好的", "明白", "我會", "我即刻", "係咪", "真係"]):
            # 显示出相信骗徒
            analysis["trust_changes"]["scammer"] = +5
            self.victim_trust.update("scammer", +5, "受害者表现出配合态度")
            analysis["alertness_change"] = -5
            self.victim_trust.update("alertness", -5, "警觉性降低")
            
        if any(word in victim_response for word in ["點解", "但係", "唔係", "等等", "我唔明"]):
            # 显示出怀疑
            analysis["trust_changes"]["scammer"] = -10
            self.victim_trust.update("scammer", -10, "受害者表现出怀疑")
            analysis["alertness_change"] = +10
            self.victim_trust.update("alertness", +10, "警觉性提高")
        
        # 分析受害者对专家的态度（如果有专家消息）
        if previous_expert_message:
            if any(word in victim_response for word in ["你講得啱", "多謝", "我明白", "好建議"]):
                # 受害者接受专家建议
                analysis["trust_changes"]["expert"] = +15
                self.victim_trust.update("expert", +15, "受害者接受专家建议")
                analysis["alertness_change"] = +10
                self.victim_trust.update("alertness", +10, "警觉性提高")
            elif any(word in victim_response for word in ["但係佢話", "我覺得", "應該冇問題"]):
                # 受害者忽视专家建议
                analysis["trust_changes"]["expert"] = -5
                self.victim_trust.update("expert", -5, "受害者忽视专家建议")
        
        # 分析情绪状态
        old_emotional_state = self.victim_trust.emotional_state
        
        if any(word in victim_response for word in ["驚", "擔心", "點算", "嚴重", "危險"]):
            self.victim_trust.emotional_state = "anxious"
            analysis["emotional_shift"] = "neutral -> anxious" if old_emotional_state == "neutral" else f"{old_emotional_state} -> anxious"
        
        if any(word in victim_response for word in ["冷靜", "慢慢嚟", "等等", "唔急"]):
            self.victim_trust.emotional_state = "calm"
            analysis["emotional_shift"] = f"{old_emotional_state} -> calm"
        
        if any(word in victim_response for word in ["騙人", "唔信", "呃人", "假嘅"]):
            self.victim_trust.emotional_state = "suspicious"
            analysis["emotional_shift"] = f"{old_emotional_state} -> suspicious"
        
        log.info(f"📊 受害者分析: 信任变化={analysis['trust_changes']}, 情绪={self.victim_trust.emotional_state}")
        
        return analysis
    
    def identify_key_moment(self, moment_type: str, description: str, turn: int):
        """识别关键时刻"""
        self.key_moments.append({
            "turn": turn,
            "type": moment_type,
            "description": description,
            "victim_trust_state": self.victim_trust.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
        
        log.info(f"🔑 关键时刻 (第{turn}轮): {moment_type} - {description}")
    
    def get_current_state(self) -> Dict:
        """获取当前状态（扁平化结构，便于直接访问）"""
        victim_trust_dict = self.victim_trust.to_dict()
        return {
            "turn": self.turn_count,
            # 扁平化信任度字段，便于直接访问
            "trust_in_scammer": victim_trust_dict["trust_in_scammer"],
            "trust_in_expert": victim_trust_dict["trust_in_expert"],
            "alertness": victim_trust_dict["alertness"],
            "emotional_state": victim_trust_dict["emotional_state"],
            "dominant_trust": victim_trust_dict["dominant_trust"],
            # 保留嵌套结构以便需要时访问完整对象
            "victim_trust": victim_trust_dict,
            "scammer_performance": self.scammer_perf.to_dict(),
            "expert_performance": self.expert_perf.to_dict(),
            "key_moments_count": len(self.key_moments)
        }
    
    def generate_final_report(self) -> Dict:
        """生成最终报告"""
        # 判定结果
        final_trust_in_scammer = self.victim_trust.trust_in_scammer
        final_trust_in_expert = self.victim_trust.trust_in_expert
        
        if final_trust_in_scammer >= 70:
            outcome = "SUCCESS"  # 骗徒成功
            winner = "scammer"
        elif final_trust_in_expert >= 70:
            outcome = "FAILURE"  # 骗徒失败
            winner = "expert"
        elif self.victim_trust.alertness >= 70:
            outcome = "PARTIAL"  # 受害者警觉但未完全相信任何一方
            winner = "victim"
        else:
            outcome = "UNCERTAIN"
            winner = "none"
        
        return {
            "outcome": outcome,
            "winner": winner,
            "total_turns": self.turn_count,
            "victim_trust_final": self.victim_trust.to_dict(),
            "victim_trust_history": self.victim_trust.history,
            "scammer_performance": self.scammer_perf.to_dict(),
            "scammer_overall_score": self.scammer_perf.calculate_overall_score(),
            "expert_performance": self.expert_perf.to_dict(),
            "expert_overall_score": self.expert_perf.calculate_overall_score(),
            "key_moments": self.key_moments,
            "summary": self._generate_summary(outcome, winner)
        }
    
    def _generate_summary(self, outcome: str, winner: str) -> str:
        """生成摘要"""
        scammer_score = self.scammer_perf.calculate_overall_score()
        expert_score = self.expert_perf.calculate_overall_score()
        
        summary = f"对话共{self.turn_count}轮。"
        
        if outcome == "SUCCESS":
            summary += f"骗徒成功建立信任（最终信任度: {self.victim_trust.trust_in_scammer}/100）。"
            summary += f"骗徒表现评分: {scammer_score}/100。"
        elif outcome == "FAILURE":
            summary += f"专家成功阻止诈骗（专家信任度: {self.victim_trust.trust_in_expert}/100）。"
            summary += f"专家表现评分: {expert_score}/100。"
        elif outcome == "PARTIAL":
            summary += f"受害者保持警觉但未完全相信任何一方。"
        else:
            summary += f"结果不确定，双方未能完全说服受害者。"
        
        return summary

