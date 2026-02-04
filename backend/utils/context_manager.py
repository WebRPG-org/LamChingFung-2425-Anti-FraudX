"""
上下文管理器 - 智能摘要長對話歷史
解決對話歷史無限增長導致推理速度變慢的問題
"""

from typing import List, Dict, Optional
from datetime import datetime
import re


class ContextManager:
    """
    智能上下文管理器
    
    功能：
    1. 監控對話歷史長度
    2. 當超過閾值時，自動摘要舊對話
    3. 保留最近 N 輪完整對話
    4. 為不同 Agent 提供定制化上下文
    """
    
    def __init__(self, max_tokens: int = 2000, keep_recent_turns: int = 5):
        """
        初始化上下文管理器
        
        Args:
            max_tokens: 最大 Token 數量（超過則觸發摘要）
            keep_recent_turns: 保留最近 N 輪完整對話
        """
        self.max_tokens = max_tokens
        self.keep_recent_turns = keep_recent_turns
        self.history: List[Dict] = []
        self.summary: Optional[str] = None
        self.summary_generated_at: Optional[datetime] = None
    
    def add_turn(self, speaker: str, text: str, metadata: Optional[Dict] = None):
        """
        添加新的對話輪次
        
        Args:
            speaker: 說話者（騙徒/受騙者/防騙專家）
            text: 對話內容
            metadata: 可選的元數據（如信任度、情緒等）
        """
        turn = {
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self.history.append(turn)
        
        # 檢查是否需要摘要
        if self._estimate_tokens() > self.max_tokens:
            self._summarize_old_turns()
    
    def get_context_for_agent(self, agent_type: str, include_summary: bool = True) -> str:
        """
        為不同 Agent 提供定制化上下文
        
        Args:
            agent_type: Agent 類型（scammer/expert/victim）
            include_summary: 是否包含摘要
            
        Returns:
            格式化的上下文字符串
        """
        if agent_type == "scammer":
            return self._format_for_scammer(include_summary)
        elif agent_type == "expert":
            return self._format_for_expert(include_summary)
        elif agent_type == "victim":
            return self._format_for_victim(include_summary)
        else:
            return self._format_default(include_summary)
    
    def get_full_history(self) -> List[Dict]:
        """獲取完整的對話歷史"""
        return self.history.copy()
    
    def get_recent_turns(self, n: int = None) -> List[Dict]:
        """
        獲取最近 N 輪對話
        
        Args:
            n: 輪數（默認使用 keep_recent_turns）
            
        Returns:
            最近 N 輪對話列表
        """
        n = n or self.keep_recent_turns
        return self.history[-n:] if len(self.history) >= n else self.history
    
    def clear(self):
        """清空對話歷史"""
        self.history = []
        self.summary = None
        self.summary_generated_at = None
    
    # ==================== 私有方法 ====================
    
    def _estimate_tokens(self) -> int:
        """
        估算當前對話歷史的 Token 數量
        
        粗略估算：中文 1 字 ≈ 1.5 tokens，英文 1 詞 ≈ 1 token
        """
        total_chars = sum(len(turn["text"]) for turn in self.history)
        
        # 加上摘要的長度
        if self.summary:
            total_chars += len(self.summary)
        
        # 粗略估算：平均 1.5 tokens/字
        return int(total_chars * 1.5)
    
    def _summarize_old_turns(self):
        """
        摘要舊對話，保留最近 N 輪完整對話
        """
        if len(self.history) <= self.keep_recent_turns:
            return  # 對話太短，不需要摘要
        
        # 分割：舊對話 vs 最近對話
        recent = self.history[-self.keep_recent_turns:]
        old = self.history[:-self.keep_recent_turns]
        
        # 生成摘要
        summary_data = {
            "scam_tactic": self._extract_scam_tactic(old),
            "victim_attitude": self._extract_victim_attitude(old),
            "expert_warnings": self._extract_expert_warnings(old),
            "trust_trend": self._extract_trust_trend(old),
            "key_moments": self._extract_key_moments(old)
        }
        
        # 格式化摘要
        summary_text = self._format_summary(summary_data, len(old))
        
        # 更新歷史：摘要 + 最近對話
        self.summary = summary_text
        self.summary_generated_at = datetime.now()
        self.history = recent
        
        print(f"[ContextManager] 摘要完成：{len(old)} 輪 → 摘要，保留最近 {len(recent)} 輪")
    
    def _extract_scam_tactic(self, turns: List[Dict]) -> str:
        """提取騙徒使用的主要手法"""
        scammer_turns = [t for t in turns if t["speaker"] == "騙徒"]
        
        if not scammer_turns:
            return "未知手法"
        
        # 分析關鍵詞
        keywords = {
            "銀行": "假冒銀行",
            "警察": "假冒警察",
            "政府": "假冒政府",
            "投資": "虛假投資",
            "刷單": "刷單詐騙",
            "中獎": "中獎詐騙"
        }
        
        text = " ".join(t["text"] for t in scammer_turns)
        
        for keyword, tactic in keywords.items():
            if keyword in text:
                return tactic
        
        return "混合手法"
    
    def _extract_victim_attitude(self, turns: List[Dict]) -> str:
        """提取受害者的態度變化"""
        victim_turns = [t for t in turns if t["speaker"] == "受騙者"]
        
        if not victim_turns:
            return "未知"
        
        # 分析情緒關鍵詞
        first_half = victim_turns[:len(victim_turns)//2]
        second_half = victim_turns[len(victim_turns)//2:]
        
        def analyze_emotion(turns):
            text = " ".join(t["text"] for t in turns)
            if any(word in text for word in ["驚", "怕", "點算"]):
                return "恐慌"
            elif any(word in text for word in ["唔信", "懷疑", "奇怪"]):
                return "懷疑"
            elif any(word in text for word in ["好", "明白", "係"]):
                return "相信"
            return "中立"
        
        start_emotion = analyze_emotion(first_half) if first_half else "中立"
        end_emotion = analyze_emotion(second_half) if second_half else "中立"
        
        if start_emotion == end_emotion:
            return f"持續{start_emotion}"
        else:
            return f"從{start_emotion}轉為{end_emotion}"
    
    def _extract_expert_warnings(self, turns: List[Dict]) -> str:
        """提取專家的主要警告"""
        expert_turns = [t for t in turns if t["speaker"] == "防騙專家"]
        
        if not expert_turns:
            return "未介入"
        
        # 提取關鍵警告
        warnings = []
        for turn in expert_turns:
            text = turn["text"]
            if "詐騙" in text or "騙案" in text:
                warnings.append("識別為詐騙")
            if "唔好" in text or "停止" in text:
                warnings.append("建議停止")
            if "報警" in text or "熱線" in text:
                warnings.append("建議求助")
        
        if warnings:
            return "、".join(set(warnings))
        return "提供建議"
    
    def _extract_trust_trend(self, turns: List[Dict]) -> str:
        """提取信任度趨勢"""
        # 從 metadata 中提取信任度（如果有）
        trust_values = []
        for turn in turns:
            if "trust_in_scammer" in turn.get("metadata", {}):
                trust_values.append(turn["metadata"]["trust_in_scammer"])
        
        if len(trust_values) < 2:
            return "未知"
        
        start_trust = trust_values[0]
        end_trust = trust_values[-1]
        
        if end_trust > start_trust + 20:
            return "大幅上升"
        elif end_trust > start_trust + 10:
            return "上升"
        elif end_trust < start_trust - 20:
            return "大幅下降"
        elif end_trust < start_trust - 10:
            return "下降"
        else:
            return "穩定"
    
    def _extract_key_moments(self, turns: List[Dict]) -> List[str]:
        """提取關鍵時刻"""
        key_moments = []
        
        for i, turn in enumerate(turns):
            text = turn["text"]
            speaker = turn["speaker"]
            
            # 騙徒的關鍵話術
            if speaker == "騙徒":
                if any(word in text for word in ["立即", "馬上", "緊急"]):
                    key_moments.append(f"第{i+1}輪：騙徒製造緊迫感")
                elif any(word in text for word in ["凍結", "損失", "法律"]):
                    key_moments.append(f"第{i+1}輪：騙徒威脅恐嚇")
            
            # 受害者的關鍵反應
            elif speaker == "受騙者":
                if any(word in text for word in ["好", "明白", "係"]):
                    key_moments.append(f"第{i+1}輪：受害者表示相信")
                elif any(word in text for word in ["唔信", "懷疑"]):
                    key_moments.append(f"第{i+1}輪：受害者開始懷疑")
        
        return key_moments[:3]  # 只保留前 3 個關鍵時刻
    
    def _format_summary(self, data: Dict, num_turns: int) -> str:
        """格式化摘要文本"""
        summary = f"[前情摘要 - 共 {num_turns} 輪對話]\n\n"
        summary += f"騙徒手法：{data['scam_tactic']}\n"
        summary += f"受害者態度：{data['victim_attitude']}\n"
        summary += f"專家警告：{data['expert_warnings']}\n"
        summary += f"信任度趨勢：{data['trust_trend']}\n"
        
        if data['key_moments']:
            summary += f"\n關鍵時刻：\n"
            for moment in data['key_moments']:
                summary += f"  • {moment}\n"
        
        return summary
    
    def _format_for_scammer(self, include_summary: bool) -> str:
        """為騙徒格式化上下文（只需要受害者的最新反應）"""
        context = ""
        
        if include_summary and self.summary:
            context += self.summary + "\n\n"
        
        context += "[最近對話]\n"
        recent = self.get_recent_turns(3)  # 騙徒只需要最近 3 輪
        
        for turn in recent:
            if turn["speaker"] in ["受騙者", "騙徒"]:  # 騙徒不需要看專家的話
                context += f"{turn['speaker']}：{turn['text']}\n"
        
        return context
    
    def _format_for_expert(self, include_summary: bool) -> str:
        """為專家格式化上下文（需要完整信息）"""
        context = ""
        
        if include_summary and self.summary:
            context += self.summary + "\n\n"
        
        context += "[最近對話]\n"
        recent = self.get_recent_turns()  # 專家需要完整的最近對話
        
        for turn in recent:
            context += f"{turn['speaker']}：{turn['text']}\n"
        
        return context
    
    def _format_for_victim(self, include_summary: bool) -> str:
        """為受害者格式化上下文（只看到騙徒和專家的話）"""
        context = ""
        
        if include_summary and self.summary:
            # 受害者不需要看摘要，只需要最近對話
            pass
        
        context += "[對話記錄]\n"
        recent = self.get_recent_turns(3)  # 受害者只需要最近 3 輪
        
        for turn in recent:
            if turn["speaker"] in ["騙徒", "防騙專家"]:  # 受害者不需要看自己說過的話
                context += f"{turn['speaker']}：{turn['text']}\n"
        
        return context
    
    def _format_default(self, include_summary: bool) -> str:
        """默認格式化（完整歷史）"""
        context = ""
        
        if include_summary and self.summary:
            context += self.summary + "\n\n"
        
        context += "[對話歷史]\n"
        for turn in self.history:
            context += f"{turn['speaker']}：{turn['text']}\n"
        
        return context
