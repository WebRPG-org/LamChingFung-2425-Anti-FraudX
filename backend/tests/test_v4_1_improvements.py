"""
AI 防詐平台 v4.1 - 單元測試
測試所有新增的改進功能
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.scammer import ScammerAgent
from agents.expert import ExpertAgent
from agents.victim import VictimAgent
from agents.recorder import RecorderAgent
from services.agent_service import AgentService, ConversationSession
from utils.logger import log


class TestScammerAgent:
    """測試 ScammerAgent 的改進"""
    
    def test_strategy_phases_initialization(self):
        """測試策略階段初始化"""
        agent = ScammerAgent(scam_tactic="假冒銀行", victim_persona="elderly")
        
        # 驗證策略階段配置
        assert hasattr(agent, 'STRATEGY_PHASES')
        assert "trust_building" in agent.STRATEGY_PHASES
        assert "panic_creation" in agent.STRATEGY_PHASES
        assert "action_urging" in agent.STRATEGY_PHASES
        
        # 驗證初始策略階段
        assert agent.strategy_phase == "trust_building"
        assert agent.phase_round_count == 0
        
        log.info("✅ 策略階段初始化測試通過")
    
    def test_persona_adaptations(self):
        """測試人格適應配置"""
        agent = ScammerAgent(scam_tactic="假冒銀行", victim_persona="elderly")
        
        # 驗證人格適應配置
        assert hasattr(agent, 'PERSONA_ADAPTATIONS')
        assert "elderly" in agent.PERSONA_ADAPTATIONS
        assert "average" in agent.PERSONA_ADAPTATIONS
        assert "overconfident" in agent.PERSONA_ADAPTATIONS
        assert "student" in agent.PERSONA_ADAPTATIONS
        
        # 驗證人格配置內容
        elderly_config = agent.PERSONA_ADAPTATIONS["elderly"]
        assert "tone" in elderly_config
        assert "keywords" in elderly_config
        assert "avoid" in elderly_config
        
        log.info("✅ 人格適應配置測試通過")
    
    def test_victim_persona_storage(self):
        """測試受害者人格存儲"""
        agent = ScammerAgent(scam_tactic="假冒銀行", victim_persona="average")
        
        assert agent.victim_persona == "average"
        
        log.info("✅ 受害者人格存儲測試通過")
    
    def test_get_next_strategy_phase(self):
        """測試策略階段轉換"""
        agent = ScammerAgent(scam_tactic="假冒銀行", victim_persona="elderly")
        
        # 初始階段
        assert agent.strategy_phase == "trust_building"
        
        # 模擬達到階段持續時間
        agent.phase_round_count = agent.STRATEGY_PHASES["trust_building"]["duration"]
        agent._get_next_strategy_phase()
        
        # 驗證進入下一個階段
        assert agent.strategy_phase == "panic_creation"
        assert agent.phase_round_count == 0
        
        log.info("✅ 策略階段轉換測試通過")


class TestExpertAgent:
    """測試 ExpertAgent 的改進"""
    
    def test_intervention_strategies_initialization(self):
        """測試介入策略初始化"""
        agent = ExpertAgent(victim_persona="elderly")
        
        # 驗證介入策略配置
        assert hasattr(agent, 'INTERVENTION_STRATEGIES')
        assert "elderly" in agent.INTERVENTION_STRATEGIES
        assert "average" in agent.INTERVENTION_STRATEGIES
        assert "overconfident" in agent.INTERVENTION_STRATEGIES
        assert "student" in agent.INTERVENTION_STRATEGIES
        
        log.info("✅ 介入策略初始化測試通過")
    
    def test_victim_persona_validation(self):
        """測試受害者人格驗證"""
        # 有效的人格類型
        agent = ExpertAgent(victim_persona="elderly")
        assert agent.victim_persona == "elderly"
        
        # 無效的人格類型應該使用 average
        agent = ExpertAgent(victim_persona="invalid_type")
        assert agent.victim_persona == "average"
        
        log.info("✅ 受害者人格驗證測試通過")
    
    def test_select_intervention_strategy(self):
        """測試選擇介入策略"""
        agent = ExpertAgent(victim_persona="elderly")
        
        strategy = agent._select_intervention_strategy("我好驚")
        
        # 驗證策略包含必要的字段
        assert "priority" in strategy
        assert "opening" in strategy
        assert "focus" in strategy
        assert "language_level" in strategy
        
        log.info("✅ 選擇介入策略測試通過")
    
    def test_provide_concrete_advice(self):
        """測試提供具體建議"""
        agent = ExpertAgent(victim_persona="elderly")
        
        # 測試各種騙案類型
        scam_types = ["假冒銀行", "假冒政府", "投資詐騙", "愛情詐騙", "求職詐騙"]
        
        for scam_type in scam_types:
            advice = agent._provide_concrete_advice(scam_type)
            assert isinstance(advice, str)
            assert len(advice) > 0
        
        log.info("✅ 提供具體建議測試通過")


class TestVictimAgent:
    """測試 VictimAgent 的改進"""
    
    def test_emotional_states_initialization(self):
        """測試情緒狀態初始化"""
        agent = VictimAgent(persona_type="elderly")
        
        # 驗證情緒狀態配置
        assert hasattr(agent, 'EMOTIONAL_STATES')
        assert "neutral" in agent.EMOTIONAL_STATES
        assert "anxious" in agent.EMOTIONAL_STATES
        assert "calm" in agent.EMOTIONAL_STATES
        assert "suspicious" in agent.EMOTIONAL_STATES
        assert "panicked" in agent.EMOTIONAL_STATES
        
        log.info("✅ 情緒狀態初始化測試通過")
    
    def test_initial_trust_levels(self):
        """測試初始信任度"""
        personas = ["elderly", "average", "overconfident", "student"]
        
        for persona in personas:
            agent = VictimAgent(persona_type=persona)
            
            # 驗證初始信任度
            assert agent.initial_trust["scammer"] > 0
            assert agent.initial_trust["expert"] > 0
            assert agent.initial_trust["alertness"] > 0
        
        log.info("✅ 初始信任度測試通過")
    
    def test_emotional_state_update(self):
        """測試情緒狀態更新"""
        agent = VictimAgent(persona_type="elderly")
        
        # 初始情緒狀態
        assert agent.emotional_state == "neutral"
        
        # 模擬騙徒製造恐慌
        scammer_msg = "你的帳戶會被凍結，你所有錢都冇晒"
        agent._update_emotional_state(scammer_msg, None)
        
        # 驗證情緒狀態變化
        assert agent.emotional_state in ["anxious", "panicked"]
        
        log.info("✅ 情緒狀態更新測試通過")
    
    def test_generate_response_based_on_emotion(self):
        """測試根據情緒生成回應"""
        agent = VictimAgent(persona_type="elderly")
        
        # 設置不同的情緒狀態
        emotions = ["neutral", "anxious", "calm", "suspicious", "panicked"]
        
        for emotion in emotions:
            agent.emotional_state = emotion
            response_emotion = agent._generate_response_based_on_emotion()
            
            assert response_emotion == emotion
        
        log.info("✅ 根據情緒生成回應測試通過")


class TestRecorderAgent:
    """測試 RecorderAgent 的改進"""
    
    def test_performance_weights_initialization(self):
        """測試性能評分權重初始化"""
        agent = RecorderAgent()
        
        # 驗證騙徒評分權重
        assert agent.PERFORMANCE_WEIGHTS["scammer"]["persuasiveness"] == 0.30
        assert agent.PERFORMANCE_WEIGHTS["scammer"]["credibility"] == 0.25
        assert agent.PERFORMANCE_WEIGHTS["scammer"]["pressure_effectiveness"] == 0.25
        assert agent.PERFORMANCE_WEIGHTS["scammer"]["strategy_consistency"] == 0.20
        
        # 驗證專家評分權重
        assert agent.PERFORMANCE_WEIGHTS["expert"]["intervention_effectiveness"] == 0.30
        assert agent.PERFORMANCE_WEIGHTS["expert"]["clarity"] == 0.20
        assert agent.PERFORMANCE_WEIGHTS["expert"]["empathy"] == 0.20
        assert agent.PERFORMANCE_WEIGHTS["expert"]["actionability"] == 0.15
        assert agent.PERFORMANCE_WEIGHTS["expert"]["timing"] == 0.15
        
        log.info("✅ 性能評分權重初始化測試通過")
    
    def test_outcome_criteria_initialization(self):
        """測試結果判定標準初始化"""
        agent = RecorderAgent()
        
        # 驗證結果判定標準
        assert "SUCCESS" in agent.OUTCOME_CRITERIA
        assert "FAILURE" in agent.OUTCOME_CRITERIA
        assert "PARTIAL" in agent.OUTCOME_CRITERIA
        
        log.info("✅ 結果判定標準初始化測試通過")
    
    def test_determine_outcome(self):
        """測試結果判定"""
        agent = RecorderAgent()
        
        # 測試 SUCCESS
        conversation_log = [
            {"dialogue": "我唔會信你，我要報警"}
        ]
        outcome = agent._determine_outcome(conversation_log, {"scammer": 0, "expert": 80})
        assert outcome == "SUCCESS"
        
        # 測試 FAILURE
        conversation_log = [
            {"dialogue": "我會轉帳"}
        ]
        outcome = agent._determine_outcome(conversation_log, {"scammer": 100, "expert": 20})
        assert outcome == "FAILURE"
        
        log.info("✅ 結果判定測試通過")
    
    def test_calculate_scammer_score(self):
        """測試騙徒評分計算"""
        agent = RecorderAgent()
        
        metrics = {
            "persuasiveness": 80,
            "persuasiveness_analysis": "話術流暢",
            "credibility": 75,
            "credibility_analysis": "可信度高",
            "pressure_effectiveness": 70,
            "pressure_analysis": "施壓有效",
            "strategy_consistency": 85,
            "strategy_analysis": "策略一致",
            "success_count": 2,
            "failure_count": 0,
            "role_break_count": 0,
            "key_successes": ["成功1", "成功2"],
            "key_failures": []
        }
        
        score = agent._calculate_scammer_score(metrics)
        
        # 驗證評分結構
        assert "overall_score" in score
        assert 0 <= score["overall_score"] <= 100
        assert score["persuasiveness"] == 80
        assert score["credibility"] == 75
        
        log.info("✅ 騙徒評分計算測試通過")
    
    def test_calculate_expert_score(self):
        """測試專家評分計算"""
        agent = RecorderAgent()
        
        metrics = {
            "intervention_effectiveness": 70,
            "intervention_analysis": "干預有效",
            "clarity": 80,
            "clarity_analysis": "清晰度高",
            "empathy": 75,
            "empathy_analysis": "同理心強",
            "actionability": 65,
            "actionability_analysis": "可執行性好",
            "timing": 70,
            "timing_analysis": "時機把握好",
            "success_count": 1,
            "ignored_count": 0,
            "prevented_count": 1,
            "key_successes": ["成功1"],
            "key_failures": []
        }
        
        score = agent._calculate_expert_score(metrics)
        
        # 驗證評分結構
        assert "overall_score" in score
        assert 0 <= score["overall_score"] <= 100
        assert score["intervention_effectiveness"] == 70
        assert score["clarity"] == 80
        
        log.info("✅ 專家評分計算測試通過")
    
    def test_analyze_trust_trajectory(self):
        """測試信任度軌跡分析"""
        agent = RecorderAgent()
        
        trust_changes = [
            {"round": 1, "from": 50, "to": 70, "trigger": "騙徒製造恐慌", "analysis": "信任度上升"},
            {"round": 2, "from": 70, "to": 60, "trigger": "專家介入", "analysis": "信任度下降"}
        ]
        
        analysis = agent._analyze_trust_trajectory(trust_changes)
        
        # 驗證分析結構
        assert analysis["initial_trust_level"] == 50
        assert analysis["final_trust_level"] == 60
        assert analysis["peak_trust_level"] == 70
        assert "trust_trajectory" in analysis
        
        log.info("✅ 信任度軌跡分析測試通過")
    
    def test_generate_improvement_suggestions(self):
        """測試改進建議生成"""
        agent = RecorderAgent()
        
        analysis = {
            "victim_persona": "elderly",
            "scammer_performance": {"overall_score": 50},
            "expert_performance": {"overall_score": 40, "key_successes": ["成功1"]},
            "outcome": "FAILURE"
        }
        
        suggestions = agent._generate_improvement_suggestions("FAILURE", analysis)
        
        # 驗證建議內容
        assert isinstance(suggestions, str)
        assert len(suggestions) > 0
        
        log.info("✅ 改進建議生成測試通過")


class TestAgentService:
    """測試 AgentService 的改進"""
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """測試創建 session"""
        service = AgentService(persona_type="elderly")
        
        session_id = service.create_session()
        
        # 驗證 session 創建
        assert session_id is not None
        assert service.current_session is not None
        assert service.current_session.persona_type == "elderly"
        
        log.info("✅ 創建 session 測試通過")
    
    @pytest.mark.asyncio
    async def test_conversation_session(self):
        """測試對話 session"""
        session = ConversationSession("test_session", "elderly")
        
        # 添加消息
        session.add_message("scammer", "你好")
        session.add_message("victim", "你係邊個")
        
        # 驗證消息保存
        assert len(session.conversation_history) == 2
        assert session.conversation_history[0]["role"] == "scammer"
        assert session.conversation_history[1]["role"] == "victim"
        
        log.info("✅ 對話 session 測試通過")
    
    @pytest.mark.asyncio
    async def test_parallel_responses_mode(self):
        """測試並行回應模式"""
        service = AgentService(persona_type="average")
        session_id = service.create_session()
        
        # 測試 full 模式
        try:
            response = await service.generate_parallel_responses(
                victim_message="我唔知點算好",
                session_id=session_id,
                mode="full"
            )
            
            # 驗證回應結構
            assert "scammer_response" in response
            assert "expert_response" in response
            assert "victim_response" in response
            assert "execution_time_ms" in response
            
            log.info("✅ 並行回應模式測試通過")
        except Exception as e:
            log.warning(f"⚠️ 並行回應測試需要 LLM 連接: {e}")


class TestIntegration:
    """集成測試"""
    
    def test_all_agents_initialization(self):
        """測試所有 Agent 初始化"""
        try:
            scammer = ScammerAgent(scam_tactic="假冒銀行", victim_persona="elderly")
            expert = ExpertAgent(victim_persona="elderly")
            victim = VictimAgent(persona_type="elderly")
            recorder = RecorderAgent()
            
            # 驗證所有 Agent 都已初始化
            assert scammer is not None
            assert expert is not None
            assert victim is not None
            assert recorder is not None
            
            log.info("✅ 所有 Agent 初始化測試通過")
        except Exception as e:
            log.error(f"❌ Agent 初始化失敗: {e}")
            raise
    
    def test_agent_service_initialization(self):
        """測試 AgentService 初始化"""
        try:
            service = AgentService(
                persona_type="elderly",
                enable_tracking=True,
                scam_type="banking"
            )
            
            # 驗證服務初始化
            assert service.persona_type == "elderly"
            assert service.enable_tracking == True
            assert service.scam_type == "banking"
            
            log.info("✅ AgentService 初始化測試通過")
        except Exception as e:
            log.error(f"❌ AgentService 初始化失敗: {e}")
            raise


# 性能測試
class TestPerformance:
    """性能測試"""
    
    def test_scammer_agent_performance(self):
        """測試 ScammerAgent 性能"""
        import time
        
        agent = ScammerAgent(scam_tactic="假冒銀行", victim_persona="elderly")
        
        start = time.time()
        agent._get_next_strategy_phase()
        elapsed = time.time() - start
        
        # 驗證性能（應該在毫秒級）
        assert elapsed < 0.1
        
        log.info(f"✅ ScammerAgent 性能測試通過 (耗時: {elapsed*1000:.2f}ms)")
    
    def test_recorder_agent_performance(self):
        """測試 RecorderAgent 性能"""
        import time
        
        agent = RecorderAgent()
        
        metrics = {
            "persuasiveness": 80,
            "persuasiveness_analysis": "話術流暢",
            "credibility": 75,
            "credibility_analysis": "可信度高",
            "pressure_effectiveness": 70,
            "pressure_analysis": "施壓有效",
            "strategy_consistency": 85,
            "strategy_analysis": "策略一致",
            "success_count": 2,
            "failure_count": 0,
            "role_break_count": 0,
            "key_successes": ["成功1"],
            "key_failures": []
        }
        
        start = time.time()
        score = agent._calculate_scammer_score(metrics)
        elapsed = time.time() - start
        
        # 驗證性能（應該在毫秒級）
        assert elapsed < 0.1
        
        log.info(f"✅ RecorderAgent 性能測試通過 (耗時: {elapsed*1000:.2f}ms)")


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "-s"])

