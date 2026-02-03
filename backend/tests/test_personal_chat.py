"""
個人對話模式 API 測試腳本
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_get_modes():
    """測試獲取可用模式"""
    print("\n" + "="*50)
    print("測試1: 獲取可用模式")
    print("="*50)
    
    response = requests.get(f"{API_BASE_URL}/api/personal-chat/modes")
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功獲取模式列表")
        print(f"可用模式: {len(data['modes'])}個")
        print(f"可用騙局: {len(data['scam_types'])}種")
        for mode in data['modes']:
            print(f"  - {mode['icon']} {mode['name']}: {mode['description']}")
        return True
    else:
        print(f"❌ 失敗: {response.text}")
        return False

def test_assistant_chat():
    """測試助手模式對話"""
    print("\n" + "="*50)
    print("測試2: 助手模式對話")
    print("="*50)
    
    # 1. 開始會話
    print("\n步驟1: 開始會話...")
    response = requests.post(
        f"{API_BASE_URL}/api/personal-chat/start",
        json={"mode": "assistant"}
    )
    
    if response.status_code != 200:
        print(f"❌ 開始會話失敗: {response.text}")
        return False
    
    data = response.json()
    session_id = data['session_id']
    print(f"✅ 會話已創建: {session_id}")
    print(f"歡迎消息: {data['reply'][:50]}...")
    
    # 2. 發送消息
    print("\n步驟2: 發送測試消息...")
    test_message = "我收到一個電話說我中獎了，要我先付稅金，這是真的嗎？"
    print(f"用戶: {test_message}")
    
    response = requests.post(
        f"{API_BASE_URL}/api/personal-chat/message",
        json={
            "session_id": session_id,
            "message": test_message
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 發送消息失敗: {response.text}")
        return False
    
    data = response.json()
    print(f"助手: {data['reply']}")
    
    # 3. 獲取會話信息
    print("\n步驟3: 獲取會話信息...")
    response = requests.get(f"{API_BASE_URL}/api/personal-chat/session/{session_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 會話歷史: {len(data['history'])}條消息")
    
    # 4. 結束會話
    print("\n步驟4: 結束會話...")
    response = requests.delete(f"{API_BASE_URL}/api/personal-chat/session/{session_id}")
    
    if response.status_code == 200:
        print(f"✅ 會話已結束")
        return True
    else:
        print(f"❌ 結束會話失敗")
        return False

def test_scammer_chat():
    """測試騙徒模式對話"""
    print("\n" + "="*50)
    print("測試3: 騙徒模式對話")
    print("="*50)
    
    # 1. 開始會話
    print("\n步驟1: 開始會話（投資理財詐騙）...")
    response = requests.post(
        f"{API_BASE_URL}/api/personal-chat/start",
        json={
            "mode": "scammer",
            "scam_type": "投資理財詐騙"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 開始會話失敗: {response.text}")
        return False
    
    data = response.json()
    session_id = data['session_id']
    print(f"✅ 會話已創建: {session_id}")
    print(f"騙徒: {data['reply']}")
    
    # 2. 進行對話
    print("\n步驟2: 進行對話...")
    messages = [
        "這個投資真的安全嗎？",
        "需要投資多少錢？",
        "我可以先投資一點試試嗎？"
    ]
    
    for msg in messages:
        print(f"\n用戶: {msg}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/personal-chat/message",
            json={
                "session_id": session_id,
                "message": msg
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"騙徒: {data['reply'][:100]}...")
        else:
            print(f"❌ 發送失敗")
            return False
        
        time.sleep(1)  # 避免請求過快
    
    # 3. 結束會話
    print("\n步驟3: 結束會話...")
    response = requests.delete(f"{API_BASE_URL}/api/personal-chat/session/{session_id}")
    
    if response.status_code == 200:
        print(f"✅ 會話已結束")
        return True
    else:
        print(f"❌ 結束會話失敗")
        return False

def main():
    """主測試函數"""
    print("\n" + "="*50)
    print("🧪 個人對話模式 API 測試")
    print("="*50)
    
    # 檢查服務是否運行
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✅ 後端服務運行中: {response.json()['status']}")
    except Exception as e:
        print(f"❌ 無法連接後端服務: {e}")
        print("請先啟動後端: python backend/main.py")
        return
    
    # 運行測試
    results = []
    
    results.append(("獲取模式列表", test_get_modes()))
    results.append(("助手模式對話", test_assistant_chat()))
    results.append(("騙徒模式對話", test_scammer_chat()))
    
    # 顯示測試結果
    print("\n" + "="*50)
    print("📊 測試結果總結")
    print("="*50)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！個人對話模式運行正常！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤信息")

if __name__ == "__main__":
    main()
