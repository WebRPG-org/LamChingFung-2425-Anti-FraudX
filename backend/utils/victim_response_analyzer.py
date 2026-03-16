"""
受害人回應分析器
分析受害人的回應，識別抵抗信號和情緒狀態
"""

from typing import Dict, List
import re
import logging

logger = logging.getLogger(__name__)


class VictimResponseAnalyzer:
    """
    受害人回應分析器
    
    識別受害人回應中的關鍵信號：
    - 抵抗信號（懷疑、拒絕、警覺）
    - 配合信號（相信、同意、行動）
    - 情緒狀態（焦慮、冷靜、懷疑、恐慌）
    """
    
    # 抵抗信號關鍵詞
    RESISTANCE_KEYWORDS = {
        "strong": [
            "詐騙", "騙子", "騙人", "假的", "呃人",
            "報警", "投訴", "舉報", "錄音", "報案"
        ],
        "moderate": [
            "不相信", "不信", "唔信", "懷疑", "奇怪",
            "有問題", "點解", "為什麼", "證明", "證據"
        ],
        "weak": [
            "考慮", "想想", "等等", "慢慢", "確認",
            "問問", "查查", "睇睇", "了解", "研究"
        ]
    }
    
    # 配合信號關鍵詞
    COMPLIANCE_KEYWORDS = {
        "strong": [
            "好的", "明白", "我會", "馬上", "立即",
            "現在就", "即刻", "幫我", "怎麼辦", "點算"
        ],
        "moderate": [
            "係咪", "真係", "是嗎", "這樣啊", "原來",
            "那我", "咁我", "應該", "可以"
        ],
        "weak": [
            "哦", "嗯", "好吧", "知道了", "了解"
        ]
    }
    
    # 情緒關鍵詞
    EMOTION_KEYWORDS = {
        "anxious": ["擔心", "驚", "害怕", "緊張", "不安"],
        "panicked": ["怎麼辦", "點算", "完了", "糟糕", "嚴重"],
        "suspicious": ["騙", "假", "奇怪", "有問題", "不對"],
        "calm": ["冷靜", "慢慢", "不急", "想想", "考慮"]
    }
    
    def __init__(self):
        self.analysis_history: List[Dict] = []
    
    def analyze_response(self, response: str, context: Dict = None) -> Dict:
        """
        分析受害人回應
        
        Args:
            response: 受害人的回應文本
            context: 上下文信息（可選）
                - previous_scammer_message: 之前的詐騙訊息
                - previous_expert_message: 之前的專家訊息
                - current_trust: 當前信任度
        
        Returns:
            分析結果字典
        """
        if not response or not response.strip():
            return self._get_default_analysis()
        
        analysis = {
            "response": response[:100],
            "resistance_level": "none",
            "resistance_score": 0,  # 0-100
            "compliance_level": "none",
            "compliance_score": 0,  # 0-100
            "emotion": "neutral",
            "emotion_confidence": 0,  # 0-100
            "alertness_change": 0,  # -20 to +20
            "trust_impact": {
                "scammer": 0,  # -20 to +20
                "expert": 0    # -20 to +20
            },
            "signals": []
        }
        
        # 1. 檢測抵抗信號
        resistance_result = self._detect_resistance(response)
        analysis["resistance_level"] = resistance_result["level"]
        analysis["resistance_score"] = resistance_result["score"]
        analysis["signals"].extend(resistance_result["signals"])
        
        # 2. 檢測配合信號
        compliance_result = self._detect_compliance(response)
        analysis["compliance_level"] = compliance_result["level"]
        analysis["compliance_score"] = compliance_result["score"]
        analysis["signals"].extend(compliance_result["signals"])
        
        # 3. 檢測情緒狀態
        emotion_result = self._detect_emotion(response)
        analysis["emotion"] = emotion_result["emotion"]
        analysis["emotion_confidence"] = emotion_result["confidence"]
        
        # 4. 計算影響
        impact = self._calculate_impact(
            resistance_result,
            compliance_result,
            emotion_result,
            context
        )
        analysis["alertness_change"] = impact["alertness_change"]
        analysis["trust_impact"] = impact["trust_impact"]
        
        # 5. 記錄歷史
        self.analysis_history.append(analysis)
        
        logger.info(
            f"📊 受害人回應分析 - "
            f"抵抗:{analysis['resistance_level']}({analysis['resistance_score']}), "
            f"配合:{analysis['compliance_level']}({analysis['compliance_score']}), "
            f"情緒:{analysis['emotion']}"
        )
        
        return analysis
    
    def _detect_resistance(self, response: str) -> Dict:
        """檢測抵抗信號"""
        result = {
            "level": "none",
            "score": 0,
            "signals": []
        }
        
        response_lower = response.lower()
        
        # 檢查強抵抗
        for keyword in self.RESISTANCE_KEYWORDS["strong"]:
            if keyword in response_lower:
                result["signals"].append(f"強抵抗:{keyword}")
                result["score"] += 30
        
        # 檢查中度抵抗
        for keyword in self.RESISTANCE_KEYWORDS["moderate"]:
            if keyword in response_lower:
                result["signals"].append(f"中度抵抗:{keyword}")
                result["score"] += 15
        
        # 檢查弱抵抗
        for keyword in self.RESISTANCE_KEYWORDS["weak"]:
            if keyword in response_lower:
                result["signals"].append(f"弱抵抗:{keyword}")
                result["score"] += 5
        
        # 限制分數範圍
        result["score"] = min(100, result["score"])
        
        # 確定抵抗等級
        if result["score"] >= 60:
            result["level"] = "strong"
        elif result["score"] >= 30:
            result["level"] = "moderate"
        elif result["score"] > 0:
            result["level"] = "weak"
        
        return result
    
    def _detect_compliance(self, response: str) -> Dict:
        """檢測配合信號"""
        result = {
            "level": "none",
            "score": 0,
            "signals": []
        }
        
        response_lower = response.lower()
        
        # 檢查強配合
        for keyword in self.COMPLIANCE_KEYWORDS["strong"]:
            if keyword in response_lower:
                result["signals"].append(f"強配合:{keyword}")
                result["score"] += 30
        
        # 檢查中度配合
        for keyword in self.COMPLIANCE_KEYWORDS["moderate"]:
            if keyword in response_lower:
                result["signals"].append(f"中度配合:{keyword}")
                result["score"] += 15
        
        # 檢查弱配合
        for keyword in self.COMPLIANCE_KEYWORDS["weak"]:
            if keyword in response_lower:
                result["signals"].append(f"弱配合:{keyword}")
                result["score"] += 5
        
        # 限制分數範圍
        result["score"] = min(100, result["score"])
        
        # 確定配合等級
        if result["score"] >= 60:
            result["level"] = "strong"
        elif result["score"] >= 30:
            result["level"] = "moderate"
        elif result["score"] > 0:
            result["level"] = "weak"
        
        return result
    
    def _detect_emotion(self, response: str) -> Dict:
        """檢測情緒狀態"""
        result = {
            "emotion": "neutral",
            "confidence": 0
        }
        
        response_lower = response.lower()
        emotion_scores = {}
        
        # 計算每種情緒的分數
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(10 for keyword in keywords if keyword in response_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        # 選擇分數最高的情緒
        if emotion_scores:
            result["emotion"] = max(emotion_scores, key=emotion_scores.get)
            result["confidence"] = min(100, emotion_scores[result["emotion"]] * 2)
        
        return result
    
    def _calculate_impact(
        self,
        resistance: Dict,
        compliance: Dict,
        emotion: Dict,
        context: Dict = None
    ) -> Dict:
        """
        計算對信任度和警覺度的影響
        
        邏輯：
        - 強抵抗 → 警覺度+20, 對scammer信任-20
        - 強配合 → 警覺度-15, 對scammer信任+15
        - 情緒影響調整效果
        """
        impact = {
            "alertness_change": 0,
            "trust_impact": {
                "scammer": 0,
                "expert": 0
            }
        }
        
        # 1. 抵抗信號的影響
        if resistance["level"] == "strong":
            impact["alertness_change"] += 20
            impact["trust_impact"]["scammer"] -= 20
            impact["trust_impact"]["expert"] += 10
        elif resistance["level"] == "moderate":
            impact["alertness_change"] += 10
            impact["trust_impact"]["scammer"] -= 10
            impact["trust_impact"]["expert"] += 5
        elif resistance["level"] == "weak":
            impact["alertness_change"] += 5
            impact["trust_impact"]["scammer"] -= 5
        
        # 2. 配合信號的影響
        if compliance["level"] == "strong":
            impact["alertness_change"] -= 15
            impact["trust_impact"]["scammer"] += 15
            impact["trust_impact"]["expert"] -= 5
        elif compliance["level"] == "moderate":
            impact["alertness_change"] -= 8
            impact["trust_impact"]["scammer"] += 8
        elif compliance["level"] == "weak":
            impact["alertness_change"] -= 3
            impact["trust_impact"]["scammer"] += 3
        
        # 3. 情緒狀態的調整
        emotion_type = emotion["emotion"]
        if emotion_type == "anxious":
            # 焦慮時更容易被騙
            impact["trust_impact"]["scammer"] = int(impact["trust_impact"]["scammer"] * 1.2)
        elif emotion_type == "panicked":
            # 恐慌時大幅增加被騙風險
            impact["trust_impact"]["scammer"] = int(impact["trust_impact"]["scammer"] * 1.5)
        elif emotion_type == "suspicious":
            # 懷疑時更難被騙
            impact["trust_impact"]["scammer"] = int(impact["trust_impact"]["scammer"] * 0.5)
            impact["alertness_change"] = int(impact["alertness_change"] * 1.3)
        elif emotion_type == "calm":
            # 冷靜時理性判斷
            impact["alertness_change"] = int(impact["alertness_change"] * 1.2)
        
        # 4. 限制範圍
        impact["alertness_change"] = max(-20, min(20, impact["alertness_change"]))
        impact["trust_impact"]["scammer"] = max(-20, min(20, impact["trust_impact"]["scammer"]))
        impact["trust_impact"]["expert"] = max(-20, min(20, impact["trust_impact"]["expert"]))
        
        return impact
    
    def _get_default_analysis(self) -> Dict:
        """獲取默認分析結果（空回應時）"""
        return {
            "response": "",
            "resistance_level": "none",
            "resistance_score": 0,
            "compliance_level": "none",
            "compliance_score": 0,
            "emotion": "neutral",
            "emotion_confidence": 0,
            "alertness_change": 0,
            "trust_impact": {
                "scammer": 0,
                "expert": 0
            },
            "signals": []
        }
    
    def get_analysis_summary(self) -> Dict:
        """獲取分析摘要"""
        if not self.analysis_history:
            return {"status": "no_data"}
        
        total = len(self.analysis_history)
        
        # 統計抵抗和配合次數
        resistance_counts = {
            "strong": 0,
            "moderate": 0,
            "weak": 0,
            "none": 0
        }
        compliance_counts = {
            "strong": 0,
            "moderate": 0,
            "weak": 0,
            "none": 0
        }
        
        for analysis in self.analysis_history:
            resistance_counts[analysis["resistance_level"]] += 1
            compliance_counts[analysis["compliance_level"]] += 1
        
        return {
            "total_responses": total,
            "resistance_distribution": resistance_counts,
            "compliance_distribution": compliance_counts,
            "avg_resistance_score": sum(a["resistance_score"] for a in self.analysis_history) / total,
            "avg_compliance_score": sum(a["compliance_score"] for a in self.analysis_history) / total
        }


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = VictimResponseAnalyzer()
    
    # 測試案例
    test_cases = [
        "這是詐騙！我要報警！",
        "好的，我馬上去銀行",
        "讓我想想，我需要確認一下",
        "怎麼辦？我很擔心",
        "你說的有道理，但我還是不太相信"
    ]
    
    print("=== 受害人回應分析測試 ===\n")
    
    for i, response in enumerate(test_cases, 1):
        print(f"測試 {i}: {response}")
        result = analyzer.analyze_response(response)
        print(f"  抵抗: {result['resistance_level']} ({result['resistance_score']})")
        print(f"  配合: {result['compliance_level']} ({result['compliance_score']})")
        print(f"  情緒: {result['emotion']}")
        print(f"  警覺度變化: {result['alertness_change']:+d}")
        print(f"  信任度影響: scammer={result['trust_impact']['scammer']:+d}, expert={result['trust_impact']['expert']:+d}")
        print()
    
    # 顯示摘要
    summary = analyzer.get_analysis_summary()
    print("=== 分析摘要 ===")
    print(f"總回應數: {summary['total_responses']}")
    print(f"平均抵抗分數: {summary['avg_resistance_score']:.1f}")
    print(f"平均配合分數: {summary['avg_compliance_score']:.1f}")
