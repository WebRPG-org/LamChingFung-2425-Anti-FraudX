"""
Local Storage Service - 本地文件存儲
支持 Anti-FraudX 本地部署的文件操作
"""

import os
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path
from utils.logger import log


class LocalStorageService:
    """
    本地存儲服務類
    管理 Anti-FraudX 本地部署的文件操作
    """
    
    _instance = None
    _base_path = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(LocalStorageService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化本地存儲
        
        Args:
            base_path: 基礎路徑（默認從環境變量讀取）
        """
        if LocalStorageService._base_path is None:
            LocalStorageService._base_path = base_path or os.getenv(
                "STORAGE_PATH",
                "./backend/uploads"
            )
            
            # 創建基礎目錄
            Path(LocalStorageService._base_path).mkdir(parents=True, exist_ok=True)
            
            log.info(
                f"[LOCAL_STORAGE_SERVICE] ✅ 本地存儲初始化成功 - "
                f"路徑: {LocalStorageService._base_path}"
            )
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str
    ) -> bool:
        """
        上傳文件到本地存儲
        
        Args:
            local_path: 本地文件路徑
            remote_path: 遠程文件路徑（相對於基礎路徑）
        
        Returns:
            bool: 是否成功
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            
            # 創建目錄
            os.makedirs(os.path.dirname(full_remote_path), exist_ok=True)
            
            # 複製文件
            shutil.copy2(local_path, full_remote_path)
            
            log.info(
                f"[LOCAL_STORAGE_SERVICE] ✅ 文件已上傳 - "
                f"本地: {local_path}, 遠程: {remote_path}"
            )
            return True
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 上傳文件失敗: {str(e)}")
            raise
    
    def upload_bytes(
        self,
        data: bytes,
        remote_path: str
    ) -> bool:
        """
        上傳字節數據到本地存儲
        
        Args:
            data: 字節數據
            remote_path: 遠程文件路徑
        
        Returns:
            bool: 是否成功
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            
            # 創建目錄
            os.makedirs(os.path.dirname(full_remote_path), exist_ok=True)
            
            # 寫入文件
            with open(full_remote_path, 'wb') as f:
                f.write(data)
            
            log.info(
                f"[LOCAL_STORAGE_SERVICE] ✅ 字節數據已上傳 - "
                f"遠程: {remote_path}, 大小: {len(data)} 字節"
            )
            return True
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 上傳字節數據失敗: {str(e)}")
            raise
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        從本地存儲下載文件
        
        Args:
            remote_path: 遠程文件路徑
            local_path: 本地文件路徑
        
        Returns:
            bool: 是否成功
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            
            # 複製文件
            shutil.copy2(full_remote_path, local_path)
            
            log.info(
                f"[LOCAL_STORAGE_SERVICE] ✅ 文件已下載 - "
                f"遠程: {remote_path}, 本地: {local_path}"
            )
            return True
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 下載文件失敗: {str(e)}")
            raise
    
    def download_bytes(self, remote_path: str) -> Optional[bytes]:
        """
        從本地存儲下載文件為字節
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            bytes: 文件內容，如果失敗則返回 None
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            
            with open(full_remote_path, 'rb') as f:
                data = f.read()
            
            log.info(
                f"[LOCAL_STORAGE_SERVICE] ✅ 字節數據已下載 - "
                f"遠程: {remote_path}, 大小: {len(data)} 字節"
            )
            return data
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 下載字節數據失敗: {str(e)}")
            return None
    
    def delete_file(self, remote_path: str) -> bool:
        """
        刪除本地存儲中的文件
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            bool: 是否成功
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            
            if os.path.exists(full_remote_path):
                os.remove(full_remote_path)
                log.info(f"[LOCAL_STORAGE_SERVICE] ✅ 文件已刪除 - 遠程: {remote_path}")
            else:
                log.warning(f"[LOCAL_STORAGE_SERVICE] ⚠️ 文件不存在 - 遠程: {remote_path}")
            
            return True
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 刪除文件失敗: {str(e)}")
            raise
    
    def list_files(self, prefix: str = "", max_results: int = 100) -> List[str]:
        """
        列出本地存儲中的文件
        
        Args:
            prefix: 文件前綴
            max_results: 最大結果數
        
        Returns:
            list: 文件列表
        """
        try:
            full_prefix_path = os.path.join(LocalStorageService._base_path, prefix)
            
            files = []
            count = 0
            
            for root, dirs, filenames in os.walk(full_prefix_path):
                for filename in filenames:
                    if count >= max_results:
                        break
                    
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, LocalStorageService._base_path)
                    files.append(relative_path)
                    count += 1
            
            log.info(
                f"[LOCAL_STORAGE_SERVICE] ✅ 列出文件成功 - "
                f"前綴: {prefix}, 數量: {len(files)}"
            )
            return files
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 列出文件失敗: {str(e)}")
            raise
    
    def get_file_url(self, remote_path: str) -> str:
        """
        獲取文件的本地 URL
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            str: 本地文件路徑
        """
        full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
        log.info(f"[LOCAL_STORAGE_SERVICE] ✅ 本地文件路徑: {full_remote_path}")
        return full_remote_path
    
    def file_exists(self, remote_path: str) -> bool:
        """
        檢查文件是否存在
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            bool: 是否存在
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            return os.path.exists(full_remote_path)
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 檢查文件失敗: {str(e)}")
            return False
    
    def get_file_size(self, remote_path: str) -> int:
        """
        獲取文件大小
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            int: 文件大小（字節）
        """
        try:
            full_remote_path = os.path.join(LocalStorageService._base_path, remote_path)
            return os.path.getsize(full_remote_path)
        except Exception as e:
            log.error(f"[LOCAL_STORAGE_SERVICE] ❌ 獲取文件大小失敗: {str(e)}")
            return 0
    
    def get_base_path(self) -> str:
        """獲取基礎路徑"""
        return LocalStorageService._base_path

