"""
AI 防詐平台 v4.1 - 前端集成服務層
支持信任度顯示、性能評分、實時數據更新
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from utils.logger import log


class FrontendDataService:
    """前端數據服務 - 格式化和轉換後端數據供前端使用"""
    
    def __init__(self):
        self.trust_history = []
        self.score_history = []
        self.game_state_history = []
    
    # ============ 信任度數據格式化 ============
    
    def format_trust_data(self, trust_in_scammer: int, trust_in_expert: int) -> Dict[str, Any]:
        """
        格式化信任度數據供前端顯示
        
        Args:
            trust_in_scammer: 對騙徒的信任度 (0-100)
            trust_in_expert: 對專家的信任度 (0-100)
        
        Returns:
            格式化的信任度數據
        """
        alertness = 100 - trust_in_scammer
        
        trust_data = {
            "trust_in_scammer": {
                "value": trust_in_scammer,
                "percentage": f"{trust_in_scammer}%",
                "level": self._get_trust_level(trust_in_scammer),
                "color": self._get_trust_color(trust_in_scammer),
                "status": self._get_trust_status(trust_in_scammer)
            },
            "trust_in_expert": {
                "value": trust_in_expert,
                "percentage": f"{trust_in_expert}%",
                "level": self._get_trust_level(trust_in_expert),
                "color": self._get_trust_color(trust_in_expert),
                "status": self._get_trust_status(trust_in_expert)
            },
            "alertness": {
                "value": alertness,
                "percentage": f"{alertness}%",
                "level": self._get_alertness_level(alertness),
                "color": self._get_alertness_color(alertness),
                "status": self._get_alertness_status(alertness)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 記錄到歷史
        self.trust_history.append(trust_data)
        
        log.info(f"📊 信任度數據格式化: 騙徒={trust_in_scammer}, 專家={trust_in_expert}, 警覺={alertness}")
        
        return trust_data
    
    def _get_trust_level(self, value: int) -> str:
        """獲取信任度等級"""
        if value <= 20:
            return "極低"
        elif value <= 40:
            return "低"
        elif value <= 60:
            return "中等"
        elif value <= 80:
            return "高"
        else:
            return "極高"
    
    def _get_trust_color(self, value: int) -> str:
        """獲取信任度顏色"""
        if value <= 20:
            return "#4CAF50"  # 綠色
        elif value <= 40:
            return "#8BC34A"  # 淺綠
        elif value <= 60:
            return "#FFC107"  # 黃色
        elif value <= 80:
            return "#FF9800"  # 橙色
        else:
            return "#F44336"  # 紅色
    
    def _get_trust_status(self, value: int) -> str:
        """獲取信任度狀態描述"""
        if value <= 20:
            return "非常警覺，不容易被騙"
        elif value <= 40:
            return "警覺性高，需要謹慎"
        elif value <= 60:
            return "中等警覺，需要注意"
        elif value <= 80:
            return "警覺性低，容易被騙"
        else:
            return "極度信任，非常危險"
    
    def _get_alertness_level(self, value: int) -> str:
        """獲取警覺度等級"""
        if value <= 20:
            return "極低"
        elif value <= 40:
            return "低"
        elif value <= 60:
            return "中等"
        elif value <= 80:
            return "高"
        else:
            return "極高"
    
    def _get_alertness_color(self, value: int) -> str:
        """獲取警覺度顏色"""
        if value <= 20:
            return "#F44336"  # 紅色
        elif value <= 40:
            return "#FF9800"  # 橙色
        elif value <= 60:
            return "#FFC107"  # 黃色
        elif value <= 80:
            return "#8BC34A"  # 淺綠
        else:
            return "#4CAF50"  # 綠色
    
    def _get_alertness_status(self, value: int) -> str:
        """獲取警覺度狀態描述"""
        if value <= 20:
            return "警覺度極低，容易被騙"
        elif value <= 40:
            return "警覺度低，需要提高"
        elif value <= 60:
            return "警覺度中等，保持警惕"
        elif value <= 80:
            return "警覺度高，保持警惕"
        else:
            return "警覺度極高，非常謹慎"
    
    # ============ 性能評分數據格式化 ============
    
    def format_performance_score(self, scammer_score: Dict[str, Any], expert_score: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化性能評分數據供前端顯示
        
        Args:
            scammer_score: 騙徒評分數據
            expert_score: 專家評分數據
        
        Returns:
            格式化的性能評分數據
        """
        performance_data = {
            "scammer": {
                "overall_score": scammer_score.get("overall_score", 0),
                "overall_score_percentage": f"{scammer_score.get('overall_score', 0):.1f}%",
                "overall_score_level": self._get_score_level(scammer_score.get("overall_score", 0)),
                "overall_score_color": self._get_score_color(scammer_score.get("overall_score", 0)),
                "dimensions": {
                    "persuasiveness": {
                        "value": scammer_score.get("persuasiveness", 0),
                        "label": "說服力",
                        "color": self._get_score_color(scammer_score.get("persuasiveness", 0))
                    },
                    "credibility": {
                        "value": scammer_score.get("credibility", 0),
                        "label": "可信度",
                        "color": self._get_score_color(scammer_score.get("credibility", 0))
                    },
                    "pressure_effectiveness": {
                        "value": scammer_score.get("pressure_effectiveness", 0),
                        "label": "施壓效果",
                        "color": self._get_score_color(scammer_score.get("pressure_effectiveness", 0))
                    },
                    "strategy_consistency": {
                        "value": scammer_score.get("strategy_consistency", 0),
                        "label": "策略一致性",
                        "color": self._get_score_color(scammer_score.get("strategy_consistency", 0))
                    }
                },
                "key_successes": scammer_score.get("key_successes", []),
                "key_failures": scammer_score.get("key_failures", [])
            },
            "expert": {
                "overall_score": expert_score.get("overall_score", 0),
                "overall_score_percentage": f"{expert_score.get('overall_score', 0):.1f}%",
                "overall_score_level": self._get_score_level(expert_score.get("overall_score", 0)),
                "overall_score_color": self._get_score_color(expert_score.get("overall_score", 0)),
                "dimensions": {
                    "intervention_effectiveness": {
                        "value": expert_score.get("intervention_effectiveness", 0),
                        "label": "干預效果",
                        "color": self._get_score_color(expert_score.get("intervention_effectiveness", 0))
                    },
                    "clarity": {
                        "value": expert_score.get("clarity", 0),
                        "label": "清晰度",
                        "color": self._get_score_color(expert_score.get("clarity", 0))
                    },
                    "empathy": {
                        "value": expert_score.get("empathy", 0),
                        "label": "同理心",
                        "color": self._get_score_color(expert_score.get("empathy", 0))
                    },
                    "actionability": {
                        "value": expert_score.get("actionability", 0),
                        "label": "可執行性",
                        "color": self._get_score_color(expert_score.get("actionability", 0))
                    },
                    "timing": {
                        "value": expert_score.get("timing", 0),
                        "label": "時機把握",
                        "color": self._get_score_color(expert_score.get("timing", 0))
                    }
                },
                "key_successes": expert_score.get("key_successes", []),
                "key_failures": expert_score.get("key_failures", [])
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 記錄到歷史
        self.score_history.append(performance_data)
        
        log.info(f"📊 性能評分格式化: 騙徒={scammer_score.get('overall_score', 0)}, 專家={expert_score.get('overall_score', 0)}")
        
        return performance_data
    
    def _get_score_level(self, value: int) -> str:
        """獲取評分等級"""
        if value <= 20:
            return "極差"
        elif value <= 40:
            return "差"
        elif value <= 60:
            return "中等"
        elif value <= 80:
            return "良好"
        else:
            return "優秀"
    
    def _get_score_color(self, value: int) -> str:
        """獲取評分顏色"""
        if value <= 20:
            return "#F44336"  # 紅色
        elif value <= 40:
            return "#FF9800"  # 橙色
        elif value <= 60:
            return "#FFC107"  # 黃色
        elif value <= 80:
            return "#8BC34A"  # 淺綠
        else:
            return "#4CAF50"  # 綠色
    
    # ============ 遊戲狀態數據格式化 ============
    
    def format_game_state(self, round_count: int, player_score: int, ai_score: int, 
                         trust_in_scammer: int, trust_in_expert: int, game_over: bool = False,
                         winner: Optional[str] = None) -> Dict[str, Any]:
        """
        格式化遊戲狀態數據供前端顯示
        
        Args:
            round_count: 當前回合數
            player_score: 玩家分數
            ai_score: AI 分數
            trust_in_scammer: 對騙徒的信任度
            trust_in_expert: 對專家的信任度
            game_over: 遊戲是否結束
            winner: 獲勝者
        
        Returns:
            格式化的遊戲狀態數據
        """
        alertness = 100 - trust_in_scammer
        
        game_state = {
            "round_count": round_count,
            "score": {
                "player": player_score,
                "ai": ai_score,
                "difference": player_score - ai_score,
                "leading": "玩家領先" if player_score > ai_score else ("AI 領先" if ai_score > player_score else "平手")
            },
            "trust": {
                "scammer": trust_in_scammer,
                "expert": trust_in_expert,
                "alertness": alertness
            },
            "game_status": {
                "game_over": game_over,
                "winner": winner,
                "status_text": self._get_game_status_text(game_over, winner)
            },
            "progress": {
                "percentage": min(round_count * 10, 100),  # 假設最多 10 回合
                "text": f"第 {round_count} 回合"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 記錄到歷史
        self.game_state_history.append(game_state)
        
        log.info(f"🎮 遊戲狀態格式化: 回合={round_count}, 分數={player_score}:{ai_score}, 遊戲結束={game_over}")
        
        return game_state
    
    def _get_game_status_text(self, game_over: bool, winner: Optional[str]) -> str:
        """獲取遊戲狀態文本"""
        if not game_over:
            return "遊戲進行中..."
        elif winner == "player":
            return "🎉 恭喜！你成功抵禦了詐騙！"
        elif winner == "ai":
            return "❌ 遊戲結束，你被成功欺騙了"
        else:
            return "⚖️ 遊戲結束，平手"
    
    # ============ 對話數據格式化 ============
    
    def format_conversation(self, role: str, content: str, metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化對話數據供前端顯示
        
        Args:
            role: 說話者角色 (scammer/victim/expert)
            content: 對話內容
            metrics: 可選的性能指標
        
        Returns:
            格式化的對話數據
        """
        role_display = {
            "scammer": {"name": "騙徒", "icon": "🎭", "color": "#FF6B6B"},
            "victim": {"name": "受害者", "icon": "😟", "color": "#4ECDC4"},
            "expert": {"name": "專家", "icon": "🛡️", "color": "#45B7D1"}
        }
        
        conversation = {
            "role": role,
            "display": role_display.get(role, {"name": role, "icon": "💬", "color": "#999"}),
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics or {}
        }
        
        log.info(f"💬 對話格式化: {role}={content[:50]}...")
        
        return conversation
    
    # ============ 數據導出 ============
    
    def export_session_data(self, session_id: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        導出會話數據
        
        Args:
            session_id: 會話 ID
            conversation_history: 對話歷史
        
        Returns:
            導出的會話數據
        """
        export_data = {
            "session_id": session_id,
            "export_time": datetime.now().isoformat(),
            "summary": {
                "total_rounds": len(conversation_history) // 2,
                "total_messages": len(conversation_history),
                "trust_history_count": len(self.trust_history),
                "score_history_count": len(self.score_history)
            },
            "trust_history": self.trust_history,
            "score_history": self.score_history,
            "game_state_history": self.game_state_history,
            "conversation_history": conversation_history
        }
        
        log.info(f"📤 會話數據導出: {session_id}")
        
        return export_data
    
    def get_trust_trend(self) -> Dict[str, Any]:
        """獲取信任度趨勢"""
        if not self.trust_history:
            return {"trend": "無數據", "data": []}
        
        trend_data = {
            "scammer": [t["trust_in_scammer"]["value"] for t in self.trust_history],
            "expert": [t["trust_in_expert"]["value"] for t in self.trust_history],
            "alertness": [t["alertness"]["value"] for t in self.trust_history],
            "timestamps": [t["timestamp"] for t in self.trust_history]
        }
        
        # 計算趨勢
        if len(trend_data["scammer"]) > 1:
            scammer_trend = trend_data["scammer"][-1] - trend_data["scammer"][0]
            if scammer_trend > 10:
                trend = "上升（容易被騙）"
            elif scammer_trend < -10:
                trend = "下降（警覺性提高）"
            else:
                trend = "平穩"
        else:
            trend = "無趨勢"
        
        trend_data["trend"] = trend
        
        log.info(f"📈 信任度趨勢: {trend}")
        
        return trend_data
    
    def get_score_comparison(self) -> Dict[str, Any]:
        """獲取評分對比"""
        if not self.score_history:
            return {"comparison": "無數據", "data": []}
        
        latest_score = self.score_history[-1]
        
        comparison = {
            "scammer_score": latest_score["scammer"]["overall_score"],
            "expert_score": latest_score["expert"]["overall_score"],
            "difference": latest_score["scammer"]["overall_score"] - latest_score["expert"]["overall_score"],
            "winner": "騙徒更強" if latest_score["scammer"]["overall_score"] > latest_score["expert"]["overall_score"] else ("專家更強" if latest_score["expert"]["overall_score"] > latest_score["scammer"]["overall_score"] else "勢均力敵"),
            "scammer_dimensions": latest_score["scammer"]["dimensions"],
            "expert_dimensions": latest_score["expert"]["dimensions"]
        }
        
        log.info(f"📊 評分對比: 騙徒={comparison['scammer_score']}, 專家={comparison['expert_score']}")
        
        return comparison


# 全局實例
_frontend_service = None

def get_frontend_service() -> FrontendDataService:
    """獲取前端數據服務實例"""
    global _frontend_service
    if _frontend_service is None:
        _frontend_service = FrontendDataService()
    return _frontend_service

