"""
測試主要 API 端點
"""
import pytest
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_server_is_running():
    """測試服務器是否正在運行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        print("✅ 服務器正在運行")
    except requests.exceptions.ConnectionError:
        pytest.fail("❌ 無法連接到服務器，請確保服務器正在運行")

def test_health_endpoint():
    """測試 /health 端點"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "Backend is running"
    assert "model_in_use" in data
    
    print(f"✅ Health check 通過")
    print(f"   模型: {data['model_in_use']}")

def test_test_endpoint():
    """測試 /test 端點（HTML 頁面）"""
    response = requests.get(f"{BASE_URL}/test")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "插件測試" in response.text or "RotatingScamSystem" in response.text
    
    print(f"✅ Test endpoint (HTML) 通過")
    print(f"   返回類型: HTML 測試頁面")

def test_test_json_endpoint():
    """測試 /test/json 端點（JSON API）"""
    response = requests.get(f"{BASE_URL}/test/json")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data
    assert "timestamp" in data
    assert "server_info" in data
    assert "available_routes" in data
    
    # 驗證 server_info
    server_info = data["server_info"]
    assert "model" in server_info
    assert "version" in server_info
    assert "environment" in server_info
    
    # 驗證 available_routes
    routes = data["available_routes"]
    assert "health" in routes
    assert "docs" in routes
    assert "test_page" in routes
    assert "test_json" in routes
    
    print(f"✅ Test JSON endpoint 通過")
    print(f"   消息: {data['message']}")
    print(f"   版本: {server_info['version']}")
    print(f"   環境: {server_info['environment']}")

def test_root_endpoint():
    """測試 / 根端點"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    print("✅ 根端點通過")

def test_app_endpoint():
    """測試 /app 端點（AI-Agent v2.5 自動模擬頁面）"""
    response = requests.get(f"{BASE_URL}/app")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "AI-Agent v2.5" in response.text or "自動模擬" in response.text or "startSimulation" in response.text
    
    print(f"✅ App endpoint (自動模擬頁面) 通過")
    print(f"   返回類型: HTML 自動模擬界面")

def test_docs_endpoint():
    """測試 /docs API 文檔端點"""
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    print("✅ API 文檔端點通過")

def test_game_info_endpoint():
    """測試 /api/game/info 端點"""
    response = requests.get(f"{BASE_URL}/api/game/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "features" in data
    assert "endpoints" in data
    
    print(f"✅ Game API info 通過")
    print(f"   名稱: {data['name']}")
    print(f"   版本: {data['version']}")

def test_game_tactics_endpoint():
    """測試 /api/game/simulation/tactics 端點"""
    response = requests.get(f"{BASE_URL}/api/game/simulation/tactics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] == True
    assert "tactics" in data
    assert len(data["tactics"]) > 0
    
    print(f"✅ 詐騙手法列表通過")
    print(f"   可用手法數量: {len(data['tactics'])}")

def test_game_personas_endpoint():
    """測試 /api/game/simulation/personas 端點"""
    response = requests.get(f"{BASE_URL}/api/game/simulation/personas")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] == True
    assert "personas" in data
    assert "display_names" in data
    assert len(data["personas"]) > 0
    
    print(f"✅ 受害者類型列表通過")
    print(f"   可用類型數量: {len(data['personas'])}")

def test_game_health_endpoint():
    """測試 /api/game/health 端點"""
    response = requests.get(f"{BASE_URL}/api/game/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "game_api" in data
    
    print(f"✅ Game API health 通過")
    print(f"   狀態: {data['status']}")
    print(f"   Game API: {data['game_api']}")
    print(f"   Simulation API: {data.get('simulation_api', 'unknown')}")
    print(f"   Ollama: {data.get('ollama', 'unknown')}")

def test_404_endpoint():
    """測試不存在的端點應該返回 404"""
    response = requests.get(f"{BASE_URL}/nonexistent")
    assert response.status_code == 404
    print("✅ 404 錯誤處理正確")

if __name__ == "__main__":
    print("=" * 80)
    print("開始測試主要 API 端點")
    print("=" * 80)
    print()
    
    # 運行所有測試
    test_server_is_running()
    print()
    
    test_health_endpoint()
    print()
    
    test_test_endpoint()
    print()
    
    test_test_json_endpoint()
    print()
    
    test_root_endpoint()
    print()
    
    test_app_endpoint()
    print()
    
    test_docs_endpoint()
    print()
    
    test_game_info_endpoint()
    print()
    
    test_game_tactics_endpoint()
    print()
    
    test_game_personas_endpoint()
    print()
    
    test_game_health_endpoint()
    print()
    
    test_404_endpoint()
    print()
    
    print("=" * 80)
    print("✅ 所有測試通過！")
    print("=" * 80)
