"""
自適應權重優化器
根據受害者persona動態調整評分權重，提升評分準確度
"""

from typing import Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeightConfig:
    """權重配置"""
    empathy: float
    clarity: float
    evidence: float
    actionability: float
    timing: float = 0.0  # 可選


class AdaptiveWeightOptimizer:
    """
    自適應權重優化器
    
    根據受害者persona動態調整專家和騙徒的評分權重
    提升評分準確度和針對性
    """
    
    # 專家評分權重配置（根據persona）
    EXPERT_WEIGHT_CONFIGS = {
        "elderly": WeightConfig(
            empathy=0.35,        # 長者最需要情緒安撫
            clarity=0.20,        # 需要簡單清晰的解釋
            evidence=0.20,       # 需要具體證據
            actionability=0.25,  # 需要明確的行動指引
            timing=0.0           # 時機由單獨計算
        ),
        "average": WeightConfig(
            empathy=0.20,        # 普通人需要適度同理心
            clarity=0.25,        # 需要清晰的邏輯
            evidence=0.35,       # 最看重證據
            actionability=0.20,  # 需要可執行的建議
            timing=0.0
        ),
        "overconfident": WeightConfig(
            empathy=0.10,        # 過度自信者不太需要安撫
            clarity=0.30,        # 需要清晰的邏輯
            evidence=0.40,       # 非常看重證據
            actionability=0.20,  # 需要具體建議
            timing=0.0
        ),
        "student": WeightConfig(
            empathy=0.25,        # 學生需要適度安撫
            clarity=0.30,        # 需要清晰解釋
            evidence=0.25,       # 需要證據
            actionability=0.20,  # 需要行動指引
            timing=0.0
        )
    }
    
    # 騙徒策略乘數配置（根據persona）
    SCAMMER_MULTIPLIER_CONFIGS = {
        "elderly": {
            "authority": 1.5,      # 長者對權威特別敏感
            "urgency": 1.3,        # 容易被緊急情況影響
            "benefits": 1.4,       # 對福利優惠敏感
            "fear": 1.5,           # 容易被恐嚇
            "empathy": 1.2,        # 情感操控有效
            "evidence": 1.0,       # 對證據不太敏感
            "challenge": 0.5       # 激將法無效
        },
        "average": {
            "authority": 1.1,      # 對權威有一定信任
            "urgency": 1.0,        # 正常反應
            "benefits": 1.2,       # 對優惠有興趣
            "fear": 1.1,           # 會被恐嚇影響
            "empathy": 1.0,        # 正常情感反應
            "evidence": 1.3,       # 看重證據
            "challenge": 0.8       # 激將法效果一般
        },
        "overconfident": {
            "authority": 0.5,      # 對權威不敏感
            "urgency": 0.8,        # 不容易被催促
            "benefits": 1.0,       # 對優惠興趣一般
            "fear": 0.6,           # 不容易被恐嚇
            "empathy": 0.7,        # 情感操控效果差
            "evidence": 1.4,       # 非常看重證據
            "challenge": 1.5       # 激將法非常有效
        },
        "student": {
            "authority": 1.2,      # 對權威有信任
            "urgency": 1.1,        # 容易被催促
            "benefits": 1.3,       # 對優惠很感興趣
            "fear": 1.0,           # 正常恐懼反應
            "empathy": 1.1,        # 情感操控有效
            "evidence": 1.1,       # 看重證據
            "challenge": 1.0       # 激將法效果一般
        }
    }
    
    def __init__(self):
        """初始化優化器"""
        logger.info("🎯 自適應權重優化器初始化")
    
    def get_expert_weights(self, persona: str) -> Dict[str, float]:
        """
        獲取專家評分權重
        
        Args:
            persona: 受害者類型 (elderly/average/overconfident/student)
            
        Returns:
            權重字典
        """
        if persona not in self.EXPERT_WEIGHT_CONFIGS:
            logger.warning(f"⚠️ 未知persona: {persona}，使用average配置")
            persona = "average"
        
        config = self.EXPERT_WEIGHT_CONFIGS[persona]
        weights = {
            "empathy": config.empathy,
            "clarity": config.clarity,
            "evidence": config.evidence,
            "actionability": config.actionability
        }
        
        logger.debug(f"📊 {persona}型專家權重: {weights}")
        return weights
    
    def get_scammer_multipliers(self, persona: str) -> Dict[str, float]:
        """
        獲取騙徒策略乘數
        
        Args:
            persona: 受害者類型
            
        Returns:
            策略乘數字典
        """
        if persona not in self.SCAMMER_MULTIPLIER_CONFIGS:
            logger.warning(f"⚠️ 未知persona: {persona}，使用average配置")
            persona = "average"
        
        multipliers = self.SCAMMER_MULTIPLIER_CONFIGS[persona]
        logger.debug(f"📊 {persona}型騙徒乘數: {multipliers}")
        return multipliers
    
    def calculate_weighted_expert_score(
        self, 
        base_scores: Dict[str, float], 
        persona: str
    ) -> float:
        """
        計算專家加權總分
        
        Args:
            base_scores: 基礎分數字典 {dimension: score (0-100)}
            persona: 受害者類型
            
        Returns:
            加權總分 (0-100)
        """
        weights = self.get_expert_weights(persona)
        
        # 計算加權分數（base_scores已經是0-100，直接加權平均）
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for dimension, weight in weights.items():
            if dimension in base_scores:
                weighted_sum += base_scores[dimension] * weight
                weight_sum += weight
        
        # 計算加權平均（不需要再乘100，因為base_scores已經是0-100）
        if weight_sum > 0:
            final_score = weighted_sum / weight_sum
        else:
            final_score = 0.0
        
        final_score = max(0.0, min(100.0, final_score))
        
        logger.debug(f"📊 專家加權分數: {final_score:.1f} (persona={persona})")
        return final_score
    
    def apply_scammer_multiplier(
        self, 
        base_change: float, 
        tactic: str, 
        persona: str
    ) -> float:
        """
        應用騙徒策略乘數
        
        Args:
            base_change: 基礎信任度變化
            tactic: 使用的策略
            persona: 受害者類型
            
        Returns:
            調整後的信任度變化
        """
        multipliers = self.get_scammer_multipliers(persona)
        
        # 獲取該策略的乘數
        multiplier = multipliers.get(tactic, 1.0)
        
        # 應用乘數
        adjusted_change = base_change * multiplier
        
        logger.debug(
            f"📊 策略乘數應用: {tactic} × {multiplier:.2f} = "
            f"{base_change:.1f} → {adjusted_change:.1f}"
        )
        
        return adjusted_change
    
    def get_optimal_expert_approach(self, persona: str) -> List[str]:
        """
        獲取針對特定persona的最佳專家策略
        
        Args:
            persona: 受害者類型
            
        Returns:
            推薦策略列表（按優先級排序）
        """
        weights = self.get_expert_weights(persona)
        
        # 按權重排序
        sorted_approaches = sorted(
            weights.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        recommendations = [approach for approach, _ in sorted_approaches]
        
        logger.info(f"💡 {persona}型最佳策略: {recommendations}")
        return recommendations
    
    def get_vulnerable_tactics(self, persona: str) -> List[tuple]:
        """
        獲取受害者最脆弱的騙徒策略
        
        Args:
            persona: 受害者類型
            
        Returns:
            [(策略, 乘數)] 列表，按脆弱程度排序
        """
        multipliers = self.get_scammer_multipliers(persona)
        
        # 按乘數排序（降序）
        sorted_tactics = sorted(
            multipliers.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 只返回乘數>1.0的（有效策略）
        vulnerable = [(tactic, mult) for tactic, mult in sorted_tactics if mult > 1.0]
        
        logger.info(f"⚠️ {persona}型脆弱策略: {vulnerable}")
        return vulnerable
    
    def analyze_persona_characteristics(self, persona: str) -> Dict[str, any]:
        """
        分析persona特徵
        
        Args:
            persona: 受害者類型
            
        Returns:
            特徵分析字典
        """
        expert_weights = self.get_expert_weights(persona)
        scammer_multipliers = self.get_scammer_multipliers(persona)
        
        # 找出最重要的專家策略
        top_expert_approach = max(expert_weights.items(), key=lambda x: x[1])
        
        # 找出最有效的騙徒策略
        top_scammer_tactic = max(scammer_multipliers.items(), key=lambda x: x[1])
        
        # 計算平均脆弱度
        avg_vulnerability = sum(scammer_multipliers.values()) / len(scammer_multipliers)
        
        analysis = {
            "persona": persona,
            "top_expert_approach": top_expert_approach[0],
            "top_expert_weight": top_expert_approach[1],
            "top_scammer_tactic": top_scammer_tactic[0],
            "top_scammer_multiplier": top_scammer_tactic[1],
            "avg_vulnerability": avg_vulnerability,
            "expert_weights": expert_weights,
            "scammer_multipliers": scammer_multipliers,
            "recommendations": self.get_optimal_expert_approach(persona),
            "vulnerabilities": self.get_vulnerable_tactics(persona)
        }
        
        logger.info(f"📊 {persona}型特徵分析完成")
        return analysis
    
    def compare_personas(self) -> Dict[str, any]:
        """
        對比所有persona的特徵
        
        Returns:
            對比分析結果
        """
        personas = ["elderly", "average", "overconfident", "student"]
        
        comparison = {
            "personas": {},
            "most_vulnerable": None,
            "least_vulnerable": None,
            "summary": {}
        }
        
        vulnerabilities = {}
        
        for persona in personas:
            analysis = self.analyze_persona_characteristics(persona)
            comparison["personas"][persona] = analysis
            vulnerabilities[persona] = analysis["avg_vulnerability"]
        
        # 找出最脆弱和最不脆弱的persona
        comparison["most_vulnerable"] = max(vulnerabilities.items(), key=lambda x: x[1])
        comparison["least_vulnerable"] = min(vulnerabilities.items(), key=lambda x: x[1])
        
        # 生成總結
        comparison["summary"] = {
            "total_personas": len(personas),
            "avg_vulnerability": sum(vulnerabilities.values()) / len(vulnerabilities),
            "vulnerability_range": (
                comparison["least_vulnerable"][1],
                comparison["most_vulnerable"][1]
            )
        }
        
        logger.info("📊 Persona對比分析完成")
        return comparison


# 使用示例
if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建優化器
    optimizer = AdaptiveWeightOptimizer()
    
    # 測試1: 獲取elderly型的專家權重
    print("\n=== 測試1: elderly型專家權重 ===")
    weights = optimizer.get_expert_weights("elderly")
    print(f"權重: {weights}")
    
    # 測試2: 計算加權分數
    print("\n=== 測試2: 計算加權分數 ===")
    base_scores = {
        "empathy": 80,
        "clarity": 70,
        "evidence": 60,
        "actionability": 75
    }
    score = optimizer.calculate_weighted_expert_score(base_scores, "elderly")
    print(f"加權分數: {score:.1f}/100")
    
    # 測試3: 應用騙徒策略乘數
    print("\n=== 測試3: 騙徒策略乘數 ===")
    adjusted = optimizer.apply_scammer_multiplier(10, "authority", "elderly")
    print(f"調整後變化: {adjusted:.1f} (原始: 10)")
    
    # 測試4: 分析persona特徵
    print("\n=== 測試4: Persona特徵分析 ===")
    analysis = optimizer.analyze_persona_characteristics("elderly")
    print(f"最佳專家策略: {analysis['top_expert_approach']}")
    print(f"最脆弱策略: {analysis['top_scammer_tactic']}")
    
    # 測試5: 對比所有persona
    print("\n=== 測試5: Persona對比 ===")
    comparison = optimizer.compare_personas()
    print(f"最脆弱: {comparison['most_vulnerable']}")
    print(f"最不脆弱: {comparison['least_vulnerable']}")
