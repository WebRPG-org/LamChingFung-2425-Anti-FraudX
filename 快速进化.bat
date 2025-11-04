@echo off
chcp 65001 >nul
title 军备竞赛系统 - 快速进化

echo ================================================
echo 🚀 军备竞赛系统 - 自动化进化流程
echo ================================================
echo.

echo 📌 当前工作目录: %CD%
cd AI-Agent
echo 📌 切换到: %CD%
echo.

echo ================================================
echo 请选择操作:
echo ================================================
echo [1] 完整进化流程 (分析 + 应用)
echo [2] 仅分析训练数据
echo [3] 仅应用进化知识
echo [4] 查看版本历史
echo [5] 运行A/B测试报告
echo [0] 退出
echo ================================================
echo.

set /p choice="请输入选项 (0-5): "

if "%choice%"=="1" goto full_evolution
if "%choice%"=="2" goto analyze_only
if "%choice%"=="3" goto apply_only
if "%choice%"=="4" goto view_versions
if "%choice%"=="5" goto ab_test
if "%choice%"=="0" goto end

:full_evolution
echo.
echo ================================================
echo 🔄 开始完整进化流程
echo ================================================
echo.

echo [步骤 1/2] 分析训练数据，生成进化策略...
python backend\scripts\arms_race_system.py
if errorlevel 1 (
    echo.
    echo ❌ 分析失败！请检查训练数据。
    pause
    goto end
)

echo.
echo ================================================
echo [步骤 2/2] 应用进化知识到Agent...
echo ================================================
python backend\scripts\automated_training.py
if errorlevel 1 (
    echo.
    echo ❌ 应用失败！请检查错误信息。
    pause
    goto end
)

echo.
echo ================================================
echo ✅ 进化完成！
echo ================================================
echo.
echo 📊 下一步:
echo   1. 运行 start_server.py 启动服务器
echo   2. 进行多轮模拟测试新版本
echo   3. 观察专家胜率变化
echo   4. 收集足够数据后再次运行进化
echo.
pause
goto end

:analyze_only
echo.
echo ================================================
echo 📊 仅分析训练数据
echo ================================================
python backend\scripts\arms_race_system.py
pause
goto end

:apply_only
echo.
echo ================================================
echo 🤖 仅应用进化知识
echo ================================================
python backend\scripts\automated_training.py
pause
goto end

:view_versions
echo.
echo ================================================
echo 📚 查看版本历史
echo ================================================
python backend\scripts\model_version_manager.py
pause
goto end

:ab_test
echo.
echo ================================================
echo 🧪 A/B测试报告
echo ================================================
echo 请在Python中使用 ABTestManager 生成报告
echo.
echo 示例:
echo   from scripts.model_version_manager import AgentVersionManager, ABTestManager
echo   ab_manager = ABTestManager(AgentVersionManager())
echo   ab_manager.generate_comparison_report('TEST_ID')
echo.
pause
goto end

:end
echo.
echo 按任意键退出...
pause >nul

