@echo off
rem Read-only: diagnoses why a new release failed; does not change the live service.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-platform.ps1 -Tag platform-9f7c5cc
echo.
pause
