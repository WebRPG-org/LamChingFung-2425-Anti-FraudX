@echo off
chcp 65001 >nul
title Docker管理 - AI反诈骗训练平台

echo ================================================
echo 🐳 Docker管理 - AI反诈骗训练平台
echo ================================================
echo.

:menu
echo ================================================
echo 请选择操作:
echo ================================================
echo [开发环境]
echo   1. 启动开发环境
echo   2. 停止开发环境
echo   3. 重启开发环境
echo   4. 查看开发环境日志
echo.
echo [生产环境]
echo   5. 启动生产环境
echo   6. 停止生产环境
echo   7. 重启生产环境
echo   8. 查看生产环境日志
echo.
echo [构建和维护]
echo   9. 构建镜像(开发)
echo  10. 构建镜像(生产)
echo  11. 清理未使用的镜像
echo  12. 查看容器状态
echo  13. 进入backend容器
echo  14. 进入ollama容器
echo.
echo [数据管理]
echo  15. 备份所有数据卷
echo  16. 查看数据卷使用情况
echo  17. 清理所有数据(危险!)
echo.
echo   0. 退出
echo ================================================
echo.

set /p choice="请输入选项 (0-17): "

if "%choice%"=="1" goto dev_up
if "%choice%"=="2" goto dev_down
if "%choice%"=="3" goto dev_restart
if "%choice%"=="4" goto dev_logs
if "%choice%"=="5" goto prod_up
if "%choice%"=="6" goto prod_down
if "%choice%"=="7" goto prod_restart
if "%choice%"=="8" goto prod_logs
if "%choice%"=="9" goto build_dev
if "%choice%"=="10" goto build_prod
if "%choice%"=="11" goto cleanup
if "%choice%"=="12" goto status
if "%choice%"=="13" goto exec_backend
if "%choice%"=="14" goto exec_ollama
if "%choice%"=="15" goto backup
if "%choice%"=="16" goto volumes
if "%choice%"=="17" goto danger_cleanup
if "%choice%"=="0" goto end

echo.
echo ❌ 无效选项，请重新选择
echo.
timeout /t 2 >nul
cls
goto menu

:dev_up
echo.
echo ================================================
echo 🚀 启动开发环境
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
echo.
echo ✅ 开发环境已启动
echo    访问地址: http://localhost:8000
echo.
pause
cls
goto menu

:dev_down
echo.
echo ================================================
echo 🛑 停止开发环境
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
echo.
echo ✅ 开发环境已停止
echo.
pause
cls
goto menu

:dev_restart
echo.
echo ================================================
echo 🔄 重启开发环境
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart
echo.
echo ✅ 开发环境已重启
echo.
pause
cls
goto menu

:dev_logs
echo.
echo ================================================
echo 📋 查看开发环境日志 (Ctrl+C退出)
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f --tail=100
pause
cls
goto menu

:prod_up
echo.
echo ================================================
echo 🚀 启动生产环境
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
echo.
echo ✅ 生产环境已启动
echo    访问地址: http://localhost:8000
echo.
pause
cls
goto menu

:prod_down
echo.
echo ================================================
echo 🛑 停止生产环境
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
echo.
echo ✅ 生产环境已停止
echo.
pause
cls
goto menu

:prod_restart
echo.
echo ================================================
echo 🔄 重启生产环境
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart
echo.
echo ✅ 生产环境已重启
echo.
pause
cls
goto menu

:prod_logs
echo.
echo ================================================
echo 📋 查看生产环境日志 (Ctrl+C退出)
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=100
pause
cls
goto menu

:build_dev
echo.
echo ================================================
echo 🔨 构建开发镜像
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
echo.
echo ✅ 开发镜像构建完成
echo.
pause
cls
goto menu

:build_prod
echo.
echo ================================================
echo 🔨 构建生产镜像
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
echo.
echo ✅ 生产镜像构建完成
echo.
pause
cls
goto menu

:cleanup
echo.
echo ================================================
echo 🧹 清理未使用的Docker镜像
echo ================================================
docker image prune -f
docker builder prune -f
echo.
echo ✅ 清理完成
echo.
pause
cls
goto menu

:status
echo.
echo ================================================
echo 📊 容器状态
echo ================================================
docker-compose ps
echo.
echo ================================================
echo 📈 资源使用情况
echo ================================================
docker stats --no-stream
echo.
pause
cls
goto menu

:exec_backend
echo.
echo ================================================
echo 🔧 进入Backend容器
echo ================================================
docker exec -it ai-antiscam-backend /bin/bash
cls
goto menu

:exec_ollama
echo.
echo ================================================
echo 🔧 进入Ollama容器
echo ================================================
docker exec -it ai-antiscam-ollama /bin/bash
cls
goto menu

:backup
echo.
echo ================================================
echo 💾 备份所有数据卷
echo ================================================
set backup_dir=docker_backups_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set backup_dir=%backup_dir: =0%
mkdir %backup_dir% 2>nul

echo 正在备份数据卷...
docker run --rm -v ai-antiscam-training-data:/data -v %cd%/%backup_dir%:/backup alpine tar czf /backup/training_data.tar.gz -C /data .
docker run --rm -v ai-antiscam-models:/data -v %cd%/%backup_dir%:/backup alpine tar czf /backup/models.tar.gz -C /data .
docker run --rm -v ai-antiscam-db:/data -v %cd%/%backup_dir%:/backup alpine tar czf /backup/db.tar.gz -C /data .
docker run --rm -v ai-antiscam-arms-race:/data -v %cd%/%backup_dir%:/backup alpine tar czf /backup/arms_race.tar.gz -C /data .

echo.
echo ✅ 备份完成
echo    备份位置: %backup_dir%
echo.
pause
cls
goto menu

:volumes
echo.
echo ================================================
echo 💿 数据卷使用情况
echo ================================================
docker volume ls
echo.
docker system df -v
echo.
pause
cls
goto menu

:danger_cleanup
echo.
echo ================================================
echo ⚠️  危险操作：清理所有数据
echo ================================================
echo 这将删除所有容器、数据卷和镜像！
echo 所有训练数据和模型将丢失！
echo.
set /p confirm="确定要继续吗？(输入 YES 确认): "

if not "%confirm%"=="YES" (
    echo.
    echo ❌ 操作已取消
    echo.
    pause
    cls
    goto menu
)

echo.
echo 正在清理...
docker-compose -f docker-compose.yml down -v
docker system prune -af --volumes
echo.
echo ✅ 清理完成
echo.
pause
cls
goto menu

:end
echo.
echo 👋 再见！
timeout /t 2 >nul
exit

