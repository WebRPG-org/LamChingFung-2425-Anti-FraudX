"""
騙術分析器測試 - Phase 2.1 測試
測試騙術分析、防騙分析、協同效果分析
"""

import pytest
from backend.services.tactic_analyzer import (
    TacticAnalyzer,
    TacticSynergyAnalyzer,
    get_tactic_analyzer,
    get_synergy_analyzer
)


class TestTacticAnalyzer:
    """測試騙術分析器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.analyzer = TacticAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_scammer_message_with_tactics(self):
        """測試分析包含騙術的騙徒消息"""
        message = "我是銀行客服，您的卡被凍結了，立即提供密碼"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert "detected_tactics" in result
        assert len(result["detected_tactics"]) > 0
        assert result["avg_score"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_scammer_message_no_tactics(self):
        """測試分析不包含騙術的消息"""
        message = "今天天氣很好"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert "detected_tactics" in result
        assert len(result["detected_tactics"]) == 0
        assert result["avg_score"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_expert_message_with_defenses(self):
        """測試分析包含防騙的專家消息"""
        message = "不要提供密碼，向官方確認，向警察報案"
        result = await self.analyzer.analyze_expert_message(message)
        
        assert "detected_defenses" in result
        assert len(result["detected_defenses"]) > 0
        assert result["avg_score"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_expert_message_no_defenses(self):
        """測試分析不包含防騙的消息"""
        message = "今天天氣很好"
        result = await self.analyzer.analyze_expert_message(message)
        
        assert "detected_defenses" in result
        assert len(result["detected_defenses"]) == 0
        assert result["avg_score"] == 0
    
    @pytest.mark.asyncio
    async def test_detect_multiple_tactics(self):
        """測試檢測多個騙術"""
        message = "我是銀行客服，您的卡被凍結了，立即轉賬保護資金，提供密碼"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert len(result["detected_tactics"]) >= 3
    
    @pytest.mark.asyncio
    async def test_effectiveness_calculation(self):
        """測試有效性計算"""
        message = "我是銀行客服，您的卡被凍結了，立即轉賬"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert result["effectiveness"] in ["低", "中", "高", "無"]
    
    @pytest.mark.asyncio
    async def test_compare_tactics(self):
        """測試比較騙徒和專家策略"""
        scammer_msg = "我是銀行客服，立即提供密碼"
        expert_msg = "不要提供密碼，向官方確認"
        
        scammer_result = await self.analyzer.analyze_scammer_message(scammer_msg)
        expert_result = await self.analyzer.analyze_expert_message(expert_msg)
        
        comparison = await self.analyzer.compare_tactics(scammer_result, expert_result)
        
        assert "winner" in comparison
        assert "advantage" in comparison
        assert comparison["winner"] in ["scammer", "expert", "tie"]
    
    @pytest.mark.asyncio
    async def test_get_analysis_report(self):
        """測試獲取分析報告"""
        session_id = "test_session"
        
        await self.analyzer.analyze_scammer_message("測試消息", session_id)
        report = await self.analyzer.get_analysis_report(session_id)
        
        assert "session_id" in report
        assert report["session_id"] == session_id


class TestTacticSynergyAnalyzer:
    """測試騙術協同分析器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.analyzer = TacticSynergyAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_single_tactic(self):
        """測試單個騙術"""
        tactics = ["冒充身份"]
        result = await self.analyzer.analyze_synergy(tactics)
        
        assert "total_synergy" in result
        assert result["total_synergy"] == 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_two_tactics_with_synergy(self):
        """測試兩個有協同效果的騙術"""
        tactics = ["冒充身份", "製造緊急感"]
        result = await self.analyzer.analyze_synergy(tactics)
        
        assert result["total_synergy"] > 1.0
        assert len(result["synergies"]) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_multiple_tactics(self):
        """測試多個騙術"""
        tactics = ["冒充身份", "製造緊急感", "要求轉賬"]
        result = await self.analyzer.analyze_synergy(tactics)
        
        assert result["total_synergy"] > 1.0
        assert len(result["synergies"]) == 3  # C(3,2) = 3
    
    @pytest.mark.asyncio
    async def test_effectiveness_boost(self):
        """測試有效性提升"""
        tactics = ["製造緊急感", "要求轉賬"]
        result = await self.analyzer.analyze_synergy(tactics)
        
        assert result["effectiveness_boost"] > 0


class TestTacticDetection:
    """測試騙術檢測"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.analyzer = TacticAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detect_impersonation(self):
        """測試檢測冒充身份"""
        message = "我是銀行客服"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert "冒充身份" in result["detected_tactics"]
    
    @pytest.mark.asyncio
    async def test_detect_urgency(self):
        """測試檢測製造緊急感"""
        message = "立即轉賬，馬上行動"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert "製造緊急感" in result["detected_tactics"]
    
    @pytest.mark.asyncio
    async def test_detect_sensitive_info_request(self):
        """測試檢測要求敏感信息"""
        message = "請提供您的密碼和驗證碼"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert "要求敏感信息" in result["detected_tactics"]
    
    @pytest.mark.asyncio
    async def test_detect_transfer_request(self):
        """測試檢測要求轉賬"""
        message = "請轉賬到這個帳號"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert "要求轉賬" in result["detected_tactics"]


class TestDefenseDetection:
    """測試防騙檢測"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.analyzer = TacticAnalyzer()
    
    @pytest.mark.asyncio
    async def test_detect_identity_verification(self):
        """測試檢測身份驗證"""
        message = "我會驗證您的身份"
        result = await self.analyzer.analyze_expert_message(message)
        
        assert "驗證身份" in result["detected_defenses"]
    
    @pytest.mark.asyncio
    async def test_detect_no_sensitive_info(self):
        """測試檢測不提供敏感信息"""
        message = "不要提供密碼"
        result = await self.analyzer.analyze_expert_message(message)
        
        assert "不提供敏感信息" in result["detected_defenses"]
    
    @pytest.mark.asyncio
    async def test_detect_official_confirmation(self):
        """測試檢測向官方確認"""
        message = "致電官方確認"
        result = await self.analyzer.analyze_expert_message(message)
        
        assert "向官方確認" in result["detected_defenses"]
    
    @pytest.mark.asyncio
    async def test_detect_police_report(self):
        """測試檢測報警"""
        message = "向警察報案，撥打 18222"
        result = await self.analyzer.analyze_expert_message(message)
        
        assert "向警察報案" in result["detected_defenses"]


class TestTacticScoring:
    """測試騙術評分"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.analyzer = TacticAnalyzer()
    
    @pytest.mark.asyncio
    async def test_score_range(self):
        """測試評分範圍"""
        message = "我是銀行客服，立即提供密碼和驗證碼"
        result = await self.analyzer.analyze_scammer_message(message)
        
        assert 0 <= result["avg_score"] <= 20
    
    @pytest.mark.asyncio
    async def test_score_increases_with_tactics(self):
        """測試評分隨騙術增加而增加"""
        msg1 = "我是銀行客服"
        msg2 = "我是銀行客服，立即提供密碼和驗證碼，轉賬保護資金"
        
        result1 = await self.analyzer.analyze_scammer_message(msg1)
        result2 = await self.analyzer.analyze_scammer_message(msg2)
        
        assert result2["avg_score"] > result1["avg_score"]


class TestAnalysisHistory:
    """測試分析歷史"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.analyzer = TacticAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analysis_history_recording(self):
        """測試分析歷史記錄"""
        await self.analyzer.analyze_scammer_message("消息 1")
        await self.analyzer.analyze_scammer_message("消息 2")
        await self.analyzer.analyze_expert_message("消息 3")
        
        assert len(self.analyzer.analysis_history) == 3
    
    @pytest.mark.asyncio
    async def test_session_tracking(self):
        """測試 Session 追蹤"""
        session_id = "test_session"
        
        await self.analyzer.analyze_scammer_message("消息 1", session_id)
        await self.analyzer.analyze_expert_message("消息 2", session_id)
        
        assert session_id in self.analyzer.scammer_tactics
        assert session_id in self.analyzer.defense_tactics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


