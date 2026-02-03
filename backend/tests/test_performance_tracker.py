"""
Unit Tests for Performance Tracker
Tests trust calculation, inertia, fatigue, and outcome detection
"""

import pytest
from utils.performance_tracker import PerformanceTracker, VictimTrustState
from config import config
from exceptions import PersonaNotFoundError


class TestPerformanceTrackerInitialization:
    """Test tracker initialization"""
    
    def test_init_with_valid_persona(self):
        """Should initialize with valid persona"""
        tracker = PerformanceTracker(victim_persona="elderly")
        assert tracker.victim_persona == "elderly"
        assert tracker.turn_count == 0
        assert tracker.victim_trust.trust_in_scammer == 70  # Elderly initial trust
    
    def test_init_with_invalid_persona(self):
        """Should raise error for invalid persona"""
        with pytest.raises(PersonaNotFoundError) as exc_info:
            PerformanceTracker(victim_persona="invalid")
        
        assert "invalid" in str(exc_info.value)
        assert "elderly" in str(exc_info.value)
    
    def test_initial_trust_values_elderly(self):
        """Should set correct initial trust for elderly"""
        tracker = PerformanceTracker(victim_persona="elderly")
        assert tracker.victim_trust.trust_in_scammer == 70
        assert tracker.victim_trust.trust_in_expert == 50
        assert tracker.victim_trust.alertness == 30
    
    def test_initial_trust_values_overconfident(self):
        """Should set correct initial trust for overconfident"""
        tracker = PerformanceTracker(victim_persona="overconfident")
        assert tracker.victim_trust.trust_in_scammer == 30
        assert tracker.victim_trust.trust_in_expert == 40
        assert tracker.victim_trust.alertness == 70


class TestTrustInertia:
    """Test psychological inertia calculations"""
    
    def test_high_trust_increase_inertia(self):
        """Should apply inertia when increasing already high trust"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.trust_in_scammer = 85
        
        multiplier = tracker._calculate_inertia_multiplier(85, +10)
        assert multiplier == config.trust.INERTIA_HIGH_TRUST_INCREASE  # 0.6
    
    def test_high_trust_decrease_inertia(self):
        """Should apply strong inertia when decreasing high trust"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.trust_in_scammer = 85
        
        multiplier = tracker._calculate_inertia_multiplier(85, -10)
        assert multiplier == config.trust.INERTIA_HIGH_TRUST_DECREASE  # 0.5
    
    def test_low_trust_no_inertia(self):
        """Should not apply inertia for low trust"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.trust_in_scammer = 30
        
        multiplier = tracker._calculate_inertia_multiplier(30, +10)
        assert multiplier == 1.0


class TestStrategyFatigue:
    """Test strategy fatigue calculations"""
    
    def test_no_fatigue_first_use(self):
        """Should have no fatigue on first use"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        multiplier = tracker._calculate_fatigue_multiplier(
            tactics=["authority"],
            recent_tactics=[]
        )
        assert multiplier == 1.0
    
    def test_fatigue_after_3_uses(self):
        """Should apply strong fatigue after 3 consecutive uses"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        multiplier = tracker._calculate_fatigue_multiplier(
            tactics=["authority"],
            recent_tactics=[["authority"], ["authority"], ["authority"]]
        )
        assert multiplier == config.trust.FATIGUE_3_TIMES  # 0.5
    
    def test_fatigue_after_2_uses(self):
        """Should apply moderate fatigue after 2 uses"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        multiplier = tracker._calculate_fatigue_multiplier(
            tactics=["authority"],
            recent_tactics=[["authority"], ["authority"]]
        )
        assert multiplier == config.trust.FATIGUE_2_TIMES  # 0.7
    
    def test_fatigue_after_1_use(self):
        """Should apply light fatigue after 1 use"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        multiplier = tracker._calculate_fatigue_multiplier(
            tactics=["authority"],
            recent_tactics=[["authority"]]
        )
        assert multiplier == config.trust.FATIGUE_1_TIME  # 0.9


class TestEmotionalMultipliers:
    """Test emotional state multipliers"""
    
    def test_anxious_boosts_scammer(self):
        """Anxious state should boost scammer effectiveness"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.emotional_state = "anxious"
        
        multiplier = tracker._calculate_emotional_multiplier(change=+10, is_scammer=True)
        assert multiplier == config.trust.EMOTIONAL_ANXIOUS_SCAMMER_BOOST  # 1.3
    
    def test_calm_reduces_scammer(self):
        """Calm state should reduce scammer effectiveness"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.emotional_state = "calm"
        
        multiplier = tracker._calculate_emotional_multiplier(change=+10, is_scammer=True)
        assert multiplier == config.trust.EMOTIONAL_CALM_SCAMMER_PENALTY  # 0.8
    
    def test_suspicious_greatly_reduces_scammer(self):
        """Suspicious state should greatly reduce scammer effectiveness"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.emotional_state = "suspicious"
        
        multiplier = tracker._calculate_emotional_multiplier(change=+10, is_scammer=True)
        assert multiplier == config.trust.EMOTIONAL_SUSPICIOUS_SCAMMER_PENALTY  # 0.5
    
    def test_panicked_greatly_boosts_scammer(self):
        """Panicked state should greatly boost scammer effectiveness"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.emotional_state = "panicked"
        
        multiplier = tracker._calculate_emotional_multiplier(change=+10, is_scammer=True)
        assert multiplier == config.trust.EMOTIONAL_PANICKED_SCAMMER_BOOST  # 1.5


class TestScammerAnalysis:
    """Test scammer turn analysis"""
    
    def test_authority_tactic_detection(self):
        """Should detect authority tactic"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_scammer_turn(
            dialogue="我係銀行職員，你嘅戶口有問題",
            victim_response="係咪真㗎？"
        )
        
        assert "authority" in analysis["tactics_used"]
        assert analysis["trust_change"] > 0
    
    def test_urgency_tactic_detection(self):
        """Should detect urgency tactic"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_scammer_turn(
            dialogue="你要立即處理，否則戶口會被凍結",
            victim_response="咁點算？"
        )
        
        assert "urgency" in analysis["tactics_used"]
        assert analysis["trust_change"] > 0
    
    def test_benefits_tactic_detection(self):
        """Should detect benefits tactic"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_scammer_turn(
            dialogue="你有政府補貼可以領取",
            victim_response="真係㗎？"
        )
        
        assert "benefits" in analysis["tactics_used"]
        assert analysis["trust_change"] > 0
    
    def test_trust_change_capped_by_max(self):
        """Trust change should be capped by max per turn"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        # Use multiple tactics to generate large change
        analysis = tracker.analyze_scammer_turn(
            dialogue="我係警察，你要立即處理，否則會被捕。你有補貼可以領取。",
            victim_response="好的"
        )
        
        max_change = config.get_max_trust_change("elderly")  # 12
        assert analysis["trust_change"] <= max_change
    
    def test_victim_suspicion_reduces_trust(self):
        """Victim suspicion should reduce scammer trust"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_scammer_turn(
            dialogue="你要俾錢",
            victim_response="你係咪呃我？有問題喎"
        )
        
        assert analysis["exposed"] == True
        assert analysis["trust_change"] < 0


class TestExpertAnalysis:
    """Test expert turn analysis"""
    
    def test_empathy_detection(self):
        """Should detect empathy approach"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_expert_turn(
            expert_advice="唔好驚，我明白你嘅擔心",
            victim_response="多謝你",
            scammer_message="你要立即處理"
        )
        
        assert "empathy" in analysis["approach"]
        assert analysis["trust_change"] > 0
    
    def test_evidence_detection(self):
        """Should detect evidence-based approach"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_expert_turn(
            expert_advice="銀行唔會咁樣聯絡你，呢個係騙案手法",
            victim_response="原來係咁",
            scammer_message="我係銀行職員"
        )
        
        assert "evidence" in analysis["approach"]
        assert analysis["trust_change"] > 0
    
    def test_actionable_advice_detection(self):
        """Should detect actionable advice"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_expert_turn(
            expert_advice="立即掛線，然後打去銀行官方熱線核實",
            victim_response="好的",
            scammer_message="你要俾錢"
        )
        
        assert "actionable" in analysis["approach"]
        assert analysis["trust_change"] > 0
    
    def test_no_empathy_penalty(self):
        """Should apply penalty if no empathy"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        analysis = tracker.analyze_expert_turn(
            expert_advice="呢個係騙案",  # No empathy
            victim_response="哦",
            scammer_message="你要俾錢"
        )
        
        # Should have negative trust change due to lack of empathy
        assert analysis["trust_change"] < 0


class TestOutcomeDetection:
    """Test outcome detection logic"""
    
    def test_scammer_wins_high_trust(self):
        """Scammer should win when victim trust >= 80"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.trust_in_scammer = 85
        
        outcome = tracker.check_outcome([])
        
        assert outcome["status"] == "SUCCESS"
        assert outcome["winner"] == "scammer"
    
    def test_expert_wins_high_trust_low_scammer(self):
        """Expert should win when expert trust >= 75 and scammer < 40"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.trust_in_expert = 80
        tracker.victim_trust.trust_in_scammer = 30
        
        outcome = tracker.check_outcome([])
        
        assert outcome["status"] == "FAILURE"
        assert outcome["winner"] == "expert"
    
    def test_victim_wins_high_alertness(self):
        """Victim should win when alertness >= 80"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.victim_trust.alertness = 85
        
        outcome = tracker.check_outcome([])
        
        assert outcome["status"] == "FAILURE"
        assert outcome["winner"] == "victim"
    
    def test_max_rounds_scammer_higher(self):
        """Should favor scammer if max rounds reached and scammer trust higher"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.turn_count = config.simulation.MAX_ROUNDS
        tracker.victim_trust.trust_in_scammer = 60
        tracker.victim_trust.trust_in_expert = 50
        
        outcome = tracker.check_outcome([])
        
        assert outcome["winner"] == "scammer"
    
    def test_max_rounds_expert_higher(self):
        """Should favor expert if max rounds reached and expert trust higher"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.turn_count = config.simulation.MAX_ROUNDS
        tracker.victim_trust.trust_in_scammer = 50
        tracker.victim_trust.trust_in_expert = 60
        
        outcome = tracker.check_outcome([])
        
        assert outcome["winner"] == "expert"
    
    def test_continue_when_no_outcome(self):
        """Should continue when no outcome conditions met"""
        tracker = PerformanceTracker(victim_persona="elderly")
        tracker.turn_count = 5
        tracker.victim_trust.trust_in_scammer = 50
        tracker.victim_trust.trust_in_expert = 50
        tracker.victim_trust.alertness = 50
        
        outcome = tracker.check_outcome([])
        
        assert outcome["status"] == "CONTINUE"


class TestVictimTrustState:
    """Test VictimTrustState class"""
    
    def test_update_scammer_trust(self):
        """Should update scammer trust correctly"""
        state = VictimTrustState()
        state.trust_in_scammer = 50
        
        state.update("scammer", +10, "Test reason")
        
        assert state.trust_in_scammer == 60
        assert len(state.history) == 1
        assert state.history[0]["type"] == "scammer_trust"
        assert state.history[0]["change"] == 10
    
    def test_trust_capped_at_100(self):
        """Trust should be capped at 100"""
        state = VictimTrustState()
        state.trust_in_scammer = 95
        
        state.update("scammer", +20, "Test reason")
        
        assert state.trust_in_scammer == 100
    
    def test_trust_floored_at_0(self):
        """Trust should be floored at 0"""
        state = VictimTrustState()
        state.trust_in_scammer = 5
        
        state.update("scammer", -20, "Test reason")
        
        assert state.trust_in_scammer == 0
    
    def test_get_dominant_trust_scammer(self):
        """Should identify scammer as dominant"""
        state = VictimTrustState()
        state.trust_in_scammer = 80
        state.trust_in_expert = 40
        
        assert state.get_dominant_trust() == "scammer"
    
    def test_get_dominant_trust_expert(self):
        """Should identify expert as dominant"""
        state = VictimTrustState()
        state.trust_in_scammer = 40
        state.trust_in_expert = 80
        
        assert state.get_dominant_trust() == "expert"
    
    def test_get_dominant_trust_conflicted(self):
        """Should identify conflicted state"""
        state = VictimTrustState()
        state.trust_in_scammer = 50
        state.trust_in_expert = 50
        
        assert state.get_dominant_trust() == "conflicted"


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""
    
    def test_elderly_falls_for_authority_scam(self):
        """Elderly should be vulnerable to authority scam"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        # Round 1: Scammer uses authority
        tracker.analyze_scammer_turn(
            dialogue="我係銀行職員，你嘅戶口有問題",
            victim_response="係咪真㗎？我好驚"
        )
        
        # Trust should increase significantly for elderly
        assert tracker.victim_trust.trust_in_scammer > 70
    
    def test_overconfident_resists_authority(self):
        """Overconfident should resist authority scam"""
        tracker = PerformanceTracker(victim_persona="overconfident")
        
        # Round 1: Scammer uses authority
        tracker.analyze_scammer_turn(
            dialogue="我係銀行職員，你嘅戶口有問題",
            victim_response="你憑咩咁講？"
        )
        
        # Trust should not increase much for overconfident
        assert tracker.victim_trust.trust_in_scammer < 40
    
    def test_expert_with_empathy_wins_elderly(self):
        """Expert with empathy should win elderly victim"""
        tracker = PerformanceTracker(victim_persona="elderly")
        
        # Multiple rounds of expert with empathy
        for _ in range(3):
            tracker.analyze_expert_turn(
                expert_advice="唔好驚，我明白你嘅擔心。銀行唔會咁樣聯絡你。立即掛線。",
                victim_response="多謝你，我明白",
                scammer_message="你要立即處理"
            )
        
        # Expert trust should be high
        assert tracker.victim_trust.trust_in_expert > 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
