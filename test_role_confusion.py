"""
Test script to detect role confusion between scammer and expert
檢測騙徒和專家角色混合問題
"""

import requests
import json
import re

BASE_URL = "http://localhost:8000"

# 騙徒不應該說的話（專家的話）
SCAMMER_FORBIDDEN_PHRASES = [
    "小心", "詐騙", "騙局", "報警", "999", "18222",
    "唔好信", "唔好俾", "假嘅", "核實", "官方",
    "保護", "防範", "警惕", "識破", "揭穿"
]

# 專家不應該說的話（騙徒的話）
EXPERT_FORBIDDEN_PHRASES = [
    "提供帳號", "提供密碼", "提供驗證碼", "立即轉賬",
    "馬上處理", "你的帳戶有問題", "需要核實身份",
    "凍結帳戶", "可疑交易", "配合調查"
]

def check_role_confusion(text, role):
    """
    檢查角色混合
    
    Args:
        text: 生成的文本
        role: 角色 (scammer/expert)
    
    Returns:
        list of detected issues
    """
    issues = []
    
    if role == "scammer":
        # 檢查騙徒是否說了專家的話
        for phrase in SCAMMER_FORBIDDEN_PHRASES:
            if phrase in text:
                issues.append(f"騙徒說了專家的話: '{phrase}'")
    
    elif role == "expert":
        # 檢查專家是否說了騙徒的話
        for phrase in EXPERT_FORBIDDEN_PHRASES:
            if phrase in text:
                issues.append(f"專家說了騙徒的話: '{phrase}'")
    
    return issues

def test_victim_mode():
    """測試受害人模式（AI騙徒 + AI專家）"""
    print("\n" + "="*80)
    print("測試受害人模式 - 檢查 AI 騙徒和 AI 專家的角色區分")
    print("="*80 + "\n")
    
    # 開始遊戲
    start_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/start",
        json={
            "mode": "victim",
            "scam_type": "investment",
            "victim_persona": "average"
        }
    )
    
    if start_response.status_code != 200:
        print(f"❌ 啟動失敗: {start_response.status_code}")
        return False
    
    data = start_response.json()
    session_id = data["session_id"]
    
    print(f"✅ 遊戲啟動成功 - Session: {session_id}\n")
    
    # 檢查開場消息
    all_issues = []
    
    print("檢查開場消息:")
    for i, msg in enumerate(data['opening_messages']):
        role = msg['role']
        content = msg['content']
        
        print(f"\n{i+1}. {role.upper()}:")
        print(f"   {content[:100]}...")
        
        issues = check_role_confusion(content, role)
        if issues:
            print(f"   ⚠️ 發現問題:")
            for issue in issues:
                print(f"      - {issue}")
                all_issues.append(f"{role}: {issue}")
        else:
            print(f"   ✅ 角色正確")
    
    # 玩家發送消息
    print("\n" + "-"*80)
    print("玩家(受害者)發送消息...")
    
    action_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/action",
        json={
            "session_id": session_id,
            "message": "聽起來很吸引，但我有點擔心..."
        }
    )
    
    if action_response.status_code != 200:
        print(f"❌ 發送失敗: {action_response.status_code}")
        return False
    
    action_data = action_response.json()
    
    print("\n檢查 AI 回應:")
    for i, response in enumerate(action_data['ai_responses']):
        role = response['role']
        content = response['content']
        
        print(f"\n{i+1}. {role.upper()}:")
        print(f"   {content[:150]}...")
        
        issues = check_role_confusion(content, role)
        if issues:
            print(f"   ⚠️ 發現問題:")
            for issue in issues:
                print(f"      - {issue}")
                all_issues.append(f"{role}: {issue}")
        else:
            print(f"   ✅ 角色正確")
    
    # 總結
    print("\n" + "="*80)
    if all_issues:
        print("❌ 測試失敗 - 發現角色混合問題:")
        for issue in all_issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ 測試通過 - 騙徒和專家角色區分清晰")
        return True

def test_scammer_mode():
    """測試騙徒模式（玩家=騙徒，AI受害者 + AI專家）"""
    print("\n" + "="*80)
    print("測試騙徒模式 - 檢查 AI 專家的角色")
    print("="*80 + "\n")
    
    # 開始遊戲
    start_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/start",
        json={
            "mode": "scammer",
            "scam_type": "investment",
            "victim_persona": "average"
        }
    )
    
    if start_response.status_code != 200:
        print(f"❌ 啟動失敗: {start_response.status_code}")
        return False
    
    data = start_response.json()
    session_id = data["session_id"]
    
    print(f"✅ 遊戲啟動成功 - Session: {session_id}\n")
    
    # 玩家(騙徒)發送消息
    print("玩家(騙徒)發送詐騙消息...")
    
    action_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/action",
        json={
            "session_id": session_id,
            "message": "你好，我是專業投資顧問。我們有一個AI交易系統，月回報15%，現在有限時優惠..."
        }
    )
    
    if action_response.status_code != 200:
        print(f"❌ 發送失敗: {action_response.status_code}")
        return False
    
    action_data = action_response.json()
    
    all_issues = []
    
    print("\n檢查 AI 回應:")
    for i, response in enumerate(action_data['ai_responses']):
        role = response['role']
        content = response['content']
        
        print(f"\n{i+1}. {role.upper()}:")
        print(f"   {content[:150]}...")
        
        if role == "expert":
            # 專家應該警告受害者，不應該幫騙徒
            issues = check_role_confusion(content, role)
            if issues:
                print(f"   ⚠️ 發現問題:")
                for issue in issues:
                    print(f"      - {issue}")
                    all_issues.append(f"{role}: {issue}")
            else:
                print(f"   ✅ 角色正確")
    
    # 總結
    print("\n" + "="*80)
    if all_issues:
        print("❌ 測試失敗 - 發現角色混合問題:")
        for issue in all_issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ 測試通過 - 專家角色正確")
        return True

def main():
    print("\n" + "="*80)
    print("角色混合檢測測試")
    print("="*80)
    
    results = {}
    
    # 測試受害人模式
    try:
        results['victim_mode'] = test_victim_mode()
    except Exception as e:
        print(f"\n❌ 受害人模式測試出錯: {e}")
        results['victim_mode'] = False
    
    # 測試騙徒模式
    try:
        results['scammer_mode'] = test_scammer_mode()
    except Exception as e:
        print(f"\n❌ 騙徒模式測試出錯: {e}")
        results['scammer_mode'] = False
    
    # 最終總結
    print("\n" + "="*80)
    print("最終結果:")
    print("="*80)
    
    for mode, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {mode}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ 所有測試通過 - 角色區分清晰")
    else:
        print("❌ 部分測試失敗 - 存在角色混合問題")
        print("\n建議:")
        print("  1. 檢查微調模型是否正確訓練")
        print("  2. 增強 prompt 的角色鎖定指令")
        print("  3. 考慮使用不同的模型或調整溫度參數")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ 無法連接到後端 http://localhost:8000")
        print("請確保後端正在運行")
        exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
