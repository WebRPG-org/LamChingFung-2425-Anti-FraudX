"""
學習曲線追蹤系統
追蹤模型性能、識別弱點、自動調整權重
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標"""
    timestamp: str
    accuracy: float  # 準確度 (0-100)
    avg_score: float  # 平均分數 (0-100)
    success_rate: float  # 成功率 (0-100)
    avg_response_time: float  # 平均響應時間（秒）
    total_sessions: int  # 總會話數
    metadata: Dict = field(default_factory=dict)


@dataclass
class WeaknessReport:
    """弱點報告"""
    category: str  # 弱點類別
    severity: str  # 嚴重程度 (low/medium/high)
    description: str  # 描述
    affected_personas: List[str]  # 受影響的persona
    suggested_fixes: List[str]  # 建議修復方案
    metrics: Dict  # 相關指標


@dataclass
class WeightAdjustment:
    """權重調整建議"""
    persona: str
    dimension: str  # 維度（empathy/evidence/clarity/actionability）
    current_weight: float
    suggested_weight: float
    reason: str
    expected_improvement: float  # 預期改進幅度


class LearningCurveTracker:
    """
    學習曲線追蹤器
    
    功能：
    1. 追蹤性能數據
    2. 識別系統弱點
    3. 自動權重調整建議
    4. 性能趨勢分析
    """
    
    def __init__(self, history_file: str = "performance_history.json"):
        """
        初始化追蹤器
        
        Args:
            history_file: 歷史數據文件路徑
        """
        self.history_file = history_file
        self.performance_history: List[PerformanceMetrics] = []
        self.weakness_history: List[WeaknessReport] = []
        
        # 嘗試加載歷史數據
        self._load_history()
        
        # 嘗試加載自適應權重優化器
        try:
            from utils.adaptive_scoring import AdaptiveWeightOptimizer
            self.weight_optimizer = AdaptiveWeightOptimizer()
            logger.info("✅ 自適應權重優化器已加載")
        except Exception as e:
            logger.warning(f"⚠️ 無法加載自適應權重優化器: {e}")
            self.weight_optimizer = None
        
        logger.info("🎯 學習曲線追蹤器初始化完成")
    
    def track_performance(
        self, 
        session_data: Dict,
        save: bool = True
    ) -> PerformanceMetrics:
        """
        追蹤性能數據
        
        Args:
            session_data: 會話數據
            save: 是否保存到文件
            
        Returns:
            PerformanceMetrics對象
        """
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            accuracy=session_data.get("accuracy", 0),
            avg_score=session_data.get("avg_score", 0),
            success_rate=session_data.get("success_rate", 0),
            avg_response_time=session_data.get("avg_response_time", 0),
            total_sessions=session_data.get("total_sessions", 1),
            metadata=session_data.get("metadata", {})
        )
        
        self.performance_history.append(metrics)
        
        logger.info(
            f"📊 性能追蹤: 準確度={metrics.accuracy:.1f}%, "
            f"成功率={metrics.success_rate:.1f}%, "
            f"平均分數={metrics.avg_score:.1f}"
        )
        
        if save:
            self._save_history()
        
        return metrics
    
    def identify_weaknesses(
        self, 
        recent_sessions: int = 10
    ) -> List[WeaknessReport]:
        """
        識別系統弱點
        
        Args:
            recent_sessions: 分析最近N個會話
            
        Returns:
            弱點報告列表
        """
        logger.info(f"🔍 識別系統弱點（最近{recent_sessions}個會話）")
        
        weaknesses = []
        
        if len(self.performance_history) < recent_sessions:
            logger.warning("⚠️ 歷史數據不足，無法進行弱點分析")
            return weaknesses
        
        recent_data = self.performance_history[-recent_sessions:]
        
        # 1. 檢查準確度下降
        accuracy_weakness = self._check_accuracy_decline(recent_data)
        if accuracy_weakness:
            weaknesses.append(accuracy_weakness)
        
        # 2. 檢查成功率問題
        success_rate_weakness = self._check_success_rate(recent_data)
        if success_rate_weakness:
            weaknesses.append(success_rate_weakness)
        
        # 3. 檢查響應時間問題
        response_time_weakness = self._check_response_time(recent_data)
        if response_time_weakness:
            weaknesses.append(response_time_weakness)
        
        # 4. 檢查persona特定問題
        persona_weaknesses = self._check_persona_performance(recent_data)
        weaknesses.extend(persona_weaknesses)
        
        # 保存弱點報告
        self.weakness_history.extend(weaknesses)
        
        logger.info(f"✅ 識別到 {len(weaknesses)} 個弱點")
        
        return weaknesses
    
    def suggest_weight_adjustments(
        self, 
        weaknesses: Optional[List[WeaknessReport]] = None
    ) -> List[WeightAdjustment]:
        """
        建議權重調整
        
        Args:
            weaknesses: 弱點報告列表（如果為None，使用最近的弱點）
            
        Returns:
            權重調整建議列表
        """
        logger.info("💡 生成權重調整建議")
        
        if weaknesses is None:
            weaknesses = self.weakness_history[-5:] if self.weakness_history else []
        
        if not weaknesses:
            logger.info("✅ 未發現需要調整的弱點")
            return []
        
        adjustments = []
        
        # 基於弱點生成調整建議
        for weakness in weaknesses:
            if weakness.category == "persona_performance":
                persona_adjustments = self._generate_persona_adjustments(weakness)
                adjustments.extend(persona_adjustments)
            elif weakness.category == "accuracy_decline":
                accuracy_adjustments = self._generate_accuracy_adjustments(weakness)
                adjustments.extend(accuracy_adjustments)
        
        logger.info(f"✅ 生成 {len(adjustments)} 個調整建議")
        
        return adjustments
    
    def get_performance_trend(
        self, 
        metric: str,
        window: int = 10
    ) -> List[float]:
        """
        獲取性能趨勢
        
        Args:
            metric: 指標名稱 (accuracy/avg_score/success_rate/avg_response_time)
            window: 時間窗口
            
        Returns:
            指標值列表
        """
        if not self.performance_history:
            return []
        
        recent_data = self.performance_history[-window:]
        
        trend = []
        for metrics in recent_data:
            if hasattr(metrics, metric):
                trend.append(getattr(metrics, metric))
        
        return trend
    
    def calculate_improvement_rate(
        self, 
        metric: str,
        window: int = 10
    ) -> float:
        """
        計算改進率
        
        Args:
            metric: 指標名稱
            window: 時間窗口
            
        Returns:
            改進率（百分比）
        """
        trend = self.get_performance_trend(metric, window)
        
        if len(trend) < 2:
            return 0.0
        
        # 計算線性回歸斜率
        n = len(trend)
        x = list(range(n))
        y = trend
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # 轉換為百分比改進率
        improvement_rate = (slope / y_mean) * 100 if y_mean != 0 else 0
        
        return round(improvement_rate, 2)
    
    def generate_performance_report(self) -> Dict:
        """
        生成性能報告
        
        Returns:
            完整的性能報告
        """
        logger.info("📋 生成性能報告")
        
        if not self.performance_history:
            return {
                "status": "no_data",
                "message": "沒有足夠的歷史數據"
            }
        
        latest = self.performance_history[-1]
        
        report = {
            "summary": {
                "latest_accuracy": latest.accuracy,
                "latest_success_rate": latest.success_rate,
                "latest_avg_score": latest.avg_score,
                "total_sessions": sum(m.total_sessions for m in self.performance_history),
                "tracking_period": {
                    "start": self.performance_history[0].timestamp,
                    "end": latest.timestamp
                }
            },
            "trends": {
                "accuracy": self.get_performance_trend("accuracy"),
                "success_rate": self.get_performance_trend("success_rate"),
                "avg_score": self.get_performance_trend("avg_score"),
                "response_time": self.get_performance_trend("avg_response_time")
            },
            "improvement_rates": {
                "accuracy": self.calculate_improvement_rate("accuracy"),
                "success_rate": self.calculate_improvement_rate("success_rate"),
                "avg_score": self.calculate_improvement_rate("avg_score")
            },
            "weaknesses": [
                {
                    "category": w.category,
                    "severity": w.severity,
                    "description": w.description
                }
                for w in self.weakness_history[-5:]
            ],
            "recommendations": self._generate_recommendations()
        }
        
        logger.info("✅ 性能報告生成完成")
        
        return report
    
    # ==================== 輔助方法 ====================
    
    def _load_history(self):
        """從文件加載歷史數據"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for item in data.get("performance_history", []):
                metrics = PerformanceMetrics(**item)
                self.performance_history.append(metrics)
            
            logger.info(f"✅ 加載 {len(self.performance_history)} 條歷史記錄")
        except FileNotFoundError:
            logger.info("📝 創建新的歷史記錄文件")
        except Exception as e:
            logger.error(f"❌ 加載歷史數據失敗: {e}")
    
    def _save_history(self):
        """保存歷史數據到文件"""
        try:
            data = {
                "performance_history": [
                    {
                        "timestamp": m.timestamp,
                        "accuracy": m.accuracy,
                        "avg_score": m.avg_score,
                        "success_rate": m.success_rate,
                        "avg_response_time": m.avg_response_time,
                        "total_sessions": m.total_sessions,
                        "metadata": m.metadata
                    }
                    for m in self.performance_history
                ]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug("💾 歷史數據已保存")
        except Exception as e:
            logger.error(f"❌ 保存歷史數據失敗: {e}")
    
    def _check_accuracy_decline(
        self, 
        recent_data: List[PerformanceMetrics]
    ) -> Optional[WeaknessReport]:
        """檢查準確度下降"""
        accuracies = [m.accuracy for m in recent_data]
        
        # 計算趨勢
        if len(accuracies) < 3:
            return None
        
        # 檢查是否持續下降
        declining = all(
            accuracies[i] >= accuracies[i+1] 
            for i in range(len(accuracies)-1)
        )
        
        if declining and accuracies[-1] < accuracies[0] - 5:
            return WeaknessReport(
                category="accuracy_decline",
                severity="high",
                description=f"準確度持續下降：{accuracies[0]:.1f}% → {accuracies[-1]:.1f}%",
                affected_personas=[],
                suggested_fixes=[
                    "檢查訓練數據質量",
                    "調整評分權重",
                    "增加訓練樣本"
                ],
                metrics={"accuracies": accuracies}
            )
        
        return None
    
    def _check_success_rate(
        self, 
        recent_data: List[PerformanceMetrics]
    ) -> Optional[WeaknessReport]:
        """檢查成功率問題"""
        success_rates = [m.success_rate for m in recent_data]
        avg_success_rate = sum(success_rates) / len(success_rates)
        
        if avg_success_rate < 70:
            return WeaknessReport(
                category="low_success_rate",
                severity="medium",
                description=f"平均成功率偏低：{avg_success_rate:.1f}%",
                affected_personas=[],
                suggested_fixes=[
                    "優化策略選擇",
                    "改進時機把握",
                    "增強專家建議質量"
                ],
                metrics={"success_rates": success_rates}
            )
        
        return None
    
    def _check_response_time(
        self, 
        recent_data: List[PerformanceMetrics]
    ) -> Optional[WeaknessReport]:
        """檢查響應時間問題"""
        response_times = [m.avg_response_time for m in recent_data]
        avg_response_time = sum(response_times) / len(response_times)
        
        if avg_response_time > 2.0:
            return WeaknessReport(
                category="slow_response",
                severity="low",
                description=f"平均響應時間過長：{avg_response_time:.2f}秒",
                affected_personas=[],
                suggested_fixes=[
                    "優化算法效率",
                    "減少不必要的計算",
                    "使用緩存機制"
                ],
                metrics={"response_times": response_times}
            )
        
        return None
    
    def _check_persona_performance(
        self, 
        recent_data: List[PerformanceMetrics]
    ) -> List[WeaknessReport]:
        """檢查persona特定性能問題"""
        weaknesses = []
        
        # 統計每個persona的表現
        persona_stats = {}
        
        for metrics in recent_data:
            metadata = metrics.metadata
            if "persona_results" in metadata:
                for persona, result in metadata["persona_results"].items():
                    if persona not in persona_stats:
                        persona_stats[persona] = []
                    persona_stats[persona].append(result.get("accuracy", 0))
        
        # 檢查每個persona
        for persona, accuracies in persona_stats.items():
            if not accuracies:
                continue
            
            avg_accuracy = sum(accuracies) / len(accuracies)
            
            if avg_accuracy < 85:
                weaknesses.append(WeaknessReport(
                    category="persona_performance",
                    severity="medium" if avg_accuracy < 80 else "low",
                    description=f"{persona}型表現不佳：平均準確度{avg_accuracy:.1f}%",
                    affected_personas=[persona],
                    suggested_fixes=[
                        f"調整{persona}型的權重配置",
                        f"增加{persona}型的訓練數據",
                        f"優化針對{persona}型的策略"
                    ],
                    metrics={"accuracies": accuracies}
                )
        
        return weaknesses
    
    def _generate_persona_adjustments(
        self, 
        weakness: WeaknessReport
    ) -> List[WeightAdjustment]:
        """生成persona相關的權重調整"""
        adjustments = []
        
        if not self.weight_optimizer:
            return adjustments
        
        for persona in weakness.affected_personas:
            # 獲取當前權重
            current_weights = self.weight_optimizer.get_expert_weights(persona)
            
            # 建議增加表現較差維度的權重
            for dimension, weight in current_weights.items():
                if weight < 0.3:  # 權重較低的維度
                    suggested_weight = min(0.4, weight + 0.1)
                    adjustments.append(WeightAdjustment(
                        persona=persona,
                        dimension=dimension,
                        current_weight=weight,
                        suggested_weight=suggested_weight,
                        reason=f"{persona}型在{dimension}維度表現不佳",
                        expected_improvement=5.0
                    ))
        
        return adjustments
    
    def _generate_accuracy_adjustments(
        self, 
        weakness: WeaknessReport
    ) -> List[WeightAdjustment]:
        """生成準確度相關的權重調整"""
        adjustments = []
        
        # 通用建議：增加evidence權重
        if self.weight_optimizer:
            for persona in ["elderly", "average", "overconfident", "student"]:
                current_weights = self.weight_optimizer.get_expert_weights(persona)
                evidence_weight = current_weights.get("evidence", 0.2)
                
                if evidence_weight < 0.35:
                    adjustments.append(WeightAdjustment(
                        persona=persona,
                        dimension="evidence",
                        current_weight=evidence_weight,
                        suggested_weight=min(0.4, evidence_weight + 0.05),
                        reason="提高證據權重以改善準確度",
                        expected_improvement=3.0
                    ))
        
        return adjustments
    
    def _generate_recommendations(self) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if not self.performance_history:
            return ["收集更多性能數據"]
        
        latest = self.performance_history[-1]
        
        # 基於最新性能生成建議
        if latest.accuracy < 90:
            recommendations.append("準確度低於90%，建議優化評分算法")
        
        if latest.success_rate < 80:
            recommendations.append("成功率低於80%，建議改進策略選擇")
        
        if latest.avg_response_time > 2.0:
            recommendations.append("響應時間過長，建議優化性能")
        
        # 基於趨勢生成建議
        accuracy_trend = self.calculate_improvement_rate("accuracy")
        if accuracy_trend < 0:
            recommendations.append("準確度呈下降趨勢，需要立即關注")
        
        if not recommendations:
            recommendations.append("系統運行良好，繼續保持！")
        
        return recommendations


# 使用示例
if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建追蹤器
    tracker = LearningCurveTracker()
    
    # 測試1: 追蹤性能
    print("\n=== 測試1: 追蹤性能 ===")
    session_data = {
        "accuracy": 95.0,
        "avg_score": 85.0,
        "success_rate": 90.0,
        "avg_response_time": 1.5,
        "total_sessions": 10
    }
    metrics = tracker.track_performance(session_data, save=False)
    print(f"準確度: {metrics.accuracy:.1f}%")
    print(f"成功率: {metrics.success_rate:.1f}%")
    
    # 測試2: 識別弱點
    print("\n=== 測試2: 識別弱點 ===")
    # 添加一些測試數據
    for i in range(10):
        tracker.track_performance({
            "accuracy": 95 - i * 0.5,  # 模擬下降趨勢
            "avg_score": 85,
            "success_rate": 90,
            "avg_response_time": 1.5,
            "total_sessions": 1
        }, save=False)
    
    weaknesses = tracker.identify_weaknesses(recent_sessions=10)
    print(f"發現 {len(weaknesses)} 個弱點:")
    for w in weaknesses:
        print(f"  - {w.category}: {w.description}")
    
    # 測試3: 權重調整建議
    print("\n=== 測試3: 權重調整建議 ===")
    adjustments = tracker.suggest_weight_adjustments(weaknesses)
    print(f"生成 {len(adjustments)} 個調整建議:")
    for adj in adjustments[:3]:
        print(f"  - {adj.persona}.{adj.dimension}: {adj.current_weight:.2f} → {adj.suggested_weight:.2f}")
    
    # 測試4: 性能報告
    print("\n=== 測試4: 性能報告 ===")
    report = tracker.generate_performance_report()
    print(f"總會話數: {report['summary']['total_sessions']}")
    print(f"最新準確度: {report['summary']['latest_accuracy']:.1f}%")
    print(f"準確度改進率: {report['improvement_rates']['accuracy']:.2f}%")
