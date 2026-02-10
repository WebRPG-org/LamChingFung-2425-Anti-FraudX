"""
測試角色切換功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_role_switching():
    """測試角色切換功能"""
    print("="*60)
    print("  測試角色切換功能")
    print("="*60)
    
    # 1. 開始遊戲（受害人模式）
    print("\n1️⃣ 開始遊戲 - 受害人模式")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/start", json={
        "mode": "victim",
        "scam_type": "假冒銀行",
        "victim_persona": "average"
    })
    
    if response.status_code != 200:
        print(f"❌ 開始遊戲失敗: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    session_id = data["session_id"]
    print(f"✅ 會話創建成功: {session_id}")
    print(f"📋 當前模式: {data['mode']}")
    print(f"📝 模式名稱: {data['mode_info']['name']}")
    
    # 2. 切換到騙徒模式
    print("\n2️⃣ 切換到騙徒模式")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "scammer"
    })
    
    if response.status_code != 200:
        print(f"❌ 切換失敗: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    if data["success"]:
        print(f"✅ {data['message']}")
        print(f"   舊模式: {data['old_mode']}")
        print(f"   新模式: {data['new_mode']}")
        print(f"   模式名稱: {data['mode_info']['name']}")
    else:
        print("❌ 切換失敗")
        return
    
    # 3. 切換到專家模式
    print("\n3️⃣ 切換到專家模式")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "expert"
    })
    
    if response.status_code != 200:
        print(f"❌ 切換失敗: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    if data["success"]:
        print(f"✅ {data['message']}")
        print(f"   舊模式: {data['old_mode']}")
        print(f"   新模式: {data['new_mode']}")
        print(f"   模式名稱: {data['mode_info']['name']}")
    else:
        print("❌ 切換失敗")
        return
    
    # 4. 切換回受害人模式
    print("\n4️⃣ 切換回受害人模式")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "victim"
    })
    
    if response.status_code != 200:
        print(f"❌ 切換失敗: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    if data["success"]:
        print(f"✅ {data['message']}")
        print(f"   舊模式: {data['old_mode']}")
        print(f"   新模式: {data['new_mode']}")
        print(f"   模式名稱: {data['mode_info']['name']}")
    else:
        print("❌ 切換失敗")
        return
    
    # 5. 測試切換到自動模式（應該失敗）
    print("\n5️⃣ 測試切換到自動模式（應該失敗）")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "auto"
    })
    
    if response.status_code == 400:
        print("✅ 正確拒絕切換到自動模式")
    else:
        print(f"⚠️ 意外的響應: {response.status_code}")
    
    # 6. 測試無效的會話 ID
    print("\n6️⃣ 測試無效的會話 ID（應該失敗）")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": "invalid-session-id",
        "new_mode": "expert"
    })
    
    if response.status_code == 404:
        print("✅ 正確拒絕無效的會話 ID")
    else:
        print(f"⚠️ 意外的響應: {response.status_code}")
    
    # 7. 清理：刪除會話
    print("\n7️⃣ 清理會話")
    response = requests.delete(f"{BASE_URL}/api/rpgv2/game/session/{session_id}")
    
    if response.status_code == 200:
        print("✅ 會話已刪除")
    else:
        print(f"⚠️ 刪除會話失敗: {response.status_code}")
    
    print("\n" + "="*60)
    print("  ✅ 角色切換功能測試完成")
    print("="*60)
    print("\n鍵盤快捷鍵對應:")
    print("  按 1 = 受害人模式")
    print("  按 2 = 騙徒模式")
    print("  按 3 = 專家模式")

if __name__ == "__main__":
    try:
        test_role_switching()
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
