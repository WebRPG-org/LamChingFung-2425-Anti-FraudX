"""
評分系統 V2 測試 - Phase 2.3 測試
測試基於受害者反應的計分系統
"""

import pytest
from backend.services.scam_scoring_v2 import (
    ScamScoringV2,
    EvaluationRecorder,
    get_scam_scoring_v2,
    get_evaluation_recorder
)


class TestScamScoringV2:
    """測試評分系統 V2"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.scoring = ScamScoringV2()
    
    @pytest.mark.asyncio
    async def test_analyze_completely_believe(self):
        """測試分析完全相信的反應"""
        response = "好的，我現在就提供密碼"
        result = await self.scoring.analyze_victim_response(response)
        
        assert result["response_type"] == "completely_believe"
        assert result["scammer_score_gain"] > 0
        assert result["expert_score_gain"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_partially_believe(self):
        """測試分析部分相信的反應"""
        response = "也許吧，但我有點不太確定"
        result = await self.scoring.analyze_victim_response(response)
        
        assert result["response_type"] == "partially_believe"
        assert result["scammer_score_gain"] > 0
        assert result["expert_score_gain"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_suspicious(self):
        """測試分析懷疑的反應"""
        response = "為什麼要我提供密碼？這有點不對勁"
        result = await self.scoring.analyze_victim_response(response)
        
        assert result["response_type"] == "suspicious"
        assert result["scammer_score_gain"] == 0
        assert result["expert_score_gain"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_refuse(self):
        """測試分析拒絕的反應"""
        response = "我不會提供密碼，我拒絕"
        result = await self.scoring.analyze_victim_response(response)
        
        assert result["response_type"] == "refuse"
        assert result["scammer_score_gain"] == 0
        assert result["expert_score_gain"] > 0
    
    @pytest.mark.asyncio
    async def test_calculate_alertness(self):
        """測試計算警覺性"""
        session_id = "test_session"
        
        # 模擬多個反應
        await self.scoring.analyze_victim_response("好的", session_id)
        await self.scoring.analyze_victim_response("我不會提供", session_id)
        
        alertness = await self.scoring.calculate_alertness(session_id)
        
        assert 0 <= alertness <= 100
    
    @pytest.mark.asyncio
    async def test_get_scores(self):
        """測試獲取評分"""
        session_id = "test_session"
        
        await self.scoring.analyze_victim_response("好的", session_id)
        scores = await self.scoring.get_scores(session_id)
        
        assert "scammer_score" in scores
        assert "expert_score" in scores
        assert "alertness" in scores
        assert "alertness_level" in scores
    
    @pytest.mark.asyncio
    async def test_alertness_level_high(self):
        """測試高警覺性等級"""
        session_id = "test_session"
        
        # 多次拒絕反應
        for _ in range(5):
            await self.scoring.analyze_victim_response("我不會提供", session_id)
        
        scores = await self.scoring.get_scores(session_id)
        assert scores["alertness_level"] == "高"
    
    @pytest.mark.asyncio
    async def test_alertness_level_low(self):
        """測試低警覺性等級"""
        session_id = "test_session"
        
        # 多次相信反應
        for _ in range(5):
            await self.scoring.analyze_victim_response("好的", session_id)
        
        scores = await self.scoring.get_scores(session_id)
        assert scores["alertness_level"] == "低"


class TestEvaluationRecorder:
    """測試評估記錄器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.recorder = EvaluationRecorder()
    
    @pytest.mark.asyncio
    async def test_record_victim_evaluation(self):
        """測試記錄受害者評估"""
        session_id = "test_session"
        evaluation = {
            "alertness": 50,
            "trust_in_scammer": 30,
            "trust_in_expert": 70
        }
        
        result = await self.recorder.record_victim_evaluation(session_id, evaluation)
        
        assert result is True
        assert session_id in self.recorder.victim_evaluations
    
    @pytest.mark.asyncio
    async def test_record_scammer_evaluation(self):
        """測試記錄騙徒評估"""
        session_id = "test_session"
        evaluation = {
            "tactics_used": ["冒充身份", "製造緊急感"],
            "effectiveness": 0.8,
            "score": 15
        }
        
        result = await self.recorder.record_scammer_evaluation(session_id, evaluation)
        
        assert result is True
        assert session_id in self.recorder.scammer_evaluations
    
    @pytest.mark.asyncio
    async def test_record_expert_evaluation(self):
        """測試記錄專家評估"""
        session_id = "test_session"
        evaluation = {
            "defenses_used": ["驗證身份", "向警察報案"],
            "effectiveness": 0.9,
            "score": 18
        }
        
        result = await self.recorder.record_expert_evaluation(session_id, evaluation)
        
        assert result is True
        assert session_id in self.recorder.expert_evaluations
    
    @pytest.mark.asyncio
    async def test_get_all_evaluations(self):
        """測試獲取所有評估"""
        session_id = "test_session"
        
        await self.recorder.record_victim_evaluation(session_id, {"alertness": 50})
        await self.recorder.record_scammer_evaluation(session_id, {"score": 15})
        await self.recorder.record_expert_evaluation(session_id, {"score": 18})
        
        evaluations = await self.recorder.get_all_evaluations(session_id)
        
        assert evaluations["victim_evaluation"] is not None
        assert evaluations["scammer_evaluation"] is not None
        assert evaluations["expert_evaluation"] is not None


class TestScoringIntegration:
    """測試評分系統集成"""
    
    @pytest.mark.asyncio
    async def test_full_game_scoring(self):
        """測試完整遊戲評分"""
        scoring = ScamScoringV2()
        session_id = "test_game"
        
        # 模擬遊戲過程
        responses = [
            "好的，我聽著",  # 部分相信
            "我不會提供密碼",  # 拒絕
            "我會向銀行確認",  # 懷疑
            "我已經報警了"  # 拒絕
        ]
        
        for response in responses:
            await scoring.analyze_victim_response(response, session_id)
        
        scores = await scoring.get_scores(session_id)
        
        assert scores["expert_score"] > scores["scammer_score"]
        assert scores["alertness_level"] in ["低", "中", "高"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


