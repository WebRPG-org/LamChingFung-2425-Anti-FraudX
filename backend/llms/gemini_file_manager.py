"""
Gemini File API 管理器
用於上傳和管理知識庫文件到 Google 臨時伺服器
"""

import os
import time
from typing import List, Dict, Optional
from google import genai
from google.genai import types
from pathlib import Path


class GeminiFileManager:
    """
    Gemini File API 管理器
    
    功能：
    1. 上傳文件到 Google 臨時伺服器（Free Tier 保存 2 天）
    2. 管理已上傳的文件
    3. 檢查文件狀態
    4. 刪除過期文件
    """
    
    def __init__(self, api_key: str):
        """
        初始化文件管理器
        
        Args:
            api_key: Gemini API Key
        """
        self._client = genai.Client(api_key=api_key)
        self.uploaded_files: Dict[str, types.File] = {}
        print("[FILE_MANAGER] Gemini File Manager initialized")
    
    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> types.File:
        """
        上傳文件到 Google 臨時伺服器
        
        Args:
            file_path: 本地文件路徑
            display_name: 顯示名稱（可選）
        
        Returns:
            types.File: 上傳後的文件對象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        print(f"[FILE_MANAGER] Uploading file: {file_path} ({file_size} bytes)")
        
        # 根據文件擴展名確定 MIME type
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_type_map = {
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.html': 'text/html',
            '.xml': 'application/xml'
        }
        mime_type = mime_type_map.get(file_ext, 'text/plain')
        
        # 上傳文件
        with open(file_path, 'rb') as f:
            uploaded_file = self._client.files.upload(
                file=f,
                config=types.UploadFileConfig(
                    mime_type=mime_type,
                    display_name=display_name or os.path.basename(file_path)
                )
            )
        
        # 等待文件處理完成
        while uploaded_file.state == types.FileState.PROCESSING:
            print(f"[FILE_MANAGER] Processing... {uploaded_file.name}")
            time.sleep(2)
            uploaded_file = self._client.files.get(name=uploaded_file.name)
        
        if uploaded_file.state == types.FileState.FAILED:
            raise Exception(f"File upload failed: {uploaded_file.name}")
        
        # 保存到管理器
        self.uploaded_files[file_path] = uploaded_file
        
        print(
            f"[FILE_MANAGER] Upload successful: {uploaded_file.name}\n"
            f"  - URI: {uploaded_file.uri}\n"
            f"  - Size: {uploaded_file.size_bytes} bytes\n"
            f"  - MIME: {uploaded_file.mime_type}\n"
            f"  - Expires: {uploaded_file.expiration_time}"
        )
        
        return uploaded_file
    
    def get_file(self, file_path: str) -> Optional[types.File]:
        """
        獲取已上傳的文件
        
        Args:
            file_path: 本地文件路徑
        
        Returns:
            types.File: 文件對象，如果不存在則返回 None
        """
        return self.uploaded_files.get(file_path)
    
    def list_files(self) -> List[types.File]:
        """
        列出所有已上傳的文件
        
        Returns:
            List[types.File]: 文件列表
        """
        try:
            files = list(self._client.files.list())
            print(f"[FILE_MANAGER] Found {len(files)} uploaded files")
            for f in files:
                print(f"  - {f.display_name} ({f.name})")
            return files
        except Exception as e:
            print(f"[FILE_MANAGER] Error listing files: {e}")
            return []
    
    def delete_file(self, file_name: str) -> bool:
        """
        刪除已上傳的文件
        
        Args:
            file_name: 文件名稱（可以是本地路徑或 Gemini 文件名）
        
        Returns:
            bool: 是否成功刪除
        """
        # 如果是本地路徑，先獲取對應的上傳文件
        if file_name in self.uploaded_files:
            uploaded_file = self.uploaded_files[file_name]
            file_name = uploaded_file.name
        
        try:
            self._client.files.delete(name=file_name)
            # 從管理器中移除
            for path, f in list(self.uploaded_files.items()):
                if f.name == file_name:
                    del self.uploaded_files[path]
            print(f"[FILE_MANAGER] File deleted: {file_name}")
            return True
        except Exception as e:
            print(f"[FILE_MANAGER] Delete failed: {e}")
            return False
    
    def delete_all_files(self):
        """刪除所有已上傳的文件"""
        files = self.list_files()
        for f in files:
            self.delete_file(f.name)
    
    def upload_knowledge_base(
        self, 
        base_dir: str = ".", 
        upload_scraped_alerts: bool = False,
        data_size: str = "ultra_lite"
    ) -> Dict[str, types.File]:
        """
        上傳知識庫文件
        
        Args:
            base_dir: 基礎目錄（默認為當前目錄）
            upload_scraped_alerts: 是否上傳 scraped_alerts（免費版建議 False）
            data_size: 數據集大小 - "ultra_lite" (5案例), "lite" (30案例), "full" (281案例)
        
        Returns:
            Dict[str, types.File]: 文件名 -> 文件對象的映射
        """
        # 基礎文件（必須上傳）
        knowledge_files = {
            "scam_knowledge_base": os.path.join(base_dir, "backend/agents/scam_knowledge_base.md"),
            "few_shot_examples": os.path.join(base_dir, "backend/agents/few_shot_examples.md"),
        }
        
        # 可選：scraped_alerts（根據配置決定是否上傳）
        if upload_scraped_alerts:
            data_file_map = {
                "ultra_lite": "data/scraped_alerts_ultra_lite.json",  # 6 KB, 5 案例
                "lite": "data/scraped_alerts_lite.json",              # 39 KB, 30 案例
                "full": "data/scraped_alerts.json"                    # 409 KB, 281 案例
            }
            data_file = data_file_map.get(data_size, "data/scraped_alerts_ultra_lite.json")
            knowledge_files["scraped_alerts"] = os.path.join(base_dir, data_file)
            print(f"[FILE_MANAGER] 使用數據集: {data_size} ({data_file})")
        else:
            print("[FILE_MANAGER] ⚠️ 跳過 scraped_alerts 上傳（節省配額模式）")
            print("[FILE_MANAGER] 💡 提示：System Instructions 仍包含關鍵防詐知識")
        
        uploaded = {}
        for name, path in knowledge_files.items():
            if not os.path.exists(path):
                print(f"[FILE_MANAGER] Warning: File not found: {path}")
                continue
            
            try:
                uploaded[name] = self.upload_file(path, display_name=name)
            except Exception as e:
                print(f"[FILE_MANAGER] Upload failed for {name}: {e}")
        
        return uploaded


# 全局文件管理器實例
_file_manager: Optional[GeminiFileManager] = None


def get_file_manager(api_key: str) -> GeminiFileManager:
    """獲取全局文件管理器實例"""
    global _file_manager
    if _file_manager is None:
        _file_manager = GeminiFileManager(api_key)
    return _file_manager


if __name__ == "__main__":
    # 測試
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not set")
        sys.exit(1)
    
    print("=" * 60)
    print("Gemini File Manager Test")
    print("=" * 60)
    
    manager = GeminiFileManager(api_key)
    
    # 列出現有文件
    print("\n[1] Listing existing files...")
    manager.list_files()
    
    # 上傳知識庫
    print("\n[2] Uploading knowledge base...")
    uploaded = manager.upload_knowledge_base()
    
    print(f"\n[3] Successfully uploaded {len(uploaded)} files")
    for name, file in uploaded.items():
        print(f"  - {name}: {file.uri}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
