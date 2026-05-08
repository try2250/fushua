#!/bin/bash
echo "============================================"
echo "      付刷 - 中学刷题平台 一键启动"
echo "============================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.10+"
    exit 1
fi

echo "[1/3] 安装依赖..."
pip3 install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "[错误] 依赖安装失败，请检查网络连接"
    exit 1
fi

echo "[2/3] 初始化数据库..."
python3 -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine); print('数据库初始化完成')"

echo "[3/3] 启动服务器..."
echo ""
echo "============================================"
echo "  启动成功！请打开浏览器访问:"
echo ""
echo "  http://localhost:8000"
echo ""
echo "  默认教师邀请码: FUSHUA2024"
echo "  按 Ctrl+C 停止服务器"
echo "============================================"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
