"""
創建精簡版的 scraped_alerts.json
只保留最近和最重要的案例，減少 token 消耗
"""

import json
import sys
from pathlib import Path

def create_lite_version():
    """創建精簡版的案例數據"""
    
    # 讀取原始文件
    data_file = Path(__file__).parent.parent.parent / 'data' / 'scraped_alerts.json'
    
    if not data_file.exists():
        print(f"[ERROR] 找不到文件: {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[INFO] 原始文件包含 {len(data)} 條案例")
    print(f"[INFO] 原始文件大小: {data_file.stat().st_size / 1024:.1f} KB")
    
    # 只保留最近的 30 條案例
    lite_data = data[:30]
    
    # 保存精簡版
    lite_file = data_file.parent / 'scraped_alerts_lite.json'
    with open(lite_file, 'w', encoding='utf-8') as f:
        json.dump(lite_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SUCCESS] 創建精簡版:")
    print(f"  文件: {lite_file}")
    print(f"  案例數: {len(lite_data)}")
    print(f"  文件大小: {lite_file.stat().st_size / 1024:.1f} KB")
    print(f"  減少: {(1 - lite_file.stat().st_size / data_file.stat().st_size) * 100:.1f}%")
    
    print(f"\n[NEXT] 更新上傳腳本使用精簡版:")
    print(f"  修改 init_gemini_files.py")
    print(f"  將 'data/scraped_alerts.json' 改為 'data/scraped_alerts_lite.json'")

if __name__ == "__main__":
    create_lite_version()
