"""
Cloud Storage Service - Google Cloud Storage 集成
支持 Anti-FraudX 在 Cloud 上的文件存儲
"""

import os
from typing import Optional, BinaryIO
from io import BytesIO
from google.cloud import storage
from utils.logger import log


class CloudStorageService:
    """
    Cloud Storage 服務類
    管理 Anti-FraudX 在 Google Cloud Storage 上的文件操作
    """
    
    _instance = None
    _client = None
    _bucket = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(CloudStorageService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, bucket_name: Optional[str] = None):
        """
        初始化 Cloud Storage 連接
        
        Args:
            bucket_name: 桶名稱（默認從環境變量讀取）
        """
        if CloudStorageService._client is None:
            try:
                # 初始化 Storage 客戶端
                CloudStorageService._client = storage.Client()
                
                # 獲取桶
                bucket_name = bucket_name or os.getenv("CLOUD_STORAGE_BUCKET", "anti-fraudx-storage")
                CloudStorageService._bucket = CloudStorageService._client.bucket(bucket_name)
                
                log.info(
                    f"[CLOUD_STORAGE_SERVICE] ✅ Cloud Storage 連接成功 - "
                    f"桶: {bucket_name}"
                )
            except Exception as e:
                log.error(f"[CLOUD_STORAGE_SERVICE] ❌ Cloud Storage 初始化失敗: {str(e)}")
                raise
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        上傳文件到 Cloud Storage
        
        Args:
            local_path: 本地文件路徑
            remote_path: 遠程文件路徑
            content_type: 文件類型
        
        Returns:
            bool: 是否成功
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            blob.upload_from_filename(local_path, content_type=content_type)
            
            log.info(
                f"[CLOUD_STORAGE_SERVICE] ✅ 文件已上傳 - "
                f"本地: {local_path}, 遠程: {remote_path}"
            )
            return True
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 上傳文件失敗: {str(e)}")
            raise
    
    def upload_bytes(
        self,
        data: bytes,
        remote_path: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        上傳字節數據到 Cloud Storage
        
        Args:
            data: 字節數據
            remote_path: 遠程文件路徑
            content_type: 文件類型
        
        Returns:
            bool: 是否成功
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            blob.upload_from_string(data, content_type=content_type)
            
            log.info(
                f"[CLOUD_STORAGE_SERVICE] ✅ 字節數據已上傳 - "
                f"遠程: {remote_path}, 大小: {len(data)} 字節"
            )
            return True
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 上傳字節數據失敗: {str(e)}")
            raise
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        從 Cloud Storage 下載文件
        
        Args:
            remote_path: 遠程文件路徑
            local_path: 本地文件路徑
        
        Returns:
            bool: 是否成功
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            blob.download_to_filename(local_path)
            
            log.info(
                f"[CLOUD_STORAGE_SERVICE] ✅ 文件已下載 - "
                f"遠程: {remote_path}, 本地: {local_path}"
            )
            return True
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 下載文件失敗: {str(e)}")
            raise
    
    def download_bytes(self, remote_path: str) -> Optional[bytes]:
        """
        從 Cloud Storage 下載文件為字節
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            bytes: 文件內容，如果失敗則返回 None
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            data = blob.download_as_bytes()
            
            log.info(
                f"[CLOUD_STORAGE_SERVICE] ✅ 字節數據已下載 - "
                f"遠程: {remote_path}, 大小: {len(data)} 字節"
            )
            return data
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 下載字節數據失敗: {str(e)}")
            return None
    
    def delete_file(self, remote_path: str) -> bool:
        """
        刪除 Cloud Storage 中的文件
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            bool: 是否成功
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            blob.delete()
            
            log.info(f"[CLOUD_STORAGE_SERVICE] ✅ 文件已刪除 - 遠程: {remote_path}")
            return True
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 刪除文件失敗: {str(e)}")
            raise
    
    def list_files(self, prefix: str = "", max_results: int = 100) -> list:
        """
        列出 Cloud Storage 中的文件
        
        Args:
            prefix: 文件前綴
            max_results: 最大結果數
        
        Returns:
            list: 文件列表
        """
        try:
            blobs = CloudStorageService._client.list_blobs(
                CloudStorageService._bucket.name,
                prefix=prefix,
                max_results=max_results
            )
            
            files = [blob.name for blob in blobs]
            log.info(
                f"[CLOUD_STORAGE_SERVICE] ✅ 列出文件成功 - "
                f"前綴: {prefix}, 數量: {len(files)}"
            )
            return files
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 列出文件失敗: {str(e)}")
            raise
    
    def get_file_url(self, remote_path: str, expiration_hours: int = 24) -> str:
        """
        獲取文件的簽名 URL
        
        Args:
            remote_path: 遠程文件路徑
            expiration_hours: 過期時間（小時）
        
        Returns:
            str: 簽名 URL
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=__import__('datetime').timedelta(hours=expiration_hours),
                method="GET"
            )
            
            log.info(
                f"[CLOUD_STORAGE_SERVICE] ✅ 簽名 URL 已生成 - "
                f"遠程: {remote_path}, 過期: {expiration_hours} 小時"
            )
            return url
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 生成簽名 URL 失敗: {str(e)}")
            raise
    
    def file_exists(self, remote_path: str) -> bool:
        """
        檢查文件是否存在
        
        Args:
            remote_path: 遠程文件路徑
        
        Returns:
            bool: 是否存在
        """
        try:
            blob = CloudStorageService._bucket.blob(remote_path)
            return blob.exists()
        except Exception as e:
            log.error(f"[CLOUD_STORAGE_SERVICE] ❌ 檢查文件失敗: {str(e)}")
            return False
    
    def get_bucket(self):
        """獲取 Storage 桶"""
        return CloudStorageService._bucket

