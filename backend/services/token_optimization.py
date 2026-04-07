"""
Token 優化服務 - Phase 1.3 實現
優化 Token 使用，降低成本，提升性能
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from utils.logger import log


class TokenCounter:
    """Token 計數器 - 計算和監控 Token 使用"""
    
    def __init__(self):
        """初始化 Token 計數器"""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.session_tokens: Dict[str, int] = {}  # session_id -> tokens
        self.round_tokens: Dict[str, List[int]] = {}  # session_id -> [tokens per round]
        
        log.info("✅ Token 計數器已初始化")
    
    def count_tokens(self, text: str) -> int:
        """
        計算文本的 Token 數
        
        Args:
            text: 輸入文本
        
        Returns:
            Token 數
        """
        try:
            # 簡單的 Token 計數方法：
            # 平均每個中文字符 = 1.5 tokens
            # 平均每個英文單詞 = 1.3 tokens
            # 平均每個空格 = 0.5 tokens
            
            if not text:
                return 0
            
            # 計算中文字符
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            chinese_tokens = int(chinese_chars * 1.5)
            
            # 計算英文單詞
            english_words = len([w for w in text.split() if w.isascii()])
            english_tokens = int(english_words * 1.3)
            
            # 計算空格
            spaces = text.count(' ')
            space_tokens = int(spaces * 0.5)
            
            total = chinese_tokens + english_tokens + space_tokens
            
            return max(1, total)  # 至少 1 個 token
        
        except Exception as e:
            log.error(f"❌ Token 計數失敗: {e}")
            return 0
    
    def add_prompt_tokens(self, text: str, session_id: Optional[str] = None) -> int:
        """
        添加 prompt token
        
        Args:
            text: Prompt 文本
            session_id: 可選的 session ID
        
        Returns:
            Token 數
        """
        try:
            tokens = self.count_tokens(text)
            self.prompt_tokens += tokens
            self.total_tokens += tokens
            
            if session_id:
                self.session_tokens[session_id] = self.session_tokens.get(session_id, 0) + tokens
                if session_id not in self.round_tokens:
                    self.round_tokens[session_id] = []
                self.round_tokens[session_id].append(tokens)
            
            log.info(f"✅ Prompt tokens 已添加: {tokens}")
            return tokens
        
        except Exception as e:
            log.error(f"❌ 添加 prompt tokens 失敗: {e}")
            return 0
    
    def add_completion_tokens(self, text: str, session_id: Optional[str] = None) -> int:
        """
        添加 completion token
        
        Args:
            text: 完成文本
            session_id: 可選的 session ID
        
        Returns:
            Token 數
        """
        try:
            tokens = self.count_tokens(text)
            self.completion_tokens += tokens
            self.total_tokens += tokens
            
            if session_id:
                self.session_tokens[session_id] = self.session_tokens.get(session_id, 0) + tokens
                if session_id not in self.round_tokens:
                    self.round_tokens[session_id] = []
                self.round_tokens[session_id].append(tokens)
            
            log.info(f"✅ Completion tokens 已添加: {tokens}")
            return tokens
        
        except Exception as e:
            log.error(f"❌ 添加 completion tokens 失敗: {e}")
            return 0
    
    def get_session_tokens(self, session_id: str) -> int:
        """
        獲取 session 的 token 使用
        
        Args:
            session_id: Session ID
        
        Returns:
            Token 數
        """
        return self.session_tokens.get(session_id, 0)
    
    def get_round_tokens(self, session_id: str) -> List[int]:
        """
        獲取 session 每輪的 token 使用
        
        Args:
            session_id: Session ID
        
        Returns:
            Token 列表
        """
        return self.round_tokens.get(session_id, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取 Token 統計信息
        
        Returns:
            統計信息
        """
        try:
            avg_tokens_per_round = 0
            if self.round_tokens:
                all_tokens = []
                for tokens_list in self.round_tokens.values():
                    all_tokens.extend(tokens_list)
                avg_tokens_per_round = sum(all_tokens) / len(all_tokens) if all_tokens else 0
            
            return {
                "total_tokens": self.total_tokens,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "sessions": len(self.session_tokens),
                "avg_tokens_per_round": int(avg_tokens_per_round),
                "prompt_completion_ratio": round(self.prompt_tokens / max(1, self.completion_tokens), 2)
            }
        
        except Exception as e:
            log.error(f"❌ 獲取統計信息失敗: {e}")
            return {}


class ContextCompressor:
    """Context 壓縮器 - 壓縮對話歷史以減少 Token 使用"""
    
    def __init__(self, compression_ratio: float = 0.7):
        """
        初始化 Context 壓縮器
        
        Args:
            compression_ratio: 壓縮比例（0-1）
        """
        self.compression_ratio = compression_ratio
        
        log.info(f"✅ Context 壓縮器已初始化: 壓縮比例 {compression_ratio}")
    
    async def compress_conversation(self, conversation: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        壓縮對話歷史
        
        Args:
            conversation: 對話列表
        
        Returns:
            壓縮後的對話列表
        """
        try:
            if not conversation:
                return []
            
            # 計算要保留的消息數
            keep_count = max(1, int(len(conversation) * self.compression_ratio))
            
            # 保留最後 keep_count 條消息
            compressed = conversation[-keep_count:]
            
            log.info(f"✅ 對話已壓縮: {len(conversation)} -> {len(compressed)}")
            return compressed
        
        except Exception as e:
            log.error(f"❌ 對話壓縮失敗: {e}")
            return conversation
    
    async def remove_redundant_messages(self, conversation: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        移除冗餘消息
        
        Args:
            conversation: 對話列表
        
        Returns:
            移除冗餘後的對話列表
        """
        try:
            if not conversation:
                return []
            
            filtered = []
            prev_content = None
            
            for msg in conversation:
                content = msg.get("content", "")
                
                # 跳過重複的消息
                if content != prev_content:
                    filtered.append(msg)
                    prev_content = content
            
            log.info(f"✅ 冗餘消息已移除: {len(conversation)} -> {len(filtered)}")
            return filtered
        
        except Exception as e:
            log.error(f"❌ 移除冗餘消息失敗: {e}")
            return conversation
    
    async def summarize_conversation(self, conversation: List[Dict[str, str]], max_length: int = 200) -> str:
        """
        總結對話
        
        Args:
            conversation: 對話列表
            max_length: 最大長度
        
        Returns:
            總結文本
        """
        try:
            if not conversation:
                return ""
            
            # 簡單的總結方法：提取關鍵信息
            summary_parts = []
            
            for msg in conversation:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                # 提取前 50 個字符
                short_content = content[:50] + "..." if len(content) > 50 else content
                summary_parts.append(f"{role}: {short_content}")
            
            summary = "\n".join(summary_parts)
            
            # 截斷到最大長度
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            log.info(f"✅ 對話已總結: {len(summary)} 字符")
            return summary
        
        except Exception as e:
            log.error(f"❌ 對話總結失敗: {e}")
            return ""


class PromptOptimizer:
    """Prompt 優化器 - 優化 Prompt 結構以減少 Token 使用"""
    
    def __init__(self):
        """初始化 Prompt 優化器"""
        log.info("✅ Prompt 優化器已初始化")
    
    async def optimize_system_instruction(self, instruction: str) -> str:
        """
        優化系統指令
        
        Args:
            instruction: 原始系統指令
        
        Returns:
            優化後的系統指令
        """
        try:
            # 移除冗餘的空格和換行
            optimized = " ".join(instruction.split())
            
            # 移除重複的句子
            sentences = optimized.split("。")
            unique_sentences = []
            for sentence in sentences:
                if sentence.strip() and sentence.strip() not in unique_sentences:
                    unique_sentences.append(sentence.strip())
            
            optimized = "。".join(unique_sentences)
            
            log.info(f"✅ 系統指令已優化: {len(instruction)} -> {len(optimized)} 字符")
            return optimized
        
        except Exception as e:
            log.error(f"❌ 系統指令優化失敗: {e}")
            return instruction
    
    async def optimize_user_prompt(self, prompt: str, max_length: int = 500) -> str:
        """
        優化用戶 Prompt
        
        Args:
            prompt: 原始 Prompt
            max_length: 最大長度
        
        Returns:
            優化後的 Prompt
        """
        try:
            # 移除冗餘的空格和換行
            optimized = " ".join(prompt.split())
            
            # 截斷到最大長度
            if len(optimized) > max_length:
                optimized = optimized[:max_length] + "..."
            
            log.info(f"✅ 用戶 Prompt 已優化: {len(prompt)} -> {len(optimized)} 字符")
            return optimized
        
        except Exception as e:
            log.error(f"❌ 用戶 Prompt 優化失敗: {e}")
            return prompt
    
    async def build_efficient_context(
        self, 
        system_instruction: str,
        conversation_history: List[Dict[str, str]],
        max_tokens: int = 2000
    ) -> Tuple[str, int]:
        """
        構建高效的 Context
        
        Args:
            system_instruction: 系統指令
            conversation_history: 對話歷史
            max_tokens: 最大 Token 數
        
        Returns:
            (構建的 context, 使用的 tokens)
        """
        try:
            token_counter = TokenCounter()
            
            # 計算系統指令的 tokens
            system_tokens = token_counter.count_tokens(system_instruction)
            remaining_tokens = max_tokens - system_tokens
            
            # 添加對話歷史
            context_parts = [system_instruction]
            current_tokens = system_tokens
            
            for msg in reversed(conversation_history):
                msg_text = f"{msg.get('role')}: {msg.get('content')}"
                msg_tokens = token_counter.count_tokens(msg_text)
                
                if current_tokens + msg_tokens <= max_tokens:
                    context_parts.insert(1, msg_text)
                    current_tokens += msg_tokens
                else:
                    break
            
            context = "\n".join(context_parts)
            
            log.info(f"✅ 高效 Context 已構建: {current_tokens} tokens")
            return context, current_tokens
        
        except Exception as e:
            log.error(f"❌ 構建高效 Context 失敗: {e}")
            return system_instruction, 0


class TokenOptimizationService:
    """Token 優化服務 - 統一的 Token 優化接口"""
    
    def __init__(self):
        """初始化 Token 優化服務"""
        self.token_counter = TokenCounter()
        self.context_compressor = ContextCompressor(compression_ratio=0.7)
        self.prompt_optimizer = PromptOptimizer()
        
        log.info("✅ Token 優化服務已初始化")
    
    async def optimize_for_llm_call(
        self,
        system_instruction: str,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        max_tokens: int = 2000,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        為 LLM 調用優化 Token 使用
        
        Args:
            system_instruction: 系統指令
            conversation_history: 對話歷史
            user_message: 用戶消息
            max_tokens: 最大 Token 數
            session_id: 可選的 session ID
        
        Returns:
            優化結果
        """
        try:
            # 1. 壓縮對話歷史
            compressed_history = await self.context_compressor.compress_conversation(
                conversation_history
            )
            
            # 2. 移除冗餘消息
            filtered_history = await self.context_compressor.remove_redundant_messages(
                compressed_history
            )
            
            # 3. 優化系統指令
            optimized_instruction = await self.prompt_optimizer.optimize_system_instruction(
                system_instruction
            )
            
            # 4. 優化用戶消息
            optimized_message = await self.prompt_optimizer.optimize_user_prompt(
                user_message,
                max_length=500
            )
            
            # 5. 構建高效 Context
            context, tokens_used = await self.prompt_optimizer.build_efficient_context(
                optimized_instruction,
                filtered_history,
                max_tokens
            )
            
            # 6. 記錄 Token 使用
            if session_id:
                self.token_counter.add_prompt_tokens(context, session_id)
            
            return {
                "optimized_context": context,
                "optimized_message": optimized_message,
                "tokens_used": tokens_used,
                "compression_ratio": len(filtered_history) / max(1, len(conversation_history)),
                "original_history_length": len(conversation_history),
                "compressed_history_length": len(filtered_history)
            }
        
        except Exception as e:
            log.error(f"❌ Token 優化失敗: {e}")
            return {
                "error": str(e),
                "optimized_context": system_instruction,
                "optimized_message": user_message,
                "tokens_used": 0
            }
    
    async def get_optimization_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取優化報告
        
        Args:
            session_id: 可選的 session ID
        
        Returns:
            優化報告
        """
        try:
            stats = self.token_counter.get_statistics()
            
            if session_id:
                session_tokens = self.token_counter.get_session_tokens(session_id)
                round_tokens = self.token_counter.get_round_tokens(session_id)
                
                return {
                    "session_id": session_id,
                    "session_tokens": session_tokens,
                    "round_tokens": round_tokens,
                    "avg_tokens_per_round": int(sum(round_tokens) / len(round_tokens)) if round_tokens else 0,
                    "global_stats": stats
                }
            
            return stats
        
        except Exception as e:
            log.error(f"❌ 獲取優化報告失敗: {e}")
            return {}


# 全局 Token 優化服務實例
_token_optimization_service: Optional[TokenOptimizationService] = None

def get_token_optimization_service() -> TokenOptimizationService:
    """獲取 Token 優化服務實例"""
    global _token_optimization_service
    if _token_optimization_service is None:
        _token_optimization_service = TokenOptimizationService()
    return _token_optimization_service


