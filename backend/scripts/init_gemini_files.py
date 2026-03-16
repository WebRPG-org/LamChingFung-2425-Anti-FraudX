"""
初始化 Gemini 文件上傳
在啟動後端前運行，上傳所有知識庫文件到 Google 臨時伺服器
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加 backend 到 path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from llms.gemini_file_manager import GeminiFileManager

# 載入環境變量
env_path = backend_dir.parent / '.env'
if not env_path.exists():
    env_path = backend_dir / '.env'
load_dotenv(env_path)


def main():
    """初始化 Gemini 文件上傳"""
    
    # 獲取 API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set")
        print("Please set GEMINI_API_KEY in your .env file")
        return 1
    
    print("=" * 60)
    print("Gemini File Upload Initialization")
    print("=" * 60)
    
    # 創建文件管理器
    file_manager = GeminiFileManager(api_key)
    
    # 列出現有文件
    print("\n[1] Checking existing files...")
    existing_files = file_manager.list_files()
    
    if existing_files:
        print(f"\nFound {len(existing_files)} uploaded files:")
        for f in existing_files:
            print(f"  - {f.display_name}")
            print(f"    Expires: {f.expiration_time}")
        
        # 詢問是否刪除
        response = input("\nDelete existing files? (y/n): ")
        if response.lower() == 'y':
            print("\nDeleting existing files...")
            for f in existing_files:
                try:
                    file_manager.delete_file(f.name)
                    print(f"  [OK] Deleted: {f.display_name}")
                except Exception as e:
                    print(f"  [FAIL] Delete failed: {f.display_name} - {e}")
    
    # 上傳知識庫文件
    print("\n[2] Uploading knowledge base files...")
    
    # 設置基礎目錄為項目根目錄
    base_dir = backend_dir.parent
    uploaded = file_manager.upload_knowledge_base(str(base_dir))
    
    if not uploaded:
        print("\n[ERROR] No files uploaded!")
        print("Please check if the following files exist:")
        print("  - backend/agents/scam_knowledge_base.md")
        print("  - backend/agents/few_shot_examples.md")
        print("  - data/scraped_alerts.json")
        return 1
    
    print(f"\n[SUCCESS] Uploaded {len(uploaded)} files:")
    for name, file in uploaded.items():
        print(f"\n  [{name}]")
        print(f"    URI: {file.uri}")
        print(f"    Size: {file.size_bytes} bytes")
        print(f"    MIME: {file.mime_type}")
        print(f"    Expires: {file.expiration_time}")
    
    print("\n" + "=" * 60)
    print("Initialization Complete!")
    print("=" * 60)
    print("\nNotes:")
    print("- Files are stored on Google servers for 2 days (Free Tier)")
    print("- After expiration, you need to re-upload")
    print("- Backend will auto-check and re-upload on startup")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
