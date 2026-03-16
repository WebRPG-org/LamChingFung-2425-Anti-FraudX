"""
創建超精簡版數據 - 只保留 5 個最重要的案例
進一步減少 token 使用
"""

import json
from pathlib import Path

def create_ultra_lite_version():
    """創建超精簡版的案例數據"""
    
    # 讀取精簡版文件
    lite_file = Path(__file__).parent.parent.parent / 'data' / 'scraped_alerts_lite.json'
    
    if not lite_file.exists():
        print(f"[ERROR] 找不到文件: {lite_file}")
        return
    
    with open(lite_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[INFO] 精簡版包含 {len(data)} 條案例")
    print(f"[INFO] 精簡版大小: {lite_file.stat().st_size / 1024:.1f} KB")
    
    # 只保留最重要的 5 條案例（涵蓋不同類型）
    ultra_lite_data = data[:5]
    
    # 保存超精簡版
    ultra_lite_file = lite_file.parent / 'scraped_alerts_ultra_lite.json'
    with open(ultra_lite_file, 'w', encoding='utf-8') as f:
        json.dump(ultra_lite_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SUCCESS] 創建超精簡版:")
    print(f"  文件: {ultra_lite_file}")
    print(f"  案例數: {len(ultra_lite_data)}")
    print(f"  文件大小: {ultra_lite_file.stat().st_size / 1024:.1f} KB")
    print(f"  從精簡版減少: {(1 - ultra_lite_file.stat().st_size / lite_file.stat().st_size) * 100:.1f}%")
    print(f"  從原始版減少: ~97%")
    
    print(f"\n[建議] 對於免費版 Gemini API:")
    print(f"  1. 使用超精簡版（5 案例）")
    print(f"  2. 或者完全不上傳 scraped_alerts，只用 System Instructions")
    print(f"  3. 考慮升級到付費版以獲得更高配額")

if __name__ == "__main__":
    create_ultra_lite_version()
