"""
評分系統重構 - Phase 2.3 實現
基於受害者反應的智能計分系統
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from utils.logger import log


class ScamScoringV2:
    """評分系統 V2 - 基於受害者反應的計分"""
    
    def __init__(self):
        """初始化評分系統"""
        self.scammer_scores: Dict[str, int] = {}  # session_id -> score
        self.expert_scores: Dict[str, int] = {}  # session_id -> score
        self.victim_alertness: Dict[str, int] = {}  # session_id -> alertness
        self.scoring_history: List[Dict[str, Any]] = []
        
        log.info("✅ 評分系統 V2 已初始化")
    
    async def analyze_victim_response(
        self,
        response: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析受害者反應
        
        Args:
            response: 受害者反應
            session_id: 可選的 session ID
        
        Returns:
            分析結果
        """
        try:
            response_lower = response.lower()
            
            # 判定受害者的反應類型
            response_type = self._classify_response(response_lower)
            
            # 計算騙徒和專家的得分
            scammer_score_gain = 0
            expert_score_gain = 0
            alertness_change = 0
            
            if response_type == "completely_believe":
                scammer_score_gain = self._random_score(10, 20)
                expert_score_gain = 0
                alertness_change = -10
            elif response_type == "partially_believe":
                scammer_score_gain = self._random_score(5, 10)
                expert_score_gain = self._random_score(1, 5)
                alertness_change = -5
            elif response_type == "suspicious":
                scammer_score_gain = 0
                expert_score_gain = self._random_score(10, 20)
                alertness_change = 10
            elif response_type == "refuse":
                scammer_score_gain = 0
                expert_score_gain = self._random_score(15, 20)
                alertness_change = 15
            
            result = {
                "response_type": response_type,
                "scammer_score_gain": scammer_score_gain,
                "expert_score_gain": expert_score_gain,
                "alertness_change": alertness_change,
                "timestamp": datetime.now().isoformat()
            }
            
            # 更新分數
            if session_id:
                self.scammer_scores[session_id] = self.scammer_scores.get(session_id, 0) + scammer_score_gain
                self.expert_scores[session_id] = self.expert_scores.get(session_id, 0) + expert_score_gain
                self.victim_alertness[session_id] = max(0, min(100, 
                    self.victim_alertness.get(session_id, 50) + alertness_change))
            
            # 記錄
            self.scoring_history.append(result)
            
            log.info(f"✅ 受害者反應已分析: {response_type}")
            return result
        
        except Exception as e:
            log.error(f"❌ 分析受害者反應失敗: {e}")
            return {"error": str(e)}
    
    def _classify_response(self, response: str) -> str:
        """
        分類受害者反應
        
        Args:
            response: 受害者反應
        
        Returns:
            反應類型
        """
        try:
            # 完全相信的關鍵詞
            completely_believe_keywords = ["好的", "可以", "會", "立即", "馬上", "現在就"]
            
            # 部分相信的關鍵詞
            partially_believe_keywords = ["可能", "也許", "好像", "有點", "不太確定"]
            
            # 懷疑的關鍵詞
            suspicious_keywords = ["為什麼", "怎麼", "不對", "奇怪", "有點不對勁"]
            
            # 拒絕的關鍵詞
            refuse_keywords = ["不會", "不要", "拒絕", "不提供", "不信"]
            
            # 判定反應類型
            if any(keyword in response for keyword in refuse_keywords):
                return "refuse"
            elif any(keyword in response for keyword in suspicious_keywords):
                return "suspicious"
            elif any(keyword in response for keyword in partially_believe_keywords):
                return "partially_believe"
            elif any(keyword in response for keyword in completely_believe_keywords):
                return "completely_believe"
            else:
                return "neutral"
        
        except Exception as e:
            log.error(f"❌ 分類反應失敗: {e}")
            return "neutral"
    
    def _random_score(self, min_score: int, max_score: int) -> int:
        """
        生成隨機評分
        
        Args:
            min_score: 最小評分
            max_score: 最大評分
        
        Returns:
            隨機評分
        """
        import random
        return random.randint(min_score, max_score)
    
    async def calculate_alertness(self, session_id: str) -> int:
        """
        計算警覺性
        
        警覺性 = 專家信用度 - 騙徒信用度
        範圍：0-100
        
        Args:
            session_id: Session ID
        
        Returns:
            警覺性 (0-100)
        """
        try:
            scammer_score = self.scammer_scores.get(session_id, 0)
            expert_score = self.expert_scores.get(session_id, 0)
            
            # 計算警覺性
            alertness = expert_score - scammer_score
            
            # 標準化到 0-100
            alertness = max(0, min(100, 50 + alertness // 2))
            
            return alertness
        
        except Exception as e:
            log.error(f"❌ 計算警覺性失敗: {e}")
            return 50
    
    async def get_scores(self, session_id: str) -> Dict[str, Any]:
        """
        獲取評分
        
        Args:
            session_id: Session ID
        
        Returns:
            評分信息
        """
        try:
            scammer_score = self.scammer_scores.get(session_id, 0)
            expert_score = self.expert_scores.get(session_id, 0)
            alertness = await self.calculate_alertness(session_id)
            
            return {
                "session_id": session_id,
                "scammer_score": scammer_score,
                "expert_score": expert_score,
                "alertness": alertness,
                "alertness_level": self._get_alertness_level(alertness)
            }
        
        except Exception as e:
            log.error(f"❌ 獲取評分失敗: {e}")
            return {"error": str(e)}
    
    def _get_alertness_level(self, alertness: int) -> str:
        """
        獲取警覺性等級
        
        Args:
            alertness: 警覺性分數
        
        Returns:
            警覺性等級
        """
        try:
            if alertness >= 70:
                return "高"
            elif alertness >= 40:
                return "中"
            else:
                return "低"
        
        except Exception as e:
            log.error(f"❌ 獲取警覺性等級失敗: {e}")
            return "未知"


class EvaluationRecorder:
    """評估記錄器 - 記錄受害者/騙徒/專家評估"""
    
    def __init__(self):
        """初始化評估記錄器"""
        self.victim_evaluations: Dict[str, Dict[str, Any]] = {}
        self.scammer_evaluations: Dict[str, Dict[str, Any]] = {}
        self.expert_evaluations: Dict[str, Dict[str, Any]] = {}
        
        log.info("✅ 評估記錄器已初始化")
    
    async def record_victim_evaluation(
        self,
        session_id: str,
        evaluation: Dict[str, Any]
    ) -> bool:
        """
        記錄受害者評估
        
        Args:
            session_id: Session ID
            evaluation: 評估數據
        
        Returns:
            是否記錄成功
        """
        try:
            self.victim_evaluations[session_id] = {
                **evaluation,
                "recorded_at": datetime.now().isoformat()
            }
            
            log.info(f"✅ 受害者評估已記錄: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 記錄受害者評估失敗: {e}")
            return False
    
    async def record_scammer_evaluation(
        self,
        session_id: str,
        evaluation: Dict[str, Any]
    ) -> bool:
        """
        記錄騙徒評估
        
        Args:
            session_id: Session ID
            evaluation: 評估數據
        
        Returns:
            是否記錄成功
        """
        try:
            self.scammer_evaluations[session_id] = {
                **evaluation,
                "recorded_at": datetime.now().isoformat()
            }
            
            log.info(f"✅ 騙徒評估已記錄: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 記錄騙徒評估失敗: {e}")
            return False
    
    async def record_expert_evaluation(
        self,
        session_id: str,
        evaluation: Dict[str, Any]
    ) -> bool:
        """
        記錄專家評估
        
        Args:
            session_id: Session ID
            evaluation: 評估數據
        
        Returns:
            是否記錄成功
        """
        try:
            self.expert_evaluations[session_id] = {
                **evaluation,
                "recorded_at": datetime.now().isoformat()
            }
            
            log.info(f"✅ 專家評估已記錄: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 記錄專家評估失敗: {e}")
            return False
    
    async def get_all_evaluations(self, session_id: str) -> Dict[str, Any]:
        """
        獲取所有評估
        
        Args:
            session_id: Session ID
        
        Returns:
            所有評估
        """
        try:
            return {
                "session_id": session_id,
                "victim_evaluation": self.victim_evaluations.get(session_id),
                "scammer_evaluation": self.scammer_evaluations.get(session_id),
                "expert_evaluation": self.expert_evaluations.get(session_id)
            }
        
        except Exception as e:
            log.error(f"❌ 獲取評估失敗: {e}")
            return {"error": str(e)}


# 全局實例
_scam_scoring_v2: Optional[ScamScoringV2] = None
_evaluation_recorder: Optional[EvaluationRecorder] = None

def get_scam_scoring_v2() -> ScamScoringV2:
    """獲取評分系統 V2 實例"""
    global _scam_scoring_v2
    if _scam_scoring_v2 is None:
        _scam_scoring_v2 = ScamScoringV2()
    return _scam_scoring_v2

def get_evaluation_recorder() -> EvaluationRecorder:
    """獲取評估記錄器實例"""
    global _evaluation_recorder
    if _evaluation_recorder is None:
        _evaluation_recorder = EvaluationRecorder()
    return _evaluation_recorder

def get_scam_scorer() -> ScamScoringV2:
    """獲取評分系統實例（get_scam_scoring_v2 的別名，保持向後兼容）"""
    return get_scam_scoring_v2()


