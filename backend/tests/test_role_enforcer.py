"""
Unit Tests for Role Enforcer
Tests role consistency checking and violation detection
"""

import pytest
from utils.role_enforcer import RoleEnforcer
from exceptions import RoleConsistencyError


class TestScammerConsistency:
    """Test scammer role consistency checks"""
    
    def test_scammer_forbidden_fear_phrases(self):
        """Should detect when scammer expresses fear"""
        dialogue = "我好驚，我唔知點算"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == False
        assert len(issues) > 0
        assert any("害怕" in issue or "困惑" in issue for issue in issues)
    
    def test_scammer_forbidden_help_seeking(self):
        """Should detect when scammer seeks help"""
        dialogue = "你可以幫我嗎？我需要幫手"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == False
        assert len(issues) > 0
        assert any("求助" in issue for issue in issues)
    
    def test_scammer_inner_thoughts_exposed(self):
        """Should detect when scammer's inner thoughts are exposed"""
        dialogue = "（心想：我要騙佢）你好，我係銀行職員"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == False
        assert any("內心獨白" in issue for issue in issues)
    
    def test_scammer_reveals_fake_identity(self):
        """Should detect when scammer reveals fake identity"""
        dialogue = "李（假官員）：你好"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == False
        assert any("假身份" in issue or "暴露" in issue for issue in issues)
    
    def test_scammer_outputs_script_example(self):
        """Should detect when scammer outputs script/teaching material"""
        dialogue = "以下是一個對話範例：**場景：** 銀行詐騙"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == False
        assert any("示例腳本" in issue or "教學材料" in issue for issue in issues)
    
    def test_scammer_valid_authority_dialogue(self):
        """Should pass valid authority dialogue"""
        dialogue = "你好，我係XX銀行嘅客戶經理。你嘅戶口有可疑交易，需要立即處理。"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == True
        assert len(issues) == 0
    
    def test_scammer_valid_urgency_dialogue(self):
        """Should pass valid urgency dialogue"""
        dialogue = "你要立即處理，否則戶口會被凍結。請提供你嘅身份證號碼。"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == True
        assert len(issues) == 0
    
    def test_scammer_role_confusion_with_victim(self):
        """Should detect when scammer says victim's lines"""
        dialogue = "我好擔心，我唔知點樣，我真係好想了解"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        assert is_valid == False
        # Should detect multiple victim phrases
        assert len(issues) >= 2
    
    def test_scammer_repetition_detection(self):
        """Should detect high repetition with previous victim message"""
        dialogue = "我好擔心你嘅戶口"
        previous_victim = "我好擔心我嘅戶口"
        
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(
            dialogue, previous_victim
        )
        
        assert is_valid == False
        assert any("重複" in issue for issue in issues)


class TestExpertConsistency:
    """Test expert role consistency checks"""
    
    def test_expert_requests_sensitive_data(self):
        """Should detect when expert requests sensitive data"""
        dialogue = "請你提供銀行賬戶號碼，我需要核實"
        is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(dialogue)
        
        assert is_valid == False
        assert any("敏感資料" in issue for issue in issues)
    
    def test_expert_impersonates_official(self):
        """Should detect when expert impersonates official"""
        dialogue = "我係金融犯罪調查局，你要配合調查"
        is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(dialogue)
        
        assert is_valid == False
        assert any("執法者" in issue or "騙徒用語" in issue for issue in issues)
    
    def test_expert_uses_scammer_language(self):
        """Should detect when expert uses scammer language"""
        dialogue = "你要配合調查，提供你嘅資料"
        is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(dialogue)
        
        assert is_valid == False
        assert any("騙徒用語" in issue for issue in issues)
    
    def test_expert_valid_warning(self):
        """Should pass valid warning"""
        dialogue = "唔好俾任何資料，立即掛線。如果你唔放心，打去銀行官方熱線核實。"
        is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(dialogue)
        
        assert is_valid == True
        assert len(issues) == 0
    
    def test_expert_valid_evidence_based(self):
        """Should pass valid evidence-based advice"""
        dialogue = "呢個係典型嘅假冒銀行詐騙。銀行唔會咁樣聯絡你。立即報警。"
        is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(dialogue)
        
        assert is_valid == True
        assert len(issues) == 0


class TestVictimConsistency:
    """Test victim role consistency checks"""
    
    def test_victim_comforts_others(self):
        """Should detect when victim comforts others"""
        dialogue = "唔好驚，我明白你嘅感受。我會幫你留意下。"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "elderly")
        
        assert is_valid == False
        assert any("安慰" in issue or "幫助" in issue for issue in issues)
    
    def test_victim_acts_like_expert(self):
        """Should detect when victim acts like expert"""
        dialogue = "你應該立即報警，建議你聯絡銀行核實"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "elderly")
        
        assert is_valid == False
        assert len(issues) > 0
    
    def test_victim_elderly_uses_professional_terms(self):
        """Should detect when elderly uses professional terms"""
        dialogue = "根據我嘅分析，呢個係詐騙手法"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "elderly")
        
        assert is_valid == False
        assert any("專業術語" in issue for issue in issues)
    
    def test_victim_overconfident_shows_weakness(self):
        """Should detect when overconfident shows weakness"""
        dialogue = "我好驚，點算好？我需要先和家人商量"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "overconfident")
        
        assert is_valid == False
        assert any("示弱" in issue for issue in issues)
    
    def test_victim_overconfident_uses_simplified_chinese(self):
        """Should detect when overconfident uses simplified Chinese"""
        dialogue = "我现在有点担心，我现在有点害怕"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "overconfident")
        
        assert is_valid == False
        assert any("簡體中文" in issue for issue in issues)
    
    def test_victim_overconfident_leaks_data(self):
        """Should detect when overconfident leaks data"""
        dialogue = "我可以提供我的身份證號碼，我可以提供我的銀行賬戶"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "overconfident")
        
        assert is_valid == False
        assert any("洩露資料" in issue for issue in issues)
    
    def test_victim_elderly_valid_fear(self):
        """Should pass valid fear expression for elderly"""
        dialogue = "我好驚啊，點算好？係咪真㗎？"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "elderly")
        
        assert is_valid == True
        assert len(issues) == 0
    
    def test_victim_overconfident_valid_challenge(self):
        """Should pass valid challenge for overconfident"""
        dialogue = "你憑咩咁講？你係咪搞錯咗？呢啲我識啦"
        is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "overconfident")
        
        assert is_valid == True
        assert len(issues) == 0


class TestRepetitionDetection:
    """Test repetition detection in conversation history"""
    
    def test_detect_exact_repetition(self):
        """Should detect exact repetition"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "你要立即處理"},
            {"speaker": "受騙者", "dialogue": "好的"},
            {"speaker": "騙徒", "dialogue": "你要立即處理"},  # Exact repeat
        ]
        
        current_dialogue = "你要立即處理"
        
        is_repetitive, error_msg, similar_turns = RoleEnforcer.detect_repetition_in_history(
            conversation_history, "騙徒", current_dialogue, threshold=0.85
        )
        
        assert is_repetitive == True
        assert len(similar_turns) > 0
    
    def test_detect_high_similarity(self):
        """Should detect high similarity (>85%)"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "你要立即處理你嘅戶口問題"},
            {"speaker": "受騙者", "dialogue": "好的"},
        ]
        
        current_dialogue = "你要立即處理你嘅戶口問題啊"  # Very similar
        
        is_repetitive, error_msg, similar_turns = RoleEnforcer.detect_repetition_in_history(
            conversation_history, "騙徒", current_dialogue, threshold=0.85
        )
        
        assert is_repetitive == True
    
    def test_no_repetition_different_content(self):
        """Should not detect repetition for different content"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "你要立即處理"},
            {"speaker": "受騙者", "dialogue": "好的"},
        ]
        
        current_dialogue = "請提供你嘅身份證號碼"  # Different content
        
        is_repetitive, error_msg, similar_turns = RoleEnforcer.detect_repetition_in_history(
            conversation_history, "騙徒", current_dialogue, threshold=0.85
        )
        
        assert is_repetitive == False
        assert len(similar_turns) == 0
    
    def test_detect_progressive_repetition(self):
        """Should detect progressive repetition (3+ similar turns)"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "你要立即處理你嘅戶口"},
            {"speaker": "受騙者", "dialogue": "好的"},
            {"speaker": "騙徒", "dialogue": "你要立即處理你嘅戶口問題"},
            {"speaker": "受騙者", "dialogue": "明白"},
            {"speaker": "騙徒", "dialogue": "你要立即處理你嘅戶口資料"},
        ]
        
        current_dialogue = "你要立即處理你嘅戶口情況"
        
        is_repetitive, error_msg, similar_turns = RoleEnforcer.detect_repetition_in_history(
            conversation_history, "騙徒", current_dialogue, threshold=0.70
        )
        
        assert is_repetitive == True
        assert "渐进式重复" in error_msg or "漸進式重複" in error_msg


class TestRewritePromptGeneration:
    """Test rewrite prompt generation"""
    
    def test_generate_scammer_rewrite_prompt(self):
        """Should generate rewrite prompt for scammer"""
        issues = ["❌ 騙徒不應表達害怕：「我好驚」"]
        original = "我好驚，我唔知點算"
        context = {
            "victim_message": "你係咪呃我？",
            "expert_message": "呢個係騙案",
            "scam_tactic": "假冒官員詐騙"
        }
        
        prompt = RoleEnforcer.generate_rewrite_prompt(
            "scammer", original, issues, context
        )
        
        assert "絕對禁止" in prompt
        assert "我好驚" in prompt
        assert "假冒官員詐騙" in prompt
        assert "重寫" in prompt
    
    def test_generate_victim_rewrite_prompt(self):
        """Should generate rewrite prompt for victim"""
        issues = ["❌ 受害者不應安慰對方：「唔好驚」"]
        original = "唔好驚，我幫你留意下"
        context = {
            "persona_type": "elderly",
            "persona_name": "陳婆婆",
            "age": "72"
        }
        
        prompt = RoleEnforcer.generate_rewrite_prompt(
            "victim", original, issues, context
        )
        
        assert "絕對禁止" in prompt
        assert "唔好驚" in prompt
        assert "重寫" in prompt
    
    def test_generate_expert_rewrite_prompt(self):
        """Should generate rewrite prompt for expert"""
        issues = ["❌ 🚨🚨🚨 絕對禁止！專家要求提供敏感資料"]
        original = "請你提供銀行賬戶號碼"
        context = {}
        
        prompt = RoleEnforcer.generate_rewrite_prompt(
            "expert", original, issues, context
        )
        
        assert "絕對禁止" in prompt
        assert "敏感資料" in prompt or "銀行賬戶" in prompt
        assert "重寫" in prompt


class TestDialogueFlowAnalysis:
    """Test dialogue flow analysis"""
    
    def test_analyze_clean_dialogue(self):
        """Should analyze clean dialogue with no issues"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "你好，我係銀行職員"},
            {"speaker": "受騙者", "dialogue": "係咪真㗎？"},
            {"speaker": "專家", "dialogue": "唔好信，立即掛線"},
        ]
        
        analysis = RoleEnforcer.analyze_dialogue_flow(conversation_history)
        
        assert analysis["total_issues"] == 0
        assert analysis["role_switches"] == 0
        assert analysis["quality_score"] == 100
    
    def test_analyze_dialogue_with_role_switches(self):
        """Should detect role switches"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "我好驚，你可以幫我嗎？"},  # Role switch
            {"speaker": "受騙者", "dialogue": "唔好驚，我幫你"},  # Role switch
        ]
        
        analysis = RoleEnforcer.analyze_dialogue_flow(conversation_history)
        
        assert analysis["role_switches"] >= 2
        assert analysis["quality_score"] < 100
    
    def test_quality_score_calculation(self):
        """Should calculate quality score correctly"""
        conversation_history = [
            {"speaker": "騙徒", "dialogue": "我好驚"},  # 1 issue
            {"speaker": "受騙者", "dialogue": "唔好驚"},  # 1 issue
        ]
        
        analysis = RoleEnforcer.analyze_dialogue_flow(conversation_history)
        
        # Score = 100 - (issues * 5) - (role_switches * 20)
        # Should be less than 100
        assert analysis["quality_score"] < 100
        assert analysis["quality_score"] >= 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_dialogue(self):
        """Should handle empty dialogue"""
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency("")
        
        # Empty dialogue should be valid (no violations)
        assert is_valid == True
    
    def test_very_short_dialogue(self):
        """Should handle very short dialogue"""
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency("好")
        
        # Short dialogue should be valid if no violations
        assert is_valid == True
    
    def test_very_long_dialogue(self):
        """Should handle very long dialogue"""
        long_dialogue = "你好，我係銀行職員。" * 100
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(long_dialogue)
        
        # Should still check for violations
        assert isinstance(is_valid, bool)
    
    def test_mixed_language_dialogue(self):
        """Should handle mixed language dialogue"""
        dialogue = "Hello, 我係銀行職員. Please provide your account number."
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        # Should still work with mixed language
        assert isinstance(is_valid, bool)
    
    def test_special_characters(self):
        """Should handle special characters"""
        dialogue = "你好！！！我係銀行職員？？？立即處理！！！"
        is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue)
        
        # Should handle special characters
        assert isinstance(is_valid, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
