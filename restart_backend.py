#!/usr/bin/env python3
"""
重啟後端服務腳本
"""

import subprocess
import time
import requests
import sys

def kill_backend_processes():
    """終止現有的後端進程"""
    try:
        # 在 Windows 上查找並終止 uvicorn 進程
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            print("發現 Python 進程，嘗試終止...")
            # 終止所有 Python 進程（謹慎使用）
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                          capture_output=True)
            time.sleep(2)
            print("已終止現有進程")
    except Exception as e:
        print(f"終止進程時出錯: {e}")

def start_backend():
    """啟動後端服務"""
    try:
        print("啟動後端服務...")
        # 啟動後端服務
        process = subprocess.Popen([
            'python', '-m', 'uvicorn', 'app.main:app', 
            '--reload', '--host', '0.0.0.0', '--port', '8000'
        ], cwd='backend')
        
        # 等待服務啟動
        print("等待服務啟動...")
        time.sleep(5)
        
        # 檢查服務是否啟動
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            if response.status_code == 200:
                print("✓ 後端服務啟動成功")
                return process
            else:
                print(f"✗ 後端服務啟動失敗: {response.status_code}")
                return None
        except requests.exceptions.RequestException:
            print("✗ 無法連接到後端服務")
            return None
            
    except Exception as e:
        print(f"啟動後端服務時出錯: {e}")
        return None

def test_new_endpoints():
    """測試新的端點"""
    print("\n測試新的 API 端點...")
    
    endpoints = [
        ("/api/v1/auth/register", "POST", {"email": "test@example.com", "password": "test123"}),
        ("/api/v1/media/analyze-text", "POST", {"text": "test", "session_id": "test"})
    ]
    
    for endpoint, method, data in endpoints:
        try:
            if method == "POST":
                response = requests.post(f"http://localhost:8000{endpoint}", json=data)
            
            if response.status_code == 200:
                print(f"✓ {endpoint}: 可用")
            else:
                print(f"✗ {endpoint}: 不可用 ({response.status_code})")
        except Exception as e:
            print(f"✗ {endpoint}: 錯誤 - {e}")

def main():
    """主函數"""
    print("AI-Agent 後端重啟工具")
    print("=" * 40)
    
    # 終止現有進程
    kill_backend_processes()
    
    # 啟動新服務
    process = start_backend()
    
    if process:
        # 測試新端點
        test_new_endpoints()
        
        print("\n後端服務已重啟，新的 API 端點應該現在可用。")
        print("按 Ctrl+C 停止服務")
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n停止服務...")
            process.terminate()
    else:
        print("無法啟動後端服務")
        sys.exit(1)

if __name__ == "__main__":
    main()
