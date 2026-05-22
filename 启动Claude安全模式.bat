@echo off
cd /d "%~dp0"
start "Claude Safe Chat - fushua" powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0scripts\start-claude-safe-chat.ps1" %*
