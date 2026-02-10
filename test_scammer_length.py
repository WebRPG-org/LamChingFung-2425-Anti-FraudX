"""
測試騙徒回應長度限制
驗證騙徒生成的內容是否在 50 字以內
"""

import asyncio
import sys
import os

# 添加 backend 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agents.scammer import ScammerAgent
from utils.logger import log


async def test_scammer_length():
    """測試騙徒回應長度"""
    
    print("\n" + "="*60)
    print("🧪 測試騙徒回應長度限制（目標：≤50字）")
    print("="*60 + "\n")
    
    # 測試場景
    test_cases = [
        {
            "tactic": "假冒銀行",
            "prompt": "你好，我想查詢我的帳戶餘額。",
            "description": "假冒銀行場景"
        },
        {
            "tactic": "假冒政府",
            "prompt": "我收到你們的電話，說我涉及案件？",
            "description": "假冒政府場景"
        },
        {
            "tactic": "虛假投資",
            "prompt": "這個投資計劃聽起來不錯，可以詳細說明嗎？",
            "description": "虛假投資場景"
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試 {i}/{len(test_cases)}: {case['description']}")
        print(f"   詐騙手法: {case['tactic']}")
        print(f"   輸入: {case['prompt']}")
        print("-" * 60)
        
        try:
            # 初始化騙徒 Agent（簡化模式）
            scammer = ScammerAgent(scam_tactic=case['tactic'], simple_mode=True)
            
            # 生成回應
            response = await scammer.run_async(case['prompt'])
            response_text = response.strip()
            
            # 計算字數
            char_count = len(response_text)
            
            # 判斷是否符合要求
            is_valid = char_count <= 50
            status = "✅ 通過" if is_valid else "❌ 超出"
            
            print(f"\n   {status} 字數: {char_count}/50")
            print(f"   回應內容:")
            print(f"   「{response_text}」")
            
            results.append({
                "case": case['description'],
                "tactic": case['tactic'],
                "char_count": char_count,
                "is_valid": is_valid,
                "response": response_text
            })
            
        except Exception as e:
            print(f"\n   ❌ 錯誤: {e}")
            results.append({
                "case": case['description'],
                "tactic": case['tactic'],
                "char_count": 0,
                "is_valid": False,
                "response": f"錯誤: {e}"
            })
    
    # 統計結果
    print("\n" + "="*60)
    print("📊 測試結果統計")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results if r['is_valid'])
    failed = total - passed
    
    print(f"\n總測試數: {total}")
    print(f"✅ 通過: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ 失敗: {failed} ({failed/total*100:.1f}%)")
    
    # 詳細結果
    print("\n詳細結果:")
    for i, r in enumerate(results, 1):
        status = "✅" if r['is_valid'] else "❌"
        print(f"{i}. {status} {r['case']}: {r['char_count']}字")
    
    # 平均字數
    avg_chars = sum(r['char_count'] for r in results if r['is_valid']) / max(passed, 1)
    print(f"\n平均字數: {avg_chars:.1f} 字")
    
    # 最長回應
    if results:
        longest = max(results, key=lambda x: x['char_count'])
        print(f"最長回應: {longest['char_count']} 字 ({longest['case']})")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("🎉 所有測試通過！騙徒回應長度控制成功！")
    else:
        print(f"⚠️ 有 {failed} 個測試失敗，需要進一步調整。")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(test_scammer_length())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
