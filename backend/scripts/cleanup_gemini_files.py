"""
清理 Gemini 重複上傳的文件
只保留每個文件的最新版本
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 添加 backend 目錄到 Python 路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 加載環境變量
load_dotenv(backend_dir / '.env')

from llms.gemini_file_manager import GeminiFileManager

def cleanup_duplicate_files():
    """清理重複的文件，只保留最新的"""
    
    print("=" * 60)
    print("Gemini 文件清理工具")
    print("=" * 60)
    
    # 初始化文件管理器
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR] 未找到 GEMINI_API_KEY 環境變量")
        print("請在 backend/.env 文件中設置 GEMINI_API_KEY")
        return
    
    file_manager = GeminiFileManager(api_key=api_key)
    
    print("\n[1] 獲取所有已上傳文件...")
    all_files = file_manager.list_files()
    
    if not all_files:
        print("[INFO] 沒有找到任何文件")
        return
    
    print(f"[INFO] 找到 {len(all_files)} 個文件\n")
    
    # 按 display_name 分組
    files_by_name = {}
    for file in all_files:
        name = file.display_name
        if name not in files_by_name:
            files_by_name[name] = []
        files_by_name[name].append(file)
    
    # 顯示分組結果
    print("[2] 文件分組:")
    for name, files in files_by_name.items():
        print(f"\n  [FILE] {name}: {len(files)} 個版本")
        for f in sorted(files, key=lambda x: x.expiration_time, reverse=True):
            print(f"    - {f.name}")
            print(f"      到期: {f.expiration_time}")
    
    # 刪除舊版本
    print("\n[3] 清理重複文件...")
    deleted_count = 0
    kept_count = 0
    
    for name, files in files_by_name.items():
        if len(files) <= 1:
            print(f"\n  [OK] {name}: 只有 1 個版本，保留")
            kept_count += 1
            continue
        
        # 按到期時間排序，保留最新的
        sorted_files = sorted(files, key=lambda x: x.expiration_time, reverse=True)
        latest = sorted_files[0]
        old_files = sorted_files[1:]
        
        print(f"\n  [FILE] {name}:")
        print(f"    [KEEP] {latest.name} (到期: {latest.expiration_time})")
        kept_count += 1
        
        for old_file in old_files:
            try:
                file_manager.delete_file(old_file.name)
                print(f"    [DELETE] {old_file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"    [WARN] 刪除失敗 {old_file.name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"清理完成！")
    print(f"  保留: {kept_count} 個文件")
    print(f"  刪除: {deleted_count} 個文件")
    print("=" * 60)
    
    # 顯示最終狀態
    print("\n[4] 最終文件列表:")
    final_files = file_manager.list_files()
    if final_files:
        for f in final_files:
            print(f"\n  [OK] {f.display_name}")
            print(f"    URI: {f.uri}")
            print(f"    到期: {f.expiration_time}")
    else:
        print("  (無文件)")

if __name__ == "__main__":
    try:
        cleanup_duplicate_files()
    except KeyboardInterrupt:
        print("\n\n[INFO] 用戶中斷")
    except Exception as e:
        print(f"\n[ERROR] 執行失敗: {e}")
        import traceback
        traceback.print_exc()
