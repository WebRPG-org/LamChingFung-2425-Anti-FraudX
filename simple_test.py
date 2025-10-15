#!/usr/bin/env python3
"""
簡化版 AI-Agent 系統測試腳本
"""

import requests
import json
import time
import os

def test_health_check():
    """測試健康檢查端點"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("健康檢查: 通過")
            return True
        else:
            print(f"健康檢查: 失敗 ({response.status_code})")
            return False
    except Exception as e:
        print(f"健康檢查: 錯誤 - {e}")
        return False

def test_auth_register():
    """測試用戶註冊"""
    try:
        data = {
            "email": "test@example.com",
            "password": "testpassword",
            "display_name": "Test User",
            "elder_mode_enabled": True
        }
        
        response = requests.post("http://localhost:8000/api/v1/auth/register", json=data)
        if response.status_code == 200:
            print("用戶註冊: 通過")
            return True
        else:
            print(f"用戶註冊: 失敗 ({response.status_code})")
            return False
    except Exception as e:
        print(f"用戶註冊: 錯誤 - {e}")
        return False

def test_text_analysis():
    """測試文字分析"""
    try:
        data = {
            "text": "這是一個測試訊息",
            "session_id": "test_session",
            "elder_mode": True
        }
        
        response = requests.post("http://localhost:8000/api/v1/media/analyze-text", json=data)
        if response.status_code == 200:
            print("文字分析: 通過")
            return True
        else:
            print(f"文字分析: 失敗 ({response.status_code})")
            return False
    except Exception as e:
        print(f"文字分析: 錯誤 - {e}")
        return False

def main():
    """主函數"""
    print("AI-Agent 系統測試")
    print("=" * 40)
    
    # 檢查環境變量
    if not os.getenv("GOOGLE_API_KEY"):
        print("警告: 未設置 GOOGLE_API_KEY 環境變量")
        print("某些功能可能無法正常工作")
    
    print("\n開始測試...")
    
    # 運行測試
    tests = [
        ("健康檢查", test_health_check),
        ("用戶註冊", test_auth_register),
        ("文字分析", test_text_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n測試 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)
        except Exception as e:
            print(f"{test_name}: 異常 - {e}")
            results.append((test_name, False))
    
    # 打印結果
    print("\n" + "=" * 40)
    print("測試結果摘要")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "通過" if result else "失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("所有測試通過！系統運行正常。")
    else:
        print("部分測試失敗，請檢查系統配置。")

if __name__ == "__main__":
    main()

