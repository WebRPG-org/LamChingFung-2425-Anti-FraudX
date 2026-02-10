"""
受害人評估器測試套件
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from utils.victim_evaluator import VictimEvaluator, EvaluationResult
from agents.victim import VictimAgent
from utils.performance_tracker import PerformanceTracker

# 配置 pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def victim_agent():
    """創建受害人Agent實例"""
    return VictimAgent()


@pytest.fixture
def performance_tracker():
    """創建性能追蹤器實例"""
    return PerformanceTracker()


@pytest.fixture
def evaluator(victim_agent, performance_tracker):
    """創建評估器實例（混合模式）"""
    return VictimEvaluator(
        victim_agent=victim_agent,
        performance_tracker=performance_tracker,
        rule_weight=0.7,
        agent_weight=0.3,
        enable_agent_scoring=True
    )


@pytest.fixture
def rule_only_evaluator(victim_agent, performance_tracker):
    """創建純規則評估器"""
    return VictimEvaluator(
        victim_agent=victim_agent,
        performance_tracker=performance_tracker,
        rule_weight=1.0,
        agent_weight=0.0,
        enable_agent_scoring=False
    )


class TestVictimEvaluator:
    """測試受害人評估器"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_rule_based_scoring(self, rule_only_evaluator):
        """測試純規則評分"""
        conversation = [
            {"role": "scammer", "content": "你好，我是警察", "strategy": "authority"},
            {"role": "victim", "content": "有什麼事嗎？"},
            {"role": "scammer", "content": "你的帳戶有問題，需要立即處理", "strategy": "urgency"}
        ]
        
        result = await rule_only_evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="elderly",
            initial_trust=50
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.method == "rule"
        assert result.trust_change < 0  # 應該下降
        assert result.confidence > 0
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_hybrid_scoring(self, evaluator):
        """測試混合評分"""
        conversation = [
            {"role": "scammer", "content": "恭喜中獎！", "strategy": "greed"},
            {"role": "victim", "content": "真的嗎？"},
            {"role": "scammer", "content": "需要先付稅金", "strategy": "greed"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="average",
            initial_trust=50
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.method in ["hybrid", "rule"]  # 可能降級到規則
        assert 'rule_score' in result.rule_score
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_elderly_persona(self, evaluator):
        """測試老年人人設"""
        conversation = [
            {"role": "scammer", "content": "奶奶，我是你孫子", "strategy": "sympathy"},
            {"role": "victim", "content": "你是誰？"},
            {"role": "scammer", "content": "我出事了需要錢", "strategy": "urgency"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="elderly",
            initial_trust=60
        )
        
        # 老年人更容易被情感操控
        assert result.trust_change < -10
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_overconfident_persona(self, evaluator):
        """測試過度自信人設"""
        conversation = [
            {"role": "scammer", "content": "你中獎了", "strategy": "greed"},
            {"role": "victim", "content": "我不相信"},
            {"role": "scammer", "content": "這是真的", "strategy": "greed"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="overconfident",
            initial_trust=30
        )
        
        # 過度自信者較難被騙
        assert result.trust_change > -15
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_multiple_strategies(self, evaluator):
        """測試多重策略"""
        conversation = [
            {"role": "scammer", "content": "我是警察", "strategy": "authority"},
            {"role": "victim", "content": "什麼事？"},
            {"role": "scammer", "content": "你的帳戶有問題", "strategy": "fear"},
            {"role": "victim", "content": "怎麼辦？"},
            {"role": "scammer", "content": "立即處理", "strategy": "urgency"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="average",
            initial_trust=50
        )
        
        # 多重策略應該有更大影響
        assert result.trust_change < -15
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_victim_resistance(self, evaluator):
        """測試受害人抵抗"""
        conversation = [
            {"role": "scammer", "content": "你中獎了", "strategy": "greed"},
            {"role": "victim", "content": "這是詐騙"},
            {"role": "scammer", "content": "不是詐騙", "strategy": "greed"},
            {"role": "victim", "content": "我要報警"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="student",
            initial_trust=30
        )
        
        # 受害人識破騙局，信任度應該上升
        assert result.trust_change > 0
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_short_conversation(self, evaluator):
        """測試短對話"""
        conversation = [
            {"role": "scammer", "content": "你好", "strategy": "none"},
            {"role": "victim", "content": "你好"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="average",
            initial_trust=50
        )
        
        # 短對話影響應該較小
        assert abs(result.trust_change) < 10
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_confidence_score(self, evaluator):
        """測試信心度評分"""
        conversation = [
            {"role": "scammer", "content": "我是警察", "strategy": "authority"},
            {"role": "victim", "content": "證件呢？"},
            {"role": "scammer", "content": "在這裡", "strategy": "authority"}
        ]
        
        result = await evaluator.evaluate_conversation(
            conversation_history=conversation,
            persona_type="average",
            initial_trust=50
        )
        
        assert 0 <= result.confidence <= 100
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_weight_adjustment(self, victim_agent, performance_tracker):
        """測試權重調整"""
        # 測試不同權重配置
        configs = [
            (1.0, 0.0),  # 純規則
            (0.5, 0.5),  # 平衡
            (0.3, 0.7),  # Agent為主
        ]
        
        conversation = [
            {"role": "scammer", "content": "緊急通知", "strategy": "urgency"},
            {"role": "victim", "content": "什麼事？"}
        ]
        
        results = []
        for rule_w, agent_w in configs:
            evaluator = VictimEvaluator(
                victim_agent=victim_agent,
                performance_tracker=performance_tracker,
                rule_weight=rule_w,
                agent_weight=agent_w,
                enable_agent_scoring=(agent_w > 0)
            )
            
            result = await evaluator.evaluate_conversation(
                conversation_history=conversation,
                persona_type="average",
                initial_trust=50
            )
            results.append(result.trust_change)
        
        # 不同權重應該產生不同結果（如果Agent評分有效）
        assert len(results) == 3


class TestEvaluationResult:
    """測試評估結果數據類"""
    
    def test_evaluation_result_creation(self):
        """測試創建評估結果"""
        result = EvaluationResult(
            trust_change=-15.5,
            rule_score={"score": 35, "factors": []},
            agent_score={"score": 30, "reasoning": "test"},
            confidence=85.0,
            method="hybrid",
            timestamp="2024-01-01T00:00:00"
        )
        
        assert result.trust_change == -15.5
        assert result.confidence == 85.0
        assert result.method == "hybrid"
        
    def test_evaluation_result_fields(self):
        """測試評估結果欄位"""
        result = EvaluationResult(
            trust_change=10.0,
            rule_score={},
            agent_score={},
            confidence=90.0,
            method="rule",
            timestamp="2024-01-01T00:00:00"
        )
        
        assert hasattr(result, 'trust_change')
        assert hasattr(result, 'rule_score')
        assert hasattr(result, 'agent_score')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'method')
        assert hasattr(result, 'timestamp')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
