# RPG 開發工具 - 快速命令

## 🚀 快速啟動（清理並重啟）

```powershell
.\restart-dev.ps1
```

這個命令會：
1. 停止所有 Node 進程
2. 清理端口 3000-3010
3. 驗證端口已清空
4. 啟動開發服務器在端口 3000

---

## 🛑 快速停止

```powershell
.\stop-dev.ps1
```

這個命令會：
1. 停止所有 Node 進程
2. 清理所有相關端口
3. 確保完全清理

---

## 📝 使用說明

### 方法 1: 直接運行腳本
```powershell
cd C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2
.\restart-dev.ps1
```

### 方法 2: 從任何位置運行
```powershell
& "C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2\restart-dev.ps1"
```

### 方法 3: 創建快捷方式
1. 右鍵桌面 → 新建 → 快捷方式
2. 位置輸入：
   ```
   powershell.exe -ExecutionPolicy Bypass -File "C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2\restart-dev.ps1"
   ```
3. 命名為 "RPG Dev Server"
4. 雙擊即可啟動

---

## ⚠️ 如果遇到執行策略錯誤

運行以下命令（以管理員身份）：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

或者每次運行時使用：
```powershell
powershell -ExecutionPolicy Bypass -File .\restart-dev.ps1
```

---

## 🎯 常見問題

### Q: 端口仍然被佔用？
**A**: 運行兩次 `stop-dev.ps1`，然後再運行 `restart-dev.ps1`

### Q: 如何查看當前端口狀態？
**A**: 
```powershell
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
```

### Q: 如何手動清理特定端口？
**A**:
```powershell
# 查找佔用端口的進程
netstat -ano | findstr :3000

# 停止進程（替換 PID）
Stop-Process -Id PID -Force
```

---

## 📊 腳本功能對比

| 功能 | restart-dev.ps1 | stop-dev.ps1 | npm run dev |
|------|----------------|--------------|-------------|
| 停止進程 | ✅ | ✅ | ❌ |
| 清理端口 | ✅ | ✅ | ❌ |
| 驗證清理 | ✅ | ❌ | ❌ |
| 啟動服務器 | ✅ | ❌ | ✅ |
| 保證端口 3000 | ✅ | N/A | ❌ |

---

## 🎉 推薦工作流程

### 每天開始開發：
```powershell
.\restart-dev.ps1
```

### 結束開發：
```powershell
.\stop-dev.ps1
```

### 遇到問題時：
```powershell
.\stop-dev.ps1
Start-Sleep -Seconds 2
.\restart-dev.ps1
```

---

**版本**: 1.0.0  
**創建日期**: 2026-02-04  
**適用於**: Windows PowerShell 5.1+
