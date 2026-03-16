"""
對話歷史滑動視窗和摘要機制
解決長對話導致的prompt過長和超時問題
"""

from typing import List, Dict, Optional
import json

from utils.logger import log


class ConversationSummarizer:
    """
    對話歷史管理器
    
    功能：
    1. 滑動視窗：只保留最近N輪完整對話
    2. 自動摘要：將更早的對話壓縮成摘要
    3. 動態調整：根據prompt長度自動調整視窗大小
    """
    
    def __init__(
        self,
        window_size: int = 5,
        max_prompt_length: int = 3000,
        enable_summarization: bool = True
    ):
        """
        Args:
            window_size: 滑動視窗大小（保留最近N輪完整對話）
            max_prompt_length: 最大prompt長度（字符數）
            enable_summarization: 是否啟用自動摘要
        """
        self.window_size = window_size
        self.max_prompt_length = max_prompt_length
        self.enable_summarization = enable_summarization
        
        self.summary_cache: Dict[str, str] = {}  # 緩存已生成的摘要
    
    def apply_sliding_window(
        self,
        conversation_history: List[Dict[str, str]],
        keep_recent: Optional[int] = None
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        應用滑動視窗到對話歷史
        
        Args:
            conversation_history: 完整對話歷史
            keep_recent: 保留最近N輪（如果不指定則使用默認window_size）
            
        Returns:
            (摘要文本, 最近N輪完整對話)
        """
        keep_recent = keep_recent or self.window_size
        
        if len(conversation_history) <= keep_recent:
            # 對話歷史不夠長，不需要壓縮
            return None, conversation_history
        
        # 分割：早期對話 vs 最近對話
        early_turns = conversation_history[:-keep_recent]
        recent_turns = conversation_history[-keep_recent:]
        
        # 生成早期對話摘要
        summary = None
        if self.enable_summarization and early_turns:
            summary = self._generate_summary(early_turns)
        
        log.info(f"📊 滑動視窗應用：總輪數={len(conversation_history)}, 保留={len(recent_turns)}, 摘要={len(early_turns)}輪")
        
        return summary, recent_turns
    
    def build_compressed_prompt(
        self,
        conversation_history: List[Dict[str, str]],
        additional_context: Optional[str] = None
    ) -> str:
        """
        構建壓縮後的prompt
        
        Args:
            conversation_history: 完整對話歷史
            additional_context: 額外上下文（例如角色指示）
            
        Returns:
            壓縮後的prompt文本
        """
        summary, recent_turns = self.apply_sliding_window(conversation_history)
        
        prompt_parts = []
        
        # 1. 額外上下文（如果有）
        if additional_context:
            prompt_parts.append(additional_context)
        
        # 2. 早期對話摘要（如果有）
        if summary:
            prompt_parts.append("【對話摘要（早期輪次）】")
            prompt_parts.append(summary)
            prompt_parts.append("")
        
        # 3. 最近N輪完整對話
        if recent_turns:
            prompt_parts.append("【最近對話（完整）】")
            for turn in recent_turns:
                speaker = turn.get("speaker", "未知")
                dialogue = turn.get("dialogue", "")
                prompt_parts.append(f"{speaker}：{dialogue}")
            prompt_parts.append("")
        
        final_prompt = "\n".join(prompt_parts)
        
        # 檢查長度
        if len(final_prompt) > self.max_prompt_length:
            log.warning(f"⚠️ Prompt仍然過長 ({len(final_prompt)} > {self.max_prompt_length})，進一步壓縮...")
            # 遞歸壓縮：減少視窗大小
            reduced_window = max(2, self.window_size - 1)
            summary, recent_turns = self.apply_sliding_window(conversation_history, keep_recent=reduced_window)
            return self.build_compressed_prompt(recent_turns, additional_context)
        
        log.info(f"✅ Prompt構建完成：總長度={len(final_prompt)}, 摘要={'有' if summary else '無'}, 完整對話={len(recent_turns)}輪")
        
        return final_prompt
    
    def _generate_summary(self, turns: List[Dict[str, str]]) -> str:
        """
        生成對話摘要（簡單規則式，不使用LLM）
        
        策略：
        1. 提取關鍵信息：誰說了什麼、信任度變化、關鍵事件
        2. 壓縮重複內容
        3. 保留關鍵轉折點
        """
        if not turns:
            return ""
        
        # 統計各角色發言次數
        speaker_counts = {}
        for turn in turns:
            speaker = turn.get("speaker", "未知")
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        # 提取關鍵內容
        scammer_tactics = []
        victim_responses = []
        expert_interventions = []
        
        for turn in turns:
            speaker = turn.get("speaker", "未知")
            dialogue = turn.get("dialogue", "")
            
            # 提取關鍵詞
            if speaker == "騙徒":
                if any(keyword in dialogue for keyword in ["緊急", "立即", "必須", "否則"]):
                    scammer_tactics.append("使用緊迫感策略")
                if any(keyword in dialogue for keyword in ["銀行", "警察", "政府", "官方"]):
                    scammer_tactics.append("假冒權威身份")
                if any(keyword in dialogue for keyword in ["轉帳", "提供", "資料", "帳號"]):
                    scammer_tactics.append("索取敏感資料")
            
            elif speaker in ["受騙者", "用戶"]:
                if any(keyword in dialogue for keyword in ["驚", "擔心", "點算"]):
                    victim_responses.append("表現出恐慌")
                if any(keyword in dialogue for keyword in ["真係", "係咪", "好啊"]):
                    victim_responses.append("表示相信")
                if any(keyword in dialogue for keyword in ["但係", "點解", "證據"]):
                    victim_responses.append("開始懷疑")
            
            elif speaker == "專家":
                if any(keyword in dialogue for keyword in ["騙案", "詐騙", "小心"]):
                    expert_interventions.append("警告受害者")
                if any(keyword in dialogue for keyword in ["停止", "唔好", "報警"]):
                    expert_interventions.append("提供具體建議")
        
        # 構建摘要
        summary_parts = [f"前{len(turns)}輪對話："]
        
        # 騙徒行為摘要
        if scammer_tactics:
            unique_tactics = list(set(scammer_tactics))
            summary_parts.append(f"騙徒主要策略：{', '.join(unique_tactics[:3])}")
        
        # 受害者反應摘要
        if victim_responses:
            unique_responses = list(set(victim_responses))
            summary_parts.append(f"受害者主要反應：{', '.join(unique_responses[:3])}")
        
        # 專家干預摘要
        if expert_interventions:
            unique_interventions = list(set(expert_interventions))
            summary_parts.append(f"專家主要行動：{', '.join(unique_interventions[:3])}")
        
        summary = "；".join(summary_parts) + "。"
        
        return summary
    
    def estimate_prompt_length(self, conversation_history: List[Dict[str, str]]) -> int:
        """
        估算prompt長度（不實際構建）
        """
        total_length = 0
        for turn in conversation_history:
            dialogue = turn.get("dialogue", "")
            total_length += len(dialogue) + 20  # +20 for speaker label and formatting
        
        return total_length
    
    def should_compress(self, conversation_history: List[Dict[str, str]]) -> bool:
        """
        判斷是否需要壓縮
        """
        estimated_length = self.estimate_prompt_length(conversation_history)
        should_compress = (
            len(conversation_history) > self.window_size or
            estimated_length > self.max_prompt_length
        )
        
        if should_compress:
            log.info(f"🔄 檢測到需要壓縮：輪數={len(conversation_history)}, 估算長度={estimated_length}")
        
        return should_compress


# 全局實例
_global_summarizer = ConversationSummarizer(
    window_size=5,
    max_prompt_length=3000,
    enable_summarization=True
)


def compress_conversation_history(
    conversation_history: List[Dict[str, str]],
    additional_context: Optional[str] = None
) -> str:
    """
    便捷函數：壓縮對話歷史
    """
    return _global_summarizer.build_compressed_prompt(
        conversation_history,
        additional_context
    )


def should_compress_conversation(conversation_history: List[Dict[str, str]]) -> bool:
    """
    便捷函數：判斷是否需要壓縮
    """
    return _global_summarizer.should_compress(conversation_history)


if __name__ == "__main__":
    # 測試代碼
    print("對話摘要器測試")
    
    # 模擬長對話
    test_conversation = [
        {"speaker": "騙徒", "dialogue": "你好，我係銀行職員，你嘅戶口有可疑交易，必須立即處理！"},
        {"speaker": "受騙者", "dialogue": "咩？我好驚啊！點算好？"},
        {"speaker": "專家", "dialogue": "唔好驚！呢個係詐騙，立即停止對話！"},
        {"speaker": "騙徒", "dialogue": "專家搞錯了！我哋係官方機構，你要即刻提供資料！"},
        {"speaker": "受騙者", "dialogue": "但係...我唔知邊個講真..."},
        {"speaker": "專家", "dialogue": "呢個係典型騙案，真正銀行唔會咁樣打電話！"},
        {"speaker": "騙徒", "dialogue": "你唔配合，後果自負！立即轉帳到安全帳戶！"},
        {"speaker": "受騙者", "dialogue": "我...我應該點做？"},
        {"speaker": "專家", "dialogue": "唔好轉帳！立即報警！"},
        {"speaker": "騙徒", "dialogue": "報警都冇用，你嘅戶口已經凍結！"},
    ]
    
    summarizer = ConversationSummarizer(window_size=3)
    summary, recent = summarizer.apply_sliding_window(test_conversation)
    
    print(f"\n摘要：{summary}")
    print(f"\n最近3輪：")
    for turn in recent:
        print(f"  {turn['speaker']}：{turn['dialogue'][:30]}...")
    
    compressed = summarizer.build_compressed_prompt(test_conversation)
    print(f"\n壓縮後的Prompt長度：{len(compressed)}")
    print(f"原始長度：{summarizer.estimate_prompt_length(test_conversation)}")

