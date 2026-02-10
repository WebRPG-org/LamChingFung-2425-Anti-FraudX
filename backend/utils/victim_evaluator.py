"""
受害人評估器 - 混合評分系統（重構版）
結合規則基礎評分和Agent主觀評分，統一評分語義
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

# 導入受害人回應分析器
try:
    from utils.victim_response_analyzer import VictimResponseAnalyzer
    RESPONSE_ANALYZER_AVAILABLE = True
except ImportError:
    RESPONSE_ANALYZER_AVAILABLE = False
    logging.warning("⚠️ VictimResponseAnalyzer 不可用，將使用簡化分析")

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """評估結果"""
    trust_change: float  # 最終信任度變化
    rule_score: Dict  # 規則評分結果
    agent_score: Dict  # Agent評分結果
    confidence: float  # 信心度 (0-100)
    method: str  # 評分方法 (rule/agent/hybrid)
    timestamp: str


class VictimEvaluator:
    """
    受害人評估器（混合方案）
    
    結合規則基礎評分和Agent主觀評分，提供更真實和準確的評估
    
    評分公式：
    最終分數 = 規則評分 × rule_weight + Agent評分 × agent_weight
    """
    
    def __init__(
        self, 
        victim_agent,
        performance_tracker,
        rule_weight: float = 0.7,
        agent_weight: float = 0.3,
        enable_agent_scoring: bool = True
    ):
        """
        初始化評估器
        
        Args:
            victim_agent: 受害人Agent實例
            performance_tracker: 性能追蹤器實例
            rule_weight: 規則評分權重（默認0.7）
            agent_weight: Agent評分權重（默認0.3）
            enable_agent_scoring: 是否啟用Agent評分（默認True）
        """
        self.victim_agent = victim_agent
        self.tracker = performance_tracker
        self.rule_weight = rule_weight
        self.agent_weight = agent_weight
        self.enable_agent_scoring = enable_agent_scoring
        
        # 初始化受害人回應分析器
        if RESPONSE_ANALYZER_AVAILABLE:
            self.response_analyzer = VictimResponseAnalyzer()
            logger.info("✅ 受害人回應分析器已啟用")
        else:
            self.response_analyzer = None
            logger.warning("⚠️ 受害人回應分析器未啟用")
        
        # 評估歷史
        self.evaluation_history: List[EvaluationResult] = []
        
        # 統計數據
        self.stats = {
            "total_evaluations": 0,
            "rule_only": 0,
            "agent_only": 0,
            "hybrid": 0,
            "avg_confidence": 0,
            "avg_difference": 0
        }
        
        logger.info(
            f"🎯 VictimEvaluator 初始化 - "
            f"規則權重={rule_weight}, Agent權重={agent_weight}, "
            f"Agent評分={'啟用' if enable_agent_scoring else '禁用'}"
        )
    
    async def evaluate_conversation(
        self,
        conversation_history: List[Dict],
        persona_type: str,
        initial_trust: int
    ) -> EvaluationResult:
        """
        評估整個對話（實驗用）
        
        Args:
            conversation_history: 對話歷史列表
            persona_type: 人設類型
            initial_trust: 初始信任度
            
        Returns:
            EvaluationResult對象
        """
        logger.info(f"📊 開始評估對話 - 人設={persona_type}, 初始信任={initial_trust}, 訊息數={len(conversation_history)}")
        
        # 累積信任度變化
        total_trust_change = 0
        rule_factors = []
        agent_factors = []
        
        # 逐條評估對話
        for i, msg in enumerate(conversation_history):
            role = msg.get("role", "")
            content = msg.get("content", "")
            strategy = msg.get("strategy", "none")
            
            # 只評估scammer和expert的訊息
            if role not in ["scammer", "expert"]:
                continue
            
            # 獲取受害人回應（下一條訊息）
            victim_response = ""
            if i + 1 < len(conversation_history):
                next_msg = conversation_history[i + 1]
                if next_msg.get("role") == "victim":
                    victim_response = next_msg.get("content", "")
            
            # 評估這條訊息
            result = await self.evaluate_message(
                message=content,
                sender=role,
                victim_response=victim_response,
                use_hybrid=(self.agent_weight > 0)
            )
            
            total_trust_change += result.trust_change
            rule_factors.append(result.rule_score)
            if result.agent_score:
                agent_factors.append(result.agent_score)
        
        # 計算平均信心度
        avg_confidence = sum(e.confidence for e in self.evaluation_history[-len(rule_factors):]) / len(rule_factors) if rule_factors else 0
        
        # 創建最終結果
        final_result = EvaluationResult(
            trust_change=round(total_trust_change, 2),
            rule_score={
                "total_change": total_trust_change,
                "factors": rule_factors,
                "count": len(rule_factors)
            },
            agent_score={
                "factors": agent_factors,
                "count": len(agent_factors)
            } if agent_factors else {},
            confidence=round(avg_confidence, 2),
            method="hybrid" if agent_factors else "rule",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ 對話評估完成 - 總變化={total_trust_change:+.2f}, 信心度={avg_confidence:.1f}%")
        
        return final_result
    
    async def evaluate_message(
        self, 
        message: str,
        sender: str,
        victim_response: str,
        use_hybrid: bool = True
    ) -> EvaluationResult:
        """
        評估訊息（主要方法）
        
        Args:
            message: 收到的訊息
            sender: 發送者（scammer/expert）
            victim_response: 受害者的回應
            use_hybrid: 是否使用混合評分（默認True）
            
        Returns:
            EvaluationResult對象
        """
        logger.info(f"📊 開始評估訊息 - 發送者={sender}, 混合={use_hybrid}")
        
        # 1. 規則評分（必須）
        rule_score = self._get_rule_score(message, sender, victim_response)
        
        # 2. Agent評分（可選）
        agent_score = None
        if self.enable_agent_scoring and use_hybrid:
            try:
                agent_score = await self._get_agent_score(message, sender)
            except Exception as e:
                logger.warning(f"⚠️ Agent評分失敗: {e}，使用規則評分")
                agent_score = None
        
        # 3. 計算最終分數
        if agent_score and use_hybrid:
            # 混合評分
            final_trust_change = (
                rule_score["trust_change"] * self.rule_weight +
                agent_score["trust_change"] * self.agent_weight
            )
            confidence = self._calculate_confidence(rule_score, agent_score)
            method = "hybrid"
            self.stats["hybrid"] += 1
        else:
            # 僅規則評分
            final_trust_change = rule_score["trust_change"]
            confidence = 85.0  # 規則評分的默認信心度
            method = "rule"
            self.stats["rule_only"] += 1
        
        # 4. 創建結果
        result = EvaluationResult(
            trust_change=round(final_trust_change, 2),
            rule_score=rule_score,
            agent_score=agent_score or {},
            confidence=confidence,
            method=method,
            timestamp=datetime.now().isoformat()
        )
        
        # 5. 記錄歷史
        self.evaluation_history.append(result)
        self.stats["total_evaluations"] += 1
        
        # 6. 更新統計
        self._update_stats(result)
        
        logger.info(
            f"✅ 評估完成 - 最終分數={final_trust_change:+.2f}, "
            f"信心度={confidence:.1f}%, 方法={method}"
        )
        
        return result
    
    def _get_rule_score(
        self, 
        message: str, 
        sender: str,
        victim_response: str
    ) -> Dict:
        """
        獲取規則評分（重構版 - 修復評分方向）
        
        整合受害人回應分析，統一評分語義
        
        重要：PerformanceTracker 的 trust_change 語義是"對sender的信任增加"
        我們需要轉換為"受害人警覺性變化"（實驗預期的語義）
        """
        # 1. 使用PerformanceTracker的基礎分析
        if sender == "scammer":
            base_analysis = self.tracker.analyze_scammer_turn(message, victim_response)
        elif sender == "expert":
            base_analysis = self.tracker.analyze_expert_turn(message, victim_response, message)
        else:
            logger.warning(f"⚠️ 未知發送者: {sender}")
            return {"trust_change": 0}
        
        # 2. 【關鍵修復】轉換評分方向
        # PerformanceTracker: trust_change > 0 表示"對scammer信任增加"（受害人更容易被騙）
        # 實驗預期: trust_change < 0 表示"受害人警覺性下降"（更容易被騙）
        # 因此需要反轉符號
        
        original_trust_change = base_analysis.get("trust_change", 0)
        
        if sender == "scammer":
            # Scammer的策略成功 → 受害人警覺性下降 → 負值
            # 原始: +5 (信任增加) → 轉換: -5 (警覺性下降)
            converted_trust_change = -original_trust_change
            
            logger.info(
                f"🔄 評分方向轉換 (Scammer): "
                f"原始={original_trust_change:+d} (信任度) → "
                f"轉換={converted_trust_change:+d} (警覺度)"
            )
        elif sender == "expert":
            # Expert的建議有效 → 受害人警覺性上升 → 正值
            # 原始: +10 (對expert信任增加) → 保持: +10 (警覺性上升)
            # 但同時應該降低對scammer的信任
            converted_trust_change = original_trust_change
            
            logger.info(
                f"🔄 評分方向轉換 (Expert): "
                f"原始={original_trust_change:+d} → "
                f"轉換={converted_trust_change:+d}"
            )
        else:
            converted_trust_change = 0
        
        # 更新分析結果
        base_analysis["original_trust_change"] = original_trust_change
        base_analysis["trust_change"] = converted_trust_change
        
        # 3. 如果有受害人回應分析器，進行深度分析
        if self.response_analyzer and victim_response:
            response_analysis = self.response_analyzer.analyze_response(
                victim_response,
                context={
                    "previous_scammer_message": message if sender == "scammer" else "",
                    "previous_expert_message": message if sender == "expert" else "",
                    "current_trust": getattr(self.tracker.victim_trust, 'trust_in_scammer', 50)
                }
            )
            
            # 4. 整合受害人回應的影響
            if sender == "scammer":
                # 如果受害人顯示強抵抗，增加警覺性（正值）
                if response_analysis["resistance_level"] == "strong":
                    # 強抵抗 → 大幅提升警覺性
                    resistance_boost = 15
                    converted_trust_change += resistance_boost
                    logger.info(f"📊 受害人強抵抗: 警覺性 +{resistance_boost}")
                    
                elif response_analysis["resistance_level"] == "moderate":
                    # 中度抵抗 → 中度提升警覺性
                    resistance_boost = 8
                    converted_trust_change += resistance_boost
                    logger.info(f"📊 受害人中度抵抗: 警覺性 +{resistance_boost}")
                
                # 如果受害人顯示強配合，降低警覺性（負值）
                elif response_analysis["compliance_level"] == "strong":
                    # 強配合 → 大幅降低警覺性
                    compliance_penalty = -10
                    converted_trust_change += compliance_penalty
                    logger.info(f"📊 受害人強配合: 警覺性 {compliance_penalty}")
                    
                elif response_analysis["compliance_level"] == "moderate":
                    # 中度配合 → 中度降低警覺性
                    compliance_penalty = -5
                    converted_trust_change += compliance_penalty
                    logger.info(f"📊 受害人中度配合: 警覺性 {compliance_penalty}")
            
            # 添加回應分析到結果中
            base_analysis["response_analysis"] = response_analysis
        
        # 5. 更新最終的trust_change
        base_analysis["trust_change"] = round(converted_trust_change)
        
        return base_analysis
    
    async def _get_agent_score(self, message: str, sender: str) -> Dict:
        """
        獲取Agent評分
        
        讓受害人Agent自己評估訊息
        """
        # 構建評估prompt
        prompt = self._build_evaluation_prompt(message, sender)
        
        # 調用Agent（修復異步生成器問題）
        try:
            # run_async 返回異步生成器，需要迭代收集
            response_parts = []
            async for chunk in self.victim_agent.run_async(prompt):
                # 提取文本內容
                if hasattr(chunk, 'text'):
                    response_parts.append(chunk.text)
                elif hasattr(chunk, 'content'):
                    response_parts.append(chunk.content)
                elif hasattr(chunk, 'parts'):
                    # 處理 Content 對象
                    for part in chunk.parts:
                        if hasattr(part, 'text'):
                            response_parts.append(part.text)
                else:
                    response_parts.append(str(chunk))
            
            response_text = ''.join(response_parts).strip()
            
            if not response_text:
                logger.warning("⚠️ Agent返回空回應")
                return self._get_default_agent_score()
                
        except Exception as e:
            logger.warning(f"⚠️ Agent調用失敗: {e}")
            return self._get_default_agent_score()
        
        # 解析回應
        agent_score = self._parse_agent_response(response_text)
        
        return agent_score
    
    def _build_evaluation_prompt(self, message: str, sender: str) -> str:
        """
        構建評估prompt（優化版）
        
        根據persona特徵定制prompt，明確評分方向
        """
        # 獲取persona信息
        persona_type = getattr(self.victim_agent, 'persona_type', 'average')
        
        # Persona特徵描述
        persona_traits = {
            "elderly": "你是一位長者（陳婆婆），對權威比較信任，容易被緊急情況影響，但也會擔心被騙。",
            "average": "你是一位普通市民（張文軒），會理性思考，但也可能被專業的說法影響。",
            "overconfident": "你是一位過度自信的人（李俊傑），不太相信權威，但對激將法敏感。",
            "student": "你是一位學生（王小明），對新事物接受度高，但經驗不足，容易被優惠吸引。"
        }
        
        trait = persona_traits.get(persona_type, persona_traits["average"])
        
        # 發送者描述
        sender_desc = {
            "scammer": "一個自稱是銀行/政府/警察的陌生人",
            "expert": "一個防詐騙專家"
        }
        
        # 優化後的prompt - 更清晰的指示和示例
        prompt = f"""你是{trait}

現在你收到來自{sender_desc.get(sender, '某人')}的訊息：

"{message}"

請根據你的性格特點，評估這個訊息對你的影響。

評估標準：
1. 警覺度變化：這個訊息會讓你的警覺性增加還是減少？
   - 如果訊息讓你起疑心、覺得不對勁 → 正數（+1到+10）
   - 如果訊息讓你放鬆警惕、相信對方 → 負數（-10到-1）
   - 如果沒什麼影響 → 0

2. 可信度：你覺得這個訊息的可信度有多高？（0-100）

3. 說服力：這個訊息的說服力有多強？（0-100）

4. 情緒影響：這個訊息讓你感到什麼？
   - calm（冷靜）
   - anxious（焦慮）
   - suspicious（懷疑）
   - panicked（恐慌）

5. 決定：你會相信這個訊息嗎？
   - believe（相信）
   - doubt（懷疑）
   - uncertain（不確定）

請嚴格按照以下JSON格式回答（只輸出JSON，不要其他文字）：
{{
    "trust_change": -5,
    "credibility": 30,
    "persuasiveness": 40,
    "emotional_impact": "suspicious",
    "decision": "doubt",
    "reasoning": "這個訊息聽起來很可疑"
}}

你的回答："""
        
        return prompt
    
    def _parse_agent_response(self, response: str) -> Dict:
        """
        解析Agent回應（改進版）
        
        處理各種可能的格式問題，更寬容的解析
        """
        if not response or not response.strip():
            logger.warning("⚠️ Agent返回空回應")
            return self._get_default_agent_score()
        
        # 記錄原始回應（用於調試）
        logger.debug(f"Agent原始回應: {response[:200]}")
        
        try:
            # 方法1: 嘗試直接解析JSON
            data = json.loads(response)
            logger.info("✅ 成功解析JSON（直接）")
        except json.JSONDecodeError:
            # 方法2: 提取JSON部分（處理markdown格式）
            import re
            
            # 移除markdown代碼塊標記
            response_cleaned = re.sub(r'```json\s*|\s*```', '', response)
            
            # 嘗試找到JSON對象
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_cleaned, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    logger.info("✅ 成功解析JSON（提取）")
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ 無法解析提取的JSON: {e}")
                    logger.debug(f"提取的內容: {json_match.group()[:200]}")
                    return self._get_default_agent_score()
            else:
                logger.warning(f"⚠️ 回應中沒有找到JSON格式")
                logger.debug(f"回應內容: {response[:200]}")
                return self._get_default_agent_score()
        
        # 驗證和提取數據
        try:
            trust_change = data.get("trust_change", 0)
            
            # 處理可能的字符串類型
            if isinstance(trust_change, str):
                trust_change = int(trust_change)
            
            # 限制範圍
            trust_change = max(-10, min(10, trust_change))
            
            credibility = max(0, min(100, int(data.get("credibility", 50))))
            persuasiveness = max(0, min(100, int(data.get("persuasiveness", 50))))
            
            result = {
                "trust_change": trust_change,
                "credibility": credibility,
                "persuasiveness": persuasiveness,
                "emotional_impact": data.get("emotional_impact", "neutral"),
                "decision": data.get("decision", "uncertain"),
                "reasoning": data.get("reasoning", "")
            }
            
            logger.info(
                f"✅ Agent評分解析成功: "
                f"trust_change={trust_change}, "
                f"credibility={credibility}, "
                f"decision={result['decision']}"
            )
            
            return result
            
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"⚠️ 數據驗證失敗: {e}")
            logger.debug(f"數據內容: {data}")
            return self._get_default_agent_score()
    
    def _get_default_agent_score(self) -> Dict:
        """獲取默認Agent評分（當解析失敗時）"""
        return {
            "trust_change": 0,
            "credibility": 50,
            "persuasiveness": 50,
            "emotional_impact": "neutral",
            "decision": "uncertain",
            "reasoning": "評估失敗，使用默認值"
        }
    
    def _calculate_confidence(self, rule_score: Dict, agent_score: Dict) -> float:
        """
        計算評分信心度
        
        如果規則和Agent評分接近，信心度高
        """
        rule_change = rule_score.get("trust_change", 0)
        agent_change = agent_score.get("trust_change", 0)
        
        # 計算差異
        diff = abs(rule_change - agent_change)
        
        # 轉換為信心度（差異越小，信心度越高）
        confidence = max(0, 100 - diff * 10)
        
        return round(confidence, 2)
    
    def _update_stats(self, result: EvaluationResult):
        """更新統計數據"""
        # 更新平均信心度
        total = self.stats["total_evaluations"]
        old_avg_conf = self.stats["avg_confidence"]
        self.stats["avg_confidence"] = (
            (old_avg_conf * (total - 1) + result.confidence) / total
        )
        
        # 更新平均差異（如果是混合評分）
        if result.method == "hybrid" and result.agent_score:
            diff = abs(
                result.rule_score.get("trust_change", 0) - 
                result.agent_score.get("trust_change", 0)
            )
            old_avg_diff = self.stats["avg_difference"]
            hybrid_count = self.stats["hybrid"]
            self.stats["avg_difference"] = (
                (old_avg_diff * (hybrid_count - 1) + diff) / hybrid_count
            )
    
    def adjust_weights(self, new_rule_weight: float, new_agent_weight: float):
        """
        調整權重
        
        Args:
            new_rule_weight: 新的規則權重
            new_agent_weight: 新的Agent權重
        """
        if abs(new_rule_weight + new_agent_weight - 1.0) > 0.01:
            logger.warning("⚠️ 權重總和不為1，自動調整")
            total = new_rule_weight + new_agent_weight
            new_rule_weight /= total
            new_agent_weight /= total
        
        self.rule_weight = new_rule_weight
        self.agent_weight = new_agent_weight
        
        logger.info(f"📊 權重已調整 - 規則={new_rule_weight:.2f}, Agent={new_agent_weight:.2f}")
    
    def generate_comparison_report(self) -> Dict:
        """
        生成對比報告
        
        分析規則評分和Agent評分的差異
        """
        if not self.evaluation_history:
            return {"status": "no_data", "message": "沒有評估數據"}
        
        # 篩選混合評分的記錄
        hybrid_evals = [e for e in self.evaluation_history if e.method == "hybrid"]
        
        if not hybrid_evals:
            return {"status": "no_hybrid", "message": "沒有混合評分數據"}
        
        # 計算統計
        differences = []
        rule_scores = []
        agent_scores = []
        
        for eval in hybrid_evals:
            rule_change = eval.rule_score.get("trust_change", 0)
            agent_change = eval.agent_score.get("trust_change", 0)
            
            differences.append(abs(rule_change - agent_change))
            rule_scores.append(rule_change)
            agent_scores.append(agent_change)
        
        # 計算相關性
        correlation = self._calculate_correlation(rule_scores, agent_scores)
        
        report = {
            "summary": {
                "total_evaluations": len(hybrid_evals),
                "avg_difference": sum(differences) / len(differences),
                "max_difference": max(differences),
                "min_difference": min(differences),
                "correlation": correlation,
                "avg_confidence": sum(e.confidence for e in hybrid_evals) / len(hybrid_evals)
            },
            "statistics": self.stats,
            "recommendations": self._generate_recommendations(
                sum(differences) / len(differences),
                correlation
            )
        }
        
        return report
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """計算相關係數"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        correlation = numerator / (denominator_x * denominator_y) ** 0.5
        return round(correlation, 3)
    
    def _generate_recommendations(self, avg_diff: float, correlation: float) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if avg_diff > 3:
            recommendations.append("規則和Agent評分差異較大，建議檢查Agent的prompt或調整權重")
        
        if correlation < 0.5:
            recommendations.append("規則和Agent評分相關性較低，建議增加Agent訓練數據")
        
        if correlation > 0.8:
            recommendations.append("規則和Agent評分高度一致，可以考慮增加Agent權重")
        
        if not recommendations:
            recommendations.append("評分系統運行良好，繼續保持！")
        
        return recommendations
    
    def export_evaluation_history(self, filepath: str):
        """導出評估歷史到文件"""
        data = []
        for eval in self.evaluation_history:
            data.append({
                "timestamp": eval.timestamp,
                "trust_change": eval.trust_change,
                "rule_score": eval.rule_score,
                "agent_score": eval.agent_score,
                "confidence": eval.confidence,
                "method": eval.method
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 評估歷史已導出到 {filepath}")


# 使用示例
if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(level=logging.INFO)
    
    print("=== VictimEvaluator 使用示例 ===\n")
    
    # 注意：這裡需要實際的victim_agent和performance_tracker實例
    # 這只是演示代碼結構
    
    print("1. 初始化評估器")
    print("evaluator = VictimEvaluator(victim_agent, tracker)")
    print()
    
    print("2. 評估訊息")
    print("result = evaluator.evaluate_message(")
    print("    message='你好，我係銀行職員，你嘅帳戶有問題。',")
    print("    sender='scammer',")
    print("    victim_response='咩問題？'")
    print(")")
    print()
    
    print("3. 查看結果")
    print("print(f'最終分數: {result.trust_change}')")
    print("print(f'信心度: {result.confidence}%')")
    print("print(f'方法: {result.method}')")
    print()
    
    print("4. 生成報告")
    print("report = evaluator.generate_comparison_report()")
    print("print(report)")
