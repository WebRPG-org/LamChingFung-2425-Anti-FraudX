"""
AgentService 集成指南 - 使用新的 Session 管理器
"""

# ============ 集成步驟 ============

# 步驟 1：在 agent_service.py 頂部添加導入
# ============================================

from backend.services.session_manager import (
    get_global_session_manager,
    EnhancedConversationSession
)

# 步驟 2：替換全局 session 存儲
# ============================================

# 舊代碼：
# _GLOBAL_SESSIONS: Dict[str, 'ConversationSession'] = {}

# 新代碼：
_session_manager = get_global_session_manager()


# 步驟 3：更新 AgentService 類
# ============================================

class AgentService:
    """Agent 服務層 - 使用新的 Session 管理器"""
    
    @staticmethod
    async def create_session(owner_id: str, game_type: str, persona_type: str) -> str:
        """
        創建新 session
        
        Args:
            owner_id: 所有者 ID（用戶 ID）
            game_type: 遊戲類型（rpg, simulation, etc）
            persona_type: 角色類型（scammer, expert, victim）
        
        Returns:
            新 session 的 ID
        """
        session_id = _session_manager.create_session(owner_id, game_type, persona_type)
        log.info(f"✅ Session 已創建: {session_id}")
        return session_id
    
    @staticmethod
    async def get_session(session_id: str, owner_id: str, game_type: str) -> Optional[EnhancedConversationSession]:
        """
        獲取 session（帶隔離驗證）
        
        Args:
            session_id: Session ID
            owner_id: 所有者 ID
            game_type: 遊戲類型
        
        Returns:
            Session 對象，如果不存在或驗證失敗則返回 None
        """
        session = _session_manager.get_session(session_id, owner_id, game_type)
        if not session:
            log.error(f"❌ Session 不存在或驗證失敗: {session_id}")
            return None
        return session
    
    @staticmethod
    async def close_session(session_id: str) -> bool:
        """
        關閉 session
        
        Args:
            session_id: Session ID
        
        Returns:
            是否關閉成功
        """
        return _session_manager.close_session(session_id)
    
    @staticmethod
    async def generate_response(
        session_id: str,
        owner_id: str,
        game_type: str,
        agent_type: str,
        user_message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成 Agent 回應
        
        Args:
            session_id: Session ID
            owner_id: 所有者 ID
            game_type: 遊戲類型
            agent_type: Agent 類型（scammer, expert, victim）
            user_message: 用戶消息
            **kwargs: 其他參數
        
        Returns:
            包含回應和遊戲狀態的字典
        """
        try:
            # 1. 獲取 session（帶隔離驗證）
            session = await AgentService.get_session(session_id, owner_id, game_type)
            if not session:
                return {
                    "error": "Session 不存在或驗證失敗",
                    "status": "error"
                }
            
            # 2. 添加用戶消息到對話歷史
            session.add_message(agent_type, user_message)
            
            # 3. 獲取對話上下文（最近 10 輪）
            context = session.get_history(limit=10)
            
            # 4. 調用 Agent 生成回應
            agent = AgentService._get_agent(agent_type)
            response = await agent.generate(
                message=user_message,
                context=context,
                **kwargs
            )
            
            # 5. 添加 Agent 回應到對話歷史
            session.add_message(agent_type, response)
            
            # 6. 更新評分系統
            game_status = session.update_scoring(agent_type, response, [])
            
            # 7. 返回結果
            return {
                "response": response,
                "game_status": game_status,
                "session_status": session.get_session_status(),
                "status": "success"
            }
        
        except Exception as e:
            log.error(f"❌ 生成回應失敗: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    def _get_agent(agent_type: str):
        """獲取 Agent 實例"""
        if agent_type == "scammer":
            from backend.agents.scammer import ScammerAgent
            return ScammerAgent()
        elif agent_type == "expert":
            from backend.agents.expert import ExpertAgent
            return ExpertAgent()
        elif agent_type == "victim":
            from backend.agents.victim import VictimAgent
            return VictimAgent()
        else:
            raise ValueError(f"未知的 Agent 類型: {agent_type}")


# 步驟 4：更新 API 路由
# ============================================

# 在 game_routes.py 或相應的路由文件中：

@app.post("/api/game/session/create")
async def create_session(request: CreateSessionRequest):
    """創建新遊戲 session"""
    try:
        session_id = await AgentService.create_session(
            owner_id=request.user_id,
            game_type=request.game_type,
            persona_type=request.persona_type
        )
        
        return {
            "session_id": session_id,
            "status": "success"
        }
    except Exception as e:
        log.error(f"❌ 創建 session 失敗: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@app.post("/api/game/session/{session_id}/message")
async def send_message(
    session_id: str,
    request: SendMessageRequest
):
    """發送消息並獲取 Agent 回應"""
    try:
        result = await AgentService.generate_response(
            session_id=session_id,
            owner_id=request.user_id,
            game_type=request.game_type,
            agent_type=request.agent_type,
            user_message=request.message
        )
        
        return result
    except Exception as e:
        log.error(f"❌ 發送消息失敗: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@app.post("/api/game/session/{session_id}/close")
async def close_session(
    session_id: str,
    request: CloseSessionRequest
):
    """關閉遊戲 session"""
    try:
        success = await AgentService.close_session(session_id)
        
        return {
            "success": success,
            "status": "success" if success else "error"
        }
    except Exception as e:
        log.error(f"❌ 關閉 session 失敗: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


# 步驟 5：更新前端調用
# ============================================

# 前端代碼示例（JavaScript/TypeScript）：

class GameClient {
    async createSession(userId, gameType, personaType) {
        const response = await fetch('/api/game/session/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                game_type: gameType,
                persona_type: personaType
            })
        });
        
        const data = await response.json();
        return data.session_id;
    }
    
    async sendMessage(sessionId, userId, gameType, agentType, message) {
        const response = await fetch(`/api/game/session/${sessionId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                game_type: gameType,
                agent_type: agentType,
                message: message
            })
        });
        
        const data = await response.json();
        return data;
    }
    
    async closeSession(sessionId, userId) {
        const response = await fetch(`/api/game/session/${sessionId}/close`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        const data = await response.json();
        return data.success;
    }
}


# 步驟 6：測試集成
# ============================================

# 運行測試：
# pytest backend/tests/test_session_manager.py -v
# pytest backend/tests/test_agent_service.py -v

# 手動測試：
# 1. 創建 session
# 2. 發送消息
# 3. 驗證隔離
# 4. 關閉 session


# ============ 遷移檢查清單 ============

# [ ] 1. 在 agent_service.py 中導入新的 Session 管理器
# [ ] 2. 替換全局 session 存儲
# [ ] 3. 更新 AgentService 類方法
# [ ] 4. 更新 API 路由
# [ ] 5. 更新前端調用
# [ ] 6. 運行單元測試
# [ ] 7. 運行集成測試
# [ ] 8. 進行手動測試
# [ ] 9. 驗證隔離機制
# [ ] 10. 驗證超時機制
# [ ] 11. 部署到測試環境
# [ ] 12. 部署到生產環境


# ============ 常見問題 ============

"""
Q1: 如何確保舊的 session 不會被污染？
A: 新的 Session 管理器會驗證 owner_id 和 game_type，
   確保只有授權的用戶才能訪問特定的 session。

Q2: 如何處理超時的 session？
A: 系統會自動檢測超時的 session（默認 60 分鐘），
   並在清理時移除它們。

Q3: 如何遷移現有的 session？
A: 可以編寫遷移腳本，將舊的 session 數據轉換為新格式。

Q4: 性能會受到影響嗎？
A: 不會。隔離驗證和超時檢測都是 O(1) 操作，
   性能開銷可以忽略不計。

Q5: 如何調試 session 問題？
A: 查看日誌文件，所有 session 操作都會記錄詳細的日誌。
"""


# ============ 下一步 ============

"""
1. 完成集成
2. 運行測試
3. 開始 Phase 1.2 - RAG 集成
4. 開始 Phase 1.3 - Token 優化
"""

