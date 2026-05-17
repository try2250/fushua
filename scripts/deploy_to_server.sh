#!/bin/bash
# FastAPI 项目部署脚本
# 用途：部署付刷项目到阿里云服务器

set -e

echo "=========================================="
echo "开始部署付刷项目"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 配置变量
PROJECT_NAME="fushua"
PROJECT_DIR="/var/www/fushua"
REPO_URL="https://github.com/try2250/fushua.git"
DB_NAME="fushua_db"
DB_USER="fushua_user"
DB_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
BACKUP_SECRET=$(openssl rand -hex 32)

# 1. 创建 PostgreSQL 数据库和用户
echo -e "${YELLOW}[1/9] 配置 PostgreSQL 数据库...${NC}"
sudo -u postgres psql <<EOF
-- 删除已存在的数据库和用户（如果存在）
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- 创建新用户和数据库
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- 显示结果
\l $DB_NAME
EOF

echo -e "${GREEN}✓ 数据库创建完成${NC}"
echo "  数据库名: $DB_NAME"
echo "  用户名: $DB_USER"
echo "  密码: $DB_PASSWORD"

# 2. 克隆项目代码
echo -e "${YELLOW}[2/9] 克隆项目代码...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "项目已存在，执行 git pull..."
    cd $PROJECT_DIR
    sudo -u fushua git pull
else
    echo "克隆新项目..."
    sudo -u fushua git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi
echo -e "${GREEN}✓ 代码克隆完成${NC}"

# 3. 创建 Python 虚拟环境
echo -e "${YELLOW}[3/9] 创建 Python 虚拟环境...${NC}"
sudo -u fushua python3 -m venv $PROJECT_DIR/venv
echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"

# 4. 安装依赖
echo -e "${YELLOW}[4/9] 安装 Python 依赖...${NC}"
sudo -u fushua $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u fushua $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 5. 配置环境变量
echo -e "${YELLOW}[5/9] 配置环境变量...${NC}"
cat > $PROJECT_DIR/.env <<EOF
# 数据库配置
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# 应用配置
SECRET_KEY=$SECRET_KEY
BACKUP_SECRET=$BACKUP_SECRET
BACKUP_DIR=$PROJECT_DIR/backups

# 环境
ENVIRONMENT=production
EOF

chown fushua:fushua $PROJECT_DIR/.env
chmod 600 $PROJECT_DIR/.env
echo -e "${GREEN}✓ 环境变量配置完成${NC}"

# 6. 创建必要的目录
echo -e "${YELLOW}[6/9] 创建项目目录...${NC}"
sudo -u fushua mkdir -p $PROJECT_DIR/backups
sudo -u fushua mkdir -p $PROJECT_DIR/logs
sudo -u fushua mkdir -p $PROJECT_DIR/uploads
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 7. 运行数据库迁移
echo -e "${YELLOW}[7/9] 运行数据库迁移...${NC}"
cd $PROJECT_DIR
sudo -u fushua $PROJECT_DIR/venv/bin/alembic upgrade head
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

# 8. 配置 Systemd 服务
echo -e "${YELLOW}[8/9] 配置 Systemd 服务...${NC}"
cat > /etc/systemd/system/fushua.service <<EOF
[Unit]
Description=Fushua FastAPI Application
After=network.target postgresql.service

[Service]
Type=notify
User=fushua
Group=fushua
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/gunicorn app.main:app \\
    --workers 4 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 127.0.0.1:8000 \\
    --access-logfile $PROJECT_DIR/logs/access.log \\
    --error-logfile $PROJECT_DIR/logs/error.log \\
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 安装 gunicorn（如果还没安装）
sudo -u fushua $PROJECT_DIR/venv/bin/pip install gunicorn

systemctl daemon-reload
systemctl enable fushua
systemctl start fushua
echo -e "${GREEN}✓ Systemd 服务配置完成${NC}"

# 9. 配置 Nginx 反向代理
echo -e "${YELLOW}[9/9] 配置 Nginx...${NC}"

# 获取服务器公网 IP
SERVER_IP=$(curl -s ifconfig.me)

cat > /etc/nginx/sites-available/fushua <<EOF
server {
    listen 80;
    server_name $SERVER_IP _;

    client_max_body_size 20M;

    # 访问日志
    access_log /var/log/nginx/fushua_access.log;
    error_log /var/log/nginx/fushua_error.log;

    # 静态文件
    location /static {
        alias $PROJECT_DIR/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 上传文件
    location /uploads {
        alias $PROJECT_DIR/uploads;
        expires 7d;
    }

    # API 代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/fushua /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
echo -e "${GREEN}✓ Nginx 配置完成${NC}"

# 10. 检查服务状态
echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务信息："
echo "  项目目录: $PROJECT_DIR"
echo "  服务状态: $(systemctl is-active fushua)"
echo "  Nginx 状态: $(systemctl is-active nginx)"
echo ""
echo "数据库信息："
echo "  数据库: $DB_NAME"
echo "  用户: $DB_USER"
echo "  密码: $DB_PASSWORD"
echo ""
echo "访问地址："
echo "  HTTP: http://$SERVER_IP"
echo ""
echo "环境变量（已保存到 $PROJECT_DIR/.env）："
echo "  SECRET_KEY: $SECRET_KEY"
echo "  BACKUP_SECRET: $BACKUP_SECRET"
echo ""
echo "常用命令："
echo "  查看服务状态: systemctl status fushua"
echo "  查看日志: journalctl -u fushua -f"
echo "  重启服务: systemctl restart fushua"
echo "  查看 Nginx 日志: tail -f /var/log/nginx/fushua_error.log"
echo ""
echo -e "${YELLOW}重要提示：${NC}"
echo "1. 请保存好数据库密码和密钥信息"
echo "2. 访问 http://$SERVER_IP 测试应用"
echo "3. 如需配置域名，请修改 /etc/nginx/sites-available/fushua"
echo "4. 配置域名后可申请 SSL 证书（Let's Encrypt）"
echo ""
echo "下一步："
echo "1. 创建管理员账号"
echo "2. 导入题库数据"
echo "3. 配置定时备份"
echo ""
