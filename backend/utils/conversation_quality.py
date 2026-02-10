"""
對話質量評估系統
評估對話的連貫性、有效性和時機把握
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """質量評分"""
    coherence: float  # 連貫性 (0-100)
    effectiveness: float  # 有效性 (0-100)
    timing: float  # 時機把握 (0-100)
    overall: float  # 總體質量 (0-100)
    details: Dict  # 詳細分析


class ConversationQualityAnalyzer:
    """
    對話質量評估器
    
    評估維度：
    1. 連貫性（Coherence）- 對話是否流暢、邏輯清晰
    2. 有效性（Effectiveness）- 策略是否達到預期效果
    3. 時機把握（Timing）- 策略使用時機是否恰當
    """
    
    # 關鍵詞列表（用於檢測上下文連續性）
    REFERENCE_KEYWORDS = [
        "你剛才說", "你提到", "關於", "但是", "不過", "所以",
        "因此", "那麼", "這樣", "如果", "既然"
    ]
    
    # 話題關鍵詞（用於檢測話題一致性）
    TOPIC_KEYWORDS = {
        "bank_scam": ["銀行", "帳戶", "轉帳", "凍結", "存款"],
        "police_scam": ["警察", "警方", "案件", "調查", "嫌疑"],
        "investment_scam": ["投資", "回報", "收益", "股票", "基金"],
        "subsidy_scam": ["補貼", "福利", "優惠", "回贈", "著數"]
    }
    
    def __init__(self):
        """初始化評估器"""
        logger.info("🎯 對話質量評估器初始化")
    
    def analyze_conversation(
        self, 
        conversation: List[Dict],
        trust_history: List[Dict]
    ) -> QualityScore:
        """
        分析整個對話的質量
        
        Args:
            conversation: 對話歷史 [{"role": "scammer", "text": "...", "timestamp": ...}, ...]
            trust_history: 信任度歷史 [{"trust_in_scammer": 50, "trust_in_expert": 50, ...}, ...]
            
        Returns:
            QualityScore對象
        """
        logger.info(f"📊 開始分析對話質量（{len(conversation)}輪）")
        
        # 1. 分析連貫性
        coherence_score = self.analyze_coherence(conversation)
        
        # 2. 分析有效性
        effectiveness_score = self.analyze_effectiveness(conversation, trust_history)
        
        # 3. 分析時機把握
        timing_score = self.analyze_timing(conversation, trust_history)
        
        # 4. 計算總體分數
        overall_score = self._calculate_overall_score(
            coherence_score,
            effectiveness_score,
            timing_score
        )
        
        # 5. 生成詳細分析
        details = self._generate_details(
            conversation,
            trust_history,
            coherence_score,
            effectiveness_score,
            timing_score
        )
        
        quality_score = QualityScore(
            coherence=coherence_score,
            effectiveness=effectiveness_score,
            timing=timing_score,
            overall=overall_score,
            details=details
        )
        
        logger.info(
            f"✅ 質量分析完成: 連貫性={coherence_score:.1f}, "
            f"有效性={effectiveness_score:.1f}, 時機={timing_score:.1f}, "
            f"總體={overall_score:.1f}"
        )
        
        return quality_score
    
    def analyze_coherence(self, conversation: List[Dict]) -> float:
        """
        分析對話連貫性
        
        評估維度：
        1. 上下文連續性（40%）- 是否回應上一輪內容
        2. 話題一致性（30%）- 是否偏離主題
        3. 邏輯流暢性（30%）- 邏輯是否通順
        
        Args:
            conversation: 對話歷史
            
        Returns:
            連貫性分數 (0-100)
        """
        if len(conversation) < 2:
            return 100.0  # 單輪對話默認滿分
        
        context_score = 0
        topic_score = 0
        logic_score = 0
        
        # 識別主要話題
        main_topic = self._identify_main_topic(conversation)
        
        for i in range(1, len(conversation)):
            current = conversation[i]
            previous = conversation[i-1]
            
            # 1. 檢查上下文連續性
            if self._has_reference_to_previous(current, previous):
                context_score += 1
            
            # 2. 檢查話題一致性
            if self._same_topic(current, main_topic):
                topic_score += 1
            
            # 3. 檢查邏輯流暢性
            if self._logical_flow(current, previous):
                logic_score += 1
        
        n = len(conversation) - 1
        final_score = (
            (context_score / n) * 0.4 +
            (topic_score / n) * 0.3 +
            (logic_score / n) * 0.3
        ) * 100
        
        logger.debug(
            f"📊 連貫性分析: 上下文={context_score}/{n}, "
            f"話題={topic_score}/{n}, 邏輯={logic_score}/{n}"
        )
        
        return round(final_score, 2)
    
    def analyze_effectiveness(
        self, 
        conversation: List[Dict],
        trust_history: List[Dict]
    ) -> float:
        """
        分析策略有效性
        
        評估維度：
        1. 目標達成度（50%）- 信任度變化是否符合預期
        2. 受害者反應（30%）- 受害者反應是否積極
        3. 策略執行（20%）- 策略是否正確執行
        
        Args:
            conversation: 對話歷史
            trust_history: 信任度歷史
            
        Returns:
            有效性分數 (0-100)
        """
        if len(conversation) == 0:
            return 0.0
        
        goal_achievement = 0
        reaction_quality = 0
        execution_quality = 0
        
        for i, turn in enumerate(conversation):
            role = turn.get("role")
            text = turn.get("text", "")
            
            # 獲取信任度變化
            if i < len(trust_history) - 1:
                trust_before = trust_history[i]
                trust_after = trust_history[i + 1]
                
                if role == "scammer":
                    trust_change = trust_after.get("trust_in_scammer", 50) - \
                                 trust_before.get("trust_in_scammer", 50)
                elif role == "expert":
                    trust_change = trust_after.get("trust_in_expert", 50) - \
                                 trust_before.get("trust_in_expert", 50)
                else:
                    trust_change = 0
                
                # 1. 目標達成度（期望正向變化）
                if trust_change > 0:
                    goal_achievement += 1
                elif trust_change == 0:
                    goal_achievement += 0.5
            
            # 2. 受害者反應質量
            if role == "victim":
                if self._is_positive_reaction(text):
                    reaction_quality += 1
            
            # 3. 策略執行質量
            if role in ["scammer", "expert"]:
                if self._has_clear_strategy(text):
                    execution_quality += 1
        
        # 計算各維度分數
        n_turns = len(conversation)
        n_agent_turns = sum(1 for t in conversation if t.get("role") in ["scammer", "expert"])
        n_victim_turns = sum(1 for t in conversation if t.get("role") == "victim")
        
        goal_score = (goal_achievement / max(1, n_agent_turns)) if n_agent_turns > 0 else 0
        reaction_score = (reaction_quality / max(1, n_victim_turns)) if n_victim_turns > 0 else 0
        execution_score = (execution_quality / max(1, n_agent_turns)) if n_agent_turns > 0 else 0
        
        final_score = (
            goal_score * 0.5 +
            reaction_score * 0.3 +
            execution_score * 0.2
        ) * 100
        
        logger.debug(
            f"📊 有效性分析: 目標={goal_score:.2f}, "
            f"反應={reaction_score:.2f}, 執行={execution_score:.2f}"
        )
        
        return round(final_score, 2)
    
    def analyze_timing(
        self, 
        conversation: List[Dict],
        trust_history: List[Dict]
    ) -> float:
        """
        分析時機把握
        
        評估維度：
        1. 策略時機（50%）- 策略使用時機是否恰當
        2. 節奏控制（30%）- 對話節奏是否合適
        3. 轉折把握（20%）- 是否抓住關鍵時刻
        
        Args:
            conversation: 對話歷史
            trust_history: 信任度歷史
            
        Returns:
            時機分數 (0-100)
        """
        if len(conversation) < 2:
            return 100.0
        
        timing_score = 0
        rhythm_score = 0
        turning_point_score = 0
        
        # 識別轉折點
        turning_points = self._identify_turning_points(trust_history)
        
        for i, turn in enumerate(conversation):
            role = turn.get("role")
            
            if role in ["scammer", "expert"]:
                # 1. 策略時機評估
                if i < len(trust_history):
                    trust_state = trust_history[i]
                    if self._is_optimal_timing(turn, trust_state):
                        timing_score += 1
                
                # 2. 節奏控制評估
                if i > 0:
                    if self._is_appropriate_rhythm(conversation[i-1], turn):
                        rhythm_score += 1
                
                # 3. 轉折把握評估
                if i in turning_points:
                    if self._has_appropriate_response(turn, trust_history[i]):
                        turning_point_score += 1
        
        n_agent_turns = sum(1 for t in conversation if t.get("role") in ["scammer", "expert"])
        n_turning_points = len(turning_points)
        
        timing_ratio = (timing_score / max(1, n_agent_turns)) if n_agent_turns > 0 else 0
        rhythm_ratio = (rhythm_score / max(1, n_agent_turns - 1)) if n_agent_turns > 1 else 1
        turning_ratio = (turning_point_score / max(1, n_turning_points)) if n_turning_points > 0 else 1
        
        final_score = (
            timing_ratio * 0.5 +
            rhythm_ratio * 0.3 +
            turning_ratio * 0.2
        ) * 100
        
        logger.debug(
            f"📊 時機分析: 策略時機={timing_ratio:.2f}, "
            f"節奏={rhythm_ratio:.2f}, 轉折={turning_ratio:.2f}"
        )
        
        return round(final_score, 2)
    
    # ==================== 輔助方法 ====================
    
    def _identify_main_topic(self, conversation: List[Dict]) -> str:
        """識別對話的主要話題"""
        topic_counts = {topic: 0 for topic in self.TOPIC_KEYWORDS.keys()}
        
        for turn in conversation:
            text = turn.get("text", "")
            for topic, keywords in self.TOPIC_KEYWORDS.items():
                if any(keyword in text for keyword in keywords):
                    topic_counts[topic] += 1
        
        main_topic = max(topic_counts.items(), key=lambda x: x[1])[0]
        return main_topic
    
    def _has_reference_to_previous(self, current: Dict, previous: Dict) -> bool:
        """檢查是否引用了上一輪內容"""
        current_text = current.get("text", "")
        return any(keyword in current_text for keyword in self.REFERENCE_KEYWORDS)
    
    def _same_topic(self, turn: Dict, main_topic: str) -> bool:
        """檢查是否與主題一致"""
        text = turn.get("text", "")
        keywords = self.TOPIC_KEYWORDS.get(main_topic, [])
        return any(keyword in text for keyword in keywords)
    
    def _logical_flow(self, current: Dict, previous: Dict) -> bool:
        """檢查邏輯流暢性"""
        # 簡化版：檢查是否有明顯的邏輯斷裂
        current_text = current.get("text", "")
        previous_text = previous.get("text", "")
        
        # 如果當前回應很短（<10字），可能邏輯不完整
        if len(current_text) < 10:
            return False
        
        # 如果有邏輯連接詞，認為邏輯流暢
        logic_connectors = ["因為", "所以", "但是", "不過", "而且", "並且", "或者"]
        if any(connector in current_text for connector in logic_connectors):
            return True
        
        return True  # 默認認為流暢
    
    def _is_positive_reaction(self, text: str) -> bool:
        """判斷受害者反應是否積極"""
        positive_keywords = ["好", "明白", "我會", "多謝", "對", "是", "啱"]
        negative_keywords = ["唔", "不", "但", "點解", "奇怪"]
        
        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)
        
        return positive_count > negative_count
    
    def _has_clear_strategy(self, text: str) -> bool:
        """判斷是否有明確的策略"""
        # 檢查是否包含策略關鍵詞
        strategy_keywords = [
            "銀行", "警察", "政府", "緊急", "立即", "馬上",  # 騙徒策略
            "唔好驚", "冷靜", "證據", "報警", "掛斷"  # 專家策略
        ]
        return any(keyword in text for keyword in strategy_keywords)
    
    def _is_optimal_timing(self, turn: Dict, trust_state: Dict) -> bool:
        """判斷策略時機是否恰當"""
        role = turn.get("role")
        text = turn.get("text", "")
        
        if role == "expert":
            # 專家應該在受害者對騙徒信任度較高時介入
            trust_in_scammer = trust_state.get("trust_in_scammer", 50)
            if trust_in_scammer > 60:
                return True
        elif role == "scammer":
            # 騙徒應該在受害者警覺度較低時施壓
            alertness = trust_state.get("alertness", 50)
            if alertness < 50:
                return True
        
        return False
    
    def _is_appropriate_rhythm(self, previous: Dict, current: Dict) -> bool:
        """判斷對話節奏是否合適"""
        # 簡化版：檢查回應長度是否合適
        prev_length = len(previous.get("text", ""))
        curr_length = len(current.get("text", ""))
        
        # 回應長度應該在合理範圍內（20-200字）
        return 20 <= curr_length <= 200
    
    def _identify_turning_points(self, trust_history: List[Dict]) -> List[int]:
        """識別信任度轉折點"""
        turning_points = []
        
        for i in range(1, len(trust_history) - 1):
            prev_trust = trust_history[i-1].get("trust_in_scammer", 50)
            curr_trust = trust_history[i].get("trust_in_scammer", 50)
            next_trust = trust_history[i+1].get("trust_in_scammer", 50)
            
            # 檢測趨勢變化
            prev_trend = curr_trust - prev_trust
            next_trend = next_trust - curr_trust
            
            # 如果趨勢反轉（正變負或負變正），認為是轉折點
            if prev_trend * next_trend < 0 and abs(prev_trend) > 5:
                turning_points.append(i)
        
        return turning_points
    
    def _has_appropriate_response(self, turn: Dict, trust_state: Dict) -> bool:
        """判斷在轉折點是否有恰當的回應"""
        # 簡化版：檢查是否有強烈的策略詞彙
        text = turn.get("text", "")
        strong_keywords = ["一定", "必須", "千萬", "絕對", "立即", "馬上", "嚴重"]
        return any(keyword in text for keyword in strong_keywords)
    
    def _calculate_overall_score(
        self, 
        coherence: float,
        effectiveness: float,
        timing: float
    ) -> float:
        """
        計算總體質量分數
        
        權重：
        - 連貫性：30%
        - 有效性：50%
        - 時機把握：20%
        """
        overall = (
            coherence * 0.3 +
            effectiveness * 0.5 +
            timing * 0.2
        )
        return round(overall, 2)
    
    def _generate_details(
        self,
        conversation: List[Dict],
        trust_history: List[Dict],
        coherence: float,
        effectiveness: float,
        timing: float
    ) -> Dict:
        """生成詳細分析"""
        return {
            "conversation_length": len(conversation),
            "main_topic": self._identify_main_topic(conversation),
            "turning_points": self._identify_turning_points(trust_history),
            "scores": {
                "coherence": coherence,
                "effectiveness": effectiveness,
                "timing": timing
            },
            "recommendations": self._generate_recommendations(
                coherence, effectiveness, timing
            )
        }
    
    def _generate_recommendations(
        self,
        coherence: float,
        effectiveness: float,
        timing: float
    ) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if coherence < 70:
            recommendations.append("提高對話連貫性：多使用邏輯連接詞，保持話題一致")
        
        if effectiveness < 70:
            recommendations.append("提高策略有效性：選擇更適合persona的策略")
        
        if timing < 70:
            recommendations.append("改善時機把握：在關鍵時刻使用強力策略")
        
        if not recommendations:
            recommendations.append("質量優秀，繼續保持！")
        
        return recommendations


# 使用示例
if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建評估器
    analyzer = ConversationQualityAnalyzer()
    
    # 測試數據
    conversation = [
        {"role": "scammer", "text": "你好，我係銀行職員，你嘅帳戶有問題。"},
        {"role": "victim", "text": "咩問題？"},
        {"role": "scammer", "text": "你嘅帳戶被凍結咗，需要立即處理。"},
        {"role": "expert", "text": "唔好驚，銀行唔會咁樣打電話嚟。"},
        {"role": "victim", "text": "但係佢話我帳戶有問題..."},
        {"role": "expert", "text": "呢個係詐騙手法，你應該掛斷電話，然後打去銀行官方熱線確認。"}
    ]
    
    trust_history = [
        {"trust_in_scammer": 50, "trust_in_expert": 50, "alertness": 50},
        {"trust_in_scammer": 55, "trust_in_expert": 50, "alertness": 45},
        {"trust_in_scammer": 60, "trust_in_expert": 50, "alertness": 40},
        {"trust_in_scammer": 55, "trust_in_expert": 55, "alertness": 50},
        {"trust_in_scammer": 50, "trust_in_expert": 60, "alertness": 55},
        {"trust_in_scammer": 40, "trust_in_expert": 70, "alertness": 65}
    ]
    
    # 分析對話質量
    quality_score = analyzer.analyze_conversation(conversation, trust_history)
    
    print(f"\n=== 對話質量分析結果 ===")
    print(f"連貫性: {quality_score.coherence:.1f}/100")
    print(f"有效性: {quality_score.effectiveness:.1f}/100")
    print(f"時機把握: {quality_score.timing:.1f}/100")
    print(f"總體質量: {quality_score.overall:.1f}/100")
    print(f"\n改進建議:")
    for rec in quality_score.details["recommendations"]:
        print(f"  - {rec}")
