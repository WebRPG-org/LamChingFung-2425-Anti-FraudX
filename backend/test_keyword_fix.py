"""
測試關鍵詞匹配修復
驗證 HI 不會誤觸發勝負
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.scam_scoring_hybrid import HybridScamScoring

print("=" * 80)
print("測試關鍵詞匹配修復")
print("=" * 80)

# 測試 1：只說 HI 不應該觸發勝負
print("\n測試 1：只說 HI（不應該觸發勝負）")
scorer = HybridScamScoring(victim_persona='average')
score, status = scorer.add_scammer_message('HI', ['authority'])
print(f"   分數: {score}, 狀態: {status}")
if status == 'ongoing':
    print("   ✅ 通過")
else:
    print(f"   ❌ 失敗：應該是 ongoing，但得到 {status}")

# 測試 2：說完整的關鍵詞應該觸發勝負
print("\n測試 2：說銀行密碼（應該觸發騙徒勝利）")
scorer2 = HybridScamScoring(victim_persona='average')
score, status = scorer2.add_scammer_message('請提供你的銀行密碼', ['authority'])
print(f"   分數: {score}, 狀態: {status}")
if status == 'scammer_win':
    print("   ✅ 通過")
else:
    print(f"   ❌ 失敗：應該是 scammer_win，但得到 {status}")

# 測試 3：專家說報警應該立即贏
print("\n測試 3：說報警（應該觸發專家勝利）")
scorer3 = HybridScamScoring(victim_persona='average')
score, status = scorer3.add_expert_message('你應該立即報警', ['actionable'])
print(f"   分數: {score}, 狀態: {status}")
if status == 'expert_win':
    print("   ✅ 通過")
else:
    print(f"   ❌ 失敗：應該是 expert_win，但得到 {status}")

# 測試 4：說密碼但不是完整詞（不應該觸發）
print("\n測試 4：說 password（不應該觸發，因為關鍵詞是中文）")
scorer4 = HybridScamScoring(victim_persona='average')
score, status = scorer4.add_scammer_message('password is 123', ['authority'])
print(f"   分數: {score}, 狀態: {status}")
if status == 'ongoing':
    print("   ✅ 通過")
else:
    print(f"   ❌ 失敗：應該是 ongoing，但得到 {status}")

# 測試 5：說驗證碼（應該觸發騙徒勝利）
print("\n測試 5：說驗證碼（應該觸發騙徒勝利）")
scorer5 = HybridScamScoring(victim_persona='average')
score, status = scorer5.add_scammer_message('請告訴我驗證碼', ['authority'])
print(f"   分數: {score}, 狀態: {status}")
if status == 'scammer_win':
    print("   ✅ 通過")
else:
    print(f"   ❌ 失敗：應該是 scammer_win，但得到 {status}")

print("\n" + "=" * 80)
print("✅ 關鍵詞匹配修復驗證完成")
print("=" * 80)

