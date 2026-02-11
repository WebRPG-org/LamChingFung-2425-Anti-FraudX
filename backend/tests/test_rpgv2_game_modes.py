"""
RPGv2 遊戲模式測試套件
測試騙徒模式、專家模式、自動模式的完整功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.rpgv2_game_mode_manager import RPGv2GameModeManager, GameSession


class TestRPGv2GameModeManager:
    """測試遊戲模式管理器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.manager = RPGv2GameModeManager()
    
    def test_create_scammer_mode_session(self):
        """測試創建騙徒模式會話"""
        session = self.manager.create_session(
            session_id="test_scammer_001",
            mode="scammer",
            scam_type="假冒銀行",
            victim_persona="elderly"
        )
        
        assert session.session_id == "test_scammer_001"
        assert session.mode == "scammer"
        assert session.scam_type == "假冒銀行"
        assert session.victim_persona == "elderly"
        assert session.trust_in_scammer == 50.0
        assert session.alertness == 50.0
        assert session.round_count == 0
        assert session.player_score == 0
        assert session.ai_score == 0
        # 騙徒模式：玩家先開始，初始對話歷史應為空
        assert len(session.conversation_history) == 0
    
    def test_create_expert_mode_session(self):
        """測試創建專家模式會話"""
        session = self.manager.create_session(
            session_id="test_expert_001",
            mode="expert",
            scam_type="假冒親友",
            victim_persona="average"
        )
        
        assert session.mode == "expert"
        assert session.scam_type == "假冒親友"
        assert session.victim_persona == "average"
    
    def test_create_auto_mode_session(self):
        """測試創建自動模式會話"""
        session = self.manager.create_session(
            session_id="test_auto_001",
            mode="auto",
            scam_type="投資詐騙",
            victim_persona="overconfident"
        )
        
        assert session.mode == "auto"
        assert session.scam_type == "投資詐騙"
    
    def test_invalid_mode(self):
        """測試無效模式"""
        with pytest.raises(ValueError, match="無效的遊戲模式"):
            self.manager.create_session(
                session_id="test_invalid",
                mode="invalid_mode",
                scam_type="test",
                victim_persona="average"
            )
    
    def test_get_session(self):
        """測試獲取會話"""
        session = self.manager.create_session(
            session_id="test_get_001",
            mode="scammer",
            scam_type="假冒銀行",
            victim_persona="elderly"
        )
        
        retrieved = self.manager.get_session("test_get_001")
        assert retrieved is not None
        assert retrieved.session_id == "test_get_001"
        
        not_found = self.manager.get_session("nonexistent")
        assert not_found is None
    
    def test_update_session_scammer_mode(self):
        """測試更新騙徒模式會話"""
        session = self.manager.create_session(
            session_id="test_update_scammer",
            mode="scammer",
            scam_type="假冒銀行",
            victim_persona="elderly"
        )
        
        result = self.manager.update_session(
            session_id="test_update_scammer",
            player_message="你好，我是XX銀行的客服，你的帳戶出現異常。",
            ai_responses=[
                {
                    "role": "victim",
                    "content": "什麼？我的帳戶怎麼了？"
                }
            ],
            trust_changes={
                "scammer": 10,
                "expert": 0,
                "alertness": -5
            }
        )
        
        assert session.round_count == 1
        assert session.trust_in_scammer == 60.0
        assert session.alertness == 45.0
        assert len(session.conversation_history) == 2
        assert result["score_update"]["player"] > 0
    
    def test_update_session_expert_mode(self):
        """測試更新專家模式會話"""
        session = self.manager.create_session(
            session_id="test_update_expert",
            mode="expert",
            scam_type="假冒親友",
            victim_persona="average"
        )
        
        result = self.manager.update_session(
            session_id="test_update_expert",
            player_message="這是典型的詐騙手法，不要相信！",
            ai_responses=[
                {
                    "role": "scammer",
                    "content": "我真的是你朋友..."
                },
                {
                    "role": "victim",
                    "content": "我明白了，謝謝提醒。"
                }
            ],
            trust_changes={
                "scammer": -10,
                "expert": 15,
                "alertness": 20
            }
        )
        
        assert session.round_count == 1
        assert session.trust_in_scammer == 40.0
        assert session.trust_in_expert == 65.0
        assert session.alertness == 70.0
        assert result["score_update"]["player"] > 0
    
    def test_trust_value_limits(self):
        """測試信任度值限制"""
        session = self.manager.create_session(
            session_id="test_limits",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        # 測試上限
        self.manager.update_session(
            session_id="test_limits",
            player_message="test",
            ai_responses=[{"role": "victim", "content": "test"}],
            trust_changes={"scammer": 100, "alertness": 100}
        )
        
        assert session.trust_in_scammer <= 100
        assert session.alertness <= 100
        
        # 測試下限
        self.manager.update_session(
            session_id="test_limits",
            player_message="test",
            ai_responses=[{"role": "victim", "content": "test"}],
            trust_changes={"scammer": -200, "alertness": -200}
        )
        
        assert session.trust_in_scammer >= 0
        assert session.alertness >= 0
    
    def test_scammer_mode_win_condition(self):
        """測試騙徒模式勝利條件"""
        session = self.manager.create_session(
            session_id="test_scammer_win",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        # 模擬騙徒獲勝
        session.trust_in_scammer = 75
        game_status = self.manager._check_win_condition(session)
        
        assert game_status["game_over"] is True
        assert game_status["winner"] == "player"
        assert "信任" in game_status["reason"]
    
    def test_expert_mode_win_condition(self):
        """測試專家模式勝利條件"""
        session = self.manager.create_session(
            session_id="test_expert_win",
            mode="expert",
            scam_type="test",
            victim_persona="average"
        )
        
        # 模擬專家獲勝
        session.alertness = 75
        game_status = self.manager._check_win_condition(session)
        
        assert game_status["game_over"] is True
        assert game_status["winner"] == "player"
        assert "保護" in game_status["reason"]
    
    def test_auto_mode_completion(self):
        """測試自動模式完成條件"""
        session = self.manager.create_session(
            session_id="test_auto_complete",
            mode="auto",
            scam_type="test",
            victim_persona="average"
        )
        
        # 模擬達到回合數
        session.round_count = 10
        game_status = self.manager._check_win_condition(session)
        
        assert game_status["game_over"] is True
        assert game_status["winner"] == "none"
    
    def test_score_calculation_scammer_mode(self):
        """測試騙徒模式分數計算"""
        session = self.manager.create_session(
            session_id="test_score_scammer",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        # 使用權威策略
        score_update = self.manager._calculate_score_update(
            session=session,
            player_message="我是警察，你的帳戶有問題。",
            ai_responses=[{"role": "victim", "content": "好的，我該怎麼做？"}]
        )
        
        assert score_update["player"] > 0
    
    def test_score_calculation_expert_mode(self):
        """測試專家模式分數計算"""
        session = self.manager.create_session(
            session_id="test_score_expert",
            mode="expert",
            scam_type="test",
            victim_persona="average"
        )
        
        session.alertness = 65
        
        # 識別詐騙
        score_update = self.manager._calculate_score_update(
            session=session,
            player_message="這是詐騙，不要相信！",
            ai_responses=[
                {"role": "scammer", "content": "..."},
                {"role": "victim", "content": "明白了"}
            ]
        )
        
        assert score_update["player"] > 0
    
    def test_get_mode_info(self):
        """測試獲取模式信息"""
        scammer_info = self.manager.get_mode_info("scammer")
        assert scammer_info["name"] == "騙徒模式"
        assert scammer_info["player_role"] == "scammer"
        
        expert_info = self.manager.get_mode_info("expert")
        assert expert_info["name"] == "專家模式"
        assert expert_info["player_role"] == "expert"
        
        auto_info = self.manager.get_mode_info("auto")
        assert auto_info["name"] == "自動模式"
        assert auto_info["player_role"] == "observer"
    
    def test_get_all_modes(self):
        """測試獲取所有模式"""
        modes = self.manager.get_all_modes()
        assert len(modes) == 3
        
        mode_names = [m["mode"] for m in modes]
        assert "scammer" in mode_names
        assert "expert" in mode_names
        assert "auto" in mode_names
    
    def test_delete_session(self):
        """測試刪除會話"""
        session = self.manager.create_session(
            session_id="test_delete",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        success = self.manager.delete_session("test_delete")
        assert success is True
        
        retrieved = self.manager.get_session("test_delete")
        assert retrieved is None
        
        # 刪除不存在的會話
        success = self.manager.delete_session("nonexistent")
        assert success is False
    
    def test_get_session_stats(self):
        """測試獲取會話統計"""
        session = self.manager.create_session(
            session_id="test_stats",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        # 添加一些對話
        self.manager.update_session(
            session_id="test_stats",
            player_message="測試消息1",
            ai_responses=[{"role": "victim", "content": "回應1"}],
            trust_changes={"scammer": 5}
        )
        
        self.manager.update_session(
            session_id="test_stats",
            player_message="測試消息2",
            ai_responses=[{"role": "victim", "content": "回應2"}],
            trust_changes={"scammer": 5}
        )
        
        stats = self.manager.get_session_stats("test_stats")
        
        assert stats["session_id"] == "test_stats"
        assert stats["mode"] == "scammer"
        assert stats["round_count"] == 2
        assert stats["message_stats"]["total_messages"] == 4
        assert stats["message_stats"]["player_messages"] == 2
        assert stats["message_stats"]["ai_messages"] == 2
        assert "trust_data" in stats
        assert "duration" in stats
    
    def test_conversation_history_tracking(self):
        """測試對話歷史記錄"""
        session = self.manager.create_session(
            session_id="test_history",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        self.manager.update_session(
            session_id="test_history",
            player_message="玩家消息",
            ai_responses=[
                {"role": "victim", "content": "AI回應"}
            ],
            trust_changes={}
        )
        
        assert len(session.conversation_history) == 2
        assert session.conversation_history[0]["role"] == "player"
        assert session.conversation_history[0]["content"] == "玩家消息"
        assert session.conversation_history[1]["role"] == "victim"
        assert session.conversation_history[1]["content"] == "AI回應"
        assert "timestamp" in session.conversation_history[0]
    
    def test_multiple_sessions(self):
        """測試多個會話管理"""
        session1 = self.manager.create_session(
            session_id="multi_001",
            mode="scammer",
            scam_type="test1",
            victim_persona="elderly"
        )
        
        session2 = self.manager.create_session(
            session_id="multi_002",
            mode="expert",
            scam_type="test2",
            victim_persona="average"
        )
        
        session3 = self.manager.create_session(
            session_id="multi_003",
            mode="auto",
            scam_type="test3",
            victim_persona="overconfident"
        )
        
        assert len(self.manager.sessions) == 3
        assert self.manager.get_session("multi_001").mode == "scammer"
        assert self.manager.get_session("multi_002").mode == "expert"
        assert self.manager.get_session("multi_003").mode == "auto"
    
    def test_max_rounds_condition(self):
        """測試最大回合數條件"""
        session = self.manager.create_session(
            session_id="test_max_rounds",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        # 模擬達到最大回合數
        session.round_count = 15
        session.trust_in_scammer = 55
        session.alertness = 45
        
        game_status = self.manager._check_win_condition(session)
        
        assert game_status["game_over"] is True
        assert game_status["winner"] == "player"  # 信任度 > 警覺性
        assert "最大回合數" in game_status["reason"]


class TestGameModeIntegration:
    """集成測試"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.manager = RPGv2GameModeManager()
    
    def test_complete_scammer_game_flow(self):
        """測試完整的騙徒模式遊戲流程"""
        # 1. 創建會話
        session = self.manager.create_session(
            session_id="flow_scammer",
            mode="scammer",
            scam_type="假冒銀行",
            victim_persona="elderly"
        )
        
        assert session.round_count == 0
        
        # 2. 第一回合
        result1 = self.manager.update_session(
            session_id="flow_scammer",
            player_message="你好，我是XX銀行客服。",
            ai_responses=[{"role": "victim", "content": "你好。"}],
            trust_changes={"scammer": 5}
        )
        
        assert session.round_count == 1
        assert result1["game_status"]["game_over"] is False
        
        # 3. 第二回合
        result2 = self.manager.update_session(
            session_id="flow_scammer",
            player_message="你的帳戶出現異常，需要立即處理。",
            ai_responses=[{"role": "victim", "content": "什麼異常？"}],
            trust_changes={"scammer": 10}
        )
        
        assert session.round_count == 2
        
        # 4. 獲取統計
        stats = self.manager.get_session_stats("flow_scammer")
        assert stats["round_count"] == 2
        assert stats["message_stats"]["total_messages"] == 4
        
        # 5. 刪除會話
        success = self.manager.delete_session("flow_scammer")
        assert success is True
    
    def test_complete_expert_game_flow(self):
        """測試完整的專家模式遊戲流程"""
        # 1. 創建會話
        session = self.manager.create_session(
            session_id="flow_expert",
            mode="expert",
            scam_type="假冒親友",
            victim_persona="average"
        )
        
        # 2. 專家介入
        result = self.manager.update_session(
            session_id="flow_expert",
            player_message="這是詐騙！不要相信！",
            ai_responses=[
                {"role": "scammer", "content": "我真的是..."},
                {"role": "victim", "content": "我明白了，謝謝。"}
            ],
            trust_changes={
                "scammer": -15,
                "expert": 20,
                "alertness": 25
            }
        )
        
        assert session.alertness == 75.0
        assert result["score_update"]["player"] > 0
        
        # 3. 檢查勝利條件
        game_status = self.manager._check_win_condition(session)
        assert game_status["game_over"] is True
        assert game_status["winner"] == "player"


class TestScoreCalculation:
    """測試分數計算邏輯"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.manager = RPGv2GameModeManager()
    
    def test_scammer_authority_strategy(self):
        """測試騙徒權威策略得分"""
        session = self.manager.create_session(
            session_id="score_auth",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        score = self.manager._calculate_score_update(
            session=session,
            player_message="我是警察，你涉嫌洗錢。",
            ai_responses=[{"role": "victim", "content": "什麼？"}]
        )
        
        assert score["player"] >= 15  # successful_tactic
    
    def test_scammer_urgency_strategy(self):
        """測試騙徒緊急策略得分"""
        session = self.manager.create_session(
            session_id="score_urgency",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        score = self.manager._calculate_score_update(
            session=session,
            player_message="必須立即處理，否則帳戶會被凍結！",
            ai_responses=[{"role": "victim", "content": "好的"}]
        )
        
        assert score["player"] >= 15
    
    def test_scammer_emotion_strategy(self):
        """測試騙徒情感策略得分"""
        session = self.manager.create_session(
            session_id="score_emotion",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        score = self.manager._calculate_score_update(
            session=session,
            player_message="我真的很困難，需要你的幫助。",
            ai_responses=[{"role": "victim", "content": "可以"}]
        )
        
        assert score["player"] >= 15
    
    def test_scammer_greed_strategy(self):
        """測試騙徒利益誘惑策略得分"""
        session = self.manager.create_session(
            session_id="score_greed",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        score = self.manager._calculate_score_update(
            session=session,
            player_message="恭喜你中獎了，可以獲得巨額獎金！",
            ai_responses=[{"role": "victim", "content": "真的嗎？"}]
        )
        
        assert score["player"] >= 15
    
    def test_expert_detection_score(self):
        """測試專家識別詐騙得分"""
        session = self.manager.create_session(
            session_id="score_detect",
            mode="expert",
            scam_type="test",
            victim_persona="average"
        )
        
        score = self.manager._calculate_score_update(
            session=session,
            player_message="這是典型的詐騙手法！",
            ai_responses=[
                {"role": "scammer", "content": "..."},
                {"role": "victim", "content": "..."}
            ]
        )
        
        assert score["player"] >= 20  # scam_detected


class TestInstantWinConditions:
    """測試即時勝負判定"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.manager = RPGv2GameModeManager()
    
    def test_scammer_instant_win_provide_data(self):
        """測試騙徒模式即時勝利：受害者同意提供資料"""
        session = self.manager.create_session(
            session_id="instant_win_data",
            mode="scammer",
            scam_type="假冒銀行",
            victim_persona="elderly"
        )
        
        # 模擬受害者同意提供資料
        result = self.manager.update_session(
            session_id="instant_win_data",
            player_message="請提供你的銀行帳號以便核實。",
            ai_responses=[{"role": "victim", "content": "好的，我會提供資料給你。"}],
            trust_changes={
                "scammer": 100,
                "alertness": -50,
                "instant_win": {
                    "instant_win": True,
                    "winner": "player",
                    "reason": "騙徒成功！受害者同意提供資料或金錢"
                }
            }
        )
        
        assert result["game_status"]["game_over"] is True
        assert result["game_status"]["winner"] == "player"
        assert result["game_status"]["instant_win"] is True
        assert "提供資料" in result["game_status"]["reason"]
    
    def test_scammer_instant_win_give_money(self):
        """測試騙徒模式即時勝利：受害者同意俾錢"""
        session = self.manager.create_session(
            session_id="instant_win_money",
            mode="scammer",
            scam_type="假冒親友",
            victim_persona="average"
        )
        
        result = self.manager.update_session(
            session_id="instant_win_money",
            player_message="我急需用錢，可以轉帳給我嗎？",
            ai_responses=[{"role": "victim", "content": "好的，我會俾錢你。"}],
            trust_changes={
                "scammer": 100,
                "alertness": -50,
                "instant_win": {
                    "instant_win": True,
                    "winner": "player",
                    "reason": "騙徒成功！受害者同意提供資料或金錢"
                }
            }
        )
        
        assert result["game_status"]["game_over"] is True
        assert result["game_status"]["winner"] == "player"
        assert result["game_status"]["instant_win"] is True
    
    def test_scammer_instant_lose_refuse_and_report(self):
        """測試騙徒模式即時失敗：受害者拒絕並報警"""
        session = self.manager.create_session(
            session_id="instant_lose_report",
            mode="scammer",
            scam_type="投資詐騙",
            victim_persona="average"
        )
        
        result = self.manager.update_session(
            session_id="instant_lose_report",
            player_message="投資這個項目可以賺大錢。",
            ai_responses=[{"role": "victim", "content": "我不會俾錢，我要報警！"}],
            trust_changes={
                "scammer": -100,
                "alertness": 100,
                "instant_win": {
                    "instant_win": True,
                    "winner": "ai",
                    "reason": "防詐成功！受害者識破騙局並拒絕配合"
                }
            }
        )
        
        assert result["game_status"]["game_over"] is True
        assert result["game_status"]["winner"] == "ai"
        assert result["game_status"]["instant_win"] is True
        assert "防詐成功" in result["game_status"]["reason"]
    
    def test_expert_instant_win_victim_trust_expert(self):
        """測試專家模式即時勝利：受害者相信專家"""
        session = self.manager.create_session(
            session_id="expert_instant_win",
            mode="expert",
            scam_type="假冒銀行",
            victim_persona="average"
        )
        
        result = self.manager.update_session(
            session_id="expert_instant_win",
            player_message="這是詐騙！不要相信他，立即報警！",
            ai_responses=[
                {"role": "scammer", "content": "我真的是銀行..."},
                {"role": "victim", "content": "我相信專家，不會提供資料，我要報警。"}
            ],
            trust_changes={
                "expert": 100,
                "alertness": 100,
                "scammer": -100,
                "instant_win": {
                    "instant_win": True,
                    "winner": "player",
                    "reason": "防詐成功！受害者聽從專家建議，拒絕被騙"
                }
            }
        )
        
        assert result["game_status"]["game_over"] is True
        assert result["game_status"]["winner"] == "player"
        assert result["game_status"]["instant_win"] is True
        assert "防詐成功" in result["game_status"]["reason"]
    
    def test_expert_instant_lose_victim_scammed(self):
        """測試專家模式即時失敗：受害者被騙"""
        session = self.manager.create_session(
            session_id="expert_instant_lose",
            mode="expert",
            scam_type="投資詐騙",
            victim_persona="overconfident"
        )
        
        result = self.manager.update_session(
            session_id="expert_instant_lose",
            player_message="小心這可能是詐騙。",
            ai_responses=[
                {"role": "scammer", "content": "這是合法投資..."},
                {"role": "victim", "content": "我不相信專家，我會提供資料和俾錢投資。"}
            ],
            trust_changes={
                "expert": -100,
                "alertness": -100,
                "scammer": 100,
                "instant_win": {
                    "instant_win": True,
                    "winner": "ai",
                    "reason": "防詐失敗！受害者不聽勸告，被騙成功"
                }
            }
        )
        
        assert result["game_status"]["game_over"] is True
        assert result["game_status"]["winner"] == "ai"
        assert result["game_status"]["instant_win"] is True
        assert "防詐失敗" in result["game_status"]["reason"]
    
    def test_instant_win_bonus_score(self):
        """測試即時勝利獎勵分數"""
        session = self.manager.create_session(
            session_id="instant_win_bonus",
            mode="scammer",
            scam_type="test",
            victim_persona="average"
        )
        
        initial_score = session.player_score
        
        result = self.manager.update_session(
            session_id="instant_win_bonus",
            player_message="測試消息",
            ai_responses=[{"role": "victim", "content": "我會俾錢你。"}],
            trust_changes={
                "scammer": 100,
                "instant_win": {
                    "instant_win": True,
                    "winner": "player",
                    "reason": "騙徒成功！"
                }
            }
        )
        
        # 即時勝利應該有額外100分獎勵
        assert session.player_score >= initial_score + 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
