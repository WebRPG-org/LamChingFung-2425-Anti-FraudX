"""
測試對話質量評估系統
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from utils.conversation_quality import ConversationQualityAnalyzer, QualityScore


class TestConversationQualityAnalyzer:
    """測試ConversationQualityAnalyzer類"""
    
    @pytest.fixture
    def analyzer(self):
        """創建分析器實例"""
        return ConversationQualityAnalyzer()
    
    @pytest.fixture
    def sample_conversation(self):
        """創建示例對話"""
        return [
            {"role": "scammer", "text": "你好，我係銀行職員，你嘅帳戶有問題。"},
            {"role": "victim", "text": "咩問題？"},
            {"role": "scammer", "text": "你嘅帳戶被凍結咗，需要立即處理。"},
            {"role": "expert", "text": "唔好驚，銀行唔會咁樣打電話嚟。"},
            {"role": "victim", "text": "但係佢話我帳戶有問題..."},
            {"role": "expert", "text": "呢個係詐騙手法，你應該掛斷電話。"}
        ]
    
    @pytest.fixture
    def sample_trust_history(self):
        """創建示例信任度歷史"""
        return [
            {"trust_in_scammer": 50, "trust_in_expert": 50, "alertness": 50},
            {"trust_in_scammer": 55, "trust_in_expert": 50, "alertness": 45},
            {"trust_in_scammer": 60, "trust_in_expert": 50, "alertness": 40},
            {"trust_in_scammer": 55, "trust_in_expert": 55, "alertness": 50},
            {"trust_in_scammer": 50, "trust_in_expert": 60, "alertness": 55},
            {"trust_in_scammer": 40, "trust_in_expert": 70, "alertness": 65}
        ]
    
    def test_analyzer_initialization(self, analyzer):
        """測試分析器初始化"""
        assert analyzer is not None
        assert hasattr(analyzer, 'analyze_conversation')
        assert hasattr(analyzer, 'analyze_coherence')
        assert hasattr(analyzer, 'analyze_effectiveness')
        assert hasattr(analyzer, 'analyze_timing')
    
    def test_analyze_conversation(self, analyzer, sample_conversation, sample_trust_history):
        """測試完整對話分析"""
        result = analyzer.analyze_conversation(sample_conversation, sample_trust_history)
        
        assert isinstance(result, QualityScore)
        assert 0 <= result.coherence <= 100
        assert 0 <= result.effectiveness <= 100
        assert 0 <= result.timing <= 100
        assert 0 <= result.overall <= 100
        assert isinstance(result.details, dict)
    
    def test_analyze_coherence(self, analyzer, sample_conversation):
        """測試連貫性分析"""
        score = analyzer.analyze_coherence(sample_conversation)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_analyze_coherence_single_turn(self, analyzer):
        """測試單輪對話的連貫性"""
        conversation = [{"role": "scammer", "text": "你好"}]
        score = analyzer.analyze_coherence(conversation)
        
        assert score == 100.0  # 單輪對話默認滿分
    
    def test_analyze_effectiveness(self, analyzer, sample_conversation, sample_trust_history):
        """測試有效性分析"""
        score = analyzer.analyze_effectiveness(sample_conversation, sample_trust_history)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_analyze_timing(self, analyzer, sample_conversation, sample_trust_history):
        """測試時機分析"""
        score = analyzer.analyze_timing(sample_conversation, sample_trust_history)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_identify_main_topic(self, analyzer, sample_conversation):
        """測試主題識別"""
        topic = analyzer._identify_main_topic(sample_conversation)
        
        assert topic in analyzer.TOPIC_KEYWORDS.keys()
        assert topic == "bank_scam"  # 示例對話是銀行詐騙
    
    def test_has_reference_to_previous(self, analyzer):
        """測試上下文引用檢測"""
        current = {"text": "你剛才說帳戶有問題"}
        previous = {"text": "你嘅帳戶被凍結"}
        
        assert analyzer._has_reference_to_previous(current, previous) is True
        
        current_no_ref = {"text": "我唔知"}
        assert analyzer._has_reference_to_previous(current_no_ref, previous) is False
    
    def test_is_positive_reaction(self, analyzer):
        """測試積極反應判斷"""
        positive_text = "好啊，我明白了，多謝你"
        negative_text = "唔係，我唔信，點解"
        
        assert analyzer._is_positive_reaction(positive_text) is True
        assert analyzer._is_positive_reaction(negative_text) is False
    
    def test_identify_turning_points(self, analyzer, sample_trust_history):
        """測試轉折點識別"""
        turning_points = analyzer._identify_turning_points(sample_trust_history)
        
        assert isinstance(turning_points, list)
        assert all(isinstance(tp, int) for tp in turning_points)
    
    def test_empty_conversation(self, analyzer):
        """測試空對話"""
        result = analyzer.analyze_conversation([], [])
        
        assert result.coherence == 100.0  # 空對話默認滿分
        assert result.effectiveness == 0.0
        assert result.timing == 100.0


class TestQualityScore:
    """測試QualityScore數據類"""
    
    def test_quality_score_creation(self):
        """測試創建QualityScore"""
        score = QualityScore(
            coherence=80.0,
            effectiveness=75.0,
            timing=85.0,
            overall=80.0,
            details={"test": "data"}
        )
        
        assert score.coherence == 80.0
        assert score.effectiveness == 75.0
        assert score.timing == 85.0
        assert score.overall == 80.0
        assert score.details == {"test": "data"}


class TestIntegration:
    """整合測試"""
    
    def test_full_analysis_workflow(self):
        """測試完整分析流程"""
        analyzer = ConversationQualityAnalyzer()
        
        # 創建測試數據
        conversation = [
            {"role": "scammer", "text": "你好，我係銀行職員。"},
            {"role": "victim", "text": "你好。"},
            {"role": "scammer", "text": "你嘅帳戶有問題，需要立即處理。"},
            {"role": "expert", "text": "唔好驚，呢個係詐騙。"},
            {"role": "victim", "text": "真係？"}
        ]
        
        trust_history = [
            {"trust_in_scammer": 50, "trust_in_expert": 50, "alertness": 50},
            {"trust_in_scammer": 52, "trust_in_expert": 50, "alertness": 48},
            {"trust_in_scammer": 58, "trust_in_expert": 50, "alertness": 45},
            {"trust_in_scammer": 52, "trust_in_expert": 58, "alertness": 55},
            {"trust_in_scammer": 45, "trust_in_expert": 65, "alertness": 60}
        ]
        
        # 執行分析
        result = analyzer.analyze_conversation(conversation, trust_history)
        
        # 驗證結果
        assert result.overall > 0
        assert len(result.details["recommendations"]) > 0
        assert "conversation_length" in result.details
        assert result.details["conversation_length"] == 5
    
    def test_high_quality_conversation(self):
        """測試高質量對話"""
        analyzer = ConversationQualityAnalyzer()
        
        # 高質量對話：連貫、有效、時機好
        conversation = [
            {"role": "scammer", "text": "你好，我係銀行職員，你嘅帳戶被凍結。"},
            {"role": "victim", "text": "點解會凍結？"},
            {"role": "scammer", "text": "因為有可疑交易，需要立即驗證身份。"},
            {"role": "expert", "text": "唔好驚，銀行唔會咁樣打電話。你應該掛斷電話，然後打去銀行官方熱線確認。"},
            {"role": "victim", "text": "你講得啱，我而家就掛線。"}
        ]
        
        trust_history = [
            {"trust_in_scammer": 50, "trust_in_expert": 50, "alertness": 50},
            {"trust_in_scammer": 55, "trust_in_expert": 50, "alertness": 45},
            {"trust_in_scammer": 62, "trust_in_expert": 50, "alertness": 40},
            {"trust_in_scammer": 50, "trust_in_expert": 65, "alertness": 60},
            {"trust_in_scammer": 35, "trust_in_expert": 80, "alertness": 75}
        ]
        
        result = analyzer.analyze_conversation(conversation, trust_history)
        
        # 高質量對話應該有較高分數
        assert result.coherence >= 60
        assert result.effectiveness >= 50
        assert result.overall >= 50


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])
