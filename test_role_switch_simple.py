"""
測試角色切換功能 - 簡化版
"""

import requests
import json
import sys

# 設置編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_role_switching():
    """測試角色切換功能"""
    print("="*60)
    print("  測試角色切換功能")
    print("="*60)
    
    # 1. 開始遊戲（受害人模式）
    print("\n[1] 開始遊戲 - 受害人模式")
    try:
        response = requests.post(f"{BASE_URL}/api/rpgv2/game/start", json={
            "mode": "victim",
            "scam_type": "假冒銀行",
            "victim_persona": "average"
        }, timeout=10)
        
        if response.status_code != 200:
            print(f"[X] 開始遊戲失敗: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        session_id = data["session_id"]
        print(f"[OK] 會話創建成功: {session_id}")
        print(f"[OK] 當前模式: {data['mode']}")
        print(f"[OK] 模式名稱: {data['mode_info']['name']}")
    except Exception as e:
        print(f"[X] 錯誤: {e}")
        return
    
    # 2. 切換到騙徒模式
    print("\n[2] 切換到騙徒模式")
    try:
        response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
            "session_id": session_id,
            "new_mode": "scammer"
        }, timeout=10)
        
        if response.status_code != 200:
            print(f"[X] 切換失敗: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        if data["success"]:
            print(f"[OK] {data['message']}")
            print(f"[OK] 舊模式: {data['old_mode']}")
            print(f"[OK] 新模式: {data['new_mode']}")
        else:
            print("[X] 切換失敗")
            return
    except Exception as e:
        print(f"[X] 錯誤: {e}")
        return
    
    # 3. 切換到專家模式
    print("\n[3] 切換到專家模式")
    try:
        response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
            "session_id": session_id,
            "new_mode": "expert"
        }, timeout=10)
        
        if response.status_code != 200:
            print(f"[X] 切換失敗: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        if data["success"]:
            print(f"[OK] {data['message']}")
            print(f"[OK] 舊模式: {data['old_mode']}")
            print(f"[OK] 新模式: {data['new_mode']}")
        else:
            print("[X] 切換失敗")
            return
    except Exception as e:
        print(f"[X] 錯誤: {e}")
        return
    
    # 4. 切換回受害人模式
    print("\n[4] 切換回受害人模式")
    try:
        response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
            "session_id": session_id,
            "new_mode": "victim"
        }, timeout=10)
        
        if response.status_code != 200:
            print(f"[X] 切換失敗: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        if data["success"]:
            print(f"[OK] {data['message']}")
            print(f"[OK] 舊模式: {data['old_mode']}")
            print(f"[OK] 新模式: {data['new_mode']}")
        else:
            print("[X] 切換失敗")
            return
    except Exception as e:
        print(f"[X] 錯誤: {e}")
        return
    
    # 5. 清理：刪除會話
    print("\n[5] 清理會話")
    try:
        response = requests.delete(f"{BASE_URL}/api/rpgv2/game/session/{session_id}", timeout=10)
        
        if response.status_code == 200:
            print("[OK] 會話已刪除")
        else:
            print(f"[!] 刪除會話失敗: {response.status_code}")
    except Exception as e:
        print(f"[X] 錯誤: {e}")
    
    print("\n" + "="*60)
    print("  [OK] 角色切換功能測試完成")
    print("="*60)
    print("\n鍵盤快捷鍵對應:")
    print("  按 1 = 受害人模式")
    print("  按 2 = 騙徒模式")
    print("  按 3 = 專家模式")

if __name__ == "__main__":
    try:
        test_role_switching()
    except Exception as e:
        print(f"\n[X] 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
