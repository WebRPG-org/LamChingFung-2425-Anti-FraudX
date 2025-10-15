#!/usr/bin/env python3
"""
AI-Agent 系統測試腳本
測試所有主要功能是否正常工作
"""

import requests
import json
import time
import os
from typing import Dict, Any

class SystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health_check(self) -> bool:
        """測試健康檢查端點"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✓ 健康檢查通過")
                return True
            else:
                print(f"✗ 健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 健康檢查錯誤: {e}")
            return False
    
    def test_auth_endpoints(self) -> bool:
        """測試認證端點"""
        try:
            # 測試註冊
            register_data = {
                "email": "test@example.com",
                "password": "testpassword",
                "display_name": "Test User",
                "elder_mode_enabled": True
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=register_data)
            if response.status_code == 200:
                print("✓ 用戶註冊成功")
                auth_data = response.json()
                self.session.headers.update({"Authorization": f"Bearer {auth_data['token']}"})
                return True
            else:
                print(f"✗ 用戶註冊失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 認證測試錯誤: {e}")
            return False
    
    def test_text_analysis(self) -> bool:
        """測試文字分析功能"""
        try:
            text_data = {
                "text": "這是一個測試訊息，請檢查是否有詐騙風險",
                "session_id": "test_session",
                "elder_mode": True
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/media/analyze-text", json=text_data)
            if response.status_code == 200:
                result = response.json()
                print("✓ 文字分析成功")
                print(f"   回應: {result.get('response', '')[:100]}...")
                print(f"   安全建議: {result.get('safety_suggestions', [])}")
                return True
            else:
                print(f"✗ 文字分析失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 文字分析錯誤: {e}")
            return False
    
    def test_upload_url_generation(self) -> bool:
        """測試上傳 URL 生成"""
        try:
            upload_data = {
                "file_type": "video",
                "file_extension": "webm",
                "user_id": "test_user"
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/media/get-signed-upload-url", json=upload_data)
            if response.status_code == 200:
                result = response.json()
                print("✓ 上傳 URL 生成成功")
                print(f"   文件 ID: {result.get('file_id')}")
                return True
            else:
                print(f"✗ 上傳 URL 生成失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 上傳 URL 測試錯誤: {e}")
            return False
    
    def test_elder_mode_settings(self) -> bool:
        """測試長者模式設置"""
        try:
            settings_data = {
                "enabled": True,
                "voice_enabled": True,
                "large_text": True,
                "high_contrast": True,
                "simplified_ui": True
            }
            
            response = self.session.put(f"{self.base_url}/api/v1/auth/elder-mode", json=settings_data)
            if response.status_code == 200:
                print("✓ 長者模式設置成功")
                return True
            else:
                print(f"✗ 長者模式設置失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 長者模式設置錯誤: {e}")
            return False
    
    def test_rag_system(self) -> bool:
        """測試 RAG 系統"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/rag/stats")
            if response.status_code == 200:
                stats = response.json()
                print("✓ RAG 系統正常")
                print(f"   統計: {stats.get('stats', {})}")
                return True
            else:
                print(f"✗ RAG 系統檢查失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ RAG 系統錯誤: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """運行所有測試"""
        print("開始 AI-Agent 系統測試...\n")
        
        tests = {
            "健康檢查": self.test_health_check,
            "認證系統": self.test_auth_endpoints,
            "文字分析": self.test_text_analysis,
            "上傳 URL": self.test_upload_url_generation,
            "長者模式": self.test_elder_mode_settings,
            "RAG 系統": self.test_rag_system
        }
        
        results = {}
        for test_name, test_func in tests.items():
            print(f"\n測試 {test_name}...")
            try:
                results[test_name] = test_func()
                time.sleep(1)  # 避免請求過於頻繁
            except Exception as e:
                print(f"✗ {test_name} 測試異常: {e}")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """打印測試摘要"""
        print("\n" + "="*50)
        print("📊 測試結果摘要")
        print("="*50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ 通過" if result else "✗ 失敗"
            print(f"{test_name}: {status}")
        
        print(f"\n總計: {passed}/{total} 測試通過")
        
        if passed == total:
            print("所有測試通過！系統運行正常。")
        else:
            print("部分測試失敗，請檢查系統配置。")

def main():
    """主函數"""
    print("AI-Agent 系統測試工具")
    print("=" * 50)
    
    # 檢查環境變量
    if not os.getenv("GOOGLE_API_KEY"):
        print("警告: 未設置 GOOGLE_API_KEY 環境變量")
        print("   某些功能可能無法正常工作")
    
    # 創建測試器
    tester = SystemTester()
    
    # 運行測試
    results = tester.run_all_tests()
    
    # 打印摘要
    tester.print_summary(results)

if __name__ == "__main__":
    main()
