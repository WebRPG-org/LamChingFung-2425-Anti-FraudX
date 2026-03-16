"""
Firestore Service - Cloud 數據庫集成
支持 Anti-FraudX 在 Google Cloud 上的數據持久化
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app
from utils.logger import log


class FirestoreService:
    """
    Firestore 服務類
    管理 Anti-FraudX 在 Cloud Firestore 上的數據操作
    """
    
    _instance = None
    _db = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(FirestoreService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 Firestore 連接"""
        if FirestoreService._db is None:
            try:
                # 初始化 Firebase Admin SDK
                if not self._is_firebase_initialized():
                    initialize_app()
                
                # 獲取 Firestore 客戶端
                FirestoreService._db = firestore.client()
                log.info("[FIRESTORE_SERVICE] ✅ Firestore 連接成功")
            except Exception as e:
                log.error(f"[FIRESTORE_SERVICE] ❌ Firestore 初始化失敗: {str(e)}")
                raise
    
    @staticmethod
    def _is_firebase_initialized() -> bool:
        """檢查 Firebase 是否已初始化"""
        try:
            from firebase_admin import get_app
            get_app()
            return True
        except ValueError:
            return False
    
    def add_game_session(self, session_data: Dict[str, Any]) -> str:
        """
        添加遊戲會話
        
        Args:
            session_data: 會話數據
        
        Returns:
            str: 文檔 ID
        """
        try:
            session_data['created_at'] = datetime.now()
            session_data['updated_at'] = datetime.now()
            
            doc_ref = FirestoreService._db.collection('game_sessions').add(session_data)
            doc_id = doc_ref[1].id
            
            log.info(f"[FIRESTORE_SERVICE] ✅ 遊戲會話已添加: {doc_id}")
            return doc_id
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 添加遊戲會話失敗: {str(e)}")
            raise
    
    def get_game_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取遊戲會話
        
        Args:
            session_id: 會話 ID
        
        Returns:
            dict: 會話數據，如果不存在則返回 None
        """
        try:
            doc = FirestoreService._db.collection('game_sessions').document(session_id).get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                log.warning(f"[FIRESTORE_SERVICE] ⚠️ 會話不存在: {session_id}")
                return None
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 獲取遊戲會話失敗: {str(e)}")
            raise
    
    def update_game_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新遊戲會話
        
        Args:
            session_id: 會話 ID
            update_data: 更新數據
        
        Returns:
            bool: 是否成功
        """
        try:
            update_data['updated_at'] = datetime.now()
            FirestoreService._db.collection('game_sessions').document(session_id).update(update_data)
            
            log.info(f"[FIRESTORE_SERVICE] ✅ 遊戲會話已更新: {session_id}")
            return True
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 更新遊戲會話失敗: {str(e)}")
            raise
    
    def add_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """
        添加對話記錄
        
        Args:
            conversation_data: 對話數據
        
        Returns:
            str: 文檔 ID
        """
        try:
            conversation_data['created_at'] = datetime.now()
            conversation_data['updated_at'] = datetime.now()
            
            doc_ref = FirestoreService._db.collection('conversations').add(conversation_data)
            doc_id = doc_ref[1].id
            
            log.info(f"[FIRESTORE_SERVICE] ✅ 對話已添加: {doc_id}")
            return doc_id
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 添加對話失敗: {str(e)}")
            raise
    
    def get_conversations(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        獲取會話的所有對話
        
        Args:
            session_id: 會話 ID
            limit: 限制數量
        
        Returns:
            list: 對話列表
        """
        try:
            docs = FirestoreService._db.collection('conversations') \
                .where('session_id', '==', session_id) \
                .order_by('created_at', direction=firestore.Query.DESCENDING) \
                .limit(limit) \
                .stream()
            
            conversations = [doc.to_dict() for doc in docs]
            log.info(f"[FIRESTORE_SERVICE] ✅ 獲取 {len(conversations)} 條對話")
            return conversations
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 獲取對話失敗: {str(e)}")
            raise
    
    def add_score_record(self, score_data: Dict[str, Any]) -> str:
        """
        添加評分記錄
        
        Args:
            score_data: 評分數據
        
        Returns:
            str: 文檔 ID
        """
        try:
            score_data['created_at'] = datetime.now()
            
            doc_ref = FirestoreService._db.collection('scores').add(score_data)
            doc_id = doc_ref[1].id
            
            log.info(f"[FIRESTORE_SERVICE] ✅ 評分記錄已添加: {doc_id}")
            return doc_id
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 添加評分記錄失敗: {str(e)}")
            raise
    
    def get_leaderboard(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        獲取排行榜
        
        Args:
            limit: 限制數量
        
        Returns:
            list: 排行榜數據
        """
        try:
            docs = FirestoreService._db.collection('scores') \
                .order_by('score', direction=firestore.Query.DESCENDING) \
                .limit(limit) \
                .stream()
            
            leaderboard = [doc.to_dict() for doc in docs]
            log.info(f"[FIRESTORE_SERVICE] ✅ 獲取排行榜 {len(leaderboard)} 條記錄")
            return leaderboard
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 獲取排行榜失敗: {str(e)}")
            raise
    
    def add_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        添加用戶資料
        
        Args:
            user_id: 用戶 ID
            profile_data: 資料數據
        
        Returns:
            bool: 是否成功
        """
        try:
            profile_data['created_at'] = datetime.now()
            profile_data['updated_at'] = datetime.now()
            
            FirestoreService._db.collection('users').document(user_id).set(profile_data)
            log.info(f"[FIRESTORE_SERVICE] ✅ 用戶資料已添加: {user_id}")
            return True
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 添加用戶資料失敗: {str(e)}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取用戶資料
        
        Args:
            user_id: 用戶 ID
        
        Returns:
            dict: 用戶資料，如果不存在則返回 None
        """
        try:
            doc = FirestoreService._db.collection('users').document(user_id).get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 獲取用戶資料失敗: {str(e)}")
            raise
    
    def batch_write(self, operations: List[Dict[str, Any]]) -> bool:
        """
        批量寫入操作
        
        Args:
            operations: 操作列表，每個操作包含 'type', 'collection', 'document', 'data'
        
        Returns:
            bool: 是否成功
        """
        try:
            batch = FirestoreService._db.batch()
            
            for op in operations:
                op_type = op.get('type')  # 'set', 'update', 'delete'
                collection = op.get('collection')
                document = op.get('document')
                data = op.get('data', {})
                
                doc_ref = FirestoreService._db.collection(collection).document(document)
                
                if op_type == 'set':
                    batch.set(doc_ref, data)
                elif op_type == 'update':
                    batch.update(doc_ref, data)
                elif op_type == 'delete':
                    batch.delete(doc_ref)
            
            batch.commit()
            log.info(f"[FIRESTORE_SERVICE] ✅ 批量操作完成: {len(operations)} 個操作")
            return True
        except Exception as e:
            log.error(f"[FIRESTORE_SERVICE] ❌ 批量操作失敗: {str(e)}")
            raise
    
    def get_db(self):
        """獲取 Firestore 客戶端"""
        return FirestoreService._db

