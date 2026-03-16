"""
Session 管理器 - Phase 1.1 升級版本
實現 session 隔離、生命週期管理、跨遊戲污染防止
"""

import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from utils.logger import log


class SessionIsolationValidator:
    """Session 隔離驗證器 - 防止跨遊戲污染"""
    
    def __init__(self):
        self.session_owners: Dict[str, str] = {}  # session_id -> owner_id
        self.session_game_types: Dict[str, str] = {}  # session_id -> game_type
        self.session_timestamps: Dict[str, datetime] = {}  # session_id -> created_time
    
    def register_session(self, session_id: str, owner_id: str, game_type: str) -> bool:
        """
        註冊新 session
        
        Args:
            session_id: Session ID
            owner_id: 所有者 ID（用戶 ID）
            game_type: 遊戲類型（rpg, simulation, etc）
        
        Returns:
            是否註冊成功
        """
        try:
            if session_id in self.session_owners:
                log.warning(f"⚠️ Session 已存在: {session_id}")
                return False
            
            self.session_owners[session_id] = owner_id
            self.session_game_types[session_id] = game_type
            self.session_timestamps[session_id] = datetime.now()
            
            log.info(f"✅ Session 已註冊: {session_id} (owner: {owner_id}, type: {game_type})")
            return True
        
        except Exception as e:
            log.error(f"❌ Session 註冊失敗: {e}")
            return False
    
    def validate_session_access(self, session_id: str, owner_id: str, game_type: str) -> bool:
        """
        驗證 session 訪問權限
        
        Args:
            session_id: Session ID
            owner_id: 所有者 ID
            game_type: 遊戲類型
        
        Returns:
            是否有訪問權限
        """
        try:
            # 檢查 session 是否存在
            if session_id not in self.session_owners:
                log.warning(f"⚠️ Session 不存在: {session_id}")
                return False
            
            # 檢查所有者是否匹配
            if self.session_owners[session_id] != owner_id:
                log.warning(f"⚠️ Session 所有者不匹配: {session_id}")
                return False
            
            # 檢查遊戲類型是否匹配
            if self.session_game_types[session_id] != game_type:
                log.warning(f"⚠️ Session 遊戲類型不匹配: {session_id}")
                return False
            
            log.info(f"✅ Session 訪問驗證通過: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Session 訪問驗證失敗: {e}")
            return False
    
    def unregister_session(self, session_id: str) -> bool:
        """
        註銷 session
        
        Args:
            session_id: Session ID
        
        Returns:
            是否註銷成功
        """
        try:
            if session_id in self.session_owners:
                del self.session_owners[session_id]
                del self.session_game_types[session_id]
                del self.session_timestamps[session_id]
                
                log.info(f"✅ Session 已註銷: {session_id}")
                return True
            
            log.warning(f"⚠️ Session 不存在: {session_id}")
            return False
        
        except Exception as e:
            log.error(f"❌ Session 註銷失敗: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取 session 信息
        
        Args:
            session_id: Session ID
        
        Returns:
            Session 信息，如果不存在則返回 None
        """
        try:
            if session_id not in self.session_owners:
                return None
            
            return {
                "session_id": session_id,
                "owner_id": self.session_owners[session_id],
                "game_type": self.session_game_types[session_id],
                "created_at": self.session_timestamps[session_id].isoformat(),
                "age_seconds": (datetime.now() - self.session_timestamps[session_id]).total_seconds()
            }
        
        except Exception as e:
            log.error(f"❌ 獲取 Session 信息失敗: {e}")
            return None


class SessionLifecycleManager:
    """Session 生命週期管理器"""
    
    def __init__(self, timeout_minutes: int = 60):
        self.timeout_minutes = timeout_minutes
        self.session_states: Dict[str, str] = {}  # session_id -> state
        self.session_created_times: Dict[str, datetime] = {}  # session_id -> created_time
        self.session_last_activity: Dict[str, datetime] = {}  # session_id -> last_activity_time
        self.session_metadata: Dict[str, Dict[str, Any]] = {}  # session_id -> metadata
    
    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        創建新 session
        
        Args:
            session_id: Session ID
            metadata: 可選的元數據
        
        Returns:
            是否創建成功
        """
        try:
            if session_id in self.session_states:
                log.warning(f"⚠️ Session 已存在: {session_id}")
                return False
            
            now = datetime.now()
            self.session_states[session_id] = "active"
            self.session_created_times[session_id] = now
            self.session_last_activity[session_id] = now
            self.session_metadata[session_id] = metadata or {}
            
            log.info(f"✅ Session 已創建: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Session 創建失敗: {e}")
            return False
    
    def update_activity(self, session_id: str) -> bool:
        """
        更新 session 活動時間
        
        Args:
            session_id: Session ID
        
        Returns:
            是否更新成功
        """
        try:
            if session_id not in self.session_states:
                log.warning(f"⚠️ Session 不存在: {session_id}")
                return False
            
            self.session_last_activity[session_id] = datetime.now()
            return True
        
        except Exception as e:
            log.error(f"❌ Session 活動更新失敗: {e}")
            return False
    
    def check_timeout(self, session_id: str) -> bool:
        """
        檢查 session 是否超時
        
        Args:
            session_id: Session ID
        
        Returns:
            是否超時
        """
        try:
            if session_id not in self.session_last_activity:
                return True
            
            last_activity = self.session_last_activity[session_id]
            timeout_threshold = datetime.now() - timedelta(minutes=self.timeout_minutes)
            
            is_timeout = last_activity < timeout_threshold
            
            if is_timeout:
                log.warning(f"⏰ Session 已超時: {session_id}")
            
            return is_timeout
        
        except Exception as e:
            log.error(f"❌ Session 超時檢查失敗: {e}")
            return True
    
    def close_session(self, session_id: str) -> bool:
        """
        關閉 session
        
        Args:
            session_id: Session ID
        
        Returns:
            是否關閉成功
        """
        try:
            if session_id not in self.session_states:
                log.warning(f"⚠️ Session 不存在: {session_id}")
                return False
            
            self.session_states[session_id] = "closed"
            log.info(f"✅ Session 已關閉: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Session 關閉失敗: {e}")
            return False
    
    def get_session_state(self, session_id: str) -> Optional[str]:
        """
        獲取 session 狀態
        
        Args:
            session_id: Session ID
        
        Returns:
            Session 狀態（active/closed/timeout），如果不存在則返回 None
        """
        try:
            if session_id not in self.session_states:
                return None
            
            # 檢查是否超時
            if self.check_timeout(session_id):
                self.session_states[session_id] = "timeout"
            
            return self.session_states[session_id]
        
        except Exception as e:
            log.error(f"❌ 獲取 Session 狀態失敗: {e}")
            return None
    
    def get_session_duration(self, session_id: str) -> Optional[int]:
        """
        獲取 session 持續時間（秒）
        
        Args:
            session_id: Session ID
        
        Returns:
            持續時間（秒），如果不存在則返回 None
        """
        try:
            if session_id not in self.session_created_times:
                return None
            
            created_time = self.session_created_times[session_id]
            duration = (datetime.now() - created_time).total_seconds()
            
            return int(duration)
        
        except Exception as e:
            log.error(f"❌ 獲取 Session 持續時間失敗: {e}")
            return None
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理過期的 session
        
        Returns:
            清理的 session 數量
        """
        try:
            expired_sessions = []
            
            for session_id in list(self.session_states.keys()):
                if self.check_timeout(session_id):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.close_session(session_id)
            
            log.info(f"🧹 已清理 {len(expired_sessions)} 個過期 session")
            return len(expired_sessions)
        
        except Exception as e:
            log.error(f"❌ Session 清理失敗: {e}")
            return 0


class EnhancedConversationSession:
    """增強版 ConversationSession - 集成隔離和生命週期管理"""
    
    def __init__(self, session_id: str, owner_id: str, game_type: str, persona_type: str):
        self.session_id = session_id
        self.owner_id = owner_id
        self.game_type = game_type
        self.persona_type = persona_type
        
        # 基本信息
        self.created_at = datetime.now()
        self.conversation_history: List[Dict[str, Any]] = []
        self.turn_count = 0
        
        # 隔離驗證
        self.isolation_validator = SessionIsolationValidator()
        self.isolation_validator.register_session(session_id, owner_id, game_type)
        
        # 生命週期管理
        self.lifecycle_manager = SessionLifecycleManager()
        self.lifecycle_manager.create_session(session_id, {
            "owner_id": owner_id,
            "game_type": game_type,
            "persona_type": persona_type
        })
        
        # 評分系統
        self.trust_in_scammer = 50
        self.trust_in_expert = 50
        
        log.info(f"✅ 增強 Session 已創建: {session_id}")
    
    def add_message(self, role: str, content: str, validate_isolation: bool = True) -> bool:
        """
        添加消息到對話歷史
        
        Args:
            role: 角色（scammer/expert/victim）
            content: 消息內容
            validate_isolation: 是否驗證隔離
        
        Returns:
            是否添加成功
        """
        try:
            # 驗證隔離
            if validate_isolation:
                if not self.isolation_validator.validate_session_access(
                    self.session_id, self.owner_id, self.game_type
                ):
                    log.error(f"❌ Session 隔離驗證失敗: {self.session_id}")
                    return False
            
            # 檢查超時
            if self.lifecycle_manager.check_timeout(self.session_id):
                log.error(f"❌ Session 已超時: {self.session_id}")
                return False
            
            # 添加消息
            self.conversation_history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "turn": self.turn_count
            })
            
            self.turn_count += 1
            
            # 更新活動時間
            self.lifecycle_manager.update_activity(self.session_id)
            
            log.info(f"✅ 消息已添加: {self.session_id} (turn: {self.turn_count})")
            return True
        
        except Exception as e:
            log.error(f"❌ 添加消息失敗: {e}")
            return False
    
    def get_history(self, limit: int = 10, validate_isolation: bool = True) -> List[Dict[str, Any]]:
        """
        獲取對話歷史
        
        Args:
            limit: 返回的最大消息數
            validate_isolation: 是否驗證隔離
        
        Returns:
            對話歷史列表
        """
        try:
            # 驗證隔離
            if validate_isolation:
                if not self.isolation_validator.validate_session_access(
                    self.session_id, self.owner_id, self.game_type
                ):
                    log.error(f"❌ Session 隔離驗證失敗: {self.session_id}")
                    return []
            
            if limit:
                return self.conversation_history[-limit:]
            return self.conversation_history
        
        except Exception as e:
            log.error(f"❌ 獲取對話歷史失敗: {e}")
            return []
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        獲取 session 狀態
        
        Returns:
            Session 狀態信息
        """
        try:
            return {
                "session_id": self.session_id,
                "owner_id": self.owner_id,
                "game_type": self.game_type,
                "persona_type": self.persona_type,
                "state": self.lifecycle_manager.get_session_state(self.session_id),
                "duration_seconds": self.lifecycle_manager.get_session_duration(self.session_id),
                "turn_count": self.turn_count,
                "message_count": len(self.conversation_history),
                "created_at": self.created_at.isoformat(),
                "trust_in_scammer": self.trust_in_scammer,
                "trust_in_expert": self.trust_in_expert
            }
        
        except Exception as e:
            log.error(f"❌ 獲取 Session 狀態失敗: {e}")
            return {}
    
    def close(self) -> bool:
        """
        關閉 session
        
        Returns:
            是否關閉成功
        """
        try:
            success = self.lifecycle_manager.close_session(self.session_id)
            if success:
                self.isolation_validator.unregister_session(self.session_id)
                log.info(f"✅ Session 已關閉: {self.session_id}")
            return success
        
        except Exception as e:
            log.error(f"❌ Session 關閉失敗: {e}")
            return False


# 全局 Session 管理器
class GlobalSessionManager:
    """全局 Session 管理器 - 管理所有活躍的 session"""
    
    def __init__(self):
        self.sessions: Dict[str, EnhancedConversationSession] = {}
        self.isolation_validator = SessionIsolationValidator()
        self.lifecycle_manager = SessionLifecycleManager()
    
    def create_session(self, owner_id: str, game_type: str, persona_type: str) -> str:
        """
        創建新 session
        
        Args:
            owner_id: 所有者 ID
            game_type: 遊戲類型
            persona_type: 角色類型
        
        Returns:
            新 session 的 ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            session = EnhancedConversationSession(
                session_id, owner_id, game_type, persona_type
            )
            
            self.sessions[session_id] = session
            
            log.info(f"✅ 全局 Session 已創建: {session_id}")
            return session_id
        
        except Exception as e:
            log.error(f"❌ 全局 Session 創建失敗: {e}")
            return ""
    
    def get_session(self, session_id: str, owner_id: str, game_type: str) -> Optional[EnhancedConversationSession]:
        """
        獲取 session
        
        Args:
            session_id: Session ID
            owner_id: 所有者 ID
            game_type: 遊戲類型
        
        Returns:
            Session 對象，如果不存在或驗證失敗則返回 None
        """
        try:
            if session_id not in self.sessions:
                log.warning(f"⚠️ Session 不存在: {session_id}")
                return None
            
            session = self.sessions[session_id]
            
            # 驗證隔離
            if not session.isolation_validator.validate_session_access(session_id, owner_id, game_type):
                log.error(f"❌ Session 隔離驗證失敗: {session_id}")
                return None
            
            return session
        
        except Exception as e:
            log.error(f"❌ 獲取 Session 失敗: {e}")
            return None
    
    def close_session(self, session_id: str) -> bool:
        """
        關閉 session
        
        Args:
            session_id: Session ID
        
        Returns:
            是否關閉成功
        """
        try:
            if session_id not in self.sessions:
                log.warning(f"⚠️ Session 不存在: {session_id}")
                return False
            
            session = self.sessions[session_id]
            success = session.close()
            
            if success:
                del self.sessions[session_id]
                log.info(f"✅ 全局 Session 已關閉: {session_id}")
            
            return success
        
        except Exception as e:
            log.error(f"❌ 全局 Session 關閉失敗: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理過期的 session
        
        Returns:
            清理的 session 數量
        """
        try:
            expired_count = 0
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if session.lifecycle_manager.check_timeout(session_id):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.close_session(session_id)
                expired_count += 1
            
            log.info(f"🧹 已清理 {expired_count} 個過期 session")
            return expired_count
        
        except Exception as e:
            log.error(f"❌ Session 清理失敗: {e}")
            return 0
    
    def get_all_sessions(self, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取所有 session
        
        Args:
            owner_id: 可選的所有者 ID 過濾
        
        Returns:
            Session 列表
        """
        try:
            sessions_list = []
            
            for session_id, session in self.sessions.items():
                if owner_id and session.owner_id != owner_id:
                    continue
                
                sessions_list.append(session.get_session_status())
            
            return sessions_list
        
        except Exception as e:
            log.error(f"❌ 獲取 Session 列表失敗: {e}")
            return []


# 全局實例
_global_session_manager: Optional[GlobalSessionManager] = None

def get_global_session_manager() -> GlobalSessionManager:
    """獲取全局 Session 管理器實例"""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = GlobalSessionManager()
    return _global_session_manager

