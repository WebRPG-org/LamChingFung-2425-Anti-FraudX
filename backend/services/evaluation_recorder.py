"""
backend/services/evaluation_recorder.py - 評估系統升級
記錄受害者、騙徒、專家的完整評估
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PlayerRole(Enum):
    """玩家角色"""
    SCAMMER = "scammer"
    EXPERT = "expert"
    VICTIM = "victim"


class EvaluationRecorder:
    """評估系統 - 記錄三角評估"""
    
    def __init__(self):
        """初始化評估記錄器"""
        self.evaluations = {}
        logger.info("✅ EvaluationRecorder initialized")
    
    # ============================================================
    # 受害者評估
    # ============================================================
    
    async def record_victim_evaluation(self, session_id: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        記錄受害者評估
        
        Args:
            session_id: Session ID
            evaluation_data: 評估數據
        
        Returns:
            評估結果
        """
        try:
            logger.info(f"📋 Recording victim evaluation: {session_id}")
            
            victim_eval = {
                'session_id': session_id,
                'role': PlayerRole.VICTIM.value,
                'evaluation_type': 'victim',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'alertness': evaluation_data.get('alertness', 0),
                    'trust_in_scammer': evaluation_data.get('trust_in_scammer', 0),
                    'trust_in_expert': evaluation_data.get('trust_in_expert', 0),
                    'response_type': evaluation_data.get('response_type', 'unknown'),
                    'vulnerability_points': evaluation_data.get('vulnerability_points', []),
                    'decision_making': evaluation_data.get('decision_making', {}),
                    'learning_points': evaluation_data.get('learning_points', [])
                }
            }
            
            # 保存到本地
            if session_id not in self.evaluations:
                self.evaluations[session_id] = {}
            self.evaluations[session_id]['victim'] = victim_eval
            
            # 保存到Firestore
            await self._save_to_firestore(session_id, 'victim', victim_eval)
            
            logger.info(f"✅ Victim evaluation recorded: {session_id}")
            return victim_eval
        
        except Exception as e:
            logger.error(f"❌ Failed to record victim evaluation: {e}")
            raise
    
    # ============================================================
    # 騙徒評估
    # ============================================================
    
    async def record_scammer_evaluation(self, session_id: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        記錄騙徒評估
        
        Args:
            session_id: Session ID
            evaluation_data: 評估數據
        
        Returns:
            評估結果
        """
        try:
            logger.info(f"📋 Recording scammer evaluation: {session_id}")
            
            scammer_eval = {
                'session_id': session_id,
                'role': PlayerRole.SCAMMER.value,
                'evaluation_type': 'scammer',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'tactics_used': evaluation_data.get('tactics_used', []),
                    'tactic_effectiveness': evaluation_data.get('tactic_effectiveness', {}),
                    'strategy_score': evaluation_data.get('strategy_score', 0),
                    'success_rate': evaluation_data.get('success_rate', 0),
                    'victim_manipulation': evaluation_data.get('victim_manipulation', {}),
                    'improvement_suggestions': evaluation_data.get('improvement_suggestions', []),
                    'credit_score': evaluation_data.get('credit_score', 0)
                }
            }
            
            # 保存到本地
            if session_id not in self.evaluations:
                self.evaluations[session_id] = {}
            self.evaluations[session_id]['scammer'] = scammer_eval
            
            # 保存到Firestore
            await self._save_to_firestore(session_id, 'scammer', scammer_eval)
            
            logger.info(f"✅ Scammer evaluation recorded: {session_id}")
            return scammer_eval
        
        except Exception as e:
            logger.error(f"❌ Failed to record scammer evaluation: {e}")
            raise
    
    # ============================================================
    # 專家評估
    # ============================================================
    
    async def record_expert_evaluation(self, session_id: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        記錄專家評估
        
        Args:
            session_id: Session ID
            evaluation_data: 評估數據
        
        Returns:
            評估結果
        """
        try:
            logger.info(f"📋 Recording expert evaluation: {session_id}")
            
            expert_eval = {
                'session_id': session_id,
                'role': PlayerRole.EXPERT.value,
                'evaluation_type': 'expert',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'prevention_methods': evaluation_data.get('prevention_methods', []),
                    'prevention_effectiveness': evaluation_data.get('prevention_effectiveness', {}),
                    'strategy_score': evaluation_data.get('strategy_score', 0),
                    'victim_protection_rate': evaluation_data.get('victim_protection_rate', 0),
                    'advice_quality': evaluation_data.get('advice_quality', {}),
                    'improvement_suggestions': evaluation_data.get('improvement_suggestions', []),
                    'credit_score': evaluation_data.get('credit_score', 0)
                }
            }
            
            # 保存到本地
            if session_id not in self.evaluations:
                self.evaluations[session_id] = {}
            self.evaluations[session_id]['expert'] = expert_eval
            
            # 保存到Firestore
            await self._save_to_firestore(session_id, 'expert', expert_eval)
            
            logger.info(f"✅ Expert evaluation recorded: {session_id}")
            return expert_eval
        
        except Exception as e:
            logger.error(f"❌ Failed to record expert evaluation: {e}")
            raise
    
    # ============================================================
    # 三角評估
    # ============================================================
    
    async def record_complete_evaluation(self, session_id: str, 
                                        victim_eval: Dict[str, Any],
                                        scammer_eval: Dict[str, Any],
                                        expert_eval: Dict[str, Any]) -> Dict[str, Any]:
        """
        記錄完整的三角評估
        
        Args:
            session_id: Session ID
            victim_eval: 受害者評估
            scammer_eval: 騙徒評估
            expert_eval: 專家評估
        
        Returns:
            完整評估結果
        """
        try:
            logger.info(f"📋 Recording complete evaluation: {session_id}")
            
            # 記錄各角色評估
            await self.record_victim_evaluation(session_id, victim_eval)
            await self.record_scammer_evaluation(session_id, scammer_eval)
            await self.record_expert_evaluation(session_id, expert_eval)
            
            # 生成綜合評估
            complete_eval = {
                'session_id': session_id,
                'evaluation_type': 'complete',
                'timestamp': datetime.now().isoformat(),
                'victim_evaluation': victim_eval,
                'scammer_evaluation': scammer_eval,
                'expert_evaluation': expert_eval,
                'summary': self._generate_summary(victim_eval, scammer_eval, expert_eval)
            }
            
            # 保存到Firestore
            await self._save_to_firestore(session_id, 'complete', complete_eval)
            
            logger.info(f"✅ Complete evaluation recorded: {session_id}")
            return complete_eval
        
        except Exception as e:
            logger.error(f"❌ Failed to record complete evaluation: {e}")
            raise
    
    # ============================================================
    # 自動訓練模式評估
    # ============================================================
    
    async def record_auto_training_evaluation(self, session_id: str, 
                                             dialogue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        記錄自動訓練模式的評估
        
        Args:
            session_id: Session ID
            dialogue_data: 對話數據
        
        Returns:
            自動訓練評估結果
        """
        try:
            logger.info(f"📋 Recording auto-training evaluation: {session_id}")
            
            # 從對話數據自動生成評估
            victim_eval = self._auto_generate_victim_eval(dialogue_data)
            scammer_eval = self._auto_generate_scammer_eval(dialogue_data)
            expert_eval = self._auto_generate_expert_eval(dialogue_data)
            
            # 記錄完整評估
            complete_eval = await self.record_complete_evaluation(
                session_id,
                victim_eval,
                scammer_eval,
                expert_eval
            )
            
            logger.info(f"✅ Auto-training evaluation recorded: {session_id}")
            return complete_eval
        
        except Exception as e:
            logger.error(f"❌ Failed to record auto-training evaluation: {e}")
            raise
    
    # ============================================================
    # 評估查詢
    # ============================================================
    
    async def get_evaluation(self, session_id: str, role: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取評估
        
        Args:
            session_id: Session ID
            role: 角色（可選）
        
        Returns:
            評估數據
        """
        try:
            if session_id not in self.evaluations:
                logger.warning(f"⚠️ No evaluation found: {session_id}")
                return {}
            
            if role:
                return self.evaluations[session_id].get(role, {})
            else:
                return self.evaluations[session_id]
        
        except Exception as e:
            logger.error(f"❌ Failed to get evaluation: {e}")
            raise
    
    # ============================================================
    # 評估分析
    # ============================================================
    
    async def analyze_evaluation(self, session_id: str) -> Dict[str, Any]:
        """
        分析評估
        
        Args:
            session_id: Session ID
        
        Returns:
            分析結果
        """
        try:
            logger.info(f"📊 Analyzing evaluation: {session_id}")
            
            evaluation = await self.get_evaluation(session_id)
            
            if not evaluation:
                return {'error': 'No evaluation found'}
            
            analysis = {
                'session_id': session_id,
                'analysis_time': datetime.now().isoformat(),
                'victim_analysis': self._analyze_victim(evaluation.get('victim', {})),
                'scammer_analysis': self._analyze_scammer(evaluation.get('scammer', {})),
                'expert_analysis': self._analyze_expert(evaluation.get('expert', {})),
                'comparative_analysis': self._comparative_analysis(evaluation)
            }
            
            logger.info(f"✅ Evaluation analysis completed: {session_id}")
            return analysis
        
        except Exception as e:
            logger.error(f"❌ Failed to analyze evaluation: {e}")
            raise
    
    # ============================================================
    # 輔助方法
    # ============================================================
    
    def _generate_summary(self, victim_eval: Dict, scammer_eval: Dict, expert_eval: Dict) -> Dict[str, Any]:
        """生成評估摘要"""
        return {
            'victim_alertness': victim_eval.get('alertness', 0),
            'scammer_effectiveness': scammer_eval.get('strategy_score', 0),
            'expert_effectiveness': expert_eval.get('strategy_score', 0),
            'overall_outcome': self._determine_outcome(victim_eval, scammer_eval, expert_eval)
        }
    
    def _determine_outcome(self, victim_eval: Dict, scammer_eval: Dict, expert_eval: Dict) -> str:
        """判定遊戲結果"""
        victim_alertness = victim_eval.get('alertness', 0)
        scammer_score = scammer_eval.get('strategy_score', 0)
        expert_score = expert_eval.get('strategy_score', 0)
        
        if scammer_score > expert_score and victim_alertness < 50:
            return "scammer_win"
        elif expert_score > scammer_score and victim_alertness > 50:
            return "expert_win"
        else:
            return "draw"
    
    def _auto_generate_victim_eval(self, dialogue_data: Dict) -> Dict[str, Any]:
        """自動生成受害者評估"""
        return {
            'alertness': dialogue_data.get('alertness', 50),
            'trust_in_scammer': dialogue_data.get('trust_in_scammer', 50),
            'trust_in_expert': dialogue_data.get('trust_in_expert', 50),
            'response_type': dialogue_data.get('response_type', 'neutral'),
            'vulnerability_points': dialogue_data.get('vulnerability_points', []),
            'decision_making': dialogue_data.get('decision_making', {}),
            'learning_points': dialogue_data.get('learning_points', [])
        }
    
    def _auto_generate_scammer_eval(self, dialogue_data: Dict) -> Dict[str, Any]:
        """自動生成騙徒評估"""
        return {
            'tactics_used': dialogue_data.get('tactics_used', []),
            'tactic_effectiveness': dialogue_data.get('tactic_effectiveness', {}),
            'strategy_score': dialogue_data.get('scammer_score', 0),
            'success_rate': dialogue_data.get('success_rate', 0),
            'victim_manipulation': dialogue_data.get('victim_manipulation', {}),
            'improvement_suggestions': dialogue_data.get('scammer_improvements', []),
            'credit_score': dialogue_data.get('scammer_credit', 0)
        }
    
    def _auto_generate_expert_eval(self, dialogue_data: Dict) -> Dict[str, Any]:
        """自動生成專家評估"""
        return {
            'prevention_methods': dialogue_data.get('prevention_methods', []),
            'prevention_effectiveness': dialogue_data.get('prevention_effectiveness', {}),
            'strategy_score': dialogue_data.get('expert_score', 0),
            'victim_protection_rate': dialogue_data.get('protection_rate', 0),
            'advice_quality': dialogue_data.get('advice_quality', {}),
            'improvement_suggestions': dialogue_data.get('expert_improvements', []),
            'credit_score': dialogue_data.get('expert_credit', 0)
        }
    
    def _analyze_victim(self, victim_eval: Dict) -> Dict[str, Any]:
        """分析受害者評估"""
        return {
            'alertness_level': self._categorize_alertness(victim_eval.get('alertness', 0)),
            'trust_balance': {
                'scammer': victim_eval.get('trust_in_scammer', 0),
                'expert': victim_eval.get('trust_in_expert', 0)
            },
            'vulnerabilities': victim_eval.get('vulnerability_points', []),
            'learning_outcomes': victim_eval.get('learning_points', [])
        }
    
    def _analyze_scammer(self, scammer_eval: Dict) -> Dict[str, Any]:
        """分析騙徒評估"""
        return {
            'effectiveness': scammer_eval.get('strategy_score', 0),
            'tactics': scammer_eval.get('tactics_used', []),
            'success_rate': scammer_eval.get('success_rate', 0),
            'areas_for_improvement': scammer_eval.get('improvement_suggestions', [])
        }
    
    def _analyze_expert(self, expert_eval: Dict) -> Dict[str, Any]:
        """分析專家評估"""
        return {
            'effectiveness': expert_eval.get('strategy_score', 0),
            'prevention_methods': expert_eval.get('prevention_methods', []),
            'protection_rate': expert_eval.get('victim_protection_rate', 0),
            'areas_for_improvement': expert_eval.get('improvement_suggestions', [])
        }
    
    def _comparative_analysis(self, evaluation: Dict) -> Dict[str, Any]:
        """比較分析"""
        victim = evaluation.get('victim', {})
        scammer = evaluation.get('scammer', {})
        expert = evaluation.get('expert', {})
        
        return {
            'scammer_vs_expert': {
                'scammer_score': scammer.get('strategy_score', 0),
                'expert_score': expert.get('strategy_score', 0),
                'winner': 'scammer' if scammer.get('strategy_score', 0) > expert.get('strategy_score', 0) else 'expert'
            },
            'victim_response': {
                'alertness': victim.get('alertness', 0),
                'decision': 'vulnerable' if victim.get('alertness', 0) < 50 else 'alert'
            }
        }
    
    def _categorize_alertness(self, alertness: int) -> str:
        """分類警覺性"""
        if alertness < 30:
            return "low"
        elif alertness < 70:
            return "medium"
        else:
            return "high"
    
    async def _save_to_firestore(self, session_id: str, eval_type: str, data: Dict[str, Any]) -> bool:
        """保存到Firestore"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            
            # 保存到 sessions/{session_id}/evaluations 子集合
            db.collection('sessions').document(session_id).collection('evaluations').add({
                'type': eval_type,
                **data,
                'saved_at': datetime.now().isoformat()
            })
            
            logger.info(f"💾 Evaluation saved to Firestore: {session_id}/{eval_type}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to save evaluation to Firestore: {e}")
            return False


# 全局實例
_evaluation_recorder = None


def get_evaluation_recorder() -> EvaluationRecorder:
    """獲取評估記錄器實例"""
    global _evaluation_recorder
    if _evaluation_recorder is None:
        _evaluation_recorder = EvaluationRecorder()
    return _evaluation_recorder


