# AgentService 和 V2 API 測試指南

> 在實施新功能前，先驗證現有基礎功能正常工作

---

## 🎯 測試目標

### 驗證以下功能
1. ✅ `AgentService` 初始化和基本功能
2. ✅ 所有 4 個 Agent（Victim, Scammer, Expert, Recorder）
3. ✅ `/api/game/v2/*` 端點正常工作
4. ✅ 性能追踪和角色一致性檢查
5. ✅ RecorderAgent 最終評分

---

## 📋 測試清單

### Phase 1: 環境檢查 ✓

- [ ] Backend 服務運行中
- [ ] 所有依賴已安裝
- [ ] 數據庫文件存在
- [ ] Ollama 服務運行中
- [ ] 模型已安裝

### Phase 2: AgentService 單元測試

- [ ] 初始化測試
- [ ] 生成響應測試
- [ ] 性能追踪測試
- [ ] RecorderAgent 分析測試

### Phase 3: V2 API 集成測試

- [ ] 健康檢查
- [ ] 會話創建
- [ ] 消息發送
- [ ] 最終分析
- [ ] 會話查詢

---

## 🧪 測試腳本

### 1. 環境檢查腳本

創建文件: `backend/tests/test_environment.py`

```python
"""
環境檢查測試
"""

import sys
import os
import requests

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
        'fastapi',
        'pydantic',
        'google.adk',
        'transformers',
        'chromadb',
        'uvicorn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.split('.')[0])
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} 未安裝")
            missing.append(package)
    
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
            
            required_models = ['gemma3:4b']
            for model in required_models:
                if any(model in m for m in models):
                    print(f"   ✅ 模型 {model} 已安裝")
                else:
                    print(f"   ⚠️  模型 {model} 未安裝")
            
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
        
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['sessions', 'conversations']
            for table in required_tables:
                if table in tables:
                    print(f"   ✅ 表 {table} 存在")
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
    
    if all_passed:
        print("\n🎉 所有檢查通過！可以開始測試 AgentService 和 V2 API")
    else:
        print("\n⚠️  部分檢查未通過，請修復後再繼續")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

### 2. AgentService 單元測試

創建文件: `backend/tests/test_agent_service.py`

```python
"""
AgentService 單元測試
"""

import asyncio
import sys
import os

# 添加 backend 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_agent_service_init():
    """測試 AgentService 初始化"""
    print("\n" + "=" * 60)
    print("測試 1: AgentService 初始化")
    print("=" * 60)
    
    try:
        from services.agent_service import AgentService
        
        print("創建 AgentService 實例...")
        service = AgentService(persona_type="average", enable_tracking=True)
        
        # 檢查 Agent 是否初始化
        assert hasattr(service, 'victim'), "VictimAgent 未初始化"
        assert hasattr(service, 'scammer'), "ScammerAgent 未初始化"
        assert hasattr(service, 'expert'), "ExpertAgent 未初始化"
        assert hasattr(service, 'recorder'), "RecorderAgent 未初始化"
        
        print("✅ 所有 4 個 Agent 初始化成功")
        
        # 檢查追踪器
        if service.enable_tracking:
            assert hasattr(service, 'tracker'), "PerformanceTracker 未初始化"
            assert hasattr(service, 'enforcer'), "RoleEnforcer 未初始化"
            print("✅ 性能追踪器初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scammer_response():
    """測試 ScammerAgent 生成響應"""
    print("\n" + "=" * 60)
    print("測試 2: ScammerAgent 生成響應")
    print("=" * 60)
    
    try:
        from services.agent_service import AgentService
        
        service = AgentService(persona_type="average", enable_tracking=True)
        
        print("生成騙徒響應...")
        result = await service.generate_response(
            agent_type="scammer",
            message="你好，請問有什麼事？",
            conversation_history=[],
            check_consistency=True,
            track_performance=True
        )
        
        # 檢查響應
        assert result is not None, "響應為空"
        assert "reply" in result, "缺少 reply 字段"
        assert isinstance(result["reply"], str), "reply 不是字符串"
        assert len(result["reply"]) > 0, "reply 為空字符串"
        
        print(f"✅ 生成響應成功")
        print(f"   長度: {len(result['reply'])} 字元")
        print(f"   前100字: {result['reply'][:100]}...")
        
        # 檢查 metrics
        if result.get("metrics"):
            print(f"✅ 性能指標已生成")
            print(f"   Metrics: {result['metrics']}")
        
        # 檢查信任度
        if result.get("trust_in_scammer") is not None:
            print(f"✅ 信任度追踪正常")
            print(f"   對騙徒信任度: {result['trust_in_scammer']}")
        
        return True
    except Exception as e:
        print(f"❌ 生成響應失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_expert_response():
    """測試 ExpertAgent 生成響應"""
    print("\n" + "=" * 60)
    print("測試 3: ExpertAgent 生成響應")
    print("=" * 60)
    
    try:
        from services.agent_service import AgentService
        
        service = AgentService(persona_type="average", enable_tracking=True)
        
        print("生成專家響應...")
        result = await service.generate_response(
            agent_type="expert",
            message="有人打電話說我涉及洗錢，要我提供帳號",
            conversation_history=[],
            check_consistency=True,
            track_performance=True
        )
        
        assert result is not None
        assert "reply" in result
        assert len(result["reply"]) > 0
        
        print(f"✅ 生成響應成功")
        print(f"   長度: {len(result['reply'])} 字元")
        print(f"   前100字: {result['reply'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ 生成響應失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_recorder_analysis():
    """測試 RecorderAgent 最終分析"""
    print("\n" + "=" * 60)
    print("測試 4: RecorderAgent 最終分析")
    print("=" * 60)
    
    try:
        from services.agent_service import AgentService
        
        service = AgentService(persona_type="average", enable_tracking=True)
        
        # 模擬對話歷史
        conversation_history = [
            {"role": "scammer", "content": "你好，我是警察，你涉及洗錢案件"},
            {"role": "victim", "content": "什麼？我沒有做過這種事！"},
            {"role": "expert", "content": "這是典型的詐騙手法，真警察不會這樣打電話"},
            {"role": "victim", "content": "原來如此，謝謝提醒"}
        ]
        
        print("生成最終分析...")
        analysis = await service.generate_final_analysis(
            conversation_history=conversation_history,
            outcome_description="受害者識破詐騙"
        )
        
        assert analysis is not None, "分析結果為空"
        print(f"✅ 分析生成成功")
        
        # 檢查分析內容
        if "scammer_performance" in analysis:
            print(f"✅ 包含騙徒評分")
            print(f"   總分: {analysis['scammer_performance'].get('overall_score', 'N/A')}")
        
        if "expert_performance" in analysis:
            print(f"✅ 包含專家評分")
            print(f"   總分: {analysis['expert_performance'].get('overall_score', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 分析生成失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("AgentService 單元測試")
    print("=" * 60)
    
    results = []
    
    results.append(("初始化測試", await test_agent_service_init()))
    results.append(("Scammer 響應", await test_scammer_response()))
    results.append(("Expert 響應", await test_expert_response()))
    results.append(("Recorder 分析", await test_recorder_analysis()))
    
    print("\n" + "=" * 60)
    print("測試結果匯總")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name:20s} {status}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n🎉 所有 AgentService 測試通過！")
    else:
        print("\n⚠️  部分測試未通過")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

---

### 3. V2 API 集成測試

創建文件: `backend/tests/test_v2_api.py`

```python
"""
V2 API 集成測試
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_health_check():
    """測試健康檢查"""
    print("\n" + "=" * 60)
    print("測試 1: 健康檢查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/game/v2/health")
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["status"] == "ok", "狀態不正常"
        assert "version" in data, "缺少 version 字段"
        assert "features" in data, "缺少 features 字段"
        
        print(f"✅ 健康檢查通過")
        print(f"   版本: {data['version']}")
        print(f"   功能: {', '.join(data['features'])}")
        
        return True
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

def test_create_session():
    """測試創建會話"""
    print("\n" + "=" * 60)
    print("測試 2: 創建會話")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/game/v2/start",
            json={"persona_type": "A"}
        )
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["success"] is True, "創建失敗"
        assert "session_id" in data, "缺少 session_id"
        assert "persona" in data, "缺少 persona"
        
        session_id = data["session_id"]
        
        print(f"✅ 會話創建成功")
        print(f"   Session ID: {session_id}")
        print(f"   Persona: {data['persona']['name']}")
        
        return session_id
    except Exception as e:
        print(f"❌ 創建會話失敗: {e}")
        return None

def test_send_message(session_id):
    """測試發送消息"""
    print("\n" + "=" * 60)
    print("測試 3: 發送消息")
    print("=" * 60)
    
    try:
        # 發送給騙徒
        response = requests.post(
            f"{API_BASE}/api/game/v2/message",
            json={
                "session_id": session_id,
                "message": "你好，請問有什麼事？",
                "target_ai": "AI-D",
                "persona_type": "A"
            }
        )
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["success"] is True, "發送失敗"
        assert "reply" in data, "缺少 reply"
        
        print(f"✅ 消息發送成功")
        print(f"   AI 回覆: {data['reply'][:100]}...")
        
        # 檢查新增字段
        if "trust_in_scammer" in data:
            print(f"   對騙徒信任度: {data['trust_in_scammer']}")
        
        if "trust_in_expert" in data:
            print(f"   對專家信任度: {data['trust_in_expert']}")
        
        if "metrics" in data:
            print(f"   性能指標: 已返回")
        
        return True
    except Exception as e:
        print(f"❌ 發送消息失敗: {e}")
        return False

def test_analyze_session(session_id):
    """測試會話分析"""
    print("\n" + "=" * 60)
    print("測試 4: 會話分析 (RecorderAgent)")
    print("=" * 60)
    
    try:
        # 先發送幾條消息製造對話
        messages = [
            ("AI-D", "你好，我是警察"),
            ("AI-C", "這可能是詐騙"),
            ("AI-D", "請提供你的帳號")
        ]
        
        for target_ai, message in messages:
            requests.post(
                f"{API_BASE}/api/game/v2/message",
                json={
                    "session_id": session_id,
                    "message": message,
                    "target_ai": target_ai,
                    "persona_type": "A"
                }
            )
            time.sleep(1)  # 避免請求過快
        
        # 請求分析
        print("請求 RecorderAgent 分析...")
        response = requests.post(
            f"{API_BASE}/api/game/v2/analyze",
            json={"session_id": session_id}
        )
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["success"] is True, "分析失敗"
        assert "analysis" in data, "缺少 analysis"
        
        analysis = data["analysis"]
        
        print(f"✅ 分析生成成功")
        print(f"   對話數: {data.get('conversation_count', 0)}")
        
        if "scammer_performance" in analysis:
            sp = analysis["scammer_performance"]
            print(f"   騙徒總分: {sp.get('overall_score', 'N/A')}")
        
        if "expert_performance" in analysis:
            ep = analysis["expert_performance"]
            print(f"   專家總分: {ep.get('overall_score', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 會話分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_session(session_id):
    """測試獲取會話"""
    print("\n" + "=" * 60)
    print("測試 5: 獲取會話信息")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/game/v2/session/{session_id}")
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert "session_id" in data, "缺少 session_id"
        assert "conversations" in data, "缺少 conversations"
        
        print(f"✅ 獲取會話成功")
        print(f"   對話數: {len(data['conversations'])}")
        print(f"   狀態: {data.get('status', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 獲取會話失敗: {e}")
        return False

def main():
    print("=" * 60)
    print("V2 API 集成測試")
    print("=" * 60)
    
    results = []
    
    # 健康檢查
    health_ok = test_health_check()
    results.append(("健康檢查", health_ok))
    
    if not health_ok:
        print("\n⚠️  健康檢查失敗，停止測試")
        return False
    
    # 創建會話
    session_id = test_create_session()
    results.append(("創建會話", session_id is not None))
    
    if session_id:
        # 發送消息
        results.append(("發送消息", test_send_message(session_id)))
        
        # 會話分析
        results.append(("會話分析", test_analyze_session(session_id)))
        
        # 獲取會話
        results.append(("獲取會話", test_get_session(session_id)))
    
    print("\n" + "=" * 60)
    print("測試結果匯總")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name:20s} {status}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n🎉 所有 V2 API 測試通過！")
        print("\n✅ 可以開始實施新功能：")
        print("   - 數據分類系統")
        print("   - 可視化訓練界面")
        print("   - 玩家互動模式")
    else:
        print("\n⚠️  部分測試未通過，請先修復問題")
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
```

---

## 🚀 運行測試

### 快速測試（按順序執行）

```bash
# 1. 環境檢查
cd backend
python tests/test_environment.py

# 2. AgentService 測試
python tests/test_agent_service.py

# 3. V2 API 測試
python tests/test_v2_api.py
```

### 一鍵測試腳本

創建文件: `run_all_tests.bat`

```batch
@echo off
chcp 65001 > nul

echo ========================================
echo 完整測試流程
echo ========================================
echo.

echo [1/3] 環境檢查...
python backend\tests\test_environment.py
if %errorlevel% neq 0 (
    echo 環境檢查失敗，停止測試
    pause
    exit /b 1
)

echo.
echo [2/3] AgentService 單元測試...
python backend\tests\test_agent_service.py
if %errorlevel% neq 0 (
    echo AgentService 測試失敗
    pause
    exit /b 1
)

echo.
echo [3/3] V2 API 集成測試...
python backend\tests\test_v2_api.py
if %errorlevel% neq 0 (
    echo V2 API 測試失敗
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 所有測試通過！
echo ========================================
echo.
echo 可以開始實施新功能：
echo   - 數據分類系統
echo   - 可視化訓練界面
echo   - 玩家互動模式
echo.
pause
```

---

## 📋 預期輸出

### 成功的測試輸出示例

```
============================================================
環境檢查測試
============================================================
1. Python 版本檢查...
   Python 3.11.0
   ✅ Python 版本符合要求 (>= 3.10)

2. 依賴檢查...
   ✅ fastapi
   ✅ pydantic
   ✅ google.adk
   ✅ transformers
   ✅ chromadb
   ✅ uvicorn

3. Ollama 服務檢查...
   ✅ Ollama 服務運行中
   ✅ 模型 gemma3:4b 已安裝

4. 數據庫檢查...
   ✅ 數據庫文件存在: anti_fraud_game.db
   ✅ 表 sessions 存在
   ✅ 表 conversations 存在

5. Backend 服務檢查...
   ✅ Backend 服務運行中
   模型: gemma3:4b

============================================================
測試結果匯總
============================================================
Python 版本          ✅ 通過
依賴安裝            ✅ 通過
Ollama 服務         ✅ 通過
數據庫              ✅ 通過
Backend 服務        ✅ 通過

🎉 所有檢查通過！可以開始測試 AgentService 和 V2 API
```

---

## 🐛 常見問題和解決方案

### 問題 1: Ollama 服務未運行

```
❌ Ollama 服務未運行: Connection refused
   啟動: ollama serve
```

**解決**:
```bash
# 啟動 Ollama
ollama serve

# 或者在 本地启动.bat 中已包含
```

### 問題 2: 模型未安裝

```
⚠️  模型 gemma3:4b 未安裝
```

**解決**:
```bash
ollama pull gemma3:4b
```

### 問題 3: Backend 服務未運行

```
❌ Backend 服務未運行: Connection refused
   啟動: python start_server.py
```

**解決**:
```bash
python start_server.py
```

### 問題 4: 依賴缺失

```
❌ google.adk 未安裝
   缺少依賴: google.adk
   運行: pip install -r backend/requirements.txt
```

**解決**:
```bash
pip install -r backend/requirements.txt
```

---

## ✅ 測試通過後

如果所有測試都通過，您可以安全地繼續：

1. ✅ 實施數據分類系統
   ```bash
   python backend/scripts/migrate_add_data_classification.py
   ```

2. ✅ 修改 game_routes_v2.py 添加數據標記

3. ✅ 創建 RPG Maker 可視化界面

4. ✅ 實施自動訓練系統

---

## 📊 測試報告模板

```
測試日期: 2025-11-11
測試人員: [姓名]
環境: Windows 10, Python 3.11

環境檢查:
  [✅] Python 版本
  [✅] 依賴安裝
  [✅] Ollama 服務
  [✅] 數據庫
  [✅] Backend 服務

AgentService:
  [✅] 初始化
  [✅] Scammer 響應
  [✅] Expert 響應
  [✅] Recorder 分析

V2 API:
  [✅] 健康檢查
  [✅] 創建會話
  [✅] 發送消息
  [✅] 會話分析
  [✅] 獲取會話

總結: 所有測試通過，可以開始實施新功能
```

---

**最後更新**: 2025-11-11  
**狀態**: ✅ 測試腳本已準備，可立即使用

