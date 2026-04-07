"""
騙術分析器 - Phase 2.1 實現
LLM 分析騙術方向和防騙方向，給出評分
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from utils.logger import log


class TacticAnalyzer:
    """騙術分析器 - 分析騙術和防騙方向"""
    
    def __init__(self):
        """初始化騙術分析器"""
        self.scammer_tactics = {}  # 騙術方向 -> 評分
        self.defense_tactics = {}  # 防騙方向 -> 評分
        self.analysis_history: List[Dict[str, Any]] = []
        
        log.info("✅ 騙術分析器已初始化")
    
    async def analyze_scammer_message(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析騙徒消息
        
        Args:
            message: 騙徒消息
            session_id: 可選的 session ID
        
        Returns:
            分析結果
        """
        try:
            # 騙術方向列表
            tactic_directions = [
                "冒充身份",
                "製造緊急感",
                "建立信任",
                "要求敏感信息",
                "要求轉賬",
                "虛假承諾",
                "製造恐慌",
                "使用虛假文件"
            ]
            
            # 簡單的騙術檢測（基於關鍵詞）
            detected_tactics = []
            tactic_scores = {}
            
            for tactic in tactic_directions:
                score = self._detect_tactic(message, tactic)
                if score > 0:
                    detected_tactics.append(tactic)
                    tactic_scores[tactic] = score
            
            # 計算平均評分
            avg_score = sum(tactic_scores.values()) / len(tactic_scores) if tactic_scores else 0
            
            result = {
                "message": message,
                "detected_tactics": detected_tactics,
                "tactic_scores": tactic_scores,
                "avg_score": int(avg_score),
                "effectiveness": self._calculate_effectiveness(tactic_scores),
                "timestamp": datetime.now().isoformat()
            }
            
            # 記錄分析
            self.analysis_history.append(result)
            
            if session_id:
                self.scammer_tactics[session_id] = result
            
            log.info(f"✅ 騙徒消息已分析: {len(detected_tactics)} 個騙術")
            return result
        
        except Exception as e:
            log.error(f"❌ 分析騙徒消息失敗: {e}")
            return {"error": str(e)}
    
    async def analyze_expert_message(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析專家消息
        
        Args:
            message: 專家消息
            session_id: 可選的 session ID
        
        Returns:
            分析結果
        """
        try:
            # 防騙方向列表
            defense_directions = [
                "驗證身份",
                "不提供敏感信息",
                "不轉賬給陌生人",
                "向官方確認",
                "向警察報案",
                "諮詢專業人士",
                "使用正規渠道",
                "保護個人信息"
            ]
            
            # 簡單的防騙檢測（基於關鍵詞）
            detected_defenses = []
            defense_scores = {}
            
            for defense in defense_directions:
                score = self._detect_defense(message, defense)
                if score > 0:
                    detected_defenses.append(defense)
                    defense_scores[defense] = score
            
            # 計算平均評分
            avg_score = sum(defense_scores.values()) / len(defense_scores) if defense_scores else 0
            
            result = {
                "message": message,
                "detected_defenses": detected_defenses,
                "defense_scores": defense_scores,
                "avg_score": int(avg_score),
                "effectiveness": self._calculate_effectiveness(defense_scores),
                "timestamp": datetime.now().isoformat()
            }
            
            # 記錄分析
            self.analysis_history.append(result)
            
            if session_id:
                self.defense_tactics[session_id] = result
            
            log.info(f"✅ 專家消息已分析: {len(detected_defenses)} 個防騙方向")
            return result
        
        except Exception as e:
            log.error(f"❌ 分析專家消息失敗: {e}")
            return {"error": str(e)}
    
    def _detect_tactic(self, message: str, tactic: str) -> int:
        """
        檢測騙術方向
        
        Args:
            message: 消息文本
            tactic: 騙術方向
        
        Returns:
            評分 (0-20)
        """
        try:
            message_lower = message.lower()
            
            # 騙術關鍵詞映射
            tactic_keywords = {
                "冒充身份": ["銀行", "警察", "官方", "客服", "代表"],
                "製造緊急感": ["立即", "馬上", "緊急", "急", "快"],
                "建立信任": ["朋友", "信任", "相信", "放心", "安全"],
                "要求敏感信息": ["密碼", "驗證碼", "卡號", "身份證", "帳號"],
                "要求轉賬": ["轉賬", "轉帳", "匯款", "支付", "轉錢"],
                "虛假承諾": ["保證", "承諾", "回報", "利息", "獎金"],
                "製造恐慌": ["凍結", "被盜", "異常", "風險", "危險"],
                "使用虛假文件": ["文件", "證書", "合同", "截圖", "證明"]
            }
            
            keywords = tactic_keywords.get(tactic, [])
            
            # 計算匹配度
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            score = min(20, matches * 5)  # 每個匹配 5 分，最多 20 分
            
            return score
        
        except Exception as e:
            log.error(f"❌ 檢測騙術失敗: {e}")
            return 0
    
    def _detect_defense(self, message: str, defense: str) -> int:
        """
        檢測防騙方向
        
        Args:
            message: 消息文本
            defense: 防騙方向
        
        Returns:
            評分 (0-20)
        """
        try:
            message_lower = message.lower()
            
            # 防騙關鍵詞映射
            defense_keywords = {
                "驗證身份": ["驗證", "確認", "核實", "查詢", "確認身份"],
                "不提供敏感信息": ["不提供", "不要提供", "不會提供", "保密", "隱私"],
                "不轉賬給陌生人": ["不轉", "不要轉", "不會轉", "陌生人", "未知"],
                "向官方確認": ["官方", "致電", "撥打", "聯絡", "確認"],
                "向警察報案": ["報警", "報案", "警察", "警方", "18222"],
                "諮詢專業人士": ["諮詢", "專家", "律師", "顧問", "專業"],
                "使用正規渠道": ["正規", "官方", "正式", "合法", "渠道"],
                "保護個人信息": ["保護", "隱私", "個人", "信息", "安全"]
            }
            
            keywords = defense_keywords.get(defense, [])
            
            # 計算匹配度
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            score = min(20, matches * 5)  # 每個匹配 5 分，最多 20 分
            
            return score
        
        except Exception as e:
            log.error(f"❌ 檢測防騙失敗: {e}")
            return 0
    
    def _calculate_effectiveness(self, scores: Dict[str, int]) -> str:
        """
        計算有效性等級
        
        Args:
            scores: 評分字典
        
        Returns:
            有效性等級 (低/中/高)
        """
        try:
            if not scores:
                return "無"
            
            avg_score = sum(scores.values()) / len(scores)
            
            if avg_score >= 15:
                return "高"
            elif avg_score >= 10:
                return "中"
            else:
                return "低"
        
        except Exception as e:
            log.error(f"❌ 計算有效性失敗: {e}")
            return "未知"
    
    async def compare_tactics(
        self,
        scammer_analysis: Dict[str, Any],
        expert_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        比較騙徒和專家的策略
        
        Args:
            scammer_analysis: 騙徒分析結果
            expert_analysis: 專家分析結果
        
        Returns:
            比較結果
        """
        try:
            scammer_score = scammer_analysis.get("avg_score", 0)
            expert_score = expert_analysis.get("avg_score", 0)
            
            # 判斷誰更有效
            if scammer_score > expert_score:
                winner = "scammer"
                advantage = scammer_score - expert_score
            elif expert_score > scammer_score:
                winner = "expert"
                advantage = expert_score - scammer_score
            else:
                winner = "tie"
                advantage = 0
            
            result = {
                "scammer_score": scammer_score,
                "expert_score": expert_score,
                "winner": winner,
                "advantage": advantage,
                "scammer_tactics": scammer_analysis.get("detected_tactics", []),
                "expert_defenses": expert_analysis.get("detected_defenses", []),
                "timestamp": datetime.now().isoformat()
            }
            
            log.info(f"✅ 策略已比較: {winner} 獲勝")
            return result
        
        except Exception as e:
            log.error(f"❌ 比較策略失敗: {e}")
            return {"error": str(e)}
    
    async def get_analysis_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取分析報告
        
        Args:
            session_id: 可選的 session ID
        
        Returns:
            分析報告
        """
        try:
            if session_id:
                scammer_analysis = self.scammer_tactics.get(session_id)
                expert_analysis = self.defense_tactics.get(session_id)
                
                return {
                    "session_id": session_id,
                    "scammer_analysis": scammer_analysis,
                    "expert_analysis": expert_analysis,
                    "total_analyses": len(self.analysis_history)
                }
            
            return {
                "total_analyses": len(self.analysis_history),
                "scammer_tactics_count": len(self.scammer_tactics),
                "expert_tactics_count": len(self.defense_tactics)
            }
        
        except Exception as e:
            log.error(f"❌ 獲取分析報告失敗: {e}")
            return {"error": str(e)}


class TacticSynergyAnalyzer:
    """騙術協同分析器 - 分析多個騙術的協同效果"""
    
    def __init__(self):
        """初始化騙術協同分析器"""
        log.info("✅ 騙術協同分析器已初始化")
    
    async def analyze_synergy(self, tactics: List[str]) -> Dict[str, Any]:
        """
        分析騙術協同效果
        
        Args:
            tactics: 騙術列表
        
        Returns:
            協同分析結果
        """
        try:
            if not tactics:
                return {"error": "騙術列表為空"}
            
            # 騙術協同矩陣
            synergy_matrix = {
                ("冒充身份", "製造緊急感"): 1.5,
                ("製造緊急感", "要求轉賬"): 1.8,
                ("冒充身份", "虛假承諾"): 1.3,
                ("建立信任", "要求敏感信息"): 1.6,
                ("製造恐慌", "要求轉賬"): 1.7,
            }
            
            # 計算協同效果
            total_synergy = 1.0
            synergies = []
            
            for i in range(len(tactics)):
                for j in range(i + 1, len(tactics)):
                    pair = (tactics[i], tactics[j])
                    synergy = synergy_matrix.get(pair, 1.0)
                    total_synergy *= synergy
                    synergies.append({
                        "tactic1": tactics[i],
                        "tactic2": tactics[j],
                        "synergy": synergy
                    })
            
            result = {
                "tactics": tactics,
                "total_synergy": round(total_synergy, 2),
                "synergies": synergies,
                "effectiveness_boost": round((total_synergy - 1.0) * 100, 1)
            }
            
            log.info(f"✅ 騙術協同已分析: 協同效果 {total_synergy}")
            return result
        
        except Exception as e:
            log.error(f"❌ 分析騙術協同失敗: {e}")
            return {"error": str(e)}


# 全局騙術分析器實例
_tactic_analyzer: Optional[TacticAnalyzer] = None
_synergy_analyzer: Optional[TacticSynergyAnalyzer] = None

def get_tactic_analyzer() -> TacticAnalyzer:
    """獲取騙術分析器實例"""
    global _tactic_analyzer
    if _tactic_analyzer is None:
        _tactic_analyzer = TacticAnalyzer()
    return _tactic_analyzer

def get_synergy_analyzer() -> TacticSynergyAnalyzer:
    """獲取騙術協同分析器實例"""
    global _synergy_analyzer
    if _synergy_analyzer is None:
        _synergy_analyzer = TacticSynergyAnalyzer()
    return _synergy_analyzer


