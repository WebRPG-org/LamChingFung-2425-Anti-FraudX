"""
SessionManager RAG集成實現
將RAG系統集成到SessionManager中
"""

from typing import Dict, Optional, Any
from datetime import datetime
import logging

from services.session_manager_rag_integration import SessionManagerRAGIntegration
from services.tactic_analyzer import get_tactic_analyzer
from services.verdict_judge import get_verdict_judge
from services.scam_scoring_v2 import get_scam_scorer
from services.firestore_rag_fraud_loader import FirestoreRAGContextProvider
from services.session_persistence_service import get_persistence_service
from services.evaluation_recorder import get_evaluation_recorder

log = logging.getLogger(__name__)


class SessionManagerWithRAG:
    """
    集成RAG系統的SessionManager
    
    功能：
    1. 使用RAG增強的system prompt生成對話
    2. 使用Phase 2.1分析對話內容
    3. 使用Phase 2.2判定勝負
    4. 使用Phase 2.3評分
    5. 使用RAG數據評估對話質量
    """
    
    def __init__(self):
        """初始化SessionManager"""
        self.rag_integration = SessionManagerRAGIntegration()
        self.rag_provider = FirestoreRAGContextProvider()
        self.tactic_analyzer = get_tactic_analyzer()
        self.verdict_judge = get_verdict_judge()
        self.scam_scorer = get_scam_scorer()
        self.persistence_service = get_persistence_service()
        self.evaluation_recorder = get_evaluation_recorder()
        
        # Session狀態
        self.session_id = None
        self.scam_type = None
        self.player_role = None
        self.system_prompt = None
        self.dialogue_history = []
        self.analysis_history = []
        
        log.info("✅ SessionManager with RAG initialized")
    
    async def initialize_session(self, session_id: str, scam_type: str, player_role: str) -> Dict[str, Any]:
        """
        初始化Session（使用RAG增強的system prompt）
        
        Args:
            session_id: Session ID
            scam_type: 騙案類型
            player_role: 玩家角色 (scammer/expert/victim)
        
        Returns:
            初始化結果
        """
        try:
            self.session_id = session_id
            self.scam_type = scam_type
            self.player_role = player_role
            
            log.info(f"🔄 Initializing session: {session_id} ({scam_type}, {player_role})")
            
            # 1. 獲取RAG增強的system prompt
            if player_role == "scammer":
                self.system_prompt = await self.rag_integration.get_scammer_system_prompt(scam_type)
            elif player_role == "expert":
                self.system_prompt = await self.rag_integration.get_expert_system_prompt(scam_type)
            elif player_role == "victim":
                self.system_prompt = await self.rag_integration.get_victim_system_prompt(scam_type)
            else:
                raise ValueError(f"Invalid player role: {player_role}")
            
            log.info(f"✅ RAG system prompt loaded for {player_role}")
            
            # 2. 初始化分析器
            self.tactic_analyzer.session_id = session_id
            self.verdict_judge.session_id = session_id
            self.scam_scorer.session_id = session_id
            
            log.info("✅ Analyzers initialized")
            
            # 3. 保存Session到Firestore
            session_data = {
                'session_id': session_id,
                'scam_type': scam_type,
                'player_role': player_role,
                'system_prompt_loaded': True,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            await self.persistence_service.save_session(session_id, session_data)
            log.info(f"💾 Session saved to Firestore: {session_id}")
            
            return {
                'status': 'success',
                'session_id': session_id,
                'scam_type': scam_type,
                'player_role': player_role,
                'system_prompt_loaded': True,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            log.error(f"❌ Session initialization failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def send_message(self, message: str, role: str = None) -> Dict[str, Any]:
        """
        發送消息並進行完整分析
        
        Args:
            message: 用戶消息
            role: 發送者角色 (可選，默認使用player_role)
        
        Returns:
            包含LLM回應和分析結果的字典
        """
        try:
            if not self.session_id:
                raise ValueError("Session not initialized")
            
            role = role or self.player_role
            
            log.info(f"📨 Processing message from {role}: {message[:50]}...")
            
            # 1. 生成LLM回應 (使用RAG增強的system prompt)
            llm_response = await self._generate_llm_response(message)
            
            log.info(f"✅ LLM response generated: {llm_response[:50]}...")
            
            # 2. Phase 2.1: 騙術分析
            tactic_result = await self._analyze_tactics(llm_response, role)
            
            # 3. Phase 2.2: 勝負判定
            verdict_result = await self._judge_verdict(llm_response, role)
            
            # 4. Phase 2.3: 評分
            score_result = await self._score_message(llm_response, role)
            
            # 5. 記錄到歷史
            self._record_to_history(message, llm_response, tactic_result, verdict_result, score_result)
            
            log.info(f"✅ Message processing completed")
            
            return {
                'status': 'success',
                'session_id': self.session_id,
                'role': role,
                'user_message': message,
                'llm_response': llm_response,
                'analysis': {
                    'tactics': tactic_result,
                    'verdict': verdict_result,
                    'score': score_result
                },
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            log.error(f"❌ Message processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _generate_llm_response(self, message: str) -> str:
        """
        生成LLM回應（使用RAG增強的system prompt）
        
        Args:
            message: 用戶消息
        
        Returns:
            LLM回應
        """
        try:
            # 這裡需要調用實際的LLM客戶端
            # 示例代碼，實際需要根據你的LLM集成方式修改
            
            from llms.llm_factory import get_llm_client
            
            llm_client = get_llm_client()
            
            response = await llm_client.chat(
                system_prompt=self.system_prompt,  # ← RAG增強的system prompt
                user_message=message,
                session_id=self.session_id
            )
            
            return response
        
        except Exception as e:
            log.error(f"❌ LLM response generation failed: {e}")
            raise
    
    async def _analyze_tactics(self, message: str, role: str) -> Dict[str, Any]:
        """
        Phase 2.1: 分析騙術
        
        Args:
            message: 消息內容
            role: 發送者角色
        
        Returns:
            分析結果
        """
        try:
            if role == "scammer":
                result = await self.tactic_analyzer.analyze_scammer_message(
                    message=message,
                    session_id=self.session_id
                )
            elif role == "expert":
                result = await self.tactic_analyzer.analyze_expert_message(
                    message=message,
                    session_id=self.session_id
                )
            else:
                result = {}
            
            log.info(f"✅ Tactic analysis completed for {role}")
            return result
        
        except Exception as e:
            log.error(f"❌ Tactic analysis failed: {e}")
            return {'error': str(e)}
    
    async def _judge_verdict(self, message: str, role: str) -> Dict[str, Any]:
        """
        Phase 2.2: 判定勝負
        
        Args:
            message: 消息內容
            role: 發送者角色
        
        Returns:
            判定結果
        """
        try:
            if role == "scammer":
                result = await self.verdict_judge.judge_scammer_win(
                    message=message,
                    session_id=self.session_id
                )
            elif role == "expert":
                result = await self.verdict_judge.judge_expert_win(
                    message=message,
                    session_id=self.session_id
                )
            else:
                result = {}
            
            log.info(f"✅ Verdict judgment completed for {role}")
            return result
        
        except Exception as e:
            log.error(f"❌ Verdict judgment failed: {e}")
            return {'error': str(e)}
    
    async def _score_message(self, message: str, role: str) -> Dict[str, Any]:
        """
        Phase 2.3: 評分
        
        Args:
            message: 消息內容
            role: 發送者角色
        
        Returns:
            評分結果
        """
        try:
            result = await self.scam_scorer.score_message(
                message=message,
                session_id=self.session_id,
                role=role
            )
            
            log.info(f"✅ Message scoring completed for {role}")
            return result
        
        except Exception as e:
            log.error(f"❌ Message scoring failed: {e}")
            return {'error': str(e)}
    
    def _record_to_history(self, user_msg: str, llm_response: str, 
                          tactic_result: Dict, verdict_result: Dict, score_result: Dict):
        """
        記錄到歷史並保存到Firestore
        
        Args:
            user_msg: 用戶消息
            llm_response: LLM回應
            tactic_result: 騙術分析結果
            verdict_result: 勝負判定結果
            score_result: 評分結果
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_msg,
            'llm_response': llm_response,
            'analysis': {
                'tactics': tactic_result,
                'verdict': verdict_result,
                'score': score_result
            }
        }
        
        self.dialogue_history.append(record)
        self.analysis_history.append(record['analysis'])
        
        # 保存對話到Firestore
        import asyncio
        conversation_data = {
            'session_id': self.session_id,
            'round_number': len(self.dialogue_history),
            'speaker': self.player_role,
            'message': user_msg,
            'llm_response': llm_response,
            'analysis': record['analysis'],
            'timestamp': record['timestamp']
        }
        
        try:
            asyncio.create_task(self.persistence_service.save_conversation(
                self.session_id,
                len(self.dialogue_history),
                self.player_role,
                user_msg,
                record['analysis']
            ))
        except Exception as e:
            log.error(f"❌ Failed to save conversation to Firestore: {e}")
        
        log.info(f"✅ Record saved to history (total: {len(self.dialogue_history)})")
    
    async def evaluate_dialogue(self) -> Dict[str, Any]:
        """
        對話評估（使用RAG數據）並保存到Firestore
        
        Returns:
            評估結果
        """
        try:
            if not self.dialogue_history:
                return {'status': 'error', 'error': 'No dialogue history'}
            
            log.info("🔄 Evaluating dialogue with RAG data...")
            
            # 1. 獲取RAG數據
            real_cases = await self.rag_provider.get_expert_context(self.scam_type)
            warning_signs = await self.rag_provider.get_warning_signs(self.scam_type)
            prevention_tips = await self.rag_provider.get_prevention_tips(self.scam_type)
            
            # 2. 評估對話質量
            dialogue_text = "\n".join([
                f"{record['user_message']}\n{record['llm_response']}"
                for record in self.dialogue_history
            ])
            
            evaluation = {
                'session_id': self.session_id,
                'scam_type': self.scam_type,
                'dialogue_length': len(self.dialogue_history),
                'quality_metrics': {
                    'realism_score': self._evaluate_realism(dialogue_text, real_cases),
                    'authenticity': self._evaluate_authenticity(dialogue_text, real_cases),
                    'warning_signs_coverage': self._evaluate_coverage(dialogue_text, warning_signs),
                    'prevention_tips_coverage': self._evaluate_coverage(dialogue_text, prevention_tips)
                },
                'analysis_summary': {
                    'total_tactics_detected': len([a for a in self.analysis_history if a.get('tactics')]),
                    'verdicts': [a.get('verdict') for a in self.analysis_history if a.get('verdict')],
                    'average_score': sum([a.get('score', {}).get('score', 0) for a in self.analysis_history]) / len(self.analysis_history) if self.analysis_history else 0
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 3. 保存評估到Firestore
            await self.persistence_service.save_analysis(self.session_id, evaluation)
            log.info(f"💾 Evaluation saved to Firestore: {self.session_id}")
            
            log.info(f"✅ Dialogue evaluation completed")
            return evaluation
        
        except Exception as e:
            log.error(f"❌ Dialogue evaluation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _evaluate_realism(self, dialogue: str, real_cases: str) -> float:
        """
        評估真實性（0-1）
        
        Args:
            dialogue: 對話文本
            real_cases: 真實案例
        
        Returns:
            真實性評分
        """
        # 簡單的相似度計算
        dialogue_words = set(dialogue.split())
        cases_words = set(real_cases.split())
        
        if not cases_words:
            return 0.5
        
        overlap = len(dialogue_words & cases_words)
        similarity = overlap / len(cases_words)
        
        return min(1.0, similarity)
    
    def _evaluate_authenticity(self, dialogue: str, real_cases: str) -> float:
        """
        評估真實案例相似度（0-1）
        
        Args:
            dialogue: 對話文本
            real_cases: 真實案例
        
        Returns:
            相似度評分
        """
        # 基於關鍵詞匹配
        dialogue_lower = dialogue.lower()
        cases_lower = real_cases.lower()
        
        # 計算匹配的關鍵詞
        keywords = ['銀行', '密碼', '驗證碼', '轉賬', '帳戶', '官方', '警察']
        matches = sum(1 for kw in keywords if kw in dialogue_lower and kw in cases_lower)
        
        return min(1.0, matches / len(keywords))
    
    def _evaluate_coverage(self, dialogue: str, items: list) -> float:
        """
        評估覆蓋率（0-1）
        
        Args:
            dialogue: 對話文本
            items: 項目列表
        
        Returns:
            覆蓋率評分
        """
        if not items:
            return 0.5
        
        dialogue_lower = dialogue.lower()
        covered = sum(1 for item in items if item.lower() in dialogue_lower)
        
        return covered / len(items)
    
    async def complete_evaluation(self, session_id: str) -> Dict[str, Any]:
        """
        完成Session評估（記錄三角評估）
        
        Args:
            session_id: Session ID
        
        Returns:
            完整評估結果
        """
        try:
            logger.info(f"📋 Completing session evaluation: {session_id}")
            
            # 1. 生成受害者評估
            victim_eval = await self._generate_victim_evaluation()
            
            # 2. 生成騙徒評估
            scammer_eval = await self._generate_scammer_evaluation()
            
            # 3. 生成專家評估
            expert_eval = await self._generate_expert_evaluation()
            
            # 4. 記錄完整評估
            complete_eval = await self.evaluation_recorder.record_complete_evaluation(
                session_id,
                victim_eval,
                scammer_eval,
                expert_eval
            )
            
            logger.info(f"✅ Session evaluation completed: {session_id}")
            return complete_eval
        
        except Exception as e:
            logger.error(f"❌ Session evaluation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _generate_victim_evaluation(self) -> Dict[str, Any]:
        """生成受害者評估"""
        try:
            # 從分析歷史計算受害者指標
            alertness = self._calculate_alertness()
            trust_in_scammer = self._calculate_trust_in_scammer()
            trust_in_expert = self._calculate_trust_in_expert()
            
            return {
                'alertness': alertness,
                'trust_in_scammer': trust_in_scammer,
                'trust_in_expert': trust_in_expert,
                'response_type': self._categorize_response_type(),
                'vulnerability_points': self._identify_vulnerabilities(),
                'decision_making': self._analyze_decision_making(),
                'learning_points': self._extract_learning_points()
            }
        except Exception as e:
            logger.error(f"❌ Failed to generate victim evaluation: {e}")
            return {}
    
    async def _generate_scammer_evaluation(self) -> Dict[str, Any]:
        """生成騙徒評估"""
        try:
            # 從分析歷史計算騙徒指標
            tactics_used = self._extract_tactics_used()
            strategy_score = self._calculate_scammer_strategy_score()
            success_rate = self._calculate_success_rate()
            
            return {
                'tactics_used': tactics_used,
                'tactic_effectiveness': self._analyze_tactic_effectiveness(tactics_used),
                'strategy_score': strategy_score,
                'success_rate': success_rate,
                'victim_manipulation': self._analyze_manipulation_techniques(),
                'improvement_suggestions': self._generate_scammer_improvements(),
                'credit_score': self.scam_scorer.scammer_credit if hasattr(self.scam_scorer, 'scammer_credit') else 0
            }
        except Exception as e:
            logger.error(f"❌ Failed to generate scammer evaluation: {e}")
            return {}
    
    async def _generate_expert_evaluation(self) -> Dict[str, Any]:
        """生成專家評估"""
        try:
            # 從分析歷史計算專家指標
            prevention_methods = self._extract_prevention_methods()
            strategy_score = self._calculate_expert_strategy_score()
            protection_rate = self._calculate_protection_rate()
            
            return {
                'prevention_methods': prevention_methods,
                'prevention_effectiveness': self._analyze_prevention_effectiveness(prevention_methods),
                'strategy_score': strategy_score,
                'victim_protection_rate': protection_rate,
                'advice_quality': self._analyze_advice_quality(),
                'improvement_suggestions': self._generate_expert_improvements(),
                'credit_score': self.scam_scorer.expert_credit if hasattr(self.scam_scorer, 'expert_credit') else 0
            }
        except Exception as e:
            logger.error(f"❌ Failed to generate expert evaluation: {e}")
            return {}
    
    # ============================================================
    # 評估計算輔助方法
    # ============================================================
    
    def _calculate_alertness(self) -> int:
        """計算警覺性"""
        if not self.analysis_history:
            return 50
        
        # 基於分析歷史計算
        alertness_scores = []
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'expert_win':
                alertness_scores.append(80)
            elif analysis.get('verdict') == 'scammer_win':
                alertness_scores.append(20)
            else:
                alertness_scores.append(50)
        
        return int(sum(alertness_scores) / len(alertness_scores)) if alertness_scores else 50
    
    def _calculate_trust_in_scammer(self) -> int:
        """計算對騙徒的信任度"""
        if not self.analysis_history:
            return 50
        
        trust_scores = []
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'scammer_win':
                trust_scores.append(80)
            elif analysis.get('verdict') == 'expert_win':
                trust_scores.append(20)
            else:
                trust_scores.append(50)
        
        return int(sum(trust_scores) / len(trust_scores)) if trust_scores else 50
    
    def _calculate_trust_in_expert(self) -> int:
        """計算對專家的信任度"""
        if not self.analysis_history:
            return 50
        
        trust_scores = []
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'expert_win':
                trust_scores.append(80)
            elif analysis.get('verdict') == 'scammer_win':
                trust_scores.append(20)
            else:
                trust_scores.append(50)
        
        return int(sum(trust_scores) / len(trust_scores)) if trust_scores else 50
    
    def _categorize_response_type(self) -> str:
        """分類回應類型"""
        if not self.dialogue_history:
            return "neutral"
        
        # 基於最後的回應判定
        last_response = self.dialogue_history[-1] if self.dialogue_history else {}
        if 'scammer' in str(last_response).lower():
            return "trusting"
        elif 'expert' in str(last_response).lower():
            return "cautious"
        else:
            return "neutral"
    
    def _identify_vulnerabilities(self) -> List[str]:
        """識別脆弱點"""
        vulnerabilities = []
        
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'scammer_win':
                vulnerabilities.append(f"Vulnerable to {analysis.get('tactics', 'unknown')}")
        
        return vulnerabilities
    
    def _analyze_decision_making(self) -> Dict[str, Any]:
        """分析決策過程"""
        return {
            'total_decisions': len(self.dialogue_history),
            'correct_decisions': len([a for a in self.analysis_history if a.get('verdict') == 'expert_win']),
            'incorrect_decisions': len([a for a in self.analysis_history if a.get('verdict') == 'scammer_win'])
        }
    
    def _extract_learning_points(self) -> List[str]:
        """提取學習要點"""
        learning_points = []
        
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'scammer_win':
                learning_points.append(f"Avoid falling for {analysis.get('tactics', 'scams')}")
            elif analysis.get('verdict') == 'expert_win':
                learning_points.append(f"Remember to {analysis.get('prevention', 'stay alert')}")
        
        return learning_points
    
    def _extract_tactics_used(self) -> List[str]:
        """提取使用的騙術"""
        tactics = []
        for analysis in self.analysis_history:
            if analysis.get('tactics'):
                tactics.append(analysis['tactics'])
        return tactics
    
    def _calculate_scammer_strategy_score(self) -> int:
        """計算騙徒策略評分"""
        if not self.analysis_history:
            return 0
        
        scores = []
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'scammer_win':
                scores.append(analysis.get('score', 10))
        
        return int(sum(scores) / len(scores)) if scores else 0
    
    def _calculate_success_rate(self) -> float:
        """計算成功率"""
        if not self.analysis_history:
            return 0.0
        
        wins = len([a for a in self.analysis_history if a.get('verdict') == 'scammer_win'])
        return (wins / len(self.analysis_history)) * 100 if self.analysis_history else 0.0
    
    def _analyze_tactic_effectiveness(self, tactics: List[str]) -> Dict[str, float]:
        """分析騙術有效性"""
        effectiveness = {}
        for tactic in tactics:
            effectiveness[tactic] = 0.75  # 示例值
        return effectiveness
    
    def _analyze_manipulation_techniques(self) -> Dict[str, Any]:
        """分析操縱技巧"""
        return {
            'emotional_manipulation': 0.6,
            'urgency_creation': 0.7,
            'trust_building': 0.8
        }
    
    def _generate_scammer_improvements(self) -> List[str]:
        """生成騙徒改進建議"""
        return [
            "Improve emotional manipulation techniques",
            "Create more urgency in requests",
            "Build stronger trust relationships"
        ]
    
    def _extract_prevention_methods(self) -> List[str]:
        """提取防騙方法"""
        methods = []
        for analysis in self.analysis_history:
            if analysis.get('prevention'):
                methods.append(analysis['prevention'])
        return methods
    
    def _calculate_expert_strategy_score(self) -> int:
        """計算專家策略評分"""
        if not self.analysis_history:
            return 0
        
        scores = []
        for analysis in self.analysis_history:
            if analysis.get('verdict') == 'expert_win':
                scores.append(analysis.get('score', 10))
        
        return int(sum(scores) / len(scores)) if scores else 0
    
    def _calculate_protection_rate(self) -> float:
        """計算保護率"""
        if not self.analysis_history:
            return 0.0
        
        wins = len([a for a in self.analysis_history if a.get('verdict') == 'expert_win'])
        return (wins / len(self.analysis_history)) * 100 if self.analysis_history else 0.0
    
    def _analyze_prevention_effectiveness(self, methods: List[str]) -> Dict[str, float]:
        """分析防騙有效性"""
        effectiveness = {}
        for method in methods:
            effectiveness[method] = 0.85  # 示例值
        return effectiveness
    
    def _analyze_advice_quality(self) -> Dict[str, Any]:
        """分析建議質量"""
        return {
            'clarity': 0.9,
            'relevance': 0.85,
            'actionability': 0.8
        }
    
    def _generate_expert_improvements(self) -> List[str]:
        """生成專家改進建議"""
        return [
            "Provide more specific prevention strategies",
            "Improve communication clarity",
            "Offer more actionable advice"
        ]
    
    async def get_evaluation_report(self, session_id: str) -> Dict[str, Any]:
        """
        獲取評估報告
        
        Args:
            session_id: Session ID
        
        Returns:
            評估報告
        """
        try:
            logger.info(f"📋 Generating evaluation report: {session_id}")
            
            # 獲取評估
            evaluation = await self.evaluation_recorder.get_evaluation(session_id)
            
            # 分析評估
            analysis = await self.evaluation_recorder.analyze_evaluation(session_id)
            
            report = {
                'session_id': session_id,
                'evaluation': evaluation,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Evaluation report generated: {session_id}")
            return report
        
        except Exception as e:
            logger.error(f"❌ Failed to generate evaluation report: {e}")
            return {'status': 'error', 'error': str(e)}


# 全局實例
_session_manager = None


def get_session_manager_with_rag() -> SessionManagerWithRAG:
    """獲取SessionManager實例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManagerWithRAG()
    return _session_manager


# 使用示例
async def example_usage():
    """使用示例"""
    
    # 1. 獲取SessionManager
    session_manager = get_session_manager_with_rag()
    
    # 2. 初始化Session
    init_result = await session_manager.initialize_session(
        session_id="session_001",
        scam_type="網上購物騙案",
        player_role="scammer"
    )
    print(f"✅ Session initialized: {init_result}")
    
    # 3. 發送消息
    response = await session_manager.send_message(
        message="你好，我係淘寶客服",
        role="scammer"
    )
    print(f"✅ Message processed: {response}")
    
    # 4. 評估對話
    evaluation = await session_manager.evaluate_dialogue()
    print(f"✅ Dialogue evaluated: {evaluation}")
    
    # 5. 獲取報告
    report = await session_manager.get_session_report()
    print(f"✅ Session report: {report}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

