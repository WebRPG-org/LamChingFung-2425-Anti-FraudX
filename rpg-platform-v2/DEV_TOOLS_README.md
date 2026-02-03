# 🚀 開發工具使用指南

## 快速命令

### 方法 1: 雙擊批處理文件（最簡單）
- **重啟服務器**: 雙擊 `restart-dev.bat`
- **停止服務器**: 雙擊 `stop-dev.bat`

### 方法 2: PowerShell 命令
```powershell
# 重啟（清理並啟動）
.\restart-dev.ps1

# 停止
.\stop-dev.ps1
```

### 方法 3: 從任何位置運行
```powershell
# 重啟
& "C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2\restart-dev.bat"

# 停止
& "C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2\stop-dev.bat"
```

---

## ✅ 功能

### restart-dev.bat / restart-dev.ps1
1. 停止所有 Node 進程
2. 清理端口 3000-3010
3. 驗證端口已清空
4. 啟動開發服務器在端口 3000
5. **保證不會再看到 "Port 3000 is in use"**

### stop-dev.bat / stop-dev.ps1
1. 停止所有 Node 進程
2. 清理所有相關端口
3. 完全清理環境

---

## 🎯 推薦工作流程

**每天開始開發**:
```
雙擊 restart-dev.bat
```

**結束開發**:
```
雙擊 stop-dev.bat
```

**遇到端口問題**:
```
雙擊 restart-dev.bat
```

---

## 📝 說明

- `.bat` 文件可以直接雙擊運行
- `.ps1` 文件是 PowerShell 腳本（功能相同）
- 所有工具都會自動清理端口，確保乾淨啟動

---

**創建日期**: 2026-02-04  
**版本**: 1.0.0
