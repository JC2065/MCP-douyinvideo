@echo off
rem Double-click to deploy the admin platform (see docs/platform-config-center.md).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\deploy-platform.ps1
echo.
pause
