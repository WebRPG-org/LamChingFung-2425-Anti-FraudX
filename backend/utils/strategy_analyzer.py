"""
策略分析系統
分析策略組合效果、識別最佳序列、預測對話走向
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyAnalysis:
    """策略分析結果"""
    synergy_score: float  # 協同效應分數 (0-2.0)
    effectiveness: float  # 預測有效性 (0-100)
    recommendations: List[str]  # 推薦策略
    warnings: List[str]  # 警告信息


@dataclass
class SequenceAnalysis:
    """序列分析結果"""
    best_sequence: List[str]  # 最佳策略序列
    expected_outcome: str  # 預期結果
    confidence: float  # 置信度 (0-100)
    alternative_sequences: List[List[str]]  # 備選序列


@dataclass
class PredictionResult:
    """預測結果"""
    predicted_trust_change: float  # 預測信任度變化
    predicted_outcome: str  # 預測結果 (success/failure/uncertain)
    confidence: float  # 置信度 (0-100)
    risk_factors: List[str]  # 風險因素


class StrategyAnalyzer:
    """
    策略分析器
    
    功能：
    1. 分析策略組合效果
    2. 識別最佳策略序列
    3. 預測對話走向
    4. 提供策略推薦
    """
    
    # 策略協同效應矩陣
    STRATEGY_SYNERGY_MATRIX = {
        # 專家策略組合（正向協同）
        ("empathy", "evidence"): 1.3,      # 同理心+證據 = 強力組合
        ("empathy", "actionability"): 1.2,  # 同理心+行動建議 = 好組合
        ("evidence", "clarity"): 1.4,       # 證據+清晰解釋 = 最佳組合
        ("clarity", "actionability"): 1.2,  # 清晰+行動 = 好組合
        ("evidence", "actionability"): 1.3, # 證據+行動 = 強力組合
        
        # 騙徒策略組合（正向協同）
        ("authority", "urgency"): 1.5,      # 權威+緊急 = 經典組合
        ("authority", "benefits"): 1.3,     # 權威+福利 = 強力組合
        ("urgency", "fear"): 1.4,           # 緊急+恐嚇 = 強力組合
        ("benefits", "urgency"): 1.3,       # 福利+緊急 = FOMO組合
        ("authority", "fear"): 1.4,         # 權威+恐嚇 = 強力組合
        ("fear", "urgency"): 1.4,           # 恐嚇+緊急 = 強力組合
        
        # 負面組合（互相削弱）
        ("empathy", "challenge"): 0.7,      # 同理心+激將法 = 矛盾
        ("authority", "empathy"): 0.8,      # 權威+同理心 = 不協調
        ("fear", "benefits"): 0.8,          # 恐嚇+福利 = 不協調
        ("challenge", "empathy"): 0.7,      # 激將法+同理心 = 矛盾
    }
    
    # 策略序列模板（經過驗證的有效序列）
    EFFECTIVE_SEQUENCES = {
        "expert_standard": ["empathy", "evidence", "actionability"],
        "expert_aggressive": ["evidence", "clarity", "actionability"],
        "expert_gentle": ["empathy", "empathy", "evidence", "actionability"],
        
        "scammer_pressure": ["authority", "urgency", "fear"],
        "scammer_temptation": ["benefits", "urgency", "authority"],
        "scammer_mixed": ["authority", "benefits", "urgency", "fear"],
    }
    
    def __init__(self):
        """初始化策略分析器"""
        logger.info("🎯 策略分析器初始化")
        
        # 嘗試加載自適應權重優化器
        try:
            from utils.adaptive_scoring import AdaptiveWeightOptimizer
            self.weight_optimizer = AdaptiveWeightOptimizer()
            logger.info("✅ 自適應權重優化器已加載")
        except Exception as e:
            logger.warning(f"⚠️ 無法加載自適應權重優化器: {e}")
            self.weight_optimizer = None
    
    def analyze_strategy_combination(
        self, 
        strategies: List[str], 
        persona: str,
        role: str = "expert"
    ) -> StrategyAnalysis:
        """
        分析策略組合效果
        
        Args:
            strategies: 策略列表
            persona: 受害者類型
            role: 角色（expert/scammer）
            
        Returns:
            StrategyAnalysis對象
        """
        logger.info(f"📊 分析策略組合: {strategies} (persona={persona}, role={role})")
        
        # 1. 計算協同效應
        synergy_score = self._calculate_synergy(strategies)
        
        # 2. 預測有效性
        effectiveness = self._predict_effectiveness(strategies, persona, role)
        
        # 3. 生成推薦
        recommendations = self._generate_recommendations(strategies, persona, role)
        
        # 4. 生成警告
        warnings = self._generate_warnings(strategies, synergy_score)
        
        analysis = StrategyAnalysis(
            synergy_score=synergy_score,
            effectiveness=effectiveness,
            recommendations=recommendations,
            warnings=warnings
        )
        
        logger.info(
            f"✅ 策略組合分析完成: 協同={synergy_score:.2f}, "
            f"有效性={effectiveness:.1f}"
        )
        
        return analysis
    
    def identify_best_sequence(
        self, 
        conversation_history: List[Dict],
        persona: str,
        role: str = "expert",
        max_length: int = 5
    ) -> SequenceAnalysis:
        """
        識別最佳策略序列
        
        Args:
            conversation_history: 對話歷史
            persona: 受害者類型
            role: 角色
            max_length: 最大序列長度
            
        Returns:
            SequenceAnalysis對象
        """
        logger.info(f"🔍 識別最佳策略序列 (persona={persona}, role={role})")
        
        # 1. 分析已使用的策略
        used_strategies = self._extract_strategies(conversation_history)
        
        # 2. 獲取候選序列
        candidate_sequences = self._generate_candidate_sequences(
            used_strategies, 
            persona, 
            role, 
            max_length
        )
        
        # 3. 評估每個序列
        scored_sequences = []
        for sequence in candidate_sequences:
            score = self._evaluate_sequence(sequence, persona, role)
            scored_sequences.append((sequence, score))
        
        # 4. 排序並選擇最佳序列
        scored_sequences.sort(key=lambda x: x[1], reverse=True)
        
        best_sequence = scored_sequences[0][0] if scored_sequences else []
        best_score = scored_sequences[0][1] if scored_sequences else 0
        
        # 5. 預測結果
        expected_outcome = self._predict_outcome(best_sequence, persona, role)
        confidence = min(100, best_score)
        
        # 6. 獲取備選序列
        alternative_sequences = [seq for seq, _ in scored_sequences[1:4]]
        
        analysis = SequenceAnalysis(
            best_sequence=best_sequence,
            expected_outcome=expected_outcome,
            confidence=confidence,
            alternative_sequences=alternative_sequences
        )
        
        logger.info(f"✅ 最佳序列: {best_sequence} (置信度={confidence:.1f}%)")
        
        return analysis
    
    def predict_dialogue_direction(
        self, 
        current_state: Dict,
        next_strategy: str,
        persona: str,
        role: str = "expert"
    ) -> PredictionResult:
        """
        預測對話走向
        
        Args:
            current_state: 當前狀態（包含信任度等）
            next_strategy: 下一個策略
            persona: 受害者類型
            role: 角色
            
        Returns:
            PredictionResult對象
        """
        logger.info(f"🔮 預測對話走向: {next_strategy} (persona={persona})")
        
        # 1. 預測信任度變化
        predicted_trust_change = self._predict_trust_change(
            current_state, 
            next_strategy, 
            persona, 
            role
        )
        
        # 2. 預測結果
        predicted_outcome = self._predict_outcome_from_trust(
            current_state, 
            predicted_trust_change, 
            role
        )
        
        # 3. 計算置信度
        confidence = self._calculate_prediction_confidence(
            current_state, 
            next_strategy, 
            persona
        )
        
        # 4. 識別風險因素
        risk_factors = self._identify_risk_factors(
            current_state, 
            next_strategy, 
            persona
        )
        
        result = PredictionResult(
            predicted_trust_change=predicted_trust_change,
            predicted_outcome=predicted_outcome,
            confidence=confidence,
            risk_factors=risk_factors
        )
        
        logger.info(
            f"✅ 預測完成: 信任度變化={predicted_trust_change:+.1f}, "
            f"結果={predicted_outcome}, 置信度={confidence:.1f}%"
        )
        
        return result
    
    # ==================== 輔助方法 ====================
    
    def _calculate_synergy(self, strategies: List[str]) -> float:
        """計算策略協同效應"""
        if len(strategies) < 2:
            return 1.0
        
        synergy = 1.0
        
        # 計算所有策略對的協同效應
        for i in range(len(strategies)):
            for j in range(i+1, len(strategies)):
                pair = (strategies[i], strategies[j])
                reverse_pair = (strategies[j], strategies[i])
                
                # 查找協同效應值
                if pair in self.STRATEGY_SYNERGY_MATRIX:
                    synergy *= self.STRATEGY_SYNERGY_MATRIX[pair]
                elif reverse_pair in self.STRATEGY_SYNERGY_MATRIX:
                    synergy *= self.STRATEGY_SYNERGY_MATRIX[reverse_pair]
        
        return round(synergy, 2)
    
    def _predict_effectiveness(
        self, 
        strategies: List[str], 
        persona: str,
        role: str
    ) -> float:
        """預測策略組合有效性"""
        base_effectiveness = 50.0
        
        # 1. 協同效應加成
        synergy = self._calculate_synergy(strategies)
        base_effectiveness *= synergy
        
        # 2. Persona適配度
        if self.weight_optimizer and role == "expert":
            weights = self.weight_optimizer.get_expert_weights(persona)
            persona_bonus = sum(weights.get(s, 0) for s in strategies) * 20
            base_effectiveness += persona_bonus
        elif self.weight_optimizer and role == "scammer":
            multipliers = self.weight_optimizer.get_scammer_multipliers(persona)
            persona_bonus = sum(multipliers.get(s, 1.0) - 1.0 for s in strategies) * 10
            base_effectiveness += persona_bonus
        
        # 3. 策略數量調整（過多會降低效果）
        if len(strategies) > 3:
            quantity_penalty = 0.9 ** (len(strategies) - 3)
            base_effectiveness *= quantity_penalty
        
        return round(min(100, max(0, base_effectiveness)), 2)
    
    def _generate_recommendations(
        self, 
        strategies: List[str], 
        persona: str,
        role: str
    ) -> List[str]:
        """生成策略推薦"""
        recommendations = []
        
        # 1. 基於persona推薦
        if self.weight_optimizer and role == "expert":
            optimal_approaches = self.weight_optimizer.get_optimal_expert_approach(persona)
            missing_strategies = [s for s in optimal_approaches[:2] if s not in strategies]
            if missing_strategies:
                recommendations.append(f"建議添加策略: {', '.join(missing_strategies)}")
        
        # 2. 基於協同效應推薦
        synergy = self._calculate_synergy(strategies)
        if synergy < 1.0:
            recommendations.append("當前策略組合存在衝突，建議調整")
        elif synergy > 1.3:
            recommendations.append("策略組合協同效應良好，繼續保持")
        
        # 3. 基於數量推薦
        if len(strategies) > 4:
            recommendations.append("策略過多，建議精簡到3-4個核心策略")
        elif len(strategies) < 2:
            recommendations.append("策略過少，建議增加1-2個輔助策略")
        
        return recommendations
    
    def _generate_warnings(self, strategies: List[str], synergy: float) -> List[str]:
        """生成警告信息"""
        warnings = []
        
        # 1. 協同效應警告
        if synergy < 0.8:
            warnings.append("⚠️ 策略組合存在嚴重衝突")
        
        # 2. 策略衝突警告
        conflict_pairs = [
            ("empathy", "challenge"),
            ("authority", "empathy"),
            ("fear", "benefits")
        ]
        for s1, s2 in conflict_pairs:
            if s1 in strategies and s2 in strategies:
                warnings.append(f"⚠️ {s1}和{s2}策略存在衝突")
        
        return warnings
    
    def _extract_strategies(self, conversation_history: List[Dict]) -> List[str]:
        """從對話歷史中提取策略"""
        strategies = []
        for turn in conversation_history:
            if "strategy" in turn:
                strategies.append(turn["strategy"])
            elif "tactics_used" in turn:
                strategies.extend(turn["tactics_used"])
        return strategies
    
    def _generate_candidate_sequences(
        self, 
        used_strategies: List[str],
        persona: str,
        role: str,
        max_length: int
    ) -> List[List[str]]:
        """生成候選策略序列"""
        candidates = []
        
        # 1. 添加預定義的有效序列
        prefix = "expert" if role == "expert" else "scammer"
        for key, sequence in self.EFFECTIVE_SEQUENCES.items():
            if key.startswith(prefix):
                candidates.append(sequence[:max_length])
        
        # 2. 基於persona生成定制序列
        if self.weight_optimizer and role == "expert":
            optimal = self.weight_optimizer.get_optimal_expert_approach(persona)
            candidates.append(optimal[:max_length])
        
        # 3. 基於已使用策略生成變體
        if used_strategies:
            # 反向序列
            candidates.append(list(reversed(used_strategies[-max_length:])))
            # 優化序列（移除重複）
            unique_strategies = []
            for s in used_strategies:
                if s not in unique_strategies:
                    unique_strategies.append(s)
            candidates.append(unique_strategies[:max_length])
        
        return candidates
    
    def _evaluate_sequence(
        self, 
        sequence: List[str], 
        persona: str,
        role: str
    ) -> float:
        """評估策略序列的分數"""
        # 1. 協同效應分數
        synergy = self._calculate_synergy(sequence)
        
        # 2. 有效性分數
        effectiveness = self._predict_effectiveness(sequence, persona, role)
        
        # 3. 序列長度分數（3-4個策略最佳）
        length_score = 100 - abs(len(sequence) - 3.5) * 10
        
        # 綜合分數
        total_score = (synergy * 30 + effectiveness * 0.5 + length_score * 0.2)
        
        return round(total_score, 2)
    
    def _predict_outcome(
        self, 
        sequence: List[str], 
        persona: str,
        role: str
    ) -> str:
        """預測序列的結果"""
        effectiveness = self._predict_effectiveness(sequence, persona, role)
        
        if effectiveness >= 75:
            return "success" if role == "expert" else "scam_success"
        elif effectiveness >= 50:
            return "partial_success"
        else:
            return "failure"
    
    def _predict_trust_change(
        self, 
        current_state: Dict,
        next_strategy: str,
        persona: str,
        role: str
    ) -> float:
        """預測信任度變化"""
        base_change = 5.0  # 基礎變化
        
        # 使用自適應權重優化器
        if self.weight_optimizer:
            if role == "expert":
                # 專家策略效果
                weights = self.weight_optimizer.get_expert_weights(persona)
                multiplier = weights.get(next_strategy, 0.2) * 5
                base_change *= multiplier
            elif role == "scammer":
                # 騙徒策略效果
                base_change = self.weight_optimizer.apply_scammer_multiplier(
                    base_change, 
                    next_strategy, 
                    persona
                )
        
        # 考慮當前信任度（信任度越高，改變越難）
        current_trust = current_state.get("trust_in_" + role, 50)
        if current_trust > 70:
            base_change *= 0.7
        elif current_trust < 30:
            base_change *= 0.7
        
        return round(base_change, 2)
    
    def _predict_outcome_from_trust(
        self, 
        current_state: Dict,
        predicted_change: float,
        role: str
    ) -> str:
        """根據信任度變化預測結果"""
        current_trust = current_state.get("trust_in_" + role, 50)
        new_trust = current_trust + predicted_change
        
        if role == "expert":
            if new_trust >= 70:
                return "expert_success"
            elif new_trust >= 50:
                return "uncertain"
            else:
                return "expert_failure"
        else:  # scammer
            if new_trust >= 70:
                return "scam_success"
            elif new_trust >= 50:
                return "uncertain"
            else:
                return "scam_failure"
    
    def _calculate_prediction_confidence(
        self, 
        current_state: Dict,
        next_strategy: str,
        persona: str
    ) -> float:
        """計算預測置信度"""
        confidence = 70.0  # 基礎置信度
        
        # 1. 如果有自適應權重優化器，置信度更高
        if self.weight_optimizer:
            confidence += 10
        
        # 2. 如果當前狀態穩定，置信度更高
        alertness = current_state.get("alertness", 50)
        if 40 <= alertness <= 60:
            confidence += 10
        
        # 3. 如果策略明確，置信度更高
        if next_strategy in ["empathy", "evidence", "authority", "urgency"]:
            confidence += 10
        
        return round(min(100, confidence), 2)
    
    def _identify_risk_factors(
        self, 
        current_state: Dict,
        next_strategy: str,
        persona: str
    ) -> List[str]:
        """識別風險因素"""
        risks = []
        
        # 1. 信任度風險
        trust_in_scammer = current_state.get("trust_in_scammer", 50)
        if trust_in_scammer > 70:
            risks.append("受害者對騙徒信任度過高")
        
        # 2. 警覺度風險
        alertness = current_state.get("alertness", 50)
        if alertness < 30:
            risks.append("受害者警覺度過低")
        
        # 3. 策略風險
        if self.weight_optimizer:
            multipliers = self.weight_optimizer.get_scammer_multipliers(persona)
            if next_strategy in multipliers and multipliers[next_strategy] > 1.3:
                risks.append(f"{next_strategy}策略對{persona}型受害者特別有效")
        
        return risks


# 使用示例
if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建分析器
    analyzer = StrategyAnalyzer()
    
    # 測試1: 分析策略組合
    print("\n=== 測試1: 策略組合分析 ===")
    analysis = analyzer.analyze_strategy_combination(
        ["empathy", "evidence", "actionability"],
        "elderly",
        "expert"
    )
    print(f"協同效應: {analysis.synergy_score:.2f}")
    print(f"有效性: {analysis.effectiveness:.1f}")
    print(f"推薦: {analysis.recommendations}")
    
    # 測試2: 識別最佳序列
    print("\n=== 測試2: 最佳序列識別 ===")
    conversation_history = [
        {"role": "expert", "strategy": "empathy"},
        {"role": "expert", "strategy": "evidence"}
    ]
    sequence = analyzer.identify_best_sequence(
        conversation_history,
        "elderly",
        "expert"
    )
    print(f"最佳序列: {sequence.best_sequence}")
    print(f"預期結果: {sequence.expected_outcome}")
    print(f"置信度: {sequence.confidence:.1f}%")
    
    # 測試3: 預測對話走向
    print("\n=== 測試3: 對話走向預測 ===")
    current_state = {
        "trust_in_expert": 60,
        "trust_in_scammer": 55,
        "alertness": 50
    }
    prediction = analyzer.predict_dialogue_direction(
        current_state,
        "evidence",
        "elderly",
        "expert"
    )
    print(f"預測信任度變化: {prediction.predicted_trust_change:+.1f}")
    print(f"預測結果: {prediction.predicted_outcome}")
    print(f"置信度: {prediction.confidence:.1f}%")
    print(f"風險因素: {prediction.risk_factors}")
