@echo off
chcp 65001 > nul

echo ================================================================================
echo 設置 Windows 任務計劃器 - 自動更新數據
echo ================================================================================
echo.

echo [INFO] 此腳本將創建一個 Windows 任務計劃，每 3 天自動運行數據更新
echo.

REM 獲取當前腳本的完整路徑
set SCRIPT_DIR=%~dp0
set TASK_NAME=AI-Agentv4-DataUpdate
set PYTHON_SCRIPT=%SCRIPT_DIR%backend\scripts\auto_update_data.py

echo 任務名稱: %TASK_NAME%
echo Python 腳本: %PYTHON_SCRIPT%
echo.

set /p CONFIRM="確定要創建任務計劃嗎？(Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo [1/3] 檢查是否已存在同名任務...
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] 發現已存在的任務，正在刪除...
    schtasks /delete /tn "%TASK_NAME%" /f
)

echo.
echo [2/3] 創建新的任務計劃...
echo [INFO] 任務將在每天凌晨 2:00 檢查，每 3 天運行一次

REM 創建任務計劃 XML
set XML_FILE=%TEMP%\ai_agent_task.xml

(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>自動更新 AI-Agentv4 詐騙案例數據和 RAG 數據庫^</Description^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<CalendarTrigger^>
echo       ^<Repetition^>
echo         ^<Interval^>P3D^</Interval^>
echo       ^</Repetition^>
echo       ^<StartBoundary^>2026-01-01T02:00:00^</StartBoundary^>
echo       ^<Enabled^>true^</Enabled^>
echo       ^<ScheduleByDay^>
echo         ^<DaysInterval^>1^</DaysInterval^>
echo       ^</ScheduleByDay^>
echo     ^</CalendarTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal^>
echo       ^<LogonType^>InteractiveToken^</LogonType^>
echo       ^<RunLevel^>LeastPrivilege^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<RunOnlyIfNetworkAvailable^>true^</RunOnlyIfNetworkAvailable^>
echo     ^<IdleSettings^>
echo       ^<StopOnIdleEnd^>false^</StopOnIdleEnd^>
echo       ^<RestartOnIdle^>false^</RestartOnIdle^>
echo     ^</IdleSettings^>
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^>
echo     ^<WakeToRun^>false^</WakeToRun^>
echo     ^<ExecutionTimeLimit^>PT2H^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo   ^</Settings^>
echo   ^<Actions^>
echo     ^<Exec^>
echo       ^<Command^>py^</Command^>
echo       ^<Arguments^>"%PYTHON_SCRIPT%" --mode once^</Arguments^>
echo       ^<WorkingDirectory^>%SCRIPT_DIR%backend^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%XML_FILE%"

REM 導入任務
schtasks /create /tn "%TASK_NAME%" /xml "%XML_FILE%" /f

if %errorlevel% equ 0 (
    echo [OK] 任務計劃創建成功！
) else (
    echo [ERROR] 任務計劃創建失敗
    del "%XML_FILE%"
    pause
    exit /b 1
)

REM 清理臨時文件
del "%XML_FILE%"

echo.
echo [3/3] 驗證任務...
schtasks /query /tn "%TASK_NAME%" /fo LIST /v

echo.
echo ================================================================================
echo ✅ 設置完成！
echo ================================================================================
echo.
echo 任務詳情：
echo   - 任務名稱: %TASK_NAME%
echo   - 運行頻率: 每 3 天
echo   - 運行時間: 每天凌晨 2:00 檢查
echo   - 下次運行: 請查看上方的 "Next Run Time"
echo.
echo 管理命令：
echo   - 查看任務: schtasks /query /tn "%TASK_NAME%"
echo   - 立即運行: schtasks /run /tn "%TASK_NAME%"
echo   - 停用任務: schtasks /change /tn "%TASK_NAME%" /disable
echo   - 啟用任務: schtasks /change /tn "%TASK_NAME%" /enable
echo   - 刪除任務: schtasks /delete /tn "%TASK_NAME%" /f
echo.
echo 或使用 Windows 任務計劃器 GUI 管理：
echo   - 按 Win+R，輸入 taskschd.msc
echo   - 找到 "%TASK_NAME%"
echo.

pause
