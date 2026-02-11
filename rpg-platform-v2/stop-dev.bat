@echo off
echo.
echo === RPG Dev Server - Quick Stop ===
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0stop-dev.ps1"
pause
