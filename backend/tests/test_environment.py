"""
環境檢查測試
"""

import sys
import os
import requests

# 設置 UTF-8 編碼輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_python_version():
    """檢查 Python 版本"""
    print("1. Python 版本檢查...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 10:
        print("   ✅ Python 版本符合要求 (>= 3.10)")
        return True
    else:
        print("   ❌ Python 版本過低，需要 >= 3.10")
        return False

def test_dependencies():
    """檢查依賴"""
    print("\n2. 依賴檢查...")
    
    required_packages = [
        ('fastapi', 'fastapi'),
        ('pydantic', 'pydantic'),
        ('google.adk', 'google-adk'),
        ('transformers', 'transformers'),
        ('chromadb', 'chromadb'),
        ('uvicorn', 'uvicorn')
    ]
    
    missing = []
    for package, pip_name in required_packages:
        try:
            __import__(package.split('.')[0])
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} 未安裝")
            missing.append(pip_name)
    
    if missing:
        print(f"\n   缺少依賴: {', '.join(missing)}")
        print("   運行: pip install -r backend/requirements.txt")
        return False
    
    return True

def test_ollama_service():
    """檢查 Ollama 服務"""
    print("\n3. Ollama 服務檢查...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("   ✅ Ollama 服務運行中")
            
            # 檢查模型
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            print(f"   已安裝模型: {len(models)} 個")
            
            # 檢查基礎模型
            required_models = ['gemma4:e4b']
            for model in required_models:
                if any(model in m for m in models):
                    print(f"   ✅ 模型 {model} 已安裝")
                else:
                    print(f"   ⚠️  模型 {model} 未安裝")
                    print(f"      運行: ollama pull {model}")
            
            # 檢查 fine-tuned 模型
            finetuned_models = [m for m in models if 'anti-fraud' in m]
            if finetuned_models:
                print(f"   ✅ Fine-tuned 模型: {len(finetuned_models)} 個")
                for m in finetuned_models[:3]:  # 只顯示前3個
                    print(f"      • {m}")
            
            return True
        else:
            print("   ❌ Ollama 服務響應異常")
            return False
    except Exception as e:
        print(f"   ❌ Ollama 服務未運行: {e}")
        print("   啟動: ollama serve")
        return False

def test_database():
    """檢查數據庫"""
    print("\n4. 數據庫檢查...")
    
    db_path = "anti_fraud_game.db"
    
    if os.path.exists(db_path):
        print(f"   ✅ 數據庫文件存在: {db_path}")
        print(f"   大小: {os.path.getsize(db_path)} bytes")
        
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"   表數量: {len(tables)}")
            
            required_tables = ['sessions', 'conversations']
            for table in required_tables:
                if table in tables:
                    # 統計記錄數
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ 表 {table}: {count} 條記錄")
                else:
                    print(f"   ⚠️  表 {table} 不存在（將自動創建）")
            
            conn.close()
            return True
        except Exception as e:
            print(f"   ❌ 數據庫連接失敗: {e}")
            return False
    else:
        print(f"   ℹ️  數據庫文件不存在（將自動創建）")
        return True

def test_backend_service():
    """檢查 Backend 服務"""
    print("\n5. Backend 服務檢查...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend 服務運行中")
            data = response.json()
            print(f"   模型: {data.get('model_in_use', 'N/A')}")
            print(f"   狀態: {data.get('status', 'N/A')}")
            
            # 檢查 v2 API
            try:
                v2_response = requests.get("http://localhost:8000/api/game/v2/health", timeout=3)
                if v2_response.status_code == 200:
                    v2_data = v2_response.json()
                    print(f"   ✅ V2 API 可用")
                    print(f"      版本: {v2_data.get('version', 'N/A')}")
                    features = v2_data.get('features', [])
                    if features:
                        print(f"      功能: {', '.join(features[:3])}...")
            except Exception:
                print(f"   ⚠️  V2 API 未響應")
            
            return True
        else:
            print("   ❌ Backend 服務響應異常")
            return False
    except Exception as e:
        print(f"   ❌ Backend 服務未運行: {e}")
        print("   啟動: python start_server.py")
        return False

def main():
    print("=" * 60)
    print("環境檢查測試")
    print("=" * 60)
    
    results = []
    
    results.append(("Python 版本", test_python_version()))
    results.append(("依賴安裝", test_dependencies()))
    results.append(("Ollama 服務", test_ollama_service()))
    results.append(("數據庫", test_database()))
    results.append(("Backend 服務", test_backend_service()))
    
    print("\n" + "=" * 60)
    print("測試結果匯總")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name:20s} {status}")
    
    all_passed = all(r for _, r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有檢查通過！可以開始測試 AgentService 和 V2 API")
        print("\n下一步:")
        print("  python backend/tests/test_agent_service.py")
    else:
        print("⚠️  部分檢查未通過，請修復後再繼續")
        print("\n常見問題:")
        print("  • Ollama 未運行: ollama serve")
        print("  • Backend 未運行: python start_server.py")
        print("  • 依賴缺失: pip install -r backend/requirements.txt")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

