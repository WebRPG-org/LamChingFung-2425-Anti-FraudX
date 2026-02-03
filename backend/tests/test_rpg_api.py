"""測試 RPG API"""
import requests
import json

# 測試 1: 開始遊戲
print("=" * 60)
print("測試 1: 開始遊戲")
print("=" * 60)

response = requests.post(
    "http://localhost:8000/api/game/v2/start",
    json={"persona_type": "A"}
)

print(f"狀態碼: {response.status_code}")
print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if response.status_code == 200:
    data = response.json()
    session_id = data["session_id"]
    
    # 測試 2: 發送訊息
    print("\n" + "=" * 60)
    print("測試 2: 發送訊息給 AI-D (騙徒)")
    print("=" * 60)
    
    response2 = requests.post(
        "http://localhost:8000/api/game/v2/message",
        json={
            "session_id": session_id,
            "message": "你好，我想了解一下投資。",
            "target_ai": "AI-D",
            "persona_type": "A"
        }
    )
    
    print(f"狀態碼: {response2.status_code}")
    print(f"回應: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")
else:
    print("❌ 開始遊戲失敗")
