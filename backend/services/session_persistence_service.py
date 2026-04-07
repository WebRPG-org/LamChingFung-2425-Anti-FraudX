"""
AI 防詐平台 v4.1 - 會話持久化服務
支持 Firestore 持久化、會話恢復、數據導出、數據分析
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from utils.logger import log


class SessionPersistenceService:
    """會話持久化服務 - 管理會話的保存、恢復和分析"""
    
    def __init__(self):
        """初始化持久化服務"""
        self.sessions_cache = {}  # 本地緩存
        self.firestore_client = None  # Firestore 客戶端（待初始化）
        
        log.info("✅ 會話持久化服務初始化完成")
    
    # ============ 會話保存 ============
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        保存會話到持久化存儲
        
        Args:
            session_id: 會話 ID
            session_data: 會話數據
        
        Returns:
            是否保存成功
        """
        try:
            # 1. 保存到本地緩存
            self.sessions_cache[session_id] = {
                **session_data,
                "saved_at": datetime.now().isoformat(),
                "version": "4.1.0"
            }
            
            # 2. 保存到 Firestore（如果已連接）
            if self.firestore_client:
                await self._save_to_firestore(session_id, session_data)
            
            log.info(f"💾 會話已保存: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 會話保存失敗: {e}")
            return False
    
    async def save_conversation(self, session_id: str, round_number: int, 
                               speaker: str, message: str, metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        保存對話記錄
        
        Args:
            session_id: 會話 ID
            round_number: 回合數
            speaker: 說話者
            message: 消息內容
            metrics: 可選的性能指標
        
        Returns:
            是否保存成功
        """
        try:
            conversation_data = {
                "session_id": session_id,
                "round_number": round_number,
                "speaker": speaker,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics or {}
            }
            
            # 保存到本地緩存
            if session_id not in self.sessions_cache:
                self.sessions_cache[session_id] = {"conversations": []}
            
            if "conversations" not in self.sessions_cache[session_id]:
                self.sessions_cache[session_id]["conversations"] = []
            
            self.sessions_cache[session_id]["conversations"].append(conversation_data)
            
            # 保存到 Firestore（如果已連接）
            if self.firestore_client:
                await self._save_conversation_to_firestore(conversation_data)
            
            log.info(f"💬 對話已保存: {session_id} - 回合 {round_number}")
            return True
        
        except Exception as e:
            log.error(f"❌ 對話保存失敗: {e}")
            return False
    
    async def save_analysis(self, session_id: str, analysis_data: Dict[str, Any]) -> bool:
        """
        保存分析結果
        
        Args:
            session_id: 會話 ID
            analysis_data: 分析數據
        
        Returns:
            是否保存成功
        """
        try:
            analysis = {
                "session_id": session_id,
                **analysis_data,
                "saved_at": datetime.now().isoformat()
            }
            
            # 保存到本地緩存
            if session_id not in self.sessions_cache:
                self.sessions_cache[session_id] = {}
            
            self.sessions_cache[session_id]["analysis"] = analysis
            
            # 保存到 Firestore（如果已連接）
            if self.firestore_client:
                await self._save_analysis_to_firestore(analysis)
            
            log.info(f"📊 分析結果已保存: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 分析結果保存失敗: {e}")
            return False
    
    # ============ 會話恢復 ============
    
    async def recover_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        恢復會話
        
        Args:
            session_id: 會話 ID
        
        Returns:
            恢復的會話數據，如果不存在則返回 None
        """
        try:
            # 1. 先從本地緩存查找
            if session_id in self.sessions_cache:
                log.info(f"🔄 從本地緩存恢復會話: {session_id}")
                return self.sessions_cache[session_id]
            
            # 2. 從 Firestore 查找（如果已連接）
            if self.firestore_client:
                session_data = await self._recover_from_firestore(session_id)
                if session_data:
                    # 保存到本地緩存
                    self.sessions_cache[session_id] = session_data
                    log.info(f"🔄 從 Firestore 恢復會話: {session_id}")
                    return session_data
            
            log.warning(f"⚠️ 會話不存在: {session_id}")
            return None
        
        except Exception as e:
            log.error(f"❌ 會話恢復失敗: {e}")
            return None
    
    async def recover_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        恢復對話歷史
        
        Args:
            session_id: 會話 ID
        
        Returns:
            對話歷史列表
        """
        try:
            # 1. 先從本地緩存查找
            if session_id in self.sessions_cache and "conversations" in self.sessions_cache[session_id]:
                log.info(f"🔄 從本地緩存恢復對話: {session_id}")
                return self.sessions_cache[session_id]["conversations"]
            
            # 2. 從 Firestore 查找（如果已連接）
            if self.firestore_client:
                conversations = await self._recover_conversations_from_firestore(session_id)
                if conversations:
                    log.info(f"🔄 從 Firestore 恢復對話: {session_id}")
                    return conversations
            
            log.warning(f"⚠️ 對話歷史不存在: {session_id}")
            return []
        
        except Exception as e:
            log.error(f"❌ 對話恢復失敗: {e}")
            return []
    
    # ============ 數據導出 ============
    
    async def export_session_json(self, session_id: str) -> Optional[str]:
        """
        導出會話為 JSON 格式
        
        Args:
            session_id: 會話 ID
        
        Returns:
            JSON 字符串，如果導出失敗則返回 None
        """
        try:
            session_data = await self.recover_session(session_id)
            if not session_data:
                return None
            
            export_data = {
                "session_id": session_id,
                "export_time": datetime.now().isoformat(),
                "format": "json",
                "version": "4.1.0",
                "data": session_data
            }
            
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            log.info(f"📤 會話已導出為 JSON: {session_id}")
            return json_str
        
        except Exception as e:
            log.error(f"❌ JSON 導出失敗: {e}")
            return None
    
    async def export_session_csv(self, session_id: str) -> Optional[str]:
        """
        導出會話為 CSV 格式
        
        Args:
            session_id: 會話 ID
        
        Returns:
            CSV 字符串，如果導出失敗則返回 None
        """
        try:
            conversations = await self.recover_conversations(session_id)
            if not conversations:
                return None
            
            # 構建 CSV 頭
            csv_lines = ["回合,說話者,消息,時間戳"]
            
            # 添加數據行
            for i, conv in enumerate(conversations, 1):
                round_num = conv.get("round_number", i)
                speaker = conv.get("speaker", "unknown")
                message = conv.get("message", "").replace(",", "，").replace("\n", " ")
                timestamp = conv.get("timestamp", "")
                
                csv_lines.append(f'{round_num},"{speaker}","{message}","{timestamp}"')
            
            csv_str = "\n".join(csv_lines)
            
            log.info(f"📤 會話已導出為 CSV: {session_id}")
            return csv_str
        
        except Exception as e:
            log.error(f"❌ CSV 導出失敗: {e}")
            return None
    
    # ============ 數據分析 ============
    
    async def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """
        分析會話數據
        
        Args:
            session_id: 會話 ID
        
        Returns:
            分析結果
        """
        try:
            session_data = await self.recover_session(session_id)
            conversations = await self.recover_conversations(session_id)
            
            if not session_data or not conversations:
                return {"error": "會話數據不完整"}
            
            analysis = {
                "session_id": session_id,
                "analysis_time": datetime.now().isoformat(),
                "summary": {
                    "total_conversations": len(conversations),
                    "total_rounds": len(conversations) // 2,
                    "duration_seconds": self._calculate_duration(conversations)
                },
                "statistics": {
                    "scammer_messages": len([c for c in conversations if c.get("speaker") == "scammer"]),
                    "victim_messages": len([c for c in conversations if c.get("speaker") == "victim"]),
                    "expert_messages": len([c for c in conversations if c.get("speaker") == "expert"]),
                    "average_message_length": self._calculate_avg_message_length(conversations)
                },
                "outcome": session_data.get("analysis", {}).get("outcome", "unknown"),
                "performance": {
                    "scammer_score": session_data.get("analysis", {}).get("scammer_performance", {}).get("overall_score", 0),
                    "expert_score": session_data.get("analysis", {}).get("expert_performance", {}).get("overall_score", 0)
                }
            }
            
            log.info(f"📊 會話分析完成: {session_id}")
            return analysis
        
        except Exception as e:
            log.error(f"❌ 會話分析失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_duration(self, conversations: List[Dict[str, Any]]) -> int:
        """計算會話時長（秒）"""
        if len(conversations) < 2:
            return 0
        
        try:
            first_time = datetime.fromisoformat(conversations[0].get("timestamp", ""))
            last_time = datetime.fromisoformat(conversations[-1].get("timestamp", ""))
            duration = (last_time - first_time).total_seconds()
            return int(duration)
        except:
            return 0
    
    def _calculate_avg_message_length(self, conversations: List[Dict[str, Any]]) -> float:
        """計算平均消息長度"""
        if not conversations:
            return 0
        
        total_length = sum(len(c.get("message", "")) for c in conversations)
        return total_length / len(conversations)
    
    # ============ 會話列表 ============
    
    async def list_sessions(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出所有會話
        
        Args:
            limit: 返回的最大會話數
            offset: 偏移量
        
        Returns:
            會話列表
        """
        try:
            sessions_list = []
            
            # 從本地緩存獲取
            cached_sessions = list(self.sessions_cache.items())[offset:offset+limit]
            
            for session_id, session_data in cached_sessions:
                sessions_list.append({
                    "session_id": session_id,
                    "created_at": session_data.get("saved_at", ""),
                    "persona_type": session_data.get("persona_type", "unknown"),
                    "scam_type": session_data.get("scam_type", "unknown"),
                    "status": session_data.get("status", "unknown"),
                    "conversation_count": len(session_data.get("conversations", []))
                })
            
            log.info(f"📋 列出會話: 共 {len(sessions_list)} 個")
            return sessions_list
        
        except Exception as e:
            log.error(f"❌ 會話列表獲取失敗: {e}")
            return []
    
    # ============ 會話刪除 ============
    
    async def delete_session(self, session_id: str) -> bool:
        """
        刪除會話
        
        Args:
            session_id: 會話 ID
        
        Returns:
            是否刪除成功
        """
        try:
            # 從本地緩存刪除
            if session_id in self.sessions_cache:
                del self.sessions_cache[session_id]
            
            # 從 Firestore 刪除（如果已連接）
            if self.firestore_client:
                await self._delete_from_firestore(session_id)
            
            log.info(f"🗑️ 會話已刪除: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 會話刪除失敗: {e}")
            return False
    
    # ============ Firestore 操作 ============
    
    async def _save_to_firestore(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存Session到 Firestore"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            
            # 保存到 sessions 集合
            db.collection('sessions').document(session_id).set({
                'session_id': session_id,
                'data': session_data,
                'saved_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }, merge=True)
            
            log.info(f"💾 Session saved to Firestore: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Firestore save failed: {e}")
            return False
    
    async def _save_conversation_to_firestore(self, conversation_data: Dict[str, Any]) -> bool:
        """保存對話到 Firestore"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            session_id = conversation_data.get('session_id')
            
            # 保存到 sessions/{session_id}/conversations 子集合
            db.collection('sessions').document(session_id).collection('conversations').add({
                **conversation_data,
                'saved_at': datetime.now().isoformat()
            })
            
            log.info(f"💬 Conversation saved to Firestore: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Firestore conversation save failed: {e}")
            return False
    
    async def _save_analysis_to_firestore(self, analysis_data: Dict[str, Any]) -> bool:
        """保存分析結果到 Firestore"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            session_id = analysis_data.get('session_id')
            
            # 保存到 sessions/{session_id}/evaluations 子集合
            db.collection('sessions').document(session_id).collection('evaluations').add({
                **analysis_data,
                'saved_at': datetime.now().isoformat()
            })
            
            log.info(f"📊 Analysis saved to Firestore: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Firestore analysis save failed: {e}")
            return False
    
    async def _recover_from_firestore(self, session_id: str) -> Optional[Dict[str, Any]]:
        """從 Firestore 恢復Session"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            
            # 從 sessions 集合獲取
            doc = db.collection('sessions').document(session_id).get()
            
            if doc.exists:
                log.info(f"🔄 Session recovered from Firestore: {session_id}")
                return doc.to_dict()
            
            log.warning(f"⚠️ Session not found in Firestore: {session_id}")
            return None
        
        except Exception as e:
            log.error(f"❌ Firestore session recovery failed: {e}")
            return None
    
    async def _recover_conversations_from_firestore(self, session_id: str) -> List[Dict[str, Any]]:
        """從 Firestore 恢復對話"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            
            # 從 sessions/{session_id}/conversations 子集合獲取
            conversations = []
            docs = db.collection('sessions').document(session_id).collection('conversations').stream()
            
            for doc in docs:
                conversations.append(doc.to_dict())
            
            log.info(f"🔄 Conversations recovered from Firestore: {session_id} ({len(conversations)} items)")
            return conversations
        
        except Exception as e:
            log.error(f"❌ Firestore conversations recovery failed: {e}")
            return []
    
    async def _delete_from_firestore(self, session_id: str) -> bool:
        """從 Firestore 刪除Session"""
        try:
            from google.cloud import firestore
            
            db = firestore.Client()
            
            # 刪除所有子集合中的文檔
            # 1. 刪除對話
            conversations = db.collection('sessions').document(session_id).collection('conversations').stream()
            for doc in conversations:
                doc.reference.delete()
            
            # 2. 刪除評估
            evaluations = db.collection('sessions').document(session_id).collection('evaluations').stream()
            for doc in evaluations:
                doc.reference.delete()
            
            # 3. 刪除Session本身
            db.collection('sessions').document(session_id).delete()
            
            log.info(f"🗑️ Session deleted from Firestore: {session_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ Firestore session deletion failed: {e}")
            return False


# 全局實例
_persistence_service = None

def get_persistence_service() -> SessionPersistenceService:
    """獲取會話持久化服務實例"""
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = SessionPersistenceService()
    return _persistence_service

