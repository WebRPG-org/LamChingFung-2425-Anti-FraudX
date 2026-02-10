"""
對話質量分析器
分析詐騙對話的質量、有效性和風險等級
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """質量指標"""
    overall_score: float  # 總體質量分數 (0-100)
    effectiveness: float  # 有效性 (0-100)
    risk_level: str  # 風險等級 (low/medium/high/critical)
    coherence: float  # 連貫性 (0-100)
    persuasiveness: float  # 說服力 (0-100)
    professionalism: float  # 專業度 (0-100)
    urgency_level: float  # 緊迫感 (0-100)
    emotional_manipulation: float  # 情感操控程度 (0-100)
    red_flags: List[str]  # 危險信號列表
    strengths: List[str]  # 優勢列表
    weaknesses: List[str]  # 弱點列表
    recommendations: List[str]  # 改進建議


class ConversationQualityAnalyzer:
    """對話質量分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 危險信號關鍵詞
        self.red_flag_keywords = {
            "authority": ["警察", "銀行", "政府", "法院", "檢察官"],
            "urgency": ["立即", "馬上", "緊急", "現在", "快"],
            "threat": ["凍結", "逮捕", "罰款", "起訴", "坐牢"],
            "secrecy": ["不要告訴", "保密", "秘密", "私下"],
            "money": ["轉帳", "匯款", "帳號", "密碼", "驗證碼"],
            "pressure": ["必須", "一定要", "否則", "後果", "責任"]
        }
        
        # 說服技巧
        self.persuasion_techniques = {
            "authority": "權威訴求",
            "urgency": "緊迫性",
            "sympathy": "情感共鳴",
            "greed": "利益誘惑",
            "fear": "恐懼訴求",
            "social_proof": "社會認同"
        }
        
        logger.info("✅ 對話質量分析器已初始化")
    
    def analyze_conversation(
        self,
        conversation_history: List[Dict],
        evaluation_result: Optional[Dict] = None
    ) -> QualityMetrics:
        """
        分析對話質量
        
        Args:
            conversation_history: 對話歷史
            evaluation_result: 評估結果（可選）
        
        Returns:
            QualityMetrics對象
        """
        logger.info(f"📊 開始分析對話質量 - 訊息數={len(conversation_history)}")
        
        # 1. 提取詐騙者訊息
        scammer_messages = [
            msg for msg in conversation_history
            if msg.get("role") == "scammer"
        ]
        
        if not scammer_messages:
            logger.warning("⚠️ 沒有詐騙者訊息")
            return self._get_default_metrics()
        
        # 2. 分析各個維度
        coherence = self._analyze_coherence(conversation_history)
        persuasiveness = self._analyze_persuasiveness(scammer_messages)
        professionalism = self._analyze_professionalism(scammer_messages)
        urgency = self._analyze_urgency(scammer_messages)
        emotional_manipulation = self._analyze_emotional_manipulation(scammer_messages)
        
        # 3. 檢測危險信號
        red_flags = self._detect_red_flags(scammer_messages)
        
        # 4. 識別優勢和弱點
        strengths = self._identify_strengths(scammer_messages, conversation_history)
        weaknesses = self._identify_weaknesses(scammer_messages, conversation_history)
        
        # 5. 計算有效性
        effectiveness = self._calculate_effectiveness(
            evaluation_result,
            persuasiveness,
            urgency,
            emotional_manipulation
        )
        
        # 6. 計算總體分數
        overall_score = self._calculate_overall_score(
            coherence,
            persuasiveness,
            professionalism,
            effectiveness
        )
        
        # 7. 評估風險等級
        risk_level = self._assess_risk_level(
            red_flags,
            urgency,
            emotional_manipulation,
            effectiveness
        )
        
        # 8. 生成建議
        recommendations = self._generate_recommendations(
            weaknesses,
            coherence,
            persuasiveness,
            professionalism
        )
        
        metrics = QualityMetrics(
            overall_score=round(overall_score, 2),
            effectiveness=round(effectiveness, 2),
            risk_level=risk_level,
            coherence=round(coherence, 2),
            persuasiveness=round(persuasiveness, 2),
            professionalism=round(professionalism, 2),
            urgency_level=round(urgency, 2),
            emotional_manipulation=round(emotional_manipulation, 2),
            red_flags=red_flags,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
        
        logger.info(
            f"✅ 質量分析完成 - "
            f"總分={overall_score:.1f}, "
            f"風險={risk_level}, "
            f"有效性={effectiveness:.1f}"
        )
        
        return metrics
    
    def _analyze_coherence(self, conversation_history: List[Dict]) -> float:
        """分析對話連貫性"""
        if len(conversation_history) < 2:
            return 50.0
        
        score = 70.0  # 基礎分數
        
        # 檢查對話流暢度
        for i in range(len(conversation_history) - 1):
            current = conversation_history[i]
            next_msg = conversation_history[i + 1]
            
            # 檢查角色交替
            if current.get("role") == next_msg.get("role"):
                score -= 5  # 同一角色連續發言，降低連貫性
            
            # 檢查回應相關性（簡單的關鍵詞匹配）
            if next_msg.get("role") == "victim":
                current_content = current.get("content", "").lower()
                next_content = next_msg.get("content", "").lower()
                
                # 如果受害人的回應與詐騙者的訊息相關
                if any(word in next_content for word in current_content.split()[:5]):
                    score += 5
        
        return max(0, min(100, score))
    
    def _analyze_persuasiveness(self, scammer_messages: List[Dict]) -> float:
        """分析說服力"""
        if not scammer_messages:
            return 0.0
        
        score = 0.0
        
        for msg in scammer_messages:
            content = msg.get("content", "")
            strategy = msg.get("strategy", "none")
            
            # 基於策略的基礎分數
            strategy_scores = {
                "authority": 20,
                "urgency": 18,
                "fear": 17,
                "sympathy": 16,
                "greed": 15,
                "none": 5
            }
            score += strategy_scores.get(strategy, 5)
            
            # 檢查說服技巧
            if any(keyword in content for keyword in ["證明", "證據", "文件"]):
                score += 5  # 提供證據
            
            if any(keyword in content for keyword in ["幫助", "協助", "配合"]):
                score += 3  # 尋求配合
            
            if len(content) > 50:
                score += 2  # 詳細說明
        
        # 平均分數
        avg_score = score / len(scammer_messages)
        return min(100, avg_score)
    
    def _analyze_professionalism(self, scammer_messages: List[Dict]) -> float:
        """分析專業度"""
        if not scammer_messages:
            return 0.0
        
        score = 50.0  # 基礎分數
        
        for msg in scammer_messages:
            content = msg.get("content", "")
            
            # 正面因素
            if any(keyword in content for keyword in ["您", "請", "謝謝"]):
                score += 5  # 禮貌用語
            
            if any(keyword in content for keyword in ["銀行", "公司", "部門", "編號"]):
                score += 3  # 專業術語
            
            # 負面因素
            if any(keyword in content for keyword in ["快", "趕緊", "馬上"]):
                score -= 3  # 過於急迫
            
            if "!" in content or "！" in content:
                score -= 2  # 過多感嘆號
            
            if content.isupper():
                score -= 5  # 全大寫
        
        return max(0, min(100, score / len(scammer_messages) * 2))
    
    def _analyze_urgency(self, scammer_messages: List[Dict]) -> float:
        """分析緊迫感"""
        if not scammer_messages:
            return 0.0
        
        urgency_keywords = ["立即", "馬上", "緊急", "現在", "快", "趕緊", "立刻"]
        time_keywords = ["今天", "現在", "馬上", "24小時", "截止"]
        
        score = 0.0
        
        for msg in scammer_messages:
            content = msg.get("content", "")
            strategy = msg.get("strategy", "")
            
            # 策略為urgency
            if strategy == "urgency":
                score += 30
            
            # 緊迫關鍵詞
            urgency_count = sum(1 for keyword in urgency_keywords if keyword in content)
            score += urgency_count * 10
            
            # 時間限制
            time_count = sum(1 for keyword in time_keywords if keyword in content)
            score += time_count * 8
        
        return min(100, score / len(scammer_messages))
    
    def _analyze_emotional_manipulation(self, scammer_messages: List[Dict]) -> float:
        """分析情感操控程度"""
        if not scammer_messages:
            return 0.0
        
        emotional_keywords = {
            "fear": ["危險", "風險", "損失", "後果", "嚴重"],
            "sympathy": ["可憐", "幫助", "困難", "不容易"],
            "guilt": ["責任", "義務", "應該", "必須"],
            "greed": ["獎金", "優惠", "賺錢", "收益", "回報"]
        }
        
        score = 0.0
        
        for msg in scammer_messages:
            content = msg.get("content", "")
            strategy = msg.get("strategy", "")
            
            # 基於策略
            if strategy in ["sympathy", "fear", "greed"]:
                score += 25
            
            # 檢查情感關鍵詞
            for emotion_type, keywords in emotional_keywords.items():
                count = sum(1 for keyword in keywords if keyword in content)
                score += count * 8
        
        return min(100, score / len(scammer_messages))
    
    def _detect_red_flags(self, scammer_messages: List[Dict]) -> List[str]:
        """檢測危險信號"""
        red_flags = []
        
        for msg in scammer_messages:
            content = msg.get("content", "")
            
            # 檢查各類危險信號
            for flag_type, keywords in self.red_flag_keywords.items():
                if any(keyword in content for keyword in keywords):
                    flag_desc = {
                        "authority": "冒充權威機構",
                        "urgency": "製造緊迫感",
                        "threat": "威脅恐嚇",
                        "secrecy": "要求保密",
                        "money": "索要金錢或敏感信息",
                        "pressure": "施加壓力"
                    }
                    
                    flag_text = flag_desc.get(flag_type, flag_type)
                    if flag_text not in red_flags:
                        red_flags.append(flag_text)
        
        return red_flags
    
    def _identify_strengths(
        self,
        scammer_messages: List[Dict],
        conversation_history: List[Dict]
    ) -> List[str]:
        """識別優勢"""
        strengths = []
        
        # 檢查策略多樣性
        strategies = set(msg.get("strategy", "none") for msg in scammer_messages)
        if len(strategies) > 2:
            strengths.append("使用多種策略")
        
        # 檢查對話長度
        if len(scammer_messages) >= 3:
            strengths.append("持續施壓")
        
        # 檢查專業術語
        professional_terms = ["銀行", "帳戶", "系統", "部門", "編號", "流程"]
        if any(
            any(term in msg.get("content", "") for term in professional_terms)
            for msg in scammer_messages
        ):
            strengths.append("使用專業術語")
        
        # 檢查情感訴求
        emotional_words = ["幫助", "協助", "理解", "擔心", "關心"]
        if any(
            any(word in msg.get("content", "") for word in emotional_words)
            for msg in scammer_messages
        ):
            strengths.append("情感共鳴")
        
        return strengths if strengths else ["無明顯優勢"]
    
    def _identify_weaknesses(
        self,
        scammer_messages: List[Dict],
        conversation_history: List[Dict]
    ) -> List[str]:
        """識別弱點"""
        weaknesses = []
        
        # 檢查過於簡短
        if any(len(msg.get("content", "")) < 20 for msg in scammer_messages):
            weaknesses.append("訊息過於簡短")
        
        # 檢查過於急迫
        urgency_keywords = ["立即", "馬上", "快"]
        if sum(
            sum(1 for keyword in urgency_keywords if keyword in msg.get("content", ""))
            for msg in scammer_messages
        ) > 3:
            weaknesses.append("過於急迫，容易引起懷疑")
        
        # 檢查缺乏細節
        if all(len(msg.get("content", "")) < 50 for msg in scammer_messages):
            weaknesses.append("缺乏具體細節")
        
        # 檢查受害人抵抗
        victim_messages = [
            msg for msg in conversation_history
            if msg.get("role") == "victim"
        ]
        
        resistance_keywords = ["詐騙", "報警", "不相信", "懷疑"]
        if any(
            any(keyword in msg.get("content", "") for keyword in resistance_keywords)
            for msg in victim_messages
        ):
            weaknesses.append("受害人產生懷疑")
        
        return weaknesses if weaknesses else ["無明顯弱點"]
    
    def _calculate_effectiveness(
        self,
        evaluation_result: Optional[Dict],
        persuasiveness: float,
        urgency: float,
        emotional_manipulation: float
    ) -> float:
        """計算有效性"""
        if evaluation_result:
            # 基於實際評估結果
            trust_change = evaluation_result.get("trust_change", 0)
            
            # 信任度下降越多，有效性越高
            if trust_change < 0:
                effectiveness = min(100, abs(trust_change) * 5)
            else:
                effectiveness = max(0, 50 - trust_change * 2)
        else:
            # 基於質量指標估算
            effectiveness = (
                persuasiveness * 0.4 +
                urgency * 0.3 +
                emotional_manipulation * 0.3
            )
        
        return effectiveness
    
    def _calculate_overall_score(
        self,
        coherence: float,
        persuasiveness: float,
        professionalism: float,
        effectiveness: float
    ) -> float:
        """計算總體質量分數"""
        overall = (
            coherence * 0.2 +
            persuasiveness * 0.3 +
            professionalism * 0.2 +
            effectiveness * 0.3
        )
        return overall
    
    def _assess_risk_level(
        self,
        red_flags: List[str],
        urgency: float,
        emotional_manipulation: float,
        effectiveness: float
    ) -> str:
        """評估風險等級"""
        risk_score = (
            len(red_flags) * 15 +
            urgency * 0.3 +
            emotional_manipulation * 0.3 +
            effectiveness * 0.4
        )
        
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self,
        weaknesses: List[str],
        coherence: float,
        persuasiveness: float,
        professionalism: float
    ) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if coherence < 60:
            recommendations.append("提高對話連貫性，確保邏輯流暢")
        
        if persuasiveness < 60:
            recommendations.append("增強說服力，使用更多證據和細節")
        
        if professionalism < 60:
            recommendations.append("提升專業度，使用正式語言和術語")
        
        if "訊息過於簡短" in weaknesses:
            recommendations.append("增加訊息長度，提供更多信息")
        
        if "過於急迫" in weaknesses:
            recommendations.append("降低緊迫感，避免引起懷疑")
        
        if "受害人產生懷疑" in weaknesses:
            recommendations.append("調整策略，重建信任")
        
        if not recommendations:
            recommendations.append("質量良好，繼續保持")
        
        return recommendations
    
    def _get_default_metrics(self) -> QualityMetrics:
        """獲取默認指標"""
        return QualityMetrics(
            overall_score=0.0,
            effectiveness=0.0,
            risk_level="low",
            coherence=0.0,
            persuasiveness=0.0,
            professionalism=0.0,
            urgency_level=0.0,
            emotional_manipulation=0.0,
            red_flags=[],
            strengths=[],
            weaknesses=["無對話數據"],
            recommendations=["需要提供對話數據"]
        )
    
    def generate_quality_report(self, metrics: QualityMetrics) -> str:
        """生成質量報告"""
        report = f"""
對話質量分析報告
{'='*60}

總體評分: {metrics.overall_score:.1f}/100
風險等級: {metrics.risk_level.upper()}
有效性: {metrics.effectiveness:.1f}/100

詳細指標:
  - 連貫性: {metrics.coherence:.1f}/100
  - 說服力: {metrics.persuasiveness:.1f}/100
  - 專業度: {metrics.professionalism:.1f}/100
  - 緊迫感: {metrics.urgency_level:.1f}/100
  - 情感操控: {metrics.emotional_manipulation:.1f}/100

危險信號 ({len(metrics.red_flags)}):
{chr(10).join(f'  - {flag}' for flag in metrics.red_flags) if metrics.red_flags else '  無'}

優勢 ({len(metrics.strengths)}):
{chr(10).join(f'  - {strength}' for strength in metrics.strengths)}

弱點 ({len(metrics.weaknesses)}):
{chr(10).join(f'  - {weakness}' for weakness in metrics.weaknesses)}

改進建議:
{chr(10).join(f'  {i+1}. {rec}' for i, rec in enumerate(metrics.recommendations))}

{'='*60}
"""
        return report


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ConversationQualityAnalyzer()
    
    # 示例對話
    conversation = [
        {"role": "scammer", "content": "你好，我是警察局的，你的銀行帳戶涉嫌洗錢！", "strategy": "authority"},
        {"role": "victim", "content": "什麼？我沒有做違法的事啊！"},
        {"role": "scammer", "content": "現在必須立即配合調查，否則會凍結你所有資產！", "strategy": "urgency"}
    ]
    
    metrics = analyzer.analyze_conversation(conversation)
    report = analyzer.generate_quality_report(metrics)
    
    print(report)
