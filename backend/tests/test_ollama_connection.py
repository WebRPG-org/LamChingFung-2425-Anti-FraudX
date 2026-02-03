"""
測試 Ollama 連接和 AI 對話功能
"""
import asyncio
import httpx

async def test_ollama_direct():
    """直接測試 Ollama API"""
    print("=" * 60)
    print("測試 1: 直接連接 Ollama")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            # 測試基本連接
            response = await client.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json()
                print("[OK] Ollama 連接成功!")
                print(f"可用模型: {[m['name'] for m in models.get('models', [])]}")
            else:
                print(f"[ERROR] Ollama 響應異常: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Ollama 連接失敗: {e}")

async def test_backend_api():
    """測試後端 API"""
    print("\n" + "=" * 60)
    print("測試 2: 測試後端 API 對話功能")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            # 測試對話 API
            payload = {
                "message": "你好，這是一個測試訊息。",
                "session_id": "test_session_123"
            }
            
            print(f"發送測試訊息: {payload['message']}")
            response = await client.post(
                "http://localhost:8000/api/chat/send",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] 後端 API 連接成功!")
                print(f"AI 回應: {result.get('response', 'N/A')[:100]}...")
            else:
                print(f"[ERROR] 後端 API 響應異常: {response.status_code}")
                print(f"錯誤: {response.text}")
    except Exception as e:
        print(f"[ERROR] 後端 API 連接失敗: {e}")

async def test_game_start():
    """測試遊戲開始功能"""
    print("\n" + "=" * 60)
    print("測試 3: 測試遊戲開始功能")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "scenario": "investment",
                "difficulty": "medium"
            }
            
            print(f"開始遊戲測試...")
            response = await client.post(
                "http://localhost:8000/api/game/start",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] 遊戲開始 API 成功!")
                print(f"Session ID: {result.get('session_id', 'N/A')}")
                print(f"初始訊息: {result.get('initial_message', 'N/A')[:100]}...")
            else:
                print(f"[ERROR] 遊戲 API 響應異常: {response.status_code}")
                print(f"錯誤: {response.text}")
    except Exception as e:
        print(f"[ERROR] 遊戲 API 連接失敗: {e}")

async def main():
    print("\nAI 反詐騙平台連接測試")
    print("=" * 60)
    
    await test_ollama_direct()
    await test_backend_api()
    await test_game_start()
    
    print("\n" + "=" * 60)
    print("[DONE] 測試完成!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

