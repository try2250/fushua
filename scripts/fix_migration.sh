#!/bin/bash
# 修复数据库迁移问题

set -e

PROJECT_DIR="/var/www/fushua"
cd $PROJECT_DIR

echo "修复 Alembic 配置..."

# 1. 安装 python-dotenv（如果还没安装）
sudo -u fushua $PROJECT_DIR/venv/bin/pip install python-dotenv

# 2. 修改 alembic/env.py 以加载 .env 文件
cat > $PROJECT_DIR/alembic/env.py <<'EOF'
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import User, FieldConfig, Question, Record, Favorite, StudyPlan, ClassGroup, ClassMember, Notification, Assignment, AssignmentRecord, ClassJoinRequest, AccountRecoveryRequest, QuestionBank

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)
    print(f"Using database: {db_url.split('@')[1] if '@' in db_url else 'SQLite'}")
else:
    print("WARNING: DATABASE_URL not found, using SQLite")


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

chown fushua:fushua $PROJECT_DIR/alembic/env.py

# 3. 删除可能存在的 SQLite 数据库文件
rm -f $PROJECT_DIR/fushua.db

# 4. 重新运行迁移
echo "重新运行数据库迁移..."
sudo -u fushua $PROJECT_DIR/venv/bin/alembic upgrade head

echo "✓ 数据库迁移修复完成"
