#!/bin/bash
# 阿里云 ECS 服务器初始化脚本
# 用途：配置基础安全设置、创建用户、安装必要软件

set -e  # 遇到错误立即退出

echo "=========================================="
echo "开始服务器初始化配置"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置变量
NEW_USER="fushua"
USER_PASSWORD="thebestfyg4"
SSH_PORT=22  # 可以改为其他端口增加安全性

# 1. 更新系统
echo -e "${YELLOW}[1/8] 更新系统软件包...${NC}"
apt update
apt upgrade -y

# 2. 安装基础工具
echo -e "${YELLOW}[2/8] 安装基础工具...${NC}"
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    unzip \
    build-essential \
    software-properties-common

# 3. 创建新用户
echo -e "${YELLOW}[3/8] 创建用户 ${NEW_USER}...${NC}"
if id "$NEW_USER" &>/dev/null; then
    echo "用户 $NEW_USER 已存在，跳过创建"
else
    useradd -m -s /bin/bash "$NEW_USER"
    echo "$NEW_USER:$USER_PASSWORD" | chpasswd
    usermod -aG sudo "$NEW_USER"
    echo -e "${GREEN}✓ 用户 $NEW_USER 创建成功${NC}"
fi

# 4. 配置 SSH 安全
echo -e "${YELLOW}[4/8] 配置 SSH 安全设置...${NC}"
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
cat > /etc/ssh/sshd_config.d/security.conf <<EOF
# 禁用 root 远程登录（建议测试新用户可登录后再启用）
# PermitRootLogin no

# 禁用密码为空的用户登录
PermitEmptyPasswords no

# 启用公钥认证
PubkeyAuthentication yes

# 设置登录超时
LoginGraceTime 60

# 最大认证尝试次数
MaxAuthTries 3

# 禁用 X11 转发
X11Forwarding no
EOF

# 重启 SSH 服务
systemctl restart sshd
echo -e "${GREEN}✓ SSH 配置完成${NC}"

# 5. 配置防火墙 UFW
echo -e "${YELLOW}[5/8] 配置防火墙...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow $SSH_PORT/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
echo -e "${GREEN}✓ 防火墙配置完成${NC}"

# 6. 配置 Fail2Ban（防暴力破解）
echo -e "${YELLOW}[6/8] 配置 Fail2Ban...${NC}"
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = $SSH_PORT
logpath = /var/log/auth.log
EOF

systemctl enable fail2ban
systemctl restart fail2ban
echo -e "${GREEN}✓ Fail2Ban 配置完成${NC}"

# 7. 安装 Python 3.12
echo -e "${YELLOW}[7/8] 安装 Python 3.12...${NC}"
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip

# 设置 Python 3.12 为默认
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
python3 --version
echo -e "${GREEN}✓ Python 3.12 安装完成${NC}"

# 8. 安装 PostgreSQL
echo -e "${YELLOW}[8/8] 安装 PostgreSQL...${NC}"
apt install -y postgresql postgresql-contrib
systemctl enable postgresql
systemctl start postgresql
echo -e "${GREEN}✓ PostgreSQL 安装完成${NC}"

# 9. 安装 Nginx
echo -e "${YELLOW}[9/9] 安装 Nginx...${NC}"
apt install -y nginx
systemctl enable nginx
systemctl start nginx
echo -e "${GREEN}✓ Nginx 安装完成${NC}"

# 10. 创建项目目录
echo -e "${YELLOW}[10/10] 创建项目目录...${NC}"
mkdir -p /var/www/fushua
chown -R $NEW_USER:$NEW_USER /var/www/fushua
echo -e "${GREEN}✓ 项目目录创建完成${NC}"

# 显示系统信息
echo ""
echo "=========================================="
echo -e "${GREEN}服务器初始化完成！${NC}"
echo "=========================================="
echo ""
echo "系统信息："
echo "  操作系统: $(lsb_release -d | cut -f2)"
echo "  Python 版本: $(python3 --version)"
echo "  PostgreSQL 版本: $(sudo -u postgres psql --version | head -n1)"
echo "  Nginx 版本: $(nginx -v 2>&1 | cut -d'/' -f2)"
echo ""
echo "用户信息："
echo "  用户名: $NEW_USER"
echo "  密码: $USER_PASSWORD"
echo "  项目目录: /var/www/fushua"
echo ""
echo "安全设置："
echo "  防火墙状态: $(ufw status | head -n1)"
echo "  Fail2Ban 状态: $(systemctl is-active fail2ban)"
echo "  SSH 端口: $SSH_PORT"
echo ""
echo -e "${YELLOW}重要提示：${NC}"
echo "1. 请使用新用户 $NEW_USER 登录测试"
echo "2. 测试成功后，编辑 /etc/ssh/sshd_config.d/security.conf"
echo "   取消注释 'PermitRootLogin no' 禁用 root 登录"
echo "3. 建议配置 SSH 密钥认证，禁用密码登录"
echo "4. 记得修改用户密码: passwd $NEW_USER"
echo ""
echo "下一步："
echo "1. 配置域名解析指向此服务器"
echo "2. 部署 FastAPI 应用"
echo "3. 配置 Nginx 反向代理"
echo "4. 申请 SSL 证书"
echo ""
