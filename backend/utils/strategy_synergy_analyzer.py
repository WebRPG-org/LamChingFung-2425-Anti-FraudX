"""
策略協同分析器
分析多種詐騙策略的組合效果和協同作用
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategySynergy:
    """策略協同效果"""
    strategy_combination: Tuple[str, ...]  # 策略組合
    synergy_score: float  # 協同分數 (0-100)
    effectiveness: float  # 有效性 (0-100)
    frequency: int  # 使用頻率
    avg_trust_change: float  # 平均信任度變化
    success_rate: float  # 成功率 (%)
    best_order: List[str]  # 最佳順序
    recommendations: List[str]  # 建議


class StrategySynergyAnalyzer:
    """策略協同分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 策略協同矩陣（預定義的協同效果）
        self.synergy_matrix = {
            ("authority", "urgency"): 1.3,  # 權威+緊急 = 強協同
            ("authority", "fear"): 1.25,    # 權威+恐懼 = 強協同
            ("urgency", "fear"): 1.2,       # 緊急+恐懼 = 中等協同
            ("sympathy", "urgency"): 1.15,  # 同情+緊急 = 中等協同
            ("greed", "urgency"): 1.2,      # 貪婪+緊急 = 中等協同
            ("authority", "sympathy"): 0.9, # 權威+同情 = 負協同（衝突）
            ("greed", "fear"): 0.95,        # 貪婪+恐懼 = 輕微負協同
        }
        
        # 策略順序效果
        self.order_effects = {
            ("authority", "urgency"): 1.2,  # 先權威後緊急效果好
            ("urgency", "authority"): 1.0,  # 先緊急後權威效果一般
            ("sympathy", "greed"): 1.15,    # 先同情後貪婪效果好
            ("greed", "sympathy"): 0.9,     # 先貪婪後同情效果差
        }
        
        # 歷史數據
        self.strategy_history: List[Dict] = []
        
        logger.info("✅ 策略協同分析器已初始化")
    
    def analyze_strategy_combination(
        self,
        conversation_history: List[Dict],
        evaluation_result: Optional[Dict] = None
    ) -> StrategySynergy:
        """
        分析策略組合的協同效果
        
        Args:
            conversation_history: 對話歷史
            evaluation_result: 評估結果（可選）
        
        Returns:
            StrategySynergy對象
        """
        logger.info("📊 開始分析策略協同效果")
        
        # 1. 提取策略序列
        strategies = self._extract_strategies(conversation_history)
        
        if not strategies:
            logger.warning("⚠️ 沒有找到策略")
            return self._get_default_synergy()
        
        # 2. 計算協同分數
        synergy_score = self._calculate_synergy_score(strategies)
        
        # 3. 計算有效性
        effectiveness = self._calculate_effectiveness(
            strategies,
            evaluation_result
        )
        
        # 4. 分析最佳順序
        best_order = self._analyze_best_order(strategies)
        
        # 5. 生成建議
        recommendations = self._generate_recommendations(
            strategies,
            synergy_score,
            effectiveness
        )
        
        # 6. 記錄歷史
        self._record_history(strategies, evaluation_result)
        
        # 7. 計算統計數據
        frequency = self._get_frequency(tuple(strategies))
        avg_trust_change = self._get_avg_trust_change(tuple(strategies))
        success_rate = self._get_success_rate(tuple(strategies))
        
        synergy = StrategySynergy(
            strategy_combination=tuple(strategies),
            synergy_score=round(synergy_score, 2),
            effectiveness=round(effectiveness, 2),
            frequency=frequency,
            avg_trust_change=round(avg_trust_change, 2),
            success_rate=round(success_rate, 2),
            best_order=best_order,
            recommendations=recommendations
        )
        
        logger.info(
            f"✅ 策略協同分析完成 - "
            f"組合={strategies}, "
            f"協同分數={synergy_score:.1f}, "
            f"有效性={effectiveness:.1f}"
        )
        
        return synergy
    
    def _extract_strategies(self, conversation_history: List[Dict]) -> List[str]:
        """提取策略序列"""
        strategies = []
        
        for msg in conversation_history:
            if msg.get("role") == "scammer":
                strategy = msg.get("strategy", "none")
                if strategy != "none":
                    strategies.append(strategy)
        
        return strategies
    
    def _calculate_synergy_score(self, strategies: List[str]) -> float:
        """計算協同分數"""
        if len(strategies) < 2:
            return 50.0  # 單一策略，基礎分數
        
        total_synergy = 0.0
        pair_count = 0
        
        # 計算所有策略對的協同效果
        for i in range(len(strategies) - 1):
            for j in range(i + 1, len(strategies)):
                strategy_pair = tuple(sorted([strategies[i], strategies[j]]))
                
                # 查找協同係數
                synergy_coef = self.synergy_matrix.get(strategy_pair, 1.0)
                
                # 考慮順序效果
                if i + 1 == j:  # 相鄰策略
                    order_pair = (strategies[i], strategies[j])
                    order_coef = self.order_effects.get(order_pair, 1.0)
                    synergy_coef *= order_coef
                
                total_synergy += synergy_coef
                pair_count += 1
        
        # 平均協同效果
        avg_synergy = total_synergy / pair_count if pair_count > 0 else 1.0
        
        # 轉換為0-100分數
        synergy_score = (avg_synergy - 0.5) * 100 + 50
        
        return max(0, min(100, synergy_score))
    
    def _calculate_effectiveness(
        self,
        strategies: List[str],
        evaluation_result: Optional[Dict]
    ) -> float:
        """計算有效性"""
        if evaluation_result:
            trust_change = evaluation_result.get("trust_change", 0)
            
            # 信任度下降越多，有效性越高
            if trust_change < 0:
                effectiveness = min(100, abs(trust_change) * 5)
            else:
                effectiveness = max(0, 50 - trust_change * 2)
        else:
            # 基於策略類型估算
            strategy_effectiveness = {
                "authority": 75,
                "urgency": 70,
                "fear": 72,
                "sympathy": 65,
                "greed": 68,
                "none": 30
            }
            
            avg_effectiveness = sum(
                strategy_effectiveness.get(s, 50) for s in strategies
            ) / len(strategies) if strategies else 50
            
            effectiveness = avg_effectiveness
        
        return effectiveness
    
    def _analyze_best_order(self, strategies: List[str]) -> List[str]:
        """分析最佳策略順序"""
        if len(strategies) <= 1:
            return strategies
        
        # 使用貪心算法找最佳順序
        best_order = []
        remaining = strategies.copy()
        
        # 第一個策略：選擇最強的
        strategy_strength = {
            "authority": 5,
            "fear": 4,
            "urgency": 4,
            "sympathy": 3,
            "greed": 3,
            "none": 1
        }
        
        first = max(remaining, key=lambda s: strategy_strength.get(s, 1))
        best_order.append(first)
        remaining.remove(first)
        
        # 後續策略：選擇與前一個協同最好的
        while remaining:
            last = best_order[-1]
            
            best_next = max(
                remaining,
                key=lambda s: self.order_effects.get((last, s), 1.0)
            )
            
            best_order.append(best_next)
            remaining.remove(best_next)
        
        return best_order
    
    def _generate_recommendations(
        self,
        strategies: List[str],
        synergy_score: float,
        effectiveness: float
    ) -> List[str]:
        """生成建議"""
        recommendations = []
        
        # 基於協同分數
        if synergy_score < 50:
            recommendations.append("策略組合協同效果差，建議調整策略選擇")
            
            # 檢查衝突策略
            for i in range(len(strategies) - 1):
                for j in range(i + 1, len(strategies)):
                    pair = tuple(sorted([strategies[i], strategies[j]]))
                    if self.synergy_matrix.get(pair, 1.0) < 1.0:
                        recommendations.append(
                            f"避免同時使用{strategies[i]}和{strategies[j]}策略"
                        )
        
        elif synergy_score > 70:
            recommendations.append("策略組合協同效果好，繼續保持")
        
        # 基於有效性
        if effectiveness < 50:
            recommendations.append("整體有效性較低，建議增強策略執行")
        
        # 基於策略數量
        if len(strategies) < 2:
            recommendations.append("建議使用多種策略組合以提高效果")
        elif len(strategies) > 4:
            recommendations.append("策略過多可能導致混亂，建議精簡")
        
        # 順序建議
        best_order = self._analyze_best_order(strategies)
        if best_order != strategies:
            recommendations.append(
                f"建議調整策略順序為: {' → '.join(best_order)}"
            )
        
        if not recommendations:
            recommendations.append("策略使用合理，無需調整")
        
        return recommendations
    
    def _record_history(
        self,
        strategies: List[str],
        evaluation_result: Optional[Dict]
    ):
        """記錄歷史數據"""
        self.strategy_history.append({
            "strategies": strategies,
            "trust_change": evaluation_result.get("trust_change", 0) if evaluation_result else 0,
            "timestamp": datetime.now().isoformat()
        })
    
    def _get_frequency(self, strategy_combination: Tuple[str, ...]) -> int:
        """獲取策略組合的使用頻率"""
        return sum(
            1 for record in self.strategy_history
            if tuple(record["strategies"]) == strategy_combination
        )
    
    def _get_avg_trust_change(self, strategy_combination: Tuple[str, ...]) -> float:
        """獲取平均信任度變化"""
        matching_records = [
            record for record in self.strategy_history
            if tuple(record["strategies"]) == strategy_combination
        ]
        
        if not matching_records:
            return 0.0
        
        return sum(r["trust_change"] for r in matching_records) / len(matching_records)
    
    def _get_success_rate(self, strategy_combination: Tuple[str, ...]) -> float:
        """獲取成功率"""
        matching_records = [
            record for record in self.strategy_history
            if tuple(record["strategies"]) == strategy_combination
        ]
        
        if not matching_records:
            return 0.0
        
        # 成功定義為信任度下降
        successes = sum(1 for r in matching_records if r["trust_change"] < 0)
        
        return (successes / len(matching_records)) * 100
    
    def _get_default_synergy(self) -> StrategySynergy:
        """獲取默認協同效果"""
        return StrategySynergy(
            strategy_combination=(),
            synergy_score=0.0,
            effectiveness=0.0,
            frequency=0,
            avg_trust_change=0.0,
            success_rate=0.0,
            best_order=[],
            recommendations=["需要提供策略數據"]
        )
    
    def get_top_combinations(self, top_n: int = 5) -> List[Dict]:
        """獲取最佳策略組合"""
        if not self.strategy_history:
            return []
        
        # 統計所有組合
        combination_stats = {}
        
        for record in self.strategy_history:
            combo = tuple(record["strategies"])
            
            if combo not in combination_stats:
                combination_stats[combo] = {
                    "count": 0,
                    "total_change": 0,
                    "successes": 0
                }
            
            stats = combination_stats[combo]
            stats["count"] += 1
            stats["total_change"] += record["trust_change"]
            if record["trust_change"] < 0:
                stats["successes"] += 1
        
        # 計算平均效果和成功率
        results = []
        for combo, stats in combination_stats.items():
            results.append({
                "combination": combo,
                "frequency": stats["count"],
                "avg_trust_change": stats["total_change"] / stats["count"],
                "success_rate": (stats["successes"] / stats["count"]) * 100
            })
        
        # 排序（按平均信任度變化，越負越好）
        results.sort(key=lambda x: x["avg_trust_change"])
        
        return results[:top_n]
    
    def generate_synergy_report(self, synergy: StrategySynergy) -> str:
        """生成協同分析報告"""
        report = f"""
策略協同分析報告
{'='*60}

策略組合: {' + '.join(synergy.strategy_combination)}

協同效果:
  - 協同分數: {synergy.synergy_score:.1f}/100
  - 有效性: {synergy.effectiveness:.1f}/100
  - 使用頻率: {synergy.frequency}次
  - 平均信任度變化: {synergy.avg_trust_change:+.2f}
  - 成功率: {synergy.success_rate:.1f}%

最佳順序:
  {' → '.join(synergy.best_order)}

建議:
{chr(10).join(f'  {i+1}. {rec}' for i, rec in enumerate(synergy.recommendations))}

{'='*60}
"""
        return report


# 使用示例
if __name__ == "__main__":
    from datetime import datetime
    
    logging.basicConfig(level=logging.INFO)
    
    analyzer = StrategySynergyAnalyzer()
    
    # 示例對話
    conversation = [
        {"role": "scammer", "content": "你好，我是警察局的", "strategy": "authority"},
        {"role": "victim", "content": "有什麼事嗎？"},
        {"role": "scammer", "content": "你的帳戶有問題，必須立即處理！", "strategy": "urgency"}
    ]
    
    evaluation_result = {"trust_change": -15.5}
    
    synergy = analyzer.analyze_strategy_combination(conversation, evaluation_result)
    report = analyzer.generate_synergy_report(synergy)
    
    print(report)
