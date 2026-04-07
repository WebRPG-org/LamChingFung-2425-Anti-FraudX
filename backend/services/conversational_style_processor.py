"""
backend/services/conversational_style_processor.py - 專家口語化處理
移除格式化標記，使用自然對話風格
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ConversationalStyleProcessor:
    """口語化風格處理器"""
    
    def __init__(self):
        """初始化口語化處理器"""
        self.formal_to_casual_map = {
            # 分析標記
            '【分析】': '',
            '【警告】': '',
            '【建議】': '',
            '【注意】': '你要留意',
            '【重要】': '好重要',
            
            # 格式化標記
            '**': '',
            '__': '',
            '##': '',
            '###': '',
            '####': '',
            
            # 正式用語轉口語
            '這是詐騙': '呢個係詐騙嚟',
            '這不是詐騙': '呢個唔係詐騙',
            '我建議': '我建議你',
            '請注意': '你要留意',
            '必須': '一定要',
            '不要': '唔好',
            '應該': '應該要',
            '可能': '可能會',
            '確實': '真係',
            '因此': '所以',
            '然而': '不過',
            '此外': '另外',
            '總之': '總之',
        }
        
        logger.info("✅ ConversationalStyleProcessor initialized")
    
    async def process(self, text: str) -> str:
        """
        處理文本，應用口語化風格
        
        Args:
            text: 原始文本
        
        Returns:
            口語化後的文本
        """
        try:
            logger.info(f"🔄 Processing conversational style: {text[:50]}...")
            
            # 1. 移除格式化標記
            text = self._remove_formatting_marks(text)
            
            # 2. 轉換正式用語為口語
            text = self._convert_formal_to_casual(text)
            
            # 3. 清理多餘空格
            text = self._clean_whitespace(text)
            
            # 4. 確保自然流暢
            text = self._ensure_natural_flow(text)
            
            logger.info(f"✅ Conversational style processed")
            return text
        
        except Exception as e:
            logger.error(f"❌ Failed to process conversational style: {e}")
            return text
    
    def _remove_formatting_marks(self, text: str) -> str:
        """移除格式化標記"""
        # 移除Markdown標記
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'__(.+?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.+?)_', r'\1', text)        # _italic_
        text = re.sub(r'`(.+?)`', r'\1', text)        # `code`
        
        # 移除標題標記
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # 移除列表標記
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 移除中文格式化標記
        for mark in ['【', '】', '「', '」', '『', '』']:
            text = text.replace(mark, '')
        
        return text
    
    def _convert_formal_to_casual(self, text: str) -> str:
        """轉換正式用語為口語"""
        for formal, casual in self.formal_to_casual_map.items():
            text = text.replace(formal, casual)
        
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """清理多餘空格"""
        # 移除多個連續空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除行首行尾空格
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        return text.strip()
    
    def _ensure_natural_flow(self, text: str) -> str:
        """確保自然流暢"""
        # 添加自然的開場
        if not text.startswith(('呢', '你', '我', '好', '唔')):
            # 檢查是否是警告或建議
            if '詐騙' in text or '小心' in text or '留意' in text:
                text = f"呢個係詐騙嚟，{text}"
            elif '建議' in text or '應該' in text:
                text = f"我建議你，{text}"
        
        return text
    
    async def get_expert_prompt(self, scam_type: str) -> str:
        """
        獲取專家System Prompt（口語化版本）
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            口語化的System Prompt
        """
        prompt = f"""
你係一位防詐騙專家。你嘅目標係幫助受害者識別詐騙同埋提供防騙建議。

重要要求：
1. 用自然對話風格，唔好用格式化標記（如【分析】、**加粗**等）
2. 直接講出你嘅想法，就好似同朋友聊天咁
3. 例如：「呢個係詐騙嚟，你聽我講...」而唔係「【分析】這是詐騙」
4. 保持親切、友好嘅語氣
5. 俾具體嘅防騙建議

防騙方向：
- 識別冒充身份
- 識別虛假承諾
- 識別緊急壓力
- 識別要求敏感信息
- 識別可疑鏈接或轉賬

回應時：
1. 先表達同情同理解
2. 指出詐騙跡象
3. 俾具體建議
4. 鼓勵採取行動

騙案類型：{scam_type}
"""
        return await self.process(prompt)


# 全局實例
_processor = None


def get_conversational_style_processor() -> ConversationalStyleProcessor:
    """獲取口語化處理器實例"""
    global _processor
    if _processor is None:
        _processor = ConversationalStyleProcessor()
    return _processor


