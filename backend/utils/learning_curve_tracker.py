"""
學習曲線追蹤器
追蹤詐騙者的學習進度和技能提升
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class LearningMetrics:
    """學習指標"""
    total_conversations: int  # 總對話數
    avg_effectiveness: float  # 平均有效性
    improvement_rate: float  # 改進率 (%)
    skill_level: str  # 技能等級 (beginner/intermediate/advanced/expert)
    strengths: List[str]  # 優勢領域
    weaknesses: List[str]  # 需改進領域
    learning_velocity: float  # 學習速度
    consistency_score: float  # 一致性分數
    recent_trend: str  # 最近趨勢 (improving/stable/declining)
    recommendations: List[str]  # 學習建議


class LearningCurveTracker:
    """學習曲線追蹤器"""
    
    def __init__(self, user_id: str = "default"):
        """
        初始化追蹤器
        
        Args:
            user_id: 用戶ID
        """
        self.user_id = user_id
        self.learning_history: List[Dict] = []
        
        # 技能等級閾值
        self.skill_thresholds = {
            "beginner": 0,
            "intermediate": 50,
            "advanced": 70,
            "expert": 85
        }
        
        logger.info(f"✅ 學習曲線追蹤器已初始化 - 用戶={user_id}")
    
    def record_session(
        self,
        conversation_history: List[Dict],
        evaluation_result: Dict,
        quality_metrics: Optional[Dict] = None
    ):
        """
        記錄學習會話
        
        Args:
            conversation_history: 對話歷史
            evaluation_result: 評估結果
            quality_metrics: 質量指標（可選）
        """
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "conversation_length": len(conversation_history),
            "trust_change": evaluation_result.get("trust_change", 0),
            "confidence": evaluation_result.get("confidence", 0),
            "method": evaluation_result.get("method", "unknown"),
            "quality_metrics": quality_metrics or {},
            "strategies_used": self._extract_strategies(conversation_history)
        }
        
        self.learning_history.append(session_data)
        
        logger.info(
            f"📝 記錄學習會話 - "
            f"會話數={len(self.learning_history)}, "
            f"信任度變化={session_data['trust_change']:+.2f}"
        )
    
    def analyze_learning_progress(
        self,
        time_window_days: int = 30
    ) -> LearningMetrics:
        """
        分析學習進度
        
        Args:
            time_window_days: 時間窗口（天）
        
        Returns:
            LearningMetrics對象
        """
        logger.info(f"📊 開始分析學習進度 - 時間窗口={time_window_days}天")
        
        if not self.learning_history:
            logger.warning("⚠️ 沒有學習歷史數據")
            return self._get_default_metrics()
        
        # 1. 過濾時間窗口內的數據
        cutoff_time = datetime.now() - timedelta(days=time_window_days)
        recent_sessions = [
            s for s in self.learning_history
            if datetime.fromisoformat(s["timestamp"]) >= cutoff_time
        ]
        
        if not recent_sessions:
            recent_sessions = self.learning_history[-10:]  # 至少取最近10次
        
        # 2. 計算平均有效性
        avg_effectiveness = self._calculate_avg_effectiveness(recent_sessions)
        
        # 3. 計算改進率
        improvement_rate = self._calculate_improvement_rate(recent_sessions)
        
        # 4. 評估技能等級
        skill_level = self._assess_skill_level(avg_effectiveness)
        
        # 5. 識別優勢和弱點
        strengths, weaknesses = self._identify_strengths_weaknesses(recent_sessions)
        
        # 6. 計算學習速度
        learning_velocity = self._calculate_learning_velocity(recent_sessions)
        
        # 7. 計算一致性
        consistency_score = self._calculate_consistency(recent_sessions)
        
        # 8. 分析趨勢
        recent_trend = self._analyze_trend(recent_sessions)
        
        # 9. 生成建議
        recommendations = self._generate_learning_recommendations(
            skill_level,
            improvement_rate,
            weaknesses,
            recent_trend
        )
        
        metrics = LearningMetrics(
            total_conversations=len(self.learning_history),
            avg_effectiveness=round(avg_effectiveness, 2),
            improvement_rate=round(improvement_rate, 2),
            skill_level=skill_level,
            strengths=strengths,
            weaknesses=weaknesses,
            learning_velocity=round(learning_velocity, 2),
            consistency_score=round(consistency_score, 2),
            recent_trend=recent_trend,
            recommendations=recommendations
        )
        
        logger.info(
            f"✅ 學習進度分析完成 - "
            f"技能等級={skill_level}, "
            f"改進率={improvement_rate:+.1f}%, "
            f"趨勢={recent_trend}"
        )
        
        return metrics
    
    def _extract_strategies(self, conversation_history: List[Dict]) -> List[str]:
        """提取使用的策略"""
        strategies = []
        for msg in conversation_history:
            if msg.get("role") == "scammer":
                strategy = msg.get("strategy", "none")
                if strategy != "none":
                    strategies.append(strategy)
        return strategies
    
    def _calculate_avg_effectiveness(self, sessions: List[Dict]) -> float:
        """計算平均有效性"""
        if not sessions:
            return 0.0
        
        total_effectiveness = 0.0
        
        for session in sessions:
            trust_change = session.get("trust_change", 0)
            
            # 信任度下降越多，有效性越高
            if trust_change < 0:
                effectiveness = min(100, abs(trust_change) * 5)
            else:
                effectiveness = max(0, 50 - trust_change * 2)
            
            total_effectiveness += effectiveness
        
        return total_effectiveness / len(sessions)
    
    def _calculate_improvement_rate(self, sessions: List[Dict]) -> float:
        """計算改進率"""
        if len(sessions) < 2:
            return 0.0
        
        # 比較前半部分和後半部分
        mid_point = len(sessions) // 2
        first_half = sessions[:mid_point]
        second_half = sessions[mid_point:]
        
        avg_first = self._calculate_avg_effectiveness(first_half)
        avg_second = self._calculate_avg_effectiveness(second_half)
        
        if avg_first == 0:
            return 0.0
        
        improvement = ((avg_second - avg_first) / avg_first) * 100
        
        return improvement
    
    def _assess_skill_level(self, avg_effectiveness: float) -> str:
        """評估技能等級"""
        if avg_effectiveness >= self.skill_thresholds["expert"]:
            return "expert"
        elif avg_effectiveness >= self.skill_thresholds["advanced"]:
            return "advanced"
        elif avg_effectiveness >= self.skill_thresholds["intermediate"]:
            return "intermediate"
        else:
            return "beginner"
    
    def _identify_strengths_weaknesses(
        self,
        sessions: List[Dict]
    ) -> tuple[List[str], List[str]]:
        """識別優勢和弱點"""
        strengths = []
        weaknesses = []
        
        # 分析策略使用
        all_strategies = []
        for session in sessions:
            all_strategies.extend(session.get("strategies_used", []))
        
        if all_strategies:
            from collections import Counter
            strategy_counts = Counter(all_strategies)
            most_common = strategy_counts.most_common(2)
            
            if most_common:
                strengths.append(f"擅長使用{most_common[0][0]}策略")
            
            # 檢查策略多樣性
            if len(strategy_counts) < 3:
                weaknesses.append("策略多樣性不足")
        
        # 分析一致性
        trust_changes = [s.get("trust_change", 0) for s in sessions]
        if trust_changes:
            import statistics
            std_dev = statistics.stdev(trust_changes) if len(trust_changes) > 1 else 0
            
            if std_dev < 5:
                strengths.append("表現穩定一致")
            elif std_dev > 15:
                weaknesses.append("表現波動較大")
        
        # 分析對話長度
        avg_length = sum(s.get("conversation_length", 0) for s in sessions) / len(sessions)
        
        if avg_length < 3:
            weaknesses.append("對話過於簡短")
        elif avg_length > 5:
            strengths.append("善於持續施壓")
        
        # 分析質量指標
        quality_scores = [
            s.get("quality_metrics", {}).get("overall_score", 0)
            for s in sessions
            if s.get("quality_metrics")
        ]
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            if avg_quality > 70:
                strengths.append("對話質量高")
            elif avg_quality < 50:
                weaknesses.append("對話質量需提升")
        
        return (
            strengths if strengths else ["持續學習中"],
            weaknesses if weaknesses else ["無明顯弱點"]
        )
    
    def _calculate_learning_velocity(self, sessions: List[Dict]) -> float:
        """計算學習速度"""
        if len(sessions) < 5:
            return 0.0
        
        # 使用線性回歸計算趨勢斜率
        x = list(range(len(sessions)))
        y = []
        
        for session in sessions:
            trust_change = session.get("trust_change", 0)
            effectiveness = min(100, abs(trust_change) * 5) if trust_change < 0 else max(0, 50 - trust_change * 2)
            y.append(effectiveness)
        
        # 簡單線性回歸
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        return slope
    
    def _calculate_consistency(self, sessions: List[Dict]) -> float:
        """計算一致性分數"""
        if len(sessions) < 2:
            return 50.0
        
        trust_changes = [s.get("trust_change", 0) for s in sessions]
        
        import statistics
        mean = statistics.mean(trust_changes)
        std_dev = statistics.stdev(trust_changes) if len(trust_changes) > 1 else 0
        
        # 標準差越小，一致性越高
        consistency = max(0, 100 - std_dev * 5)
        
        return consistency
    
    def _analyze_trend(self, sessions: List[Dict]) -> str:
        """分析最近趨勢"""
        if len(sessions) < 3:
            return "stable"
        
        # 比較最近3次和之前的平均值
        recent = sessions[-3:]
        previous = sessions[:-3] if len(sessions) > 3 else sessions
        
        recent_avg = self._calculate_avg_effectiveness(recent)
        previous_avg = self._calculate_avg_effectiveness(previous)
        
        diff = recent_avg - previous_avg
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _generate_learning_recommendations(
        self,
        skill_level: str,
        improvement_rate: float,
        weaknesses: List[str],
        recent_trend: str
    ) -> List[str]:
        """生成學習建議"""
        recommendations = []
        
        # 基於技能等級
        if skill_level == "beginner":
            recommendations.append("建議學習基礎詐騙策略和話術")
            recommendations.append("多練習權威和緊急策略的組合")
        elif skill_level == "intermediate":
            recommendations.append("嘗試更複雜的策略組合")
            recommendations.append("提高對話的專業度和連貫性")
        elif skill_level == "advanced":
            recommendations.append("精煉現有技能，提高一致性")
            recommendations.append("學習高級情感操控技巧")
        else:  # expert
            recommendations.append("保持當前水平，繼續創新")
            recommendations.append("可以嘗試指導其他學習者")
        
        # 基於改進率
        if improvement_rate < 0:
            recommendations.append("最近表現下滑，建議回顧基礎知識")
        elif improvement_rate > 20:
            recommendations.append("進步快速，繼續保持學習節奏")
        
        # 基於弱點
        for weakness in weaknesses:
            if "策略多樣性" in weakness:
                recommendations.append("嘗試使用更多不同類型的策略")
            elif "波動" in weakness:
                recommendations.append("注重穩定性，建立標準流程")
            elif "簡短" in weakness:
                recommendations.append("增加對話輪次，提供更多細節")
            elif "質量" in weakness:
                recommendations.append("提升對話的專業度和說服力")
        
        # 基於趨勢
        if recent_trend == "declining":
            recommendations.append("最近表現下降，建議休息調整")
        elif recent_trend == "improving":
            recommendations.append("保持良好勢頭，繼續努力")
        
        return recommendations if recommendations else ["繼續練習，保持進步"]
    
    def _get_default_metrics(self) -> LearningMetrics:
        """獲取默認指標"""
        return LearningMetrics(
            total_conversations=0,
            avg_effectiveness=0.0,
            improvement_rate=0.0,
            skill_level="beginner",
            strengths=[],
            weaknesses=["需要開始練習"],
            learning_velocity=0.0,
            consistency_score=0.0,
            recent_trend="stable",
            recommendations=["開始第一次對話練習"]
        )
    
    def get_learning_curve_data(self) -> Dict:
        """獲取學習曲線數據（用於可視化）"""
        if not self.learning_history:
            return {"timestamps": [], "effectiveness": [], "trend": []}
        
        timestamps = []
        effectiveness_scores = []
        
        for session in self.learning_history:
            timestamps.append(session["timestamp"])
            
            trust_change = session.get("trust_change", 0)
            effectiveness = min(100, abs(trust_change) * 5) if trust_change < 0 else max(0, 50 - trust_change * 2)
            effectiveness_scores.append(effectiveness)
        
        # 計算移動平均（趨勢線）
        window_size = min(5, len(effectiveness_scores))
        trend = []
        
        for i in range(len(effectiveness_scores)):
            start = max(0, i - window_size + 1)
            window = effectiveness_scores[start:i+1]
            trend.append(sum(window) / len(window))
        
        return {
            "timestamps": timestamps,
            "effectiveness": effectiveness_scores,
            "trend": trend
        }
    
    def export_learning_data(self, filepath: str):
        """導出學習數據"""
        data = {
            "user_id": self.user_id,
            "export_time": datetime.now().isoformat(),
            "total_sessions": len(self.learning_history),
            "learning_history": self.learning_history,
            "learning_curve": self.get_learning_curve_data()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 學習數據已導出到 {filepath}")
    
    def generate_learning_report(self, metrics: LearningMetrics) -> str:
        """生成學習報告"""
        report = f"""
學習曲線分析報告
{'='*60}

用戶ID: {self.user_id}
總對話數: {metrics.total_conversations}

技能評估:
  - 技能等級: {metrics.skill_level.upper()}
  - 平均有效性: {metrics.avg_effectiveness:.1f}/100
  - 改進率: {metrics.improvement_rate:+.1f}%
  - 學習速度: {metrics.learning_velocity:.2f}
  - 一致性分數: {metrics.consistency_score:.1f}/100
  - 最近趨勢: {metrics.recent_trend.upper()}

優勢 ({len(metrics.strengths)}):
{chr(10).join(f'  ✓ {strength}' for strength in metrics.strengths)}

需改進 ({len(metrics.weaknesses)}):
{chr(10).join(f'  ✗ {weakness}' for weakness in metrics.weaknesses)}

學習建議:
{chr(10).join(f'  {i+1}. {rec}' for i, rec in enumerate(metrics.recommendations))}

{'='*60}
"""
        return report


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tracker = LearningCurveTracker(user_id="user_001")
    
    # 模擬多次學習會話
    for i in range(10):
        conversation = [
            {"role": "scammer", "content": f"測試訊息{i}", "strategy": "authority"},
            {"role": "victim", "content": "回應"}
        ]
        
        evaluation_result = {
            "trust_change": -10 - i,  # 逐漸改進
            "confidence": 80,
            "method": "rule"
        }
        
        tracker.record_session(conversation, evaluation_result)
    
    # 分析學習進度
    metrics = tracker.analyze_learning_progress()
    report = tracker.generate_learning_report(metrics)
    
    print(report)
