# 測試指南

## 📋 測試文件列表

```
backend/tests/
├── __init__.py
├── test_main_endpoints.py ⭐ 新增！主要端點測試
├── test_agent_service.py
├── test_environment.py
├── test_finetuning_save.py
├── test_ollama_connection.py
├── test_ollama_direct.py
├── test_personal_chat.py
├── test_rpg_api.py
├── test_v2_api.py
└── test_vision.py
```

---

## 🚀 運行測試

### **方法 1：運行單個測試文件**

```bash
# 測試主要端點（包括 /test）
cd c:\Users\fungr\Documents\AI-Agentv4\backend
python tests\test_main_endpoints.py
```

### **方法 2：使用 pytest 運行所有測試**

```bash
# 安裝 pytest（如果還沒安裝）
pip install pytest requests

# 運行所有測試
cd c:\Users\fungr\Documents\AI-Agentv4\backend
pytest tests/ -v

# 運行特定測試文件
pytest tests/test_main_endpoints.py -v

# 運行特定測試函數
pytest tests/test_main_endpoints.py::test_test_endpoint -v
```

### **方法 3：運行特定測試**

```bash
# 只測試 /test 端點
cd c:\Users\fungr\Documents\AI-Agentv4\backend
python -c "from tests.test_main_endpoints import test_test_endpoint; test_test_endpoint()"
```

---

## 📊 測試覆蓋範圍

### **test_main_endpoints.py** - 主要端點測試

| 測試函數 | 測試內容 | 端點 |
|---------|---------|------|
| `test_server_is_running()` | 服務器是否運行 | `/health` |
| `test_health_endpoint()` | 健康檢查 | `/health` |
| `test_test_endpoint()` | 測試端點 | `/test` ⭐ |
| `test_root_endpoint()` | 根端點 | `/` |
| `test_docs_endpoint()` | API 文檔 | `/docs` |
| `test_game_info_endpoint()` | 遊戲 API 信息 | `/api/game/info` |
| `test_game_tactics_endpoint()` | 詐騙手法列表 | `/api/game/simulation/tactics` |
| `test_game_personas_endpoint()` | 受害者類型列表 | `/api/game/simulation/personas` |
| `test_game_health_endpoint()` | 遊戲 API 健康檢查 | `/api/game/health` |
| `test_404_endpoint()` | 404 錯誤處理 | `/nonexistent` |

---

## ✅ 預期輸出

運行 `python tests\test_main_endpoints.py` 應該看到：

```
================================================================================
開始測試主要 API 端點
================================================================================

✅ 服務器正在運行

✅ Health check 通過
   模型: gemma3:4b

✅ Test endpoint 通過
   消息: Test endpoint is working! 🎉
   版本: 2.0.0
   環境: development

✅ 根端點通過

✅ API 文檔端點通過

✅ Game API info 通過
   名稱: Anti-Fraud Game API
   版本: 2.0.0

✅ 詐騙手法列表通過
   可用手法數量: 10

✅ 受害者類型列表通過
   可用類型數量: 4

✅ Game API health 通過
   狀態: ok
   Game API: ok
   Simulation API: ok
   Ollama: running

✅ 404 錯誤處理正確

================================================================================
✅ 所有測試通過！
================================================================================
```

---

## 🔧 故障排除

### **問題 1：ConnectionError**
```
❌ 無法連接到服務器，請確保服務器正在運行
```

**解決方法**：
```bash
# 啟動服務器
cd c:\Users\fungr\Documents\AI-Agentv4
python scripts\start_server.py
```

### **問題 2：404 Not Found on /test**
```
AssertionError: assert 404 == 200
```

**解決方法**：
1. 確認 `backend/main.py` 包含 `/test` 端點
2. 重啟服務器
3. 清除 Python 緩存：
   ```bash
   cd c:\Users\fungr\Documents\AI-Agentv4\backend
   del /s /q __pycache__
   ```

### **問題 3：ModuleNotFoundError**
```
ModuleNotFoundError: No module named 'requests'
```

**解決方法**：
```bash
pip install requests pytest
```

---

## 📝 快速測試命令

### **測試 /test 端點是否工作**
```bash
# 方法 1：使用 curl
curl http://127.0.0.1:8000/test

# 方法 2：使用 Python
python -c "import requests; print(requests.get('http://127.0.0.1:8000/test').json())"

# 方法 3：使用測試文件
cd c:\Users\fungr\Documents\AI-Agentv4\backend
python tests\test_main_endpoints.py
```

### **測試所有端點**
```bash
cd c:\Users\fungr\Documents\AI-Agentv4\backend
pytest tests/test_main_endpoints.py -v
```

---

## 🎯 持續集成（CI）

如果您使用 CI/CD，可以添加到 GitHub Actions：

```yaml
# .github/workflows/test.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest requests
      - name: Run tests
        run: |
          cd backend
          pytest tests/test_main_endpoints.py -v
```

---

## 📚 相關文檔

- **API Routes**: `docs/API_ROUTES.md`
- **Database Design**: `docs/DATABASE_DESIGN.md`
- **Metadata Dictionary**: `docs/METADATA_DICTIONARY.md`

---

**最後更新**: 2026-01-11  
**測試框架**: pytest  
**Python 版本**: 3.10+
