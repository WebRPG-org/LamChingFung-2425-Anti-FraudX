# 🧹 啟動腳本清理報告

## 清理日期
2026-02-12

## 清理目標
刪除重複的啟動/停止/重啟腳本，統一使用 `quick_start.bat` 和 `quick_start_gemini.bat`

---

## ✅ 已刪除的文件

### 根目錄重複啟動腳本
- ❌ `start_services.bat` - 與 quick_start.bat 功能重複
- ❌ `start_all.bat` - 與 quick_start.bat 功能重複
- ❌ `啟動.bat` - 與 quick_start.bat 功能重複
- ❌ `run.bat` - 與 quick_start.bat 功能重複

### 根目錄重複停止/重啟腳本
- ❌ `stop_services.bat` - 功能已整合到 quick_start.bat
- ❌ `restart_backend.bat` - 功能已整合到 quick_start.bat
- ❌ `check_services.bat` - 功能已整合到 quick_start.bat

### scripts/ 文件夾舊版本
- ❌ `scripts/本地啟動.bat` - 舊版本
- ❌ `scripts/停止服務.bat` - 舊版本
- ❌ `scripts/start_all.bat` - 舊版本
- ❌ `scripts/start_backend.bat` - 舊版本
- ❌ `scripts/start_rpg.bat` - 舊版本
- ❌ `scripts/quick_start.bat` - 舊版本

**總計刪除**: 13 個重複文件

---

## ✅ 保留的文件

### 主要啟動腳本
- ✅ `quick_start.bat` - **主要啟動腳本**（支持 Ollama 和 Gemini）
- ✅ `quick_start_gemini.bat` - **Gemini 專用啟動腳本**

### 測試和實驗腳本
- ✅ `test_encoding.bat` - 編碼測試
- ✅ `test_rpg_start.bat` - RPG 啟動測試
- ✅ `run_phase2_tests.bat` - Phase 2 測試
- ✅ `run_victim_eval_experiment.bat` - 受害人評分實驗
- ✅ `run_victim_scoring_experiment.bat` - 受害人評分實驗

### 工具腳本
- ✅ `validate_integration.bat` - 系統整合驗證
- ✅ `view_logs.bat` - 日誌查看工具

### 子目錄腳本
- ✅ `rpg-platform-v2/stop-dev.bat` - RPG 專用停止腳本
- ✅ `rpg-platform-v2/restart-dev.bat` - RPG 專用重啟腳本
- ✅ `ansible/deploy.bat` - 部署腳本

---

## 📋 使用指南

### 日常使用

#### 啟動服務（Ollama 模式）
```bash
.\quick_start.bat
```

#### 啟動服務（Gemini 模式）
```bash
.\quick_start_gemini.bat
```

#### 停止服務
在 `quick_start.bat` 啟動後，按任意鍵查看狀態，然後關閉窗口即可。
或者使用任務管理器結束 Python 和 Node 進程。

### 測試和開發

#### 運行 Phase 2 測試
```bash
.\run_phase2_tests.bat
```

#### 運行受害人評分實驗
```bash
.\run_victim_scoring_experiment.bat
```

#### 驗證系統整合
```bash
.\validate_integration.bat
```

#### 查看日誌
```bash
.\view_logs.bat
```

---

## 🎯 清理效果

### 之前
- 13 個重複的啟動/停止腳本
- 功能分散，容易混淆
- 維護困難

### 之後
- 2 個主要啟動腳本（清晰明確）
- 功能統一，易於使用
- 維護簡單

---

## 📝 腳本功能對比

| 功能 | 舊腳本 | 新腳本 |
|------|--------|--------|
| 啟動 Ollama 模式 | start_services.bat, start_all.bat, 啟動.bat, run.bat | **quick_start.bat** |
| 啟動 Gemini 模式 | 無 | **quick_start_gemini.bat** |
| 停止服務 | stop_services.bat | 整合到 quick_start.bat |
| 重啟後端 | restart_backend.bat | 整合到 quick_start.bat |
| 檢查狀態 | check_services.bat | 整合到 quick_start.bat |
| 自動創建精簡數據 | 無 | ✨ 新增功能 |
| 自動上傳 Gemini 文件 | 無 | ✨ 新增功能 |

---

## 🚀 新增功能

### quick_start.bat 增強
1. **自動檢測精簡數據** - 如不存在自動創建
2. **LLM 提供者檢測** - 自動檢測 Ollama 或 Gemini
3. **服務狀態檢查** - 啟動後自動驗證
4. **統一的步驟顯示** - 1/5 到 5/5

### quick_start_gemini.bat 增強
1. **API Key 驗證** - 啟動前檢查配置
2. **自動文件上傳** - 初始化 Gemini 文件
3. **精簡數據支持** - 減少 90% token 使用
4. **詳細的狀態報告** - 顯示優化效果

---

## 📚 相關文檔

- [快速啟動指南](QUICK_START_GUIDE.md)
- [Gemini 配額優化](GEMINI_QUOTA_OPTIMIZATION.md)
- [Gemini 快速參考](GEMINI_QUICK_REFERENCE.md)

---

**清理完成！** 🎉

現在項目結構更清晰，使用更簡單！
