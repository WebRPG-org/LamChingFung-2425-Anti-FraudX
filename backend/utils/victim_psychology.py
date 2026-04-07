"""
受害者心理模型
提供 HybridScamScoring 需要的心理狀態與更新介面。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional


EmotionalState = Literal["neutral", "anxious", "calm", "suspicious", "panicked"]


@dataclass
class TrustState:
    """受害者信任狀態"""

    trust_in_scammer: int = 50
    trust_in_expert: int = 50
    alertness: int = 50
    emotional_state: EmotionalState = "neutral"
    history: List[Dict] = field(default_factory=list)

    def update(self, target: str, delta: int, reason: str = "") -> None:
        """更新信任/警覺數值，並記錄歷史。"""
        if target == "scammer":
            self.trust_in_scammer = max(0, min(100, self.trust_in_scammer + int(delta)))
        elif target == "expert":
            self.trust_in_expert = max(0, min(100, self.trust_in_expert + int(delta)))
        elif target == "alertness":
            self.alertness = max(0, min(100, self.alertness + int(delta)))

        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "target": target,
                "delta": int(delta),
                "reason": reason,
                "trust_in_scammer": self.trust_in_scammer,
                "trust_in_expert": self.trust_in_expert,
                "alertness": self.alertness,
                "emotional_state": self.emotional_state,
            }
        )

    def get_dominant_trust(self) -> str:
        """回傳目前主要信任對象。"""
        if self.trust_in_scammer > self.trust_in_expert:
            return "scammer"
        if self.trust_in_expert > self.trust_in_scammer:
            return "expert"
        return "balanced"


class VictimPsychologyModel:
    """混合評分系統使用的受害者心理模型。"""

    def __init__(self, victim_persona: str = "average"):
        self.victim_persona = victim_persona
        self.trust_state = TrustState()
        self.emotional_transitions: List[Dict] = []

    def analyze_emotional_cues(self, message: str) -> Optional[EmotionalState]:
        """由訊息內容判斷情緒線索。"""
        if not message:
            return None

        msg = message.lower()

        panic_keywords = ["完了", "點算", "怎么辦", "怎麼辦", "糟糕", "立即", "緊急"]
        anxious_keywords = ["擔心", "害怕", "怕", "不安", "緊張", "焦慮"]
        suspicious_keywords = ["騙", "詐騙", "可疑", "唔信", "不信", "點解", "為什麼", "證據"]
        calm_keywords = ["冷靜", "慢慢", "想想", "考慮", "先確認", "查證"]

        if any(k in msg for k in panic_keywords):
            return "panicked"
        if any(k in msg for k in anxious_keywords):
            return "anxious"
        if any(k in msg for k in suspicious_keywords):
            return "suspicious"
        if any(k in msg for k in calm_keywords):
            return "calm"
        return None

    def update_emotional_state(self, new_state: EmotionalState, reason: str = "") -> None:
        """更新情緒狀態，記錄轉移歷史。"""
        if not new_state:
            return

        old_state = self.trust_state.emotional_state
        if old_state == new_state:
            return

        self.trust_state.emotional_state = new_state
        self.emotional_transitions.append(
            {
                "timestamp": datetime.now().isoformat(),
                "from": old_state,
                "to": new_state,
                "reason": reason,
            }
        )

    def get_current_state(self) -> Dict:
        """回傳完整心理狀態。"""
        return {
            "victim_persona": self.victim_persona,
            "trust_in_scammer": self.trust_state.trust_in_scammer,
            "trust_in_expert": self.trust_state.trust_in_expert,
            "alertness": self.trust_state.alertness,
            "emotional_state": self.trust_state.emotional_state,
            "dominant_trust": self.trust_state.get_dominant_trust(),
            "history_count": len(self.trust_state.history),
            "emotional_transitions": self.emotional_transitions,
        }
