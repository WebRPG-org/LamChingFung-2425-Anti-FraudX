"""
勝負判定器測試 - Phase 2.2 測試
測試騙徒勝利判定、專家勝利判定、一輪判定、驗證
"""

import pytest
from backend.services.verdict_judge import (
    VerdictJudge,
    VerdictValidator,
    get_verdict_judge,
    get_verdict_validator
)


class TestVerdictJudge:
    """測試勝負判定器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.judge = VerdictJudge()
    
    @pytest.mark.asyncio
    async def test_judge_scammer_win_with_password(self):
        """測試判定騙徒勝利 - 密碼"""
        message = "我的密碼是 123456"
        result = await self.judge.judge_scammer_win(message)
        
        assert result["is_win"] is True
        assert result["verdict"] == "scammer_win"
        assert "銀行密碼" in result["detected_conditions"]
    
    @pytest.mark.asyncio
    async def test_judge_scammer_win_with_account(self):
        """測試判定騙徒勝利 - 帳號"""
        message = "我的帳號是 123456789012"
        result = await self.judge.judge_scammer_win(message)
        
        assert result["is_win"] is True
        assert result["verdict"] == "scammer_win"
        assert "銀行帳號" in result["detected_conditions"]
    
    @pytest.mark.asyncio
    async def test_judge_scammer_win_with_transfer(self):
        """測試判定騙徒勝利 - 轉賬"""
        message = "我已經轉了 5000 元"
        result = await self.judge.judge_scammer_win(message)
        
        assert result["is_win"] is True
        assert result["verdict"] == "scammer_win"
        assert "轉賬" in result["detected_conditions"]
    
    @pytest.mark.asyncio
    async def test_judge_scammer_no_win(self):
        """測試判定騙徒未勝利"""
        message = "我不會提供密碼"
        result = await self.judge.judge_scammer_win(message)
        
        assert result["is_win"] is False
        assert result["verdict"] == "ongoing"
    
    @pytest.mark.asyncio
    async def test_judge_expert_win_with_police(self):
        """測試判定專家勝利 - 報警"""
        message = "我已經報警了，撥打了 18222"
        result = await self.judge.judge_expert_win(message)
        
        assert result["is_win"] is True
        assert result["verdict"] == "expert_win"
        assert "報警" in result["detected_conditions"]
    
    @pytest.mark.asyncio
    async def test_judge_expert_win_with_official(self):
        """測試判定專家勝利 - 官方確認"""
        message = "我會致電銀行官方確認"
        result = await self.judge.judge_expert_win(message)
        
        assert result["is_win"] is True
        assert result["verdict"] == "expert_win"
        assert "官方確認" in result["detected_conditions"]
    
    @pytest.mark.asyncio
    async def test_judge_expert_no_win(self):
        """測試判定專家未勝利"""
        message = "我不知道該怎麼辦"
        result = await self.judge.judge_expert_win(message)
        
        assert result["is_win"] is False
        assert result["verdict"] == "ongoing"
    
    @pytest.mark.asyncio
    async def test_judge_round_winner_scammer(self):
        """測試判定一輪贏家 - 騙徒"""
        result = await self.judge.judge_round_winner(
            scammer_message="提供密碼",
            expert_message="不要提供",
            victim_response="我的密碼是 123456"
        )
        
        assert result["winner"] == "scammer"
    
    @pytest.mark.asyncio
    async def test_judge_round_winner_expert(self):
        """測試判定一輪贏家 - 專家"""
        result = await self.judge.judge_round_winner(
            scammer_message="提供密碼",
            expert_message="報警",
            victim_response="我已經報警了"
        )
        
        assert result["winner"] == "expert"
    
    @pytest.mark.asyncio
    async def test_judge_round_winner_ongoing(self):
        """測試判定一輪贏家 - 繼續"""
        result = await self.judge.judge_round_winner(
            scammer_message="提供密碼",
            expert_message="不要提供",
            victim_response="我不知道"
        )
        
        assert result["winner"] == "ongoing"
    
    @pytest.mark.asyncio
    async def test_confidence_score(self):
        """測試信心度評分"""
        message = "我已經轉了 5000 元"
        result = await self.judge.judge_scammer_win(message)
        
        assert 0 <= result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_get_verdict_report(self):
        """測試獲取判定報告"""
        session_id = "test_session"
        
        await self.judge.judge_scammer_win("密碼", session_id)
        report = await self.judge.get_verdict_report(session_id)
        
        assert "session_id" in report
        assert report["session_id"] == session_id


class TestVerdictValidator:
    """測試勝負驗證器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.validator = VerdictValidator()
    
    @pytest.mark.asyncio
    async def test_validate_valid_verdict(self):
        """測試驗證有效的判定"""
        verdict = {
            "is_win": True,
            "detected_conditions": ["銀行密碼"],
            "confidence": 0.95,
            "reasoning": "受害者提供了密碼"
        }
        context = {}
        
        result = await self.validator.validate_verdict(verdict, context)
        
        assert result["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_validate_invalid_verdict_low_confidence(self):
        """測試驗證低信心度的判定"""
        verdict = {
            "is_win": True,
            "detected_conditions": ["銀行密碼"],
            "confidence": 0.5,
            "reasoning": "受害者提供了密碼"
        }
        context = {}
        
        result = await self.validator.validate_verdict(verdict, context)
        
        assert result["confidence_valid"] is False
    
    @pytest.mark.asyncio
    async def test_validate_invalid_verdict_no_reasoning(self):
        """測試驗證沒有理由的判定"""
        verdict = {
            "is_win": True,
            "detected_conditions": ["銀行密碼"],
            "confidence": 0.95,
            "reasoning": ""
        }
        context = {}
        
        result = await self.validator.validate_verdict(verdict, context)
        
        assert result["reasoning_valid"] is False
    
    @pytest.mark.asyncio
    async def test_validate_inconsistent_verdict(self):
        """測試驗證不一致的判定"""
        verdict = {
            "is_win": False,
            "detected_conditions": ["銀行密碼"],
            "confidence": 0.95,
            "reasoning": "受害者提供了密碼"
        }
        context = {}
        
        result = await self.validator.validate_verdict(verdict, context)
        
        assert result["consistency"] is False
    
    @pytest.mark.asyncio
    async def test_validation_score(self):
        """測試驗證評分"""
        verdict = {
            "is_win": True,
            "detected_conditions": ["銀行密碼"],
            "confidence": 0.95,
            "reasoning": "受害者提供了密碼"
        }
        context = {}
        
        result = await self.validator.validate_verdict(verdict, context)
        
        assert 0 <= result["validation_score"] <= 1


class TestVerdictConditions:
    """測試勝利條件檢測"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.judge = VerdictJudge()
    
    @pytest.mark.asyncio
    async def test_detect_password_condition(self):
        """測試檢測密碼條件"""
        messages = [
            "密碼是 123456",
            "password is 123456",
            "我的密碼是 abc123"
        ]
        
        for msg in messages:
            result = await self.judge.judge_scammer_win(msg)
            assert result["is_win"] is True
    
    @pytest.mark.asyncio
    async def test_detect_account_condition(self):
        """測試檢測帳號條件"""
        messages = [
            "帳號是 123456789012",
            "account is 123456789012",
            "卡號 1234567890"
        ]
        
        for msg in messages:
            result = await self.judge.judge_scammer_win(msg)
            assert result["is_win"] is True
    
    @pytest.mark.asyncio
    async def test_detect_police_condition(self):
        """測試檢測報警條件"""
        messages = [
            "我已經報警了",
            "我報案了",
            "撥打了 18222"
        ]
        
        for msg in messages:
            result = await self.judge.judge_expert_win(msg)
            assert result["is_win"] is True


class TestVerdictEdgeCases:
    """測試邊界情況"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.judge = VerdictJudge()
    
    @pytest.mark.asyncio
    async def test_hypothetical_not_win(self):
        """測試假設句不算勝利"""
        message = "如果我提供密碼會怎樣"
        result = await self.judge.judge_scammer_win(message)
        
        # 假設句應該降低信心度
        assert result["confidence"] < 0.8
    
    @pytest.mark.asyncio
    async def test_friend_story_not_win(self):
        """測試朋友的故事不算勝利"""
        message = "我有朋友報案過"
        result = await self.judge.judge_expert_win(message)
        
        # 朋友的故事應該降低信心度
        assert result["confidence"] < 0.8
    
    @pytest.mark.asyncio
    async def test_multiple_conditions(self):
        """測試多個條件"""
        message = "我的密碼是 123456，帳號是 987654321"
        result = await self.judge.judge_scammer_win(message)
        
        assert len(result["detected_conditions"]) >= 2
        assert result["is_win"] is True


class TestVerdictHistory:
    """測試判定歷史"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.judge = VerdictJudge()
    
    @pytest.mark.asyncio
    async def test_verdict_history_recording(self):
        """測試判定歷史記錄"""
        await self.judge.judge_scammer_win("密碼")
        await self.judge.judge_scammer_win("帳號")
        await self.judge.judge_expert_win("報警")
        
        assert len(self.judge.verdict_history) == 3
    
    @pytest.mark.asyncio
    async def test_session_verdict_tracking(self):
        """測試 Session 判定追蹤"""
        session_id = "test_session"
        
        await self.judge.judge_scammer_win("密碼", session_id)
        
        assert session_id in self.judge.verdicts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


