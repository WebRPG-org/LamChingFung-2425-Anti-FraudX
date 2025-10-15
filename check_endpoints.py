#!/usr/bin/env python3
"""
檢查可用的 API 端點
"""

import requests
import json

def check_endpoint(url, method="GET", data=None):
    """檢查單個端點"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"{method} {url}")
        print(f"  狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"  回應: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
            except:
                print(f"  回應: {response.text[:200]}...")
        else:
            print(f"  錯誤: {response.text}")
        
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"  異常: {e}")
        print()
        return False

def main():
    """主函數"""
    print("檢查 AI-Agent API 端點")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 檢查基本端點
    endpoints = [
        ("/health", "GET"),
        ("/docs", "GET"),
        ("/api/v1/chat", "POST", {"query": "test", "session_id": "test"}),
        ("/api/v1/auth/register", "POST", {"email": "test@example.com", "password": "test123"}),
        ("/api/v1/media/analyze-text", "POST", {"text": "test", "session_id": "test"}),
        ("/api/v1/rag/stats", "GET"),
    ]
    
    results = []
    for endpoint in endpoints:
        if len(endpoint) == 2:
            url, method = endpoint
            data = None
        else:
            url, method, data = endpoint
        
        full_url = f"{base_url}{url}"
        success = check_endpoint(full_url, method, data)
        results.append((url, success))
    
    # 總結
    print("=" * 50)
    print("端點檢查結果:")
    print("=" * 50)
    
    for url, success in results:
        status = "✓ 可用" if success else "✗ 不可用"
        print(f"{url}: {status}")
    
    available = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n總計: {available}/{total} 端點可用")

if __name__ == "__main__":
    main()
