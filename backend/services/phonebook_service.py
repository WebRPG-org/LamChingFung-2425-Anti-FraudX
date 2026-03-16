"""
電話簿服務 - 官方機構聯絡資訊數據庫
供防詐專家查詢官方電話號碼，幫助受害者核實身份
"""

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


class PhonebookService:
    """
    電話簿服務類
    管理官方機構的聯絡資訊
    """
    
    # 預設的官方機構電話簿
    DEFAULT_PHONEBOOK = {
        "銀行": [
            {"name": "滙豐銀行", "phone": "2288 8822", "type": "客服"},
            {"name": "中銀香港", "phone": "3988 8888", "type": "客服"},
            {"name": "恒生銀行", "phone": "2822 8822", "type": "客服"},
            {"name": "渣打銀行", "phone": "2886 8686", "type": "客服"},
            {"name": "東亞銀行", "phone": "2211 1111", "type": "客服"},
        ],
        "政府部門": [
            {"name": "香港警務處", "phone": "2860 5012", "type": "反詐騙組"},
            {"name": "廉政公署", "phone": "2852 3633", "type": "舉報熱線"},
            {"name": "入境事務處", "phone": "2824 6111", "type": "查詢"},
            {"name": "稅務局", "phone": "2594 3000", "type": "查詢"},
            {"name": "社會福利署", "phone": "2343 2255", "type": "查詢"},
        ],
        "防騙熱線": [
            {"name": "防騙易熱線", "phone": "18222", "type": "24小時防騙"},
            {"name": "警務處反詐騙協調中心", "phone": "2860 5012", "type": "報案"},
            {"name": "消費者委員會", "phone": "2929 8799", "type": "投訴"},
        ],
        "電訊公司": [
            {"name": "香港電訊", "phone": "2888 0008", "type": "客服"},
            {"name": "新世界電訊", "phone": "2888 1888", "type": "客服"},
            {"name": "和記電訊", "phone": "2888 0008", "type": "客服"},
            {"name": "中國移動", "phone": "1860", "type": "客服"},
            {"name": "SmarTone", "phone": "2988 8888", "type": "客服"},
        ],
        "快遞公司": [
            {"name": "DHL", "phone": "2400 3333", "type": "查詢"},
            {"name": "FedEx", "phone": "2730 3333", "type": "查詢"},
            {"name": "順豐速運", "phone": "2988 8888", "type": "查詢"},
            {"name": "EMS", "phone": "2921 8888", "type": "查詢"},
        ],
    }
    
    def __init__(self):
        """初始化電話簿服務"""
        try:
            if FirestoreService is None:
                log.warning("[PHONEBOOK] ⚠️ FirestoreService 不可用")
                self.firestore_service = None
                self.db = None
                return
            
            self.firestore_service = FirestoreService()
            self.db = self.firestore_service.get_db()
            
            # 初始化預設電話簿
            self._init_default_phonebook()
            
            log.info("[PHONEBOOK] ✅ 電話簿服務初始化完成")
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 初始化失敗: {str(e)}")
            self.firestore_service = None
            self.db = None
    
    def _init_default_phonebook(self):
        """初始化預設電話簿到 Firestore"""
        try:
            # 檢查是否已存在
            doc = self.db.collection('phonebook_metadata').document('initialized').get()
            if doc.exists:
                log.info("[PHONEBOOK] ℹ️ 電話簿已初始化，跳過")
                return
            
            # 添加預設電話簿
            for category, entries in self.DEFAULT_PHONEBOOK.items():
                for entry in entries:
                    entry['category'] = category
                    entry['created_at'] = datetime.now()
                    entry['updated_at'] = datetime.now()
                    entry['verified'] = True  # 預設為已驗證
                    
                    self.db.collection('phonebook').add(entry)
            
            # 標記為已初始化
            self.db.collection('phonebook_metadata').document('initialized').set({
                'initialized_at': datetime.now(),
                'total_entries': sum(len(entries) for entries in self.DEFAULT_PHONEBOOK.values())
            })
            
            log.info("[PHONEBOOK] ✅ 預設電話簿已初始化")
        except Exception as e:
            log.warning(f"[PHONEBOOK] ⚠️ 初始化預設電話簿失敗: {str(e)}")
    
    def search_by_organization(self, org_name: str) -> List[Dict[str, Any]]:
        """
        按機構名稱搜索電話號碼
        
        Args:
            org_name: 機構名稱
        
        Returns:
            list: 匹配的電話簿條目
        """
        try:
            docs = self.db.collection('phonebook') \
                .where('name', '==', org_name) \
                .where('verified', '==', True) \
                .stream()
            
            results = [doc.to_dict() for doc in docs]
            log.info(f"[PHONEBOOK] ✅ 搜索 '{org_name}' 找到 {len(results)} 個結果")
            return results
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 搜索失敗: {str(e)}")
            return []
    
    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        按類別搜索電話號碼
        
        Args:
            category: 類別（銀行、政府部門、防騙熱線等）
        
        Returns:
            list: 該類別的所有電話簿條目
        """
        try:
            docs = self.db.collection('phonebook') \
                .where('category', '==', category) \
                .where('verified', '==', True) \
                .stream()
            
            results = [doc.to_dict() for doc in docs]
            log.info(f"[PHONEBOOK] ✅ 搜索類別 '{category}' 找到 {len(results)} 個結果")
            return results
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 搜索失敗: {str(e)}")
            return []
    
    def get_official_phone(self, org_name: str) -> Optional[str]:
        """
        獲取官方電話號碼
        
        Args:
            org_name: 機構名稱
        
        Returns:
            str: 官方電話號碼，如果不存在則返回 None
        """
        try:
            results = self.search_by_organization(org_name)
            if results:
                return results[0]['phone']
            return None
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 獲取電話號碼失敗: {str(e)}")
            return None
    
    def verify_phone_number(self, org_name: str, phone: str) -> bool:
        """
        驗證電話號碼是否為官方號碼
        
        Args:
            org_name: 機構名稱
            phone: 電話號碼
        
        Returns:
            bool: 是否為官方號碼
        """
        try:
            results = self.search_by_organization(org_name)
            for result in results:
                if result['phone'] == phone:
                    log.info(f"[PHONEBOOK] ✅ 驗證成功: {org_name} {phone}")
                    return True
            
            log.warning(f"[PHONEBOOK] ⚠️ 驗證失敗: {org_name} {phone} 不是官方號碼")
            return False
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 驗證失敗: {str(e)}")
            return False
    
    def get_all_categories(self) -> List[str]:
        """
        獲取所有類別
        
        Returns:
            list: 類別列表
        """
        try:
            docs = self.db.collection('phonebook').stream()
            categories = set()
            
            for doc in docs:
                category = doc.get('category')
                if category:
                    categories.add(category)
            
            return sorted(list(categories))
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 獲取類別失敗: {str(e)}")
            return []
    
    def add_entry(self, entry: Dict[str, Any]) -> str:
        """
        添加新的電話簿條目
        
        Args:
            entry: 條目數據
                - name: 機構名稱
                - phone: 電話號碼
                - category: 類別
                - type: 類型（客服、查詢等）
                - verified: 是否已驗證
        
        Returns:
            str: 條目 ID
        """
        try:
            entry['created_at'] = datetime.now()
            entry['updated_at'] = datetime.now()
            entry['verified'] = entry.get('verified', False)
            
            doc_ref = self.db.collection('phonebook').add(entry)
            entry_id = doc_ref[1].id
            
            log.info(f"[PHONEBOOK] ✅ 添加電話簿條目: {entry_id}")
            return entry_id
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 添加條目失敗: {str(e)}")
            raise
    
    def get_expert_reference(self, suspected_org: str) -> str:
        """
        為專家生成參考資訊
        
        Args:
            suspected_org: 懷疑的機構名稱
        
        Returns:
            str: 格式化的參考資訊
        """
        try:
            # 搜索官方號碼
            official_phone = self.get_official_phone(suspected_org)
            
            if official_phone:
                return f"""
🔍 **官方聯絡資訊驗證**：
- 機構：{suspected_org}
- 官方電話：{official_phone}
- 建議：請撥打上述官方電話核實身份

⚠️ **警告**：如果對方提供的電話號碼與上述不符，很可能是詐騙！
"""
            else:
                return f"""
⚠️ **無法驗證**：
- 機構：{suspected_org}
- 建議：請直接撥打 18222（防騙易熱線）或 2860 5012（警務處反詐騙組）查詢

🛡️ **安全建議**：
- 不要相信對方提供的電話號碼
- 自己查詢官方電話號碼
- 如有疑問，立即報警
"""
        except Exception as e:
            log.error(f"[PHONEBOOK] ❌ 生成參考資訊失敗: {str(e)}")
            return "無法獲取官方聯絡資訊，請撥打 18222 防騙易熱線。"


# 創建全局實例
phonebook_service = PhonebookService()

