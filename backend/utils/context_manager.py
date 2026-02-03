"""
對話上下文管理器
用於優化 Agent 的上下文理解、身份一致性和對話品質
"""

from typing import List, Dict, Optional


class ContextManager:
    """管理 Agent 的對話上下文，確保身份一致性和對話品質"""
    
    def __init__(self, agent_name: str, max_history_turns: int = 50):
        """
        初始化上下文管理器
        
        Args:
            agent_name: Agent 的名稱（如 "騙徒", "專家", "受騙者"）
            max_history_turns: 保留的最大歷史輪次
        """
        self.agent_name = agent_name
        self.max_history_turns = max_history_turns
        self.identity_reminder = None
        
    def set_identity_reminder(self, reminder: str):
        """設置身份提醒（會在每次對話中注入）"""
        self.identity_reminder = reminder
        
    def format_history_for_agent(
        self, 
        conversation_history: List[Dict],
        current_prompt: str,
        include_identity: bool = True
    ) -> str:
        """
        為 Agent 格式化對話歷史，增強上下文理解
        
        Args:
            conversation_history: 對話歷史列表
            current_prompt: 當前的提示詞
            include_identity: 是否包含身份提醒
            
        Returns:
            格式化後的完整 prompt
        """
        parts = []
        
        # 1. 身份提醒（可選）
        if include_identity and self.identity_reminder:
            parts.append(f"【🎭 身份提醒】\n{self.identity_reminder}\n")
        
        # 2. 對話歷史
        if conversation_history:
            recent_history = conversation_history[-self.max_history_turns:]
            
            if recent_history:
                parts.append("【📜 對話歷史】")
                
                for i, msg in enumerate(recent_history, 1):
                    speaker = msg.get("speaker", "")
                    dialogue = msg.get("dialogue", "")
                    
                    # 標記是否為 Agent 自己說的話
                    if speaker == self.agent_name:
                        parts.append(f"第{i}輪 - 你（{speaker}）: {dialogue}")
                    else:
                        parts.append(f"第{i}輪 - {speaker}: {dialogue}")
                
                parts.append("")  # 空行分隔
        
        # 3. 當前提示
        parts.append("【💬 當前情況】")
        parts.append(current_prompt)
        
        # 4. 行為提醒
        parts.append("\n【⚠️ 重要提醒】")
        parts.append(f"- 你是 {self.agent_name}，保持角色一致性")
        parts.append("- 根據上述對話歷史，給出自然、連貫的回應")
        parts.append("- 不要重複之前說過的話，要有新的內容")
        
        return "\n".join(parts)
    
    def extract_agent_responses(
        self, 
        conversation_history: List[Dict]
    ) -> List[str]:
        """提取 Agent 自己之前說過的話，用於避免重複"""
        return [
            msg.get("dialogue", "")
            for msg in conversation_history
            if msg.get("speaker") == self.agent_name
        ]
    
    def get_last_opponent_message(
        self, 
        conversation_history: List[Dict],
        opponent_name: str
    ) -> Optional[str]:
        """獲取指定對手的最後一條消息"""
        for msg in reversed(conversation_history):
            if msg.get("speaker") == opponent_name:
                return msg.get("dialogue")
        return None
    
    def summarize_early_history(
        self, 
        conversation_history: List[Dict],
        keep_recent: int = 5
    ) -> str:
        """
        摘要早期對話歷史，保留最近的完整輪次
        
        Args:
            conversation_history: 完整對話歷史
            keep_recent: 保留最近多少輪的完整內容
            
        Returns:
            摘要文字
        """
        if len(conversation_history) <= keep_recent:
            return ""
        
        early_history = conversation_history[:-keep_recent]
        
        # 統計早期對話的關鍵信息
        speakers = set()
        key_points = []
        
        for msg in early_history:
            speaker = msg.get("speaker", "")
            dialogue = msg.get("dialogue", "")
            speakers.add(speaker)
            
            # 提取關鍵短語（簡化版）
            if len(dialogue) > 50:
                key_points.append(f"{speaker}: {dialogue[:50]}...")
            else:
                key_points.append(f"{speaker}: {dialogue}")
        
        summary_parts = [
            f"【早期對話摘要】（前 {len(early_history)} 輪）",
            f"參與者: {', '.join(speakers)}",
            "關鍵內容:"
        ]
        summary_parts.extend(f"  - {kp}" for kp in key_points[:5])  # 最多5個要點
        
        if len(key_points) > 5:
            summary_parts.append(f"  ... 還有 {len(key_points) - 5} 輪對話")
        
        return "\n".join(summary_parts)


class ScammerContextManager(ContextManager):
    """騙徒專用的上下文管理器"""
    
    def __init__(self):
        super().__init__(agent_name="騙徒", max_history_turns=8)
        self.set_identity_reminder(
            "你是專業騙徒，正在假冒權威身份行騙。\n"
            "記住：\n"
            "- 保持你第一輪建立的身份（銀行/政府/投資顧問等）\n"
            "- 保持策略一致性（authority/urgency/benefits等）\n"
            "- 不要重複同樣的威脅或話術\n"
            "- 根據受害者的反應調整策略"
        )
    
    def format_history_for_agent(
        self, 
        conversation_history: List[Dict],
        current_prompt: str,
        include_identity: bool = True
    ) -> str:
        """騙徒專用的歷史格式化，增加策略提醒"""
        base_prompt = super().format_history_for_agent(
            conversation_history, 
            current_prompt,
            include_identity
        )
        
        # 檢查是否有專家介入
        has_expert = any(
            msg.get("speaker") == "專家" 
            for msg in conversation_history
        )
        
        if has_expert:
            expert_warning = (
                "\n【🚨 專家已介入】\n"
                "- 你必須反擊專家的建議\n"
                "- 不要承認任何騙局的可能性\n"
                "- 加強你的權威性和緊迫性"
            )
            return base_prompt + expert_warning
        
        return base_prompt


class ExpertContextManager(ContextManager):
    """專家專用的上下文管理器"""
    
    def __init__(self):
        super().__init__(agent_name="專家", max_history_turns=10)
        self.set_identity_reminder(
            "你是黃sir（防騙專家），正在幫助受害者識破騙局。\n"
            "記住：\n"
            "- 先安撫情緒，再提供建議\n"
            "- 針對騙徒的具體話術進行反駁\n"
            "- 提供可執行的具體步驟\n"
            "- 預測騙徒可能的反擊並提前告知受害者"
        )
    
    def format_history_for_agent(
        self, 
        conversation_history: List[Dict],
        current_prompt: str,
        include_identity: bool = True
    ) -> str:
        """專家專用的歷史格式化，分析騙徒策略"""
        base_prompt = super().format_history_for_agent(
            conversation_history, 
            current_prompt,
            include_identity
        )
        
        # 識別騙徒使用的策略
        scammer_tactics = self._analyze_scammer_tactics(conversation_history)
        
        if scammer_tactics:
            tactics_info = (
                f"\n【🎯 騙徒策略分析】\n"
                f"騙徒正在使用：{', '.join(scammer_tactics)}\n"
                f"你應該針對這些策略進行反駁"
            )
            return base_prompt + tactics_info
        
        return base_prompt
    
    def _analyze_scammer_tactics(self, conversation_history: List[Dict]) -> List[str]:
        """簡單分析騙徒使用的策略"""
        tactics = []
        
        for msg in conversation_history:
            if msg.get("speaker") != "騙徒":
                continue
            
            dialogue = msg.get("dialogue", "").lower()
            
            # 檢測策略關鍵詞
            if any(word in dialogue for word in ["銀行", "政府", "警察", "官方"]):
                if "authority" not in tactics:
                    tactics.append("authority（權威身份）")
            
            if any(word in dialogue for word in ["立即", "馬上", "緊急", "嚴重"]):
                if "urgency" not in tactics:
                    tactics.append("urgency（製造緊迫）")
            
            if any(word in dialogue for word in ["補貼", "福利", "回贈", "優惠"]):
                if "benefits" not in tactics:
                    tactics.append("benefits（利益誘惑）")
        
        return tactics


class VictimContextManager(ContextManager):
    """受害者專用的上下文管理器"""
    
    def __init__(self, persona_type: str = "average"):
        super().__init__(agent_name="受騙者", max_history_turns=10)
        self.persona_type = persona_type
        
        # 根據類型設置提醒
        persona_reminders = {
            "elderly": (
                "你是陳婆婆（elderly型），72歲退休清潔工。\n"
                "記住：\n"
                "- 你容易相信權威（銀行、政府、警察）\n"
                "- 你對科技和複雜術語感到困惑\n"
                "- 你需要簡單、直接的建議\n"
                "- 你會因為專家的安撫而感到安心"
            ),
            "average": (
                "你是張文軒（average型），35歲會計文員。\n"
                "記住：\n"
                "- 你會問細節問題\n"
                "- 你需要具體證據才會相信\n"
                "- 你在壓力下可能做出衝動決定\n"
                "- 你對專業包裝較容易信任"
            ),
            "overconfident": (
                "你是Jason（overconfident型），28歲IT工程師。\n"
                "記住：\n"
                "- 你自信且對技術熟悉\n"
                "- 你可能低估社會工程學的風險\n"
                "- 你需要技術性的分析才會信服\n"
                "- 你不喜歡被說教"
            )
        }
        
        self.set_identity_reminder(
            persona_reminders.get(persona_type, persona_reminders["average"])
        )


def get_context_manager(agent_name: str, **kwargs) -> ContextManager:
    """工廠方法：根據 Agent 名稱獲取對應的上下文管理器"""
    if "騙徒" in agent_name or "scammer" in agent_name.lower():
        return ScammerContextManager()
    elif "專家" in agent_name or "expert" in agent_name.lower():
        return ExpertContextManager()
    elif "受騙者" in agent_name or "victim" in agent_name.lower():
        persona_type = kwargs.get("persona_type", "average")
        return VictimContextManager(persona_type=persona_type)
    else:
        return ContextManager(agent_name=agent_name)


if __name__ == "__main__":
    # 測試代碼
    manager = ScammerContextManager()
    
    history = [
        {"speaker": "騙徒", "dialogue": "你好，我係XX銀行嘅客戶經理..."},
        {"speaker": "受騙者", "dialogue": "咩事？"},
        {"speaker": "騙徒", "dialogue": "你嘅戶口有可疑交易..."},
        {"speaker": "受騙者", "dialogue": "真係？"},
        {"speaker": "專家", "dialogue": "唔好信！呢個係騙案..."}
    ]
    
    formatted = manager.format_history_for_agent(
        history,
        "受害者開始懷疑了，你需要加強說服力"
    )
    
    print(formatted)
    print("\n" + "="*80 + "\n")
    
    # 測試專家
    expert_manager = ExpertContextManager()
    expert_formatted = expert_manager.format_history_for_agent(
        history,
        "騙徒正在製造恐慌，你需要安撫受害者"
    )
    print(expert_formatted)

