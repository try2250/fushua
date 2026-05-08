@echo off
chcp 65001 >nul 2>&1
title 付刷 - 刷题平台

echo ============================================
echo       付刷 - 中学刷题平台 一键启动
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo [2/3] 初始化数据库...
python -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine); print('数据库初始化完成')"

echo [3/3] 启动服务器...
echo.
echo ============================================
echo   启动成功！请打开浏览器访问:
echo.
echo   http://localhost:8000
echo.
echo   默认教师邀请码: FUSHUA2024
echo   按 Ctrl+C 停止服务器
echo ============================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
