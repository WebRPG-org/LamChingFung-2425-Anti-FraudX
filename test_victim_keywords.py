"""
測試受害人關鍵詞判定
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('backend')

from utils.ai_judgment_optimizer import FastPathJudgment

def test_keywords():
    """測試關鍵詞判定"""
    fast_path = FastPathJudgment()
    
    # 測試案例
    test_cases = [
        # 騙徒模式 - 應該判定為騙徒勝出
        ("我會提供資料", "scammer", "victim", True, "player"),
        ("我會俾錢", "scammer", "victim", True, "player"),
        ("我會畀錢", "scammer", "victim", True, "player"),
        ("我可以提供資料", "scammer", "victim", True, "player"),
        ("好的我會俾錢", "scammer", "victim", True, "player"),
        ("我會過數", "scammer", "victim", True, "player"),
        ("我會轉帳", "scammer", "victim", True, "player"),
        
        # 騙徒模式 - 應該判定為防詐成功
        ("我要報警", "scammer", "victim", True, "ai"),
        ("你係騙徒", "scammer", "victim", True, "ai"),
        ("我唔會上當", "scammer", "victim", True, "ai"),
        
        # 專家模式 - 應該判定為專家勝出
        ("我聽專家講", "expert", "victim", True, "player"),
        ("我唔會俾資料佢", "expert", "victim", True, "player"),
        
        # 專家模式 - 應該判定為專家失敗
        ("我唔信專家", "expert", "victim", True, "ai"),
        ("我會俾資料佢", "expert", "victim", True, "ai"),
        
        # 不應該觸發判定
        ("我在考慮", "scammer", "victim", False, None),
        ("讓我想想", "scammer", "victim", False, None),
    ]
    
    print("=" * 80)
    print("測試受害人關鍵詞判定")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for message, mode, role, should_trigger, expected_winner in test_cases:
        result = fast_path.check(message, mode, role)
        
        if should_trigger:
            if result is None:
                print(f"❌ FAILED: '{message}'")
                print(f"   預期: 觸發判定 (勝者: {expected_winner})")
                print(f"   實際: 沒有觸發")
                print()
                failed += 1
            else:
                judgment, confidence = result
                actual_winner = judgment.get("winner")
                if actual_winner == expected_winner:
                    print(f"✅ PASSED: '{message}'")
                    print(f"   勝者: {actual_winner}")
                    print(f"   原因: {judgment.get('reason')}")
                    print(f"   信心度: {confidence}%")
                    print()
                    passed += 1
                else:
                    print(f"❌ FAILED: '{message}'")
                    print(f"   預期勝者: {expected_winner}")
                    print(f"   實際勝者: {actual_winner}")
                    print()
                    failed += 1
        else:
            if result is None:
                print(f"✅ PASSED: '{message}' (正確不觸發)")
                print()
                passed += 1
            else:
                print(f"❌ FAILED: '{message}'")
                print(f"   預期: 不觸發")
                print(f"   實際: 觸發了判定")
                print()
                failed += 1
    
    print("=" * 80)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("=" * 80)
    print()
    
    # 顯示統計
    stats = fast_path.get_stats()
    print("快速路徑統計:")
    print(f"  總檢查次數: {stats['total_checks']}")
    print(f"  快速路徑命中: {stats['fast_path_hits']}")
    print(f"  命中率: {stats['hit_rate']}%")
    print()
    print(f"  騙徒勝出: {stats['scammer_win']}")
    print(f"  騙徒失敗: {stats['scammer_lose']}")
    print(f"  專家勝出: {stats['expert_win']}")
    print(f"  專家失敗: {stats['expert_lose']}")

if __name__ == "__main__":
    test_keywords()
