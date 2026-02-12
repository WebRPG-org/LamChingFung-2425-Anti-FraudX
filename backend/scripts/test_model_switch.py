"""
測試 Gemini 模式切換功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加 backend �?path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 確保從正確位置加�?.env
from dotenv import load_dotenv
env_path = backend_dir.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[INFO] Loaded .env from: {env_path}")
else:
    load_dotenv()
    print(f"[INFO] Loaded .env from default location")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_model_status():
    """測試獲取模型狀�?""
    print("\n" + "=" * 60)
    print("Test 1: Get Model Status")
    print("=" * 60)
    
    response = client.get("/api/model/status")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Current Provider: {data['current_provider']}")
        print(f"[OK] Gemini Enabled: {data['gemini_enabled']}")
        print(f"[OK] Gemini Configured: {data['gemini_configured']}")
        print(f"[OK] Provider Info: {data['provider_info']['provider']}")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False


def test_get_providers():
    """測試獲取可用提供�?""
    print("\n" + "=" * 60)
    print("Test 2: Get Available Providers")
    print("=" * 60)
    
    response = client.get("/api/model/providers")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Current: {data['current']}")
        print(f"[OK] Providers:")
        for provider in data['providers']:
            print(f"  - {provider['name']}: configured={provider['configured']}")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False


def test_switch_to_gemini():
    """測試切換�?Gemini"""
    print("\n" + "=" * 60)
    print("Test 3: Switch to Gemini")
    print("=" * 60)
    
    response = client.post(
        "/api/model/switch",
        json={"use_gemini": True}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Success: {data['success']}")
        print(f"[OK] Message: {data['message']}")
        print(f"[OK] Current Provider: {data['current_provider']}")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False


def test_switch_to_ollama():
    """測試切換�?Ollama"""
    print("\n" + "=" * 60)
    print("Test 4: Switch to Ollama")
    print("=" * 60)
    
    response = client.post(
        "/api/model/switch",
        json={"use_gemini": False}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Success: {data['success']}")
        print(f"[OK] Message: {data['message']}")
        print(f"[OK] Current Provider: {data['current_provider']}")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False


def test_validate_gemini_config():
    """測試驗證 Gemini 配置"""
    print("\n" + "=" * 60)
    print("Test 5: Validate Gemini Config")
    print("=" * 60)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[SKIP] GEMINI_API_KEY not set")
        return None
    
    response = client.post(
        "/api/model/validate",
        json={
            "api_key": api_key,
            "scammer_model": "gemini-2.5-flash",
            "victim_model": "gemini-2.5-flash",
            "expert_model": "gemini-2.5-flash",
            "recorder_model": "gemini-2.5-flash"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Valid: {data['valid']}")
        if data.get('errors'):
            print(f"[WARN] Errors: {data['errors']}")
        if data.get('warnings'):
            print(f"[WARN] Warnings: {data['warnings']}")
        return data['valid']
    else:
        print(f"[FAIL] {response.text}")
        return False


def main():
    print("=" * 60)
    print("Gemini Model Switch Test")
    print("=" * 60)
    
    results = []
    
    # 測試 1: 獲取模型狀�?
    results.append(("Get Model Status", test_get_model_status()))
    
    # 測試 2: 獲取可用提供�?
    results.append(("Get Providers", test_get_providers()))
    
    # 測試 3: 驗證 Gemini 配置
    validation_result = test_validate_gemini_config()
    if validation_result is not None:
        results.append(("Validate Config", validation_result))
    
    # 測試 4: 切換�?Gemini
    if validation_result:
        results.append(("Switch to Gemini", test_switch_to_gemini()))
        
        # 測試 5: 切換�?Ollama
        results.append(("Switch to Ollama", test_switch_to_ollama()))
    else:
        print("\n[SKIP] Skipping switch tests (config not valid)")
    
    # 總結
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        if result is None:
            status = "[SKIP]"
        elif result:
            status = "[PASS]"
        else:
            status = "[FAIL]"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result is True)
    total = len([r for r in results if r[1] is not None])
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
