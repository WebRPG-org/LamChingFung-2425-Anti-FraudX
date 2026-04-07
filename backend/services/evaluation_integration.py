"""
backend/services/evaluation_integration.py - 評估記錄器集成
整合口語化、長度控制、評估記錄
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .conversational_style_processor import get_conversational_style_processor
from .response_length_controller import get_response_length_controller
from .evaluation_recorder import get_evaluation_recorder

logger = logging.getLogger(__name__)


class EvaluationIntegration:
    """評估集成服務"""
    
    def __init__(self):
        """初始化評估集成"""
        self.style_processor = get_conversational_style_processor()
        self.length_controller = get_response_length_controller(max_length=80, max_tokens=100)
        self.recorder = get_evaluation_recorder()
        
        logger.info("✅ EvaluationIntegration initialized")
    
    async def process_expert_response(
        self,
        response: str,
        session_id: str,
        scam_type: str,
        user_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        處理專家回應的完整流程
        
        Args:
            response: 原始回應
            session_id: 會話ID
            scam_type: 騙案類型
            user_message: 用戶消息
            metadata: 額外元數據
        
        Returns:
            處理結果
        """
        try:
            logger.info(f"🔄 Processing expert response for session {session_id}")
            
            # 1. 應用口語化風格
            conversational = await self.style_processor.process(response)
            logger.info(f"✅ Applied conversational style")
            
            # 2. 控制回應長度
            length_controlled = await self.length_controller.process(conversational)
            logger.info(f"✅ Controlled response length: {len(length_controlled)} chars")
            
            # 3. 驗證長度
            is_valid, length_details = await self.length_controller.validate_length(length_controlled)
            logger.info(f"✅ Length validation: {is_valid}")
            
            # 4. 記錄評估
            evaluation_record = await self.recorder.record_evaluation(
                session_id=session_id,
                scam_type=scam_type,
                user_message=user_message,
                expert_response=length_controlled,
                metadata={
                    **(metadata or {}),
                    'original_length': len(response),
                    'conversational_length': len(conversational),
                    'final_length': len(length_controlled),
                    'length_details': length_details,
                    'processing_timestamp': datetime.now().isoformat()
                }
            )
            logger.info(f"✅ Recorded evaluation: {evaluation_record.get('id')}")
            
            # 5. 構建結果
            result = {
                'success': True,
                'session_id': session_id,
                'original_response': response,
                'conversational_response': conversational,
                'final_response': length_controlled,
                'length_valid': is_valid,
                'length_details': length_details,
                'evaluation_record': evaluation_record,
                'processing_steps': [
                    'conversational_style_applied',
                    'length_controlled',
                    'length_validated',
                    'evaluation_recorded'
                ]
            }
            
            logger.info(f"✅ Expert response processing completed")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to process expert response: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    async def build_expert_system_prompt(self, scam_type: str) -> str:
        """
        構建完整的專家System Prompt
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            完整的System Prompt
        """
        try:
            logger.info(f"🔄 Building expert system prompt for {scam_type}")
            
            # 1. 獲取口語化Prompt
            conversational_prompt = await self.style_processor.get_expert_prompt(scam_type)
            
            # 2. 添加長度控制指令
            length_controlled_prompt = await self.length_controller.build_length_controlled_prompt(
                conversational_prompt
            )
            
            logger.info(f"✅ Expert system prompt built")
            return length_controlled_prompt
        
        except Exception as e:
            logger.error(f"❌ Failed to build expert system prompt: {e}")
            return ""
    
    async def get_session_evaluation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話評估摘要
        
        Args:
            session_id: 會話ID
        
        Returns:
            評估摘要
        """
        try:
            logger.info(f"🔄 Getting evaluation summary for session {session_id}")
            
            # 從評估記錄器獲取會話記錄
            session_records = await self.recorder.get_session_records(session_id)
            
            if not session_records:
                logger.warning(f"⚠️ No records found for session {session_id}")
                return {
                    'session_id': session_id,
                    'records_count': 0,
                    'summary': 'No records found'
                }
            
            # 計算統計信息
            total_records = len(session_records)
            avg_response_length = sum(
                len(r.get('expert_response', '')) for r in session_records
            ) / total_records if total_records > 0 else 0
            
            scam_types = set(r.get('scam_type') for r in session_records)
            
            summary = {
                'session_id': session_id,
                'records_count': total_records,
                'avg_response_length': avg_response_length,
                'scam_types': list(scam_types),
                'records': session_records,
                'summary_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Evaluation summary retrieved: {total_records} records")
            return summary
        
        except Exception as e:
            logger.error(f"❌ Failed to get evaluation summary: {e}")
            return {
                'session_id': session_id,
                'error': str(e)
            }
    
    async def validate_response_quality(
        self,
        response: str,
        scam_type: str
    ) -> Dict[str, Any]:
        """
        驗證回應質量
        
        Args:
            response: 回應文本
            scam_type: 騙案類型
        
        Returns:
            質量驗證結果
        """
        try:
            logger.info(f"🔄 Validating response quality for {scam_type}")
            
            # 1. 檢查長度
            is_length_valid, length_details = await self.length_controller.validate_length(response)
            
            # 2. 檢查是否包含關鍵詞
            key_phrases = ['詐騙', '小心', '建議', '留意', '不要']
            has_key_phrases = any(phrase in response for phrase in key_phrases)
            
            # 3. 檢查是否是口語化
            formal_markers = ['【', '】', '**', '__', '##']
            is_conversational = not any(marker in response for marker in formal_markers)
            
            # 4. 計算質量分數
            quality_score = 0
            if is_length_valid:
                quality_score += 30
            if has_key_phrases:
                quality_score += 35
            if is_conversational:
                quality_score += 35
            
            result = {
                'response': response,
                'scam_type': scam_type,
                'length_valid': is_length_valid,
                'length_details': length_details,
                'has_key_phrases': has_key_phrases,
                'is_conversational': is_conversational,
                'quality_score': quality_score,
                'quality_level': self._get_quality_level(quality_score),
                'validation_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Response quality validated: score={quality_score}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to validate response quality: {e}")
            return {
                'error': str(e),
                'scam_type': scam_type
            }
    
    def _get_quality_level(self, score: int) -> str:
        """根據分數獲取質量等級"""
        if score >= 90:
            return '優秀'
        elif score >= 70:
            return '良好'
        elif score >= 50:
            return '中等'
        else:
            return '需改進'


# 全局實例
_integration = None


def get_evaluation_integration() -> EvaluationIntegration:
    """獲取評估集成實例"""
    global _integration
    if _integration is None:
        _integration = EvaluationIntegration()
    return _integration


