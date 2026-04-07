"""
backend/services/response_length_controller.py - 回應長度控制
智能截斷、Token計數、長度驗證
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ResponseLengthController:
    """回應長度控制器"""
    
    def __init__(self, max_length: int = 80, max_tokens: int = 100):
        """
        初始化長度控制器
        
        Args:
            max_length: 最大字符數
            max_tokens: 最大Token數
        """
        self.max_length = max_length
        self.max_tokens = max_tokens
        
        logger.info(f"✅ ResponseLengthController initialized (max_length={max_length}, max_tokens={max_tokens})")
    
    async def process(self, response: str) -> str:
        """
        處理回應長度
        
        Args:
            response: 原始回應
        
        Returns:
            處理後的回應
        """
        try:
            logger.info(f"🔄 Processing response length: {response[:50]}...")
            
            # 1. 智能截斷
            truncated = await self.smart_truncate(response)
            
            # 2. 驗證長度
            is_valid = await self.validate_length(truncated)
            
            if not is_valid:
                logger.warning(f"⚠️ Response length validation failed")
            
            logger.info(f"✅ Response length processed: {len(truncated)} chars")
            return truncated
        
        except Exception as e:
            logger.error(f"❌ Failed to process response length: {e}")
            return response
    
    async def smart_truncate(self, text: str, max_length: int = None) -> str:
        """
        智能截斷回應，保留完整句子
        
        Args:
            text: 原始文本
            max_length: 最大長度（可選）
        
        Returns:
            截斷後的文本
        """
        max_length = max_length or self.max_length
        
        if len(text) <= max_length:
            return text
        
        logger.info(f"🔄 Smart truncating: {len(text)} -> {max_length}")
        
        # 在max_length處截斷
        truncated = text[:max_length]
        
        # 找到最後一個完整句子
        last_period = truncated.rfind('。')
        last_comma = truncated.rfind('，')
        last_space = truncated.rfind(' ')
        
        # 優先選擇句號（最自然的斷點）
        if last_period > max_length * 0.7:
            result = truncated[:last_period + 1]
            logger.info(f"✅ Truncated at period: {len(result)} chars")
            return result
        
        # 其次選擇逗號
        elif last_comma > max_length * 0.7:
            result = truncated[:last_comma + 1]
            logger.info(f"✅ Truncated at comma: {len(result)} chars")
            return result
        
        # 再次選擇空格
        elif last_space > max_length * 0.7:
            result = truncated[:last_space]
            logger.info(f"✅ Truncated at space: {len(result)} chars")
            return result
        
        # 最後才直接截斷
        else:
            logger.info(f"✅ Direct truncation: {len(truncated)} chars")
            return truncated
    
    async def count_tokens(self, text: str) -> int:
        """
        計算Token數量
        
        Args:
            text: 文本
        
        Returns:
            Token數量
        """
        try:
            # 簡單估算：中文約1個字=1個token，英文約4個字=1個token
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_words = len(re.findall(r'[a-zA-Z]+', text))
            
            # 中文：1字=1token，英文：1詞≈1.3token
            tokens = chinese_chars + int(english_words * 1.3)
            
            logger.info(f"📊 Token count: {tokens} (Chinese: {chinese_chars}, English: {english_words})")
            return tokens
        
        except Exception as e:
            logger.error(f"❌ Failed to count tokens: {e}")
            return len(text)  # 降級方案
    
    async def validate_length(self, text: str) -> Tuple[bool, dict]:
        """
        驗證回應長度
        
        Args:
            text: 文本
        
        Returns:
            (是否有效, 驗證詳情)
        """
        try:
            char_count = len(text)
            token_count = await self.count_tokens(text)
            
            char_valid = char_count <= self.max_length
            token_valid = token_count <= self.max_tokens
            
            is_valid = char_valid and token_valid
            
            details = {
                'char_count': char_count,
                'max_length': self.max_length,
                'char_valid': char_valid,
                'token_count': token_count,
                'max_tokens': self.max_tokens,
                'token_valid': token_valid,
                'is_valid': is_valid
            }
            
            if is_valid:
                logger.info(f"✅ Length validation passed: {char_count} chars, {token_count} tokens")
            else:
                logger.warning(f"⚠️ Length validation failed: {char_count}/{self.max_length} chars, {token_count}/{self.max_tokens} tokens")
            
            return is_valid, details
        
        except Exception as e:
            logger.error(f"❌ Failed to validate length: {e}")
            return False, {'error': str(e)}
    
    async def build_length_controlled_prompt(self, base_prompt: str) -> str:
        """
        構建長度控制的Prompt
        
        Args:
            base_prompt: 基礎Prompt
        
        Returns:
            添加長度控制指令的Prompt
        """
        length_instruction = f"""
重要要求：
1. 請在{self.max_length}字以內回應
2. 不要超過{self.max_length}字
3. 保持完整的句子，不要中斷
4. 如果需要更多信息，可以在下一輪對話中提供

{base_prompt}
"""
        return length_instruction
    
    async def post_process_response(self, response: str) -> str:
        """
        後處理回應
        
        Args:
            response: 原始回應
        
        Returns:
            後處理後的回應
        """
        try:
            logger.info(f"🔄 Post-processing response: {response[:50]}...")
            
            # 1. 智能截斷
            truncated = await self.smart_truncate(response)
            
            # 2. 移除多餘空格
            cleaned = ' '.join(truncated.split())
            
            # 3. 確保以完整句子結尾
            if not cleaned.endswith(('。', '，', '！', '？', '...', '…')):
                # 找到最後一個標點符號
                last_punct = max(
                    cleaned.rfind('。'),
                    cleaned.rfind('，'),
                    cleaned.rfind('！'),
                    cleaned.rfind('？')
                )
                
                if last_punct > 0:
                    cleaned = cleaned[:last_punct + 1]
            
            logger.info(f"✅ Post-processing completed: {len(cleaned)} chars")
            return cleaned
        
        except Exception as e:
            logger.error(f"❌ Failed to post-process response: {e}")
            return response


# 全局實例
_controller = None


def get_response_length_controller(max_length: int = 80, max_tokens: int = 100) -> ResponseLengthController:
    """獲取回應長度控制器實例"""
    global _controller
    if _controller is None:
        _controller = ResponseLengthController(max_length, max_tokens)
    return _controller


