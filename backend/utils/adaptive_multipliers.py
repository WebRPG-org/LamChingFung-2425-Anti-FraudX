"""
動態乘數引擎 - 計算策略效果的動態調整
整合舊版 performance_tracker.py 的 5 種乘數系統
"""

from typing import List, Dict, Optional
from utils.logger import log


class AdaptiveMultiplierEngine:
    """動態乘數引擎 - 根據多個因素調整策略效果"""
    
    def __init__(self, victim_persona: str = "average"):
        self.victim_persona = victim_persona
        self.recent_scammer_tactics = []  # 最近3輪的騙徒策略
        self.recent_expert_approaches = []  # 最近3輪的專家方法
    
    # ============================================================================
    # 1. Persona 乘數 - 根據受害者類型調整策略效果
    # ============================================================================
    
    def calculate_persona_multiplier(self, tactic: str) -> float:
        """
        根據 persona 調整不同策略的效果
        
        Args:
            tactic: 策略類型
        
        Returns:
            乘數 (0.5-1.5)
        """
        if self.victim_persona == "elderly":
            # 長者：對權威和福利特別敏感
            if tactic == "authority":
                return 1.5
            elif tactic == "benefits":
                return 1.3
            elif tactic == "urgency":
                return 1.2
            elif tactic == "challenge":
                return 0.6  # 對激將法不敏感
        
        elif self.victim_persona == "average":
            # 普通人：對專業包裝和證據敏感
            if tactic == "authority":
                return 1.1
            elif tactic == "evidence":
                return 1.3
            elif tactic == "urgency":
                return 1.0
        
        elif self.victim_persona == "overconfident":
            # 過度自信：對激將法敏感，對權威不敏感
            if tactic == "authority":
                return 0.5
            elif tactic == "challenge":
                return 1.5
            elif tactic == "urgency":
                return 0.8
        
        return 1.0  # 默認
    
    # ============================================================================
    # 2. 策略疲勞乘數 - 重複使用同一策略，效果遞減
    # ============================================================================
    
    def calculate_fatigue_multiplier(self, tactics: List[str], recent_tactics: List[List[str]]) -> float:
        """
        計算策略疲勞乘數
        重複使用同一策略，效果遞減
        
        Args:
            tactics: 本輪使用的策略
            recent_tactics: 最近3輪的策略列表
        
        Returns:
            乘數 (0.5-1.0)
        """
        if not tactics or not recent_tactics:
            return 1.0
        
        # 檢查每個策略在最近幾輪中使用的次數
        fatigue_penalties = []
        for tactic in tactics:
            count = sum(1 for recent in recent_tactics if tactic in recent)
            if count >= 3:
                fatigue_penalties.append(0.5)  # 使用3次以上：效果減半
            elif count >= 2:
                fatigue_penalties.append(0.7)  # 使用2次：效果減30%
            elif count >= 1:
                fatigue_penalties.append(0.85)  # 使用1次：效果減15%
        
        if fatigue_penalties:
            return min(fatigue_penalties)  # 取最嚴重的懲罰
        return 1.0
    
    # ============================================================================
    # 3. 情緒狀態乘數 - 不同情緒對信任度變化的影響
    # ============================================================================
    
    def calculate_emotional_multiplier(self, emotional_state: str, change: int, is_scammer: bool) -> float:
        """
        計算情緒狀態乘數
        不同情緒狀態對信任度變化的影響
        
        Args:
            emotional_state: 當前情緒狀態
            change: 即將發生的變化
            is_scammer: True=騙徒的影響, False=專家的影響
        
        Returns:
            乘數 (0.5-1.5)
        """
        if emotional_state == "anxious":
            # 焦慮狀態：容易被騙徒的恐慌策略影響，但也容易被專家安撫
            return 1.3 if (is_scammer and change > 0) else 1.2
        
        elif emotional_state == "calm":
            # 冷靜狀態：對騙徒的恐慌策略有抵抗力，但對專家的建議也不太敏感
            return 0.6 if (is_scammer and change > 0) else 0.8
        
        elif emotional_state == "suspicious":
            # 懷疑狀態：對騙徒的策略有強烈抵抗，對專家的建議很敏感
            return 0.4 if (is_scammer and change > 0) else 1.4
        
        elif emotional_state == "panicked":
            # 恐慌狀態：容易被騙徒利用，但也容易被專家的冷靜建議影響
            return 1.5 if (is_scammer and change > 0) else 1.1
        
        return 1.0  # 中性狀態
    
    # ============================================================================
    # 4. 心理慣性乘數 - 認知失調理論
    # ============================================================================
    
    def calculate_inertia_multiplier(self, current_trust: int, change: int) -> float:
        """
        計算心理慣性乘數（認知失調理論）
        信任度很高/很低時，改變更困難
        
        Args:
            current_trust: 當前信任度
            change: 即將發生的變化
        
        Returns:
            乘數 (0.5-1.0)
        """
        if change > 0:
            # 正向變化：信任度越高，增加越難
            if current_trust >= 80:
                return 0.6  # 信任度已很高，難以進一步增加
            elif current_trust >= 60:
                return 0.8  # 信任度中等偏高，增加有難度
        else:
            # 負向變化：信任度越高，降低越難（更容易找借口）
            if current_trust >= 80:
                return 0.5  # 信任度很高，難以降低
            elif current_trust >= 60:
                return 0.7  # 信任度中等偏高，降低有難度
        
        return 1.0  # 默認不調整
    
    # ============================================================================
    # 5. 組合策略加成 - 多個策略同時使用有協同效果
    # ============================================================================
    
    def calculate_combination_bonus(self, tactics: List[str]) -> int:
        """
        計算組合策略加成
        多個策略同時使用有協同效果
        
        Args:
            tactics: 本輪使用的策略列表
        
        Returns:
            額外加成分數
        """
        bonus = 0
        
        # 權威+緊急：經典組合
        if "authority" in tactics and "urgency" in tactics:
            bonus += 3
            log.info("🎯 組合策略：權威+緊急 (+3)")
        
        # 權威+福利：吸引力組合
        if "authority" in tactics and "benefits" in tactics:
            bonus += 2
            log.info("🎯 組合策略：權威+福利 (+2)")
        
        # 緊急+福利：FOMO 組合
        if "urgency" in tactics and "benefits" in tactics:
            bonus += 2
            log.info("🎯 組合策略：緊急+福利 (+2)")
        
        # 三重組合：超級有效
        if len(tactics) >= 3:
            bonus += 3
            log.info("🎯 三重組合策略 (+3)")
        
        return bonus
    
    # ============================================================================
    # 綜合計算方法
    # ============================================================================
    
    def apply_all_multipliers(self, base_score: int, tactics: List[str], 
                             emotional_state: str, current_trust: int, 
                             is_scammer: bool = True) -> Dict:
        """
        應用所有乘數，計算最終分數
        
        Args:
            base_score: 基礎分數
            tactics: 使用的策略列表
            emotional_state: 當前情緒狀態
            current_trust: 當前信任度
            is_scammer: 是否為騙徒
        
        Returns:
            包含所有乘數和最終分數的字典
        """
        result = {
            "base_score": base_score,
            "tactics": tactics,
            "multipliers": {},
            "final_score": base_score
        }
        
        # 應用 Persona 乘數
        if tactics:
            persona_mult = self.calculate_persona_multiplier(tactics[0])
            result["multipliers"]["persona"] = persona_mult
            result["final_score"] *= persona_mult
        
        # 應用策略疲勞乘數
        recent = self.recent_scammer_tactics if is_scammer else self.recent_expert_approaches
        fatigue_mult = self.calculate_fatigue_multiplier(tactics, recent)
        if fatigue_mult < 1.0:
            result["multipliers"]["fatigue"] = fatigue_mult
            result["final_score"] *= fatigue_mult
        
        # 應用情緒狀態乘數
        emotional_mult = self.calculate_emotional_multiplier(emotional_state, result["final_score"], is_scammer)
        if emotional_mult != 1.0:
            result["multipliers"]["emotional"] = emotional_mult
            result["final_score"] *= emotional_mult
        
        # 應用心理慣性乘數
        inertia_mult = self.calculate_inertia_multiplier(current_trust, result["final_score"])
        if inertia_mult != 1.0:
            result["multipliers"]["inertia"] = inertia_mult
            result["final_score"] *= inertia_mult
        
        # 應用組合策略加成
        combo_bonus = self.calculate_combination_bonus(tactics)
        if combo_bonus > 0:
            result["multipliers"]["combo_bonus"] = combo_bonus
            result["final_score"] += combo_bonus
        
        # 四舍五入
        result["final_score"] = round(result["final_score"])
        
        return result
    
    def record_tactics(self, tactics: List[str], is_scammer: bool = True):
        """記錄本輪使用的策略（用於疲勞計算）"""
        if is_scammer:
            self.recent_scammer_tactics.append(tactics)
            if len(self.recent_scammer_tactics) > 3:
                self.recent_scammer_tactics.pop(0)
        else:
            self.recent_expert_approaches.append(tactics)
            if len(self.recent_expert_approaches) > 3:
                self.recent_expert_approaches.pop(0)

