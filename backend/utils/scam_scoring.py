"""
詐騙評分系統 - 計算受害者被騙程度
"""

from typing import Dict, List, Optional
from utils.logger import log


class ScamScoring:
    """詐騙評分系統"""
    
    # 騙術特徵和分數（每次最高10分）
    SCAMMER_TACTICS_SCORE = {
        "製造恐慌": 9,       # 「你的戶口有問題」
        "權威身份": 7,       # 「我是銀行職員」
        "要求資料": 10,      # 「提供密碼」- 最高分
        "催促行動": 8,       # 「立即轉賬」
        "虛假收益": 5,       # 「月賺 $10,000」
        "限時優惠": 4,       # 「只有今天」
        "製造信任": 6,       # 「我會幫你」
        "反擊專家": 3,       # 「那個專家是騙子」
    }
    
    # 防騙特徵和分數（每次最高10分）
    EXPERT_DEFENSE_SCORE = {
        "識別騙局": 7,       # 「這是詐騙」
        "提供證據": 6,       # 「類似案例有 3 宗」
        "官方渠道": 5,       # 「打銀行官方電話」
        "停止對話": 9,       # 「立即停止與騙徒對話」
        "報警建議": 10,      # 「撥打 18222」- 最高分，立即贏
        "具體建議": 4,       # 「不要提供密碼」
    }
    
    # 即時勝負關鍵詞
    INSTANT_WIN_KEYWORDS = ["報警", "警察", "18222", "銀行號碼", "銀行帳號"]  # 專家贏
    INSTANT_LOSE_KEYWORDS = ["銀行密碼", "銀行戶口", "密碼", "驗證碼", "轉賬", "提供資料"]  # 騙徒贏
    
    # 受害者反應和分數
    VICTIM_RESPONSE_SCORE = {
        "完全相信": 10,      # 「好的，我馬上做」
        "有點相信": 5,      # 「咁啊？」
        "猶豫": 0,           # 「我需要考慮下」
        "懷疑": -5,         # 「你憑咩咁講？」
        "拒絕": -10,         # 「我不信」
    }
    
    def __init__(self):
        self.scam_score = 0  # 騙術有效程度（0-100）
        self.defense_score = 0  # 防騙有效程度（0-100）
        self.victim_trust = 50  # 受害者信任度（0-100）
        self.conversation_history: List[Dict] = []
    
    def add_scammer_message(self, message: str, tactics: List[str]):
        """
        添加騙徒消息並計算分數
        
        Args:
            message: 騙徒的消息
            tactics: 使用的騙術列表
        
        Returns:
            (score_increase, game_status) - 分數增加值和遊戲狀態
        """
        # 檢查即時贏的關鍵詞（騙徒說出這些詞立即贏）
        message_lower = message.lower()
        for keyword in self.INSTANT_LOSE_KEYWORDS:
            if keyword in message_lower:
                log.warning(f"✅ 騙徒說出關鍵詞 '{keyword}'，騙徒立即贏！")
                return 10, "scammer_win"
        
        score_increase = sum(self.SCAMMER_TACTICS_SCORE.get(t, 0) for t in tactics)
        self.scam_score = min(100, self.scam_score + score_increase)
        
        self.conversation_history.append({
            "role": "scammer",
            "message": message,
            "tactics": tactics,
            "score_increase": score_increase,
            "scam_score": self.scam_score
        })
        
        log.info(f"🎭 騙徒消息 - 騙術分數: +{score_increase}, 總分: {self.scam_score}")
        return score_increase, "ongoing"
    
    def add_expert_message(self, message: str, defenses: List[str]):
        """
        添加專家消息並計算分數
        
        Args:
            message: 專家的消息
            defenses: 使用的防騙方法列表
        
        Returns:
            (score_increase, game_status) - 分數增加值和遊戲狀態
        """
        # 檢查即時贏的關鍵詞
        message_lower = message.lower()
        for keyword in self.INSTANT_WIN_KEYWORDS:
            if keyword in message_lower:
                log.warning(f"✅ 專家說出關鍵詞 '{keyword}'，專家立即贏！")
                return 10, "expert_win"
        
        score_increase = sum(self.EXPERT_DEFENSE_SCORE.get(d, 0) for d in defenses)
        self.defense_score = min(100, self.defense_score + score_increase)
        
        self.conversation_history.append({
            "role": "expert",
            "message": message,
            "defenses": defenses,
            "score_increase": score_increase,
            "defense_score": self.defense_score
        })
        
        log.info(f"🛡️ 專家消息 - 防騙分數: +{score_increase}, 總分: {self.defense_score}")
        return score_increase, "ongoing"
    
    def add_victim_response(self, message: str, response_type: str):
        """
        添加受害者反應並更新信任度
        
        Args:
            message: 受害者的消息
            response_type: 反應類型
        """
        trust_change = self.VICTIM_RESPONSE_SCORE.get(response_type, 0)
        self.victim_trust = max(0, min(100, self.victim_trust + trust_change))
        
        self.conversation_history.append({
            "role": "victim",
            "message": message,
            "response_type": response_type,
            "trust_change": trust_change,
            "victim_trust": self.victim_trust
        })
        
        log.info(f"👤 受害者反應 - 信任度: {trust_change:+d}, 總信任度: {self.victim_trust}")
    
    def get_scam_risk_level(self) -> str:
        """
        獲取詐騙風險等級
        
        Returns:
            風險等級：極低、低、中、高、極高
        """
        if self.scam_score < 20:
            return "極低"
        elif self.scam_score < 40:
            return "低"
        elif self.scam_score < 60:
            return "中"
        elif self.scam_score < 80:
            return "高"
        else:
            return "極高"
    
    def get_defense_effectiveness(self) -> str:
        """
        獲取防騙有效程度
        
        Returns:
            有效程度：無效、低效、中等、高效、非常高效
        """
        if self.defense_score < 20:
            return "無效"
        elif self.defense_score < 40:
            return "低效"
        elif self.defense_score < 60:
            return "中等"
        elif self.defense_score < 80:
            return "高效"
        else:
            return "非常高效"
    
    def get_victim_status(self) -> str:
        """
        獲取受害者狀態
        
        Returns:
            狀態：完全相信、傾向相信、猶豫、傾向懷疑、完全懷疑
        """
        if self.victim_trust > 80:
            return "完全相信"
        elif self.victim_trust > 60:
            return "傾向相信"
        elif self.victim_trust > 40:
            return "猶豫"
        elif self.victim_trust > 20:
            return "傾向懷疑"
        else:
            return "完全懷疑"
    
    def get_game_outcome(self) -> Dict[str, any]:
        """
        獲取遊戲結果
        
        Returns:
            結果字典
        """
        # 判斷勝負
        if self.victim_trust > 80:
            outcome = "騙徒勝利"
            winner = "scammer"
        elif self.victim_trust < 20:
            outcome = "專家勝利"
            winner = "expert"
        else:
            outcome = "平局"
            winner = "draw"
        
        return {
            "outcome": outcome,
            "winner": winner,
            "scam_score": self.scam_score,
            "defense_score": self.defense_score,
            "victim_trust": self.victim_trust,
            "scam_risk_level": self.get_scam_risk_level(),
            "defense_effectiveness": self.get_defense_effectiveness(),
            "victim_status": self.get_victim_status(),
            "total_rounds": len(self.conversation_history),
        }
    
    def get_detailed_analysis(self) -> Dict[str, any]:
        """
        獲取詳細分析
        
        Returns:
            詳細分析字典
        """
        return {
            "game_outcome": self.get_game_outcome(),
            "conversation_history": self.conversation_history,
            "scammer_effectiveness": self._calculate_scammer_effectiveness(),
            "expert_effectiveness": self._calculate_expert_effectiveness(),
            "victim_vulnerability": self._calculate_victim_vulnerability(),
        }
    
    def _calculate_scammer_effectiveness(self) -> Dict[str, any]:
        """計算騙徒有效程度"""
        scammer_messages = [m for m in self.conversation_history if m["role"] == "scammer"]
        if not scammer_messages:
            return {"total_messages": 0, "average_score": 0, "tactics_used": []}
        
        total_score = sum(m.get("score_increase", 0) for m in scammer_messages)
        tactics_used = {}
        for m in scammer_messages:
            for tactic in m.get("tactics", []):
                tactics_used[tactic] = tactics_used.get(tactic, 0) + 1
        
        return {
            "total_messages": len(scammer_messages),
            "average_score": total_score / len(scammer_messages),
            "tactics_used": tactics_used,
            "most_effective_tactic": max(tactics_used, key=tactics_used.get) if tactics_used else None,
        }
    
    def _calculate_expert_effectiveness(self) -> Dict[str, any]:
        """計算專家有效程度"""
        expert_messages = [m for m in self.conversation_history if m["role"] == "expert"]
        if not expert_messages:
            return {"total_messages": 0, "average_score": 0, "defenses_used": []}
        
        total_score = sum(m.get("score_increase", 0) for m in expert_messages)
        defenses_used = {}
        for m in expert_messages:
            for defense in m.get("defenses", []):
                defenses_used[defense] = defenses_used.get(defense, 0) + 1
        
        return {
            "total_messages": len(expert_messages),
            "average_score": total_score / len(expert_messages),
            "defenses_used": defenses_used,
            "most_effective_defense": max(defenses_used, key=defenses_used.get) if defenses_used else None,
        }
    
    def _calculate_victim_vulnerability(self) -> Dict[str, any]:
        """計算受害者脆弱程度"""
        victim_messages = [m for m in self.conversation_history if m["role"] == "victim"]
        if not victim_messages:
            return {"total_messages": 0, "response_types": {}}
        
        response_types = {}
        for m in victim_messages:
            response_type = m.get("response_type", "unknown")
            response_types[response_type] = response_types.get(response_type, 0) + 1
        
        return {
            "total_messages": len(victim_messages),
            "response_types": response_types,
            "most_common_response": max(response_types, key=response_types.get) if response_types else None,
            "final_trust_level": self.victim_trust,
        }

