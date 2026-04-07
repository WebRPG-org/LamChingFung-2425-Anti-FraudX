"""
Session 管理器測試 - Phase 1.1 測試
測試 session 隔離、生命週期管理、跨遊戲污染防止
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from backend.services.session_manager import (
    SessionIsolationValidator,
    SessionLifecycleManager,
    EnhancedConversationSession,
    GlobalSessionManager,
    get_global_session_manager
)


class TestSessionIsolationValidator:
    """測試 Session 隔離驗證器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.validator = SessionIsolationValidator()
    
    def test_register_session(self):
        """測試註冊 session"""
        session_id = "test_session_1"
        owner_id = "user_1"
        game_type = "rpg"
        
        result = self.validator.register_session(session_id, owner_id, game_type)
        assert result is True
        assert self.validator.session_owners[session_id] == owner_id
        assert self.validator.session_game_types[session_id] == game_type
    
    def test_validate_session_access_success(self):
        """測試成功的 session 訪問驗證"""
        session_id = "test_session_2"
        owner_id = "user_2"
        game_type = "simulation"
        
        self.validator.register_session(session_id, owner_id, game_type)
        result = self.validator.validate_session_access(session_id, owner_id, game_type)
        
        assert result is True
    
    def test_validate_session_access_wrong_owner(self):
        """測試錯誤的所有者訪問"""
        session_id = "test_session_3"
        owner_id = "user_3"
        game_type = "rpg"
        
        self.validator.register_session(session_id, owner_id, game_type)
        result = self.validator.validate_session_access(session_id, "wrong_owner", game_type)
        
        assert result is False
    
    def test_validate_session_access_wrong_game_type(self):
        """測試錯誤的遊戲類型訪問"""
        session_id = "test_session_4"
        owner_id = "user_4"
        game_type = "rpg"
        
        self.validator.register_session(session_id, owner_id, game_type)
        result = self.validator.validate_session_access(session_id, owner_id, "simulation")
        
        assert result is False
    
    def test_unregister_session(self):
        """測試註銷 session"""
        session_id = "test_session_5"
        owner_id = "user_5"
        game_type = "rpg"
        
        self.validator.register_session(session_id, owner_id, game_type)
        result = self.validator.unregister_session(session_id)
        
        assert result is True
        assert session_id not in self.validator.session_owners
    
    def test_get_session_info(self):
        """測試獲取 session 信息"""
        session_id = "test_session_6"
        owner_id = "user_6"
        game_type = "rpg"
        
        self.validator.register_session(session_id, owner_id, game_type)
        info = self.validator.get_session_info(session_id)
        
        assert info is not None
        assert info["session_id"] == session_id
        assert info["owner_id"] == owner_id
        assert info["game_type"] == game_type


class TestSessionLifecycleManager:
    """測試 Session 生命週期管理器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.manager = SessionLifecycleManager(timeout_minutes=1)
    
    def test_create_session(self):
        """測試創建 session"""
        session_id = "test_session_7"
        metadata = {"test": "data"}
        
        result = self.manager.create_session(session_id, metadata)
        
        assert result is True
        assert self.manager.session_states[session_id] == "active"
    
    def test_update_activity(self):
        """測試更新活動時間"""
        session_id = "test_session_8"
        self.manager.create_session(session_id)
        
        old_time = self.manager.session_last_activity[session_id]
        
        # 等待一點時間
        import time
        time.sleep(0.1)
        
        result = self.manager.update_activity(session_id)
        new_time = self.manager.session_last_activity[session_id]
        
        assert result is True
        assert new_time > old_time
    
    def test_check_timeout_not_expired(self):
        """測試未超時的 session"""
        session_id = "test_session_9"
        self.manager.create_session(session_id)
        
        result = self.manager.check_timeout(session_id)
        
        assert result is False
    
    def test_check_timeout_expired(self):
        """測試已超時的 session"""
        session_id = "test_session_10"
        self.manager.create_session(session_id)
        
        # 手動設置超時時間
        self.manager.session_last_activity[session_id] = datetime.now() - timedelta(minutes=2)
        
        result = self.manager.check_timeout(session_id)
        
        assert result is True
    
    def test_close_session(self):
        """測試關閉 session"""
        session_id = "test_session_11"
        self.manager.create_session(session_id)
        
        result = self.manager.close_session(session_id)
        
        assert result is True
        assert self.manager.session_states[session_id] == "closed"
    
    def test_get_session_state(self):
        """測試獲取 session 狀態"""
        session_id = "test_session_12"
        self.manager.create_session(session_id)
        
        state = self.manager.get_session_state(session_id)
        
        assert state == "active"
    
    def test_get_session_duration(self):
        """測試獲取 session 持續時間"""
        session_id = "test_session_13"
        self.manager.create_session(session_id)
        
        import time
        time.sleep(0.1)
        
        duration = self.manager.get_session_duration(session_id)
        
        assert duration is not None
        assert duration >= 0


class TestEnhancedConversationSession:
    """測試增強版 ConversationSession"""
    
    def test_create_session(self):
        """測試創建增強 session"""
        session_id = "test_session_14"
        owner_id = "user_14"
        game_type = "rpg"
        persona_type = "scammer"
        
        session = EnhancedConversationSession(session_id, owner_id, game_type, persona_type)
        
        assert session.session_id == session_id
        assert session.owner_id == owner_id
        assert session.game_type == game_type
        assert session.persona_type == persona_type
    
    def test_add_message(self):
        """測試添加消息"""
        session = EnhancedConversationSession("test_15", "user_15", "rpg", "scammer")
        
        result = session.add_message("scammer", "Hello, victim!")
        
        assert result is True
        assert len(session.conversation_history) == 1
        assert session.turn_count == 1
    
    def test_add_message_with_isolation_check(self):
        """測試添加消息時的隔離檢查"""
        session = EnhancedConversationSession("test_16", "user_16", "rpg", "scammer")
        
        # 正常添加
        result = session.add_message("scammer", "Message 1", validate_isolation=True)
        assert result is True
        
        # 嘗試用錯誤的所有者訪問
        session.owner_id = "wrong_owner"
        result = session.add_message("scammer", "Message 2", validate_isolation=True)
        assert result is False
    
    def test_get_history(self):
        """測試獲取對話歷史"""
        session = EnhancedConversationSession("test_17", "user_17", "rpg", "scammer")
        
        session.add_message("scammer", "Message 1")
        session.add_message("victim", "Message 2")
        session.add_message("scammer", "Message 3")
        
        history = session.get_history(limit=2)
        
        assert len(history) == 2
        assert history[0]["content"] == "Message 2"
        assert history[1]["content"] == "Message 3"
    
    def test_get_session_status(self):
        """測試獲取 session 狀態"""
        session = EnhancedConversationSession("test_18", "user_18", "rpg", "scammer")
        
        session.add_message("scammer", "Test message")
        
        status = session.get_session_status()
        
        assert status["session_id"] == "test_18"
        assert status["owner_id"] == "user_18"
        assert status["game_type"] == "rpg"
        assert status["persona_type"] == "scammer"
        assert status["turn_count"] == 1
        assert status["message_count"] == 1
    
    def test_close_session(self):
        """測試關閉 session"""
        session = EnhancedConversationSession("test_19", "user_19", "rpg", "scammer")
        
        result = session.close()
        
        assert result is True
        assert session.lifecycle_manager.get_session_state("test_19") == "closed"


class TestGlobalSessionManager:
    """測試全局 Session 管理器"""
    
    def setup_method(self):
        """每個測試前的設置"""
        self.manager = GlobalSessionManager()
    
    def test_create_session(self):
        """測試創建 session"""
        session_id = self.manager.create_session("user_20", "rpg", "scammer")
        
        assert session_id != ""
        assert session_id in self.manager.sessions
    
    def test_get_session(self):
        """測試獲取 session"""
        session_id = self.manager.create_session("user_21", "rpg", "scammer")
        
        session = self.manager.get_session(session_id, "user_21", "rpg")
        
        assert session is not None
        assert session.session_id == session_id
    
    def test_get_session_wrong_owner(self):
        """測試用錯誤的所有者獲取 session"""
        session_id = self.manager.create_session("user_22", "rpg", "scammer")
        
        session = self.manager.get_session(session_id, "wrong_owner", "rpg")
        
        assert session is None
    
    def test_close_session(self):
        """測試關閉 session"""
        session_id = self.manager.create_session("user_23", "rpg", "scammer")
        
        result = self.manager.close_session(session_id)
        
        assert result is True
        assert session_id not in self.manager.sessions
    
    def test_get_all_sessions(self):
        """測試獲取所有 session"""
        self.manager.create_session("user_24", "rpg", "scammer")
        self.manager.create_session("user_24", "simulation", "expert")
        self.manager.create_session("user_25", "rpg", "victim")
        
        all_sessions = self.manager.get_all_sessions()
        user_24_sessions = self.manager.get_all_sessions(owner_id="user_24")
        
        assert len(all_sessions) == 3
        assert len(user_24_sessions) == 2
    
    def test_cleanup_expired_sessions(self):
        """測試清理過期 session"""
        session_id_1 = self.manager.create_session("user_26", "rpg", "scammer")
        session_id_2 = self.manager.create_session("user_26", "rpg", "expert")
        
        # 手動設置第一個 session 為過期
        session_1 = self.manager.sessions[session_id_1]
        session_1.lifecycle_manager.session_last_activity[session_id_1] = datetime.now() - timedelta(minutes=2)
        
        cleaned_count = self.manager.cleanup_expired_sessions()
        
        assert cleaned_count == 1
        assert session_id_1 not in self.manager.sessions
        assert session_id_2 in self.manager.sessions


class TestCrossGamePollutionPrevention:
    """測試跨遊戲污染防止"""
    
    def test_different_game_types_isolation(self):
        """測試不同遊戲類型的隔離"""
        manager = GlobalSessionManager()
        
        # 創建 RPG session
        rpg_session_id = manager.create_session("user_27", "rpg", "scammer")
        
        # 創建 Simulation session
        sim_session_id = manager.create_session("user_27", "simulation", "expert")
        
        # 嘗試用 RPG 類型訪問 Simulation session
        session = manager.get_session(sim_session_id, "user_27", "rpg")
        
        assert session is None  # 應該失敗
    
    def test_different_owners_isolation(self):
        """測試不同所有者的隔離"""
        manager = GlobalSessionManager()
        
        # 用戶 1 創建 session
        session_id = manager.create_session("user_28", "rpg", "scammer")
        
        # 用戶 2 嘗試訪問
        session = manager.get_session(session_id, "user_29", "rpg")
        
        assert session is None  # 應該失敗
    
    def test_conversation_isolation(self):
        """測試對話隔離"""
        manager = GlobalSessionManager()
        
        # 創建兩個 session
        session_id_1 = manager.create_session("user_30", "rpg", "scammer")
        session_id_2 = manager.create_session("user_30", "rpg", "expert")
        
        session_1 = manager.get_session(session_id_1, "user_30", "rpg")
        session_2 = manager.get_session(session_id_2, "user_30", "rpg")
        
        # 添加消息到第一個 session
        session_1.add_message("scammer", "Message in session 1")
        
        # 檢查第二個 session 是否被污染
        history_2 = session_2.get_history()
        
        assert len(history_2) == 0  # 應該是空的


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


