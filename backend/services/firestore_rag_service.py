"""
Firestore RAG Service - 詐騙案例知識庫
存儲和檢索詐騙案例數據用於 RAG（檢索增強生成）
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from services.firestore_service import FirestoreService
except ImportError:
    FirestoreService = None

try:
    from utils.logger import log
except ImportError:
    import logging
    log = logging.getLogger(__name__)


class FirestoreRAGService:
    """
    Firestore RAG 服務類
    管理詐騙案例數據和對話記錄的存儲與檢索
    """
    
    def __init__(self):
        """初始化 Firestore RAG 服務"""
        try:
            if FirestoreService is None:
                log.warning("[FIRESTORE_RAG] ⚠️ FirestoreService 不可用")
                self.firestore_service = None
                self.db = None
                return
            
            self.firestore_service = FirestoreService()
            self.db = self.firestore_service.get_db()
            log.info("[FIRESTORE_RAG] ✅ Firestore RAG 服務初始化完成")
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 初始化失敗: {str(e)}")
            self.firestore_service = None
            self.db = None
    
    # ========== 詐騙案例管理 ==========
    
    def add_scam_case(self, scam_data: Dict[str, Any]) -> str:
        """
        添加詐騙案例
        
        Args:
            scam_data: 詐騙案例數據
                - scam_type: 詐騙類型
                - description: 描述
                - tactics: 詐騙手法
                - warning_signs: 警告信號
                - prevention_tips: 防範建議
                - real_case: 真實案例
        
        Returns:
            str: 案例 ID
        """
        try:
            scam_data['created_at'] = datetime.now()
            scam_data['updated_at'] = datetime.now()
            scam_data['views'] = 0
            scam_data['helpful_count'] = 0
            
            doc_ref = self.db.collection('scam_cases').add(scam_data)
            case_id = doc_ref[1].id
            
            log.info(f"[FIRESTORE_RAG] ✅ 詐騙案例已添加: {case_id} ({scam_data.get('scam_type')})")
            return case_id
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 添加詐騙案例失敗: {str(e)}")
            raise
    
    def get_scam_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取詐騙案例
        
        Args:
            case_id: 案例 ID
        
        Returns:
            dict: 案例數據
        """
        try:
            doc = self.db.collection('scam_cases').document(case_id).get()
            
            if doc.exists:
                # 增加瀏覽次數
                self.db.collection('scam_cases').document(case_id).update({
                    'views': doc.get('views', 0) + 1,
                    'updated_at': datetime.now()
                })
                return doc.to_dict()
            else:
                log.warning(f"[FIRESTORE_RAG] ⚠️ 案例不存在: {case_id}")
                return None
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取詐騙案例失敗: {str(e)}")
            raise
    
    def search_scam_cases(self, scam_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索詐騙案例
        
        Args:
            scam_type: 詐騙類型（可選）
            limit: 限制數量
        
        Returns:
            list: 案例列表
        """
        try:
            query = self.db.collection('scam_cases')
            
            if scam_type:
                query = query.where('scam_type', '==', scam_type)
            
            docs = query.order_by('views', direction='DESCENDING').limit(limit).stream()
            cases = [doc.to_dict() for doc in docs]
            
            log.info(f"[FIRESTORE_RAG] ✅ 搜索到 {len(cases)} 個詐騙案例")
            return cases
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 搜索詐騙案例失敗: {str(e)}")
            raise
    
    def get_all_scam_types(self) -> List[str]:
        """
        獲取所有詐騙類型
        
        Returns:
            list: 詐騙類型列表
        """
        try:
            docs = self.db.collection('scam_cases').stream()
            scam_types = set()
            
            for doc in docs:
                scam_type = doc.get('scam_type')
                if scam_type:
                    scam_types.add(scam_type)
            
            return list(scam_types)
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取詐騙類型失敗: {str(e)}")
            raise
    
    # ========== 對話記錄管理 ==========
    
    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """
        保存對話記錄
        
        Args:
            conversation_data: 對話數據
                - session_id: 會話 ID
                - user_id: 用戶 ID（可選）
                - messages: 消息列表
                - scam_type: 詐騙類型
                - player_role: 玩家角色
                - game_mode: 遊戲模式
                - save_to_cloud: 是否保存到雲端
        
        Returns:
            str: 對話記錄 ID
        """
        try:
            # 檢查是否需要保存到雲端
            if not conversation_data.get('save_to_cloud', True):
                log.info("[FIRESTORE_RAG] ⏭️ 對話記錄不保存到雲端（用戶選擇）")
                return None
            
            conversation_data['created_at'] = datetime.now()
            conversation_data['updated_at'] = datetime.now()
            conversation_data['message_count'] = len(conversation_data.get('messages', []))
            
            doc_ref = self.db.collection('conversations').add(conversation_data)
            conv_id = doc_ref[1].id
            
            log.info(f"[FIRESTORE_RAG] ✅ 對話記錄已保存: {conv_id}")
            return conv_id
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 保存對話記錄失敗: {str(e)}")
            raise
    
    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取對話記錄
        
        Args:
            conv_id: 對話記錄 ID
        
        Returns:
            dict: 對話數據
        """
        try:
            doc = self.db.collection('conversations').document(conv_id).get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                log.warning(f"[FIRESTORE_RAG] ⚠️ 對話記錄不存在: {conv_id}")
                return None
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取對話記錄失敗: {str(e)}")
            raise
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取用戶的所有對話記錄
        
        Args:
            user_id: 用戶 ID
            limit: 限制數量
        
        Returns:
            list: 對話記錄列表
        """
        try:
            docs = self.db.collection('conversations') \
                .where('user_id', '==', user_id) \
                .order_by('created_at', direction='DESCENDING') \
                .limit(limit) \
                .stream()
            
            conversations = [doc.to_dict() for doc in docs]
            log.info(f"[FIRESTORE_RAG] ✅ 獲取用戶 {user_id} 的 {len(conversations)} 條對話記錄")
            return conversations
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取用戶對話記錄失敗: {str(e)}")
            raise
    
    def get_session_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        獲取會話的所有對話記錄
        
        Args:
            session_id: 會話 ID
        
        Returns:
            list: 對話記錄列表
        """
        try:
            docs = self.db.collection('conversations') \
                .where('session_id', '==', session_id) \
                .order_by('created_at', direction='ASCENDING') \
                .stream()
            
            conversations = [doc.to_dict() for doc in docs]
            log.info(f"[FIRESTORE_RAG] ✅ 獲取會話 {session_id} 的 {len(conversations)} 條對話記錄")
            return conversations
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取會話對話記錄失敗: {str(e)}")
            raise
    
    # ========== 統計和分析 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取統計信息
        
        Returns:
            dict: 統計數據
        """
        try:
            # 詐騙案例數量
            scam_cases_count = len(list(self.db.collection('scam_cases').stream()))
            
            # 對話記錄數量
            conversations_count = len(list(self.db.collection('conversations').stream()))
            
            # 用戶數量
            users_count = len(list(self.db.collection('users').stream()))
            
            stats = {
                'scam_cases_count': scam_cases_count,
                'conversations_count': conversations_count,
                'users_count': users_count,
                'timestamp': datetime.now().isoformat()
            }
            
            log.info(f"[FIRESTORE_RAG] ✅ 統計信息: {stats}")
            return stats
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取統計信息失敗: {str(e)}")
            raise
    
    def get_popular_scam_types(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        獲取最受歡迎的詐騙類型
        
        Args:
            limit: 限制數量
        
        Returns:
            list: 詐騙類型及其統計
        """
        try:
            docs = self.db.collection('scam_cases') \
                .order_by('views', direction='DESCENDING') \
                .limit(limit) \
                .stream()
            
            popular = [doc.to_dict() for doc in docs]
            log.info(f"[FIRESTORE_RAG] ✅ 獲取 {len(popular)} 個最受歡迎的詐騙類型")
            return popular
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 獲取最受歡迎的詐騙類型失敗: {str(e)}")
            raise
    
    # ========== 批量操作 ==========
    
    def batch_add_scam_cases(self, cases: List[Dict[str, Any]]) -> List[str]:
        """
        批量添加詐騙案例
        
        Args:
            cases: 案例列表
        
        Returns:
            list: 案例 ID 列表
        """
        try:
            case_ids = []
            batch = self.db.batch()
            
            for case in cases:
                case['created_at'] = datetime.now()
                case['updated_at'] = datetime.now()
                case['views'] = 0
                case['helpful_count'] = 0
                
                doc_ref = self.db.collection('scam_cases').document()
                batch.set(doc_ref, case)
                case_ids.append(doc_ref.id)
            
            batch.commit()
            log.info(f"[FIRESTORE_RAG] ✅ 批量添加 {len(case_ids)} 個詐騙案例")
            return case_ids
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 批量添加詐騙案例失敗: {str(e)}")
            raise
    
    def delete_old_conversations(self, days: int = 30) -> int:
        """
        刪除舊的對話記錄（超過指定天數）
        
        Args:
            days: 天數
        
        Returns:
            int: 刪除的記錄數
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            docs = self.db.collection('conversations') \
                .where('created_at', '<', cutoff_date) \
                .stream()
            
            batch = self.db.batch()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
            
            batch.commit()
            log.info(f"[FIRESTORE_RAG] ✅ 刪除 {count} 條超過 {days} 天的對話記錄")
            return count
        except Exception as e:
            log.error(f"[FIRESTORE_RAG] ❌ 刪除舊對話記錄失敗: {str(e)}")
            raise


# 創建全局實例
firestore_rag_service = FirestoreRAGService()

