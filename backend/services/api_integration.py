"""
backend/services/api_integration.py - API端點集成
提供REST API端點，整合所有Phase 3服務
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .evaluation_integration import get_evaluation_integration
from .conversational_style_processor import get_conversational_style_processor
from .response_length_controller import get_response_length_controller

logger = logging.getLogger(__name__)


class APIIntegration:
    """API集成服務"""
    
    def __init__(self):
        """初始化API集成"""
        self.evaluation_integration = get_evaluation_integration()
        self.style_processor = get_conversational_style_processor()
        self.length_controller = get_response_length_controller()
        
        logger.info("✅ APIIntegration initialized")
    
    async def handle_expert_evaluation(
        self,
        session_id: str,
        scam_type: str,
        user_message: str,
        expert_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        處理專家評估請求
        
        Args:
            session_id: 會話ID
            scam_type: 騙案類型
            user_message: 用戶消息
            expert_response: 專家回應
            metadata: 額外元數據
        
        Returns:
            API響應
        """
        try:
            logger.info(f"🔄 Handling expert evaluation request for session {session_id}")
            
            # 1. 處理專家回應
            processing_result = await self.evaluation_integration.process_expert_response(
                response=expert_response,
                session_id=session_id,
                scam_type=scam_type,
                user_message=user_message,
                metadata=metadata
            )
            
            if not processing_result.get('success'):
                logger.error(f"❌ Processing failed: {processing_result.get('error')}")
                return {
                    'success': False,
                    'error': processing_result.get('error'),
                    'status_code': 500
                }
            
            # 2. 驗證回應質量
            quality_result = await self.evaluation_integration.validate_response_quality(
                response=processing_result['final_response'],
                scam_type=scam_type
            )
            
            # 3. 構建API響應
            api_response = {
                'success': True,
                'status_code': 200,
                'data': {
                    'session_id': session_id,
                    'scam_type': scam_type,
                    'original_response': processing_result['original_response'],
                    'final_response': processing_result['final_response'],
                    'length_valid': processing_result['length_valid'],
                    'quality_score': quality_result.get('quality_score'),
                    'quality_level': quality_result.get('quality_level'),
                    'evaluation_record_id': processing_result['evaluation_record'].get('id')
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Expert evaluation handled successfully")
            return api_response
        
        except Exception as e:
            logger.error(f"❌ Failed to handle expert evaluation: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    async def handle_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        處理會話摘要請求
        
        Args:
            session_id: 會話ID
        
        Returns:
            API響應
        """
        try:
            logger.info(f"🔄 Handling session summary request for {session_id}")
            
            # 獲取評估摘要
            summary = await self.evaluation_integration.get_session_evaluation_summary(session_id)
            
            api_response = {
                'success': True,
                'status_code': 200,
                'data': summary,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Session summary handled successfully")
            return api_response
        
        except Exception as e:
            logger.error(f"❌ Failed to handle session summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    async def handle_response_processing(
        self,
        response: str,
        processing_type: str = 'full'
    ) -> Dict[str, Any]:
        """
        處理回應處理請求
        
        Args:
            response: 原始回應
            processing_type: 處理類型 ('full', 'conversational', 'length_control')
        
        Returns:
            API響應
        """
        try:
            logger.info(f"🔄 Handling response processing request: {processing_type}")
            
            result = {
                'success': True,
                'status_code': 200,
                'data': {
                    'original_response': response,
                    'processing_type': processing_type
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 根據處理類型進行處理
            if processing_type in ['full', 'conversational']:
                conversational = await self.style_processor.process(response)
                result['data']['conversational_response'] = conversational
            
            if processing_type in ['full', 'length_control']:
                length_controlled = await self.length_controller.process(response)
                result['data']['length_controlled_response'] = length_controlled
                
                is_valid, details = await self.length_controller.validate_length(length_controlled)
                result['data']['length_valid'] = is_valid
                result['data']['length_details'] = details
            
            if processing_type == 'full':
                # 完整處理
                conversational = await self.style_processor.process(response)
                final = await self.length_controller.process(conversational)
                result['data']['final_response'] = final
            
            logger.info(f"✅ Response processing handled successfully")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to handle response processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    async def handle_quality_validation(
        self,
        response: str,
        scam_type: str
    ) -> Dict[str, Any]:
        """
        處理質量驗證請求
        
        Args:
            response: 回應文本
            scam_type: 騙案類型
        
        Returns:
            API響應
        """
        try:
            logger.info(f"🔄 Handling quality validation request for {scam_type}")
            
            # 驗證回應質量
            quality_result = await self.evaluation_integration.validate_response_quality(
                response=response,
                scam_type=scam_type
            )
            
            api_response = {
                'success': True,
                'status_code': 200,
                'data': quality_result,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Quality validation handled successfully")
            return api_response
        
        except Exception as e:
            logger.error(f"❌ Failed to handle quality validation: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    async def handle_system_prompt_generation(self, scam_type: str) -> Dict[str, Any]:
        """
        處理System Prompt生成請求
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            API響應
        """
        try:
            logger.info(f"🔄 Handling system prompt generation for {scam_type}")
            
            # 構建專家System Prompt
            system_prompt = await self.evaluation_integration.build_expert_system_prompt(scam_type)
            
            api_response = {
                'success': True,
                'status_code': 200,
                'data': {
                    'scam_type': scam_type,
                    'system_prompt': system_prompt,
                    'prompt_length': len(system_prompt)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ System prompt generation handled successfully")
            return api_response
        
        except Exception as e:
            logger.error(f"❌ Failed to handle system prompt generation: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }


# 全局實例
_api_integration = None


def get_api_integration() -> APIIntegration:
    """獲取API集成實例"""
    global _api_integration
    if _api_integration is None:
        _api_integration = APIIntegration()
    return _api_integration


