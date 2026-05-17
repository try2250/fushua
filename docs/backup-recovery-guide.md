# 数据备份恢复演练指南

## 概述

本文档提供付刷系统数据备份的恢复步骤和演练清单，确保在数据丢失或损坏时能够快速恢复。

## 备份文件位置

### 生产环境（Render）
- **路径**: `./backups/`
- **命名格式**: `fushua_YYYYMMDD_HHMMSS.{db|sql.gz}`
- **示例**: 
  - SQLite: `fushua_20260517_020000.db`
  - PostgreSQL: `fushua_20260517_020000.sql.gz`

### 本地开发环境
- **路径**: `./backups/`（项目根目录）
- **访问方式**: 通过管理员界面下载

## 恢复步骤

### SQLite 数据库恢复

#### 方法 1：直接替换（推荐用于开发环境）

```bash
# 1. 停止应用
# 如果使用 systemd
sudo systemctl stop fushua

# 如果使用 Docker
docker stop fushua-container

# 2. 备份当前数据库（以防万一）
cp fushua.db fushua.db.backup_$(date +%Y%m%d_%H%M%S)

# 3. 恢复备份文件
cp backups/fushua_20260517_020000.db fushua.db

# 4. 验证数据库完整性
sqlite3 fushua.db "PRAGMA integrity_check;"
# 应该输出: ok

# 5. 重启应用
sudo systemctl start fushua
# 或
docker start fushua-container
```

#### 方法 2：使用 SQLite 命令恢复

```bash
# 1. 创建新数据库并导入备份
sqlite3 fushua_restored.db ".restore 'backups/fushua_20260517_020000.db'"

# 2. 验证恢复的数据
sqlite3 fushua_restored.db "SELECT COUNT(*) FROM users;"
sqlite3 fushua_restored.db "SELECT COUNT(*) FROM questions;"

# 3. 替换当前数据库
mv fushua.db fushua.db.old
mv fushua_restored.db fushua.db
```

### PostgreSQL 数据库恢复

#### 方法 1：完整恢复（会删除现有数据）

```bash
# 1. 解压备份文件
gunzip -c backups/fushua_20260517_020000.sql.gz > restore.sql

# 2. 停止应用（避免连接冲突）
# Render 环境：暂停 Web Service

# 3. 删除现有数据库并重新创建
psql $DATABASE_URL -c "DROP DATABASE IF EXISTS fushua;"
psql $DATABASE_URL -c "CREATE DATABASE fushua;"

# 4. 恢复数据
psql $DATABASE_URL < restore.sql

# 5. 验证数据
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM questions;"

# 6. 重启应用
```

#### 方法 2：选择性恢复（恢复特定表）

```bash
# 1. 解压备份文件
gunzip -c backups/fushua_20260517_020000.sql.gz > restore.sql

# 2. 提取特定表的数据
pg_restore -t users -t questions restore.sql > partial_restore.sql

# 3. 恢复特定表
psql $DATABASE_URL < partial_restore.sql
```

### Render 环境特殊说明

由于 Render 免费版的限制，恢复流程略有不同：

```bash
# 1. 从管理员界面下载备份文件到本地

# 2. 连接到 Render PostgreSQL
# 获取 DATABASE_URL（在 Render Dashboard 的环境变量中）
export DATABASE_URL="postgresql://user:pass@host:port/db"

# 3. 本地恢复
gunzip -c fushua_20260517_020000.sql.gz | psql $DATABASE_URL

# 4. 验证恢复结果
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
```

## 验证方法

### 1. 数据完整性检查

```bash
# SQLite
sqlite3 fushua.db "PRAGMA integrity_check;"

# PostgreSQL
psql $DATABASE_URL -c "SELECT pg_database_size('fushua');"
```

### 2. 关键数据验证

```sql
-- 检查用户数量
SELECT COUNT(*) FROM users;

-- 检查题目数量
SELECT COUNT(*) FROM questions;

-- 检查班级数量
SELECT COUNT(*) FROM class_groups;

-- 检查作业数量
SELECT COUNT(*) FROM assignments;

-- 检查最近的记录
SELECT MAX(created_at) FROM users;
SELECT MAX(created_at) FROM questions;
```

### 3. 功能测试

- [ ] 登录功能正常
- [ ] 题库浏览正常
- [ ] 作业提交正常
- [ ] 班级管理正常
- [ ] 统计数据正确

## 回滚计划

如果恢复后发现问题，需要回滚到恢复前的状态：

```bash
# 1. 停止应用
sudo systemctl stop fushua

# 2. 恢复到恢复前的备份
cp fushua.db.backup_YYYYMMDD_HHMMSS fushua.db

# 3. 重启应用
sudo systemctl start fushua

# 4. 验证回滚成功
sqlite3 fushua.db "SELECT COUNT(*) FROM users;"
```

## 常见问题

### 问题 1：备份文件损坏

**症状**: 恢复时报错 "database disk image is malformed"

**解决方案**:
```bash
# 尝试使用 SQLite 的恢复工具
sqlite3 corrupted.db ".recover" | sqlite3 recovered.db

# 或使用更早的备份
ls -lt backups/ | head -10
```

### 问题 2：PostgreSQL 连接超时

**症状**: 恢复时连接数据库超时

**解决方案**:
```bash
# 增加连接超时时间
export PGCONNECT_TIMEOUT=60

# 或分批恢复
pg_restore -j 4 backup.sql  # 使用 4 个并行任务
```

### 问题 3：磁盘空间不足

**症状**: 恢复时报错 "No space left on device"

**解决方案**:
```bash
# 检查磁盘空间
df -h

# 清理旧备份
cd backups/
ls -lt | tail -n +31 | awk '{print $9}' | xargs rm

# 或压缩备份文件
gzip fushua_*.db
```

## 每月演练清单

为确保备份恢复流程有效，建议每月进行一次演练：

### 演练步骤

- [ ] **准备阶段**（5分钟）
  - [ ] 选择最近的一个备份文件
  - [ ] 记录当前数据库状态（用户数、题目数等）
  - [ ] 准备测试环境（本地或测试服务器）

- [ ] **恢复阶段**（15分钟）
  - [ ] 按照恢复步骤执行
  - [ ] 记录恢复耗时
  - [ ] 记录遇到的问题

- [ ] **验证阶段**（10分钟）
  - [ ] 执行数据完整性检查
  - [ ] 验证关键数据数量
  - [ ] 测试核心功能

- [ ] **文档更新**（5分钟）
  - [ ] 更新演练记录
  - [ ] 记录改进建议
  - [ ] 更新本文档（如有必要）

### 演练记录模板

```
演练日期: YYYY-MM-DD
执行人: [姓名]
备份文件: fushua_YYYYMMDD_HHMMSS.{db|sql.gz}
备份大小: XX MB
恢复耗时: XX 分钟

数据验证:
- 用户数: XXX (预期: XXX)
- 题目数: XXX (预期: XXX)
- 班级数: XXX (预期: XXX)

遇到的问题:
1. [问题描述]
2. [问题描述]

改进建议:
1. [建议]
2. [建议]

结论: ✓ 成功 / ✗ 失败
```

## 紧急联系方式

如果在恢复过程中遇到无法解决的问题：

1. **技术支持**: [联系方式]
2. **数据库管理员**: [联系方式]
3. **Render 支持**: https://render.com/docs/support

## 附录

### A. 自动化恢复脚本

```bash
#!/bin/bash
# restore_backup.sh - 自动化恢复脚本

set -euo pipefail

BACKUP_FILE="${1:-}"
DB_FILE="${2:-fushua.db}"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件> [数据库文件]"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "[1/5] 备份当前数据库..."
cp "$DB_FILE" "${DB_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "[2/5] 恢复备份文件..."
cp "$BACKUP_FILE" "$DB_FILE"

echo "[3/5] 验证数据库完整性..."
if sqlite3 "$DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✓ 数据库完整性检查通过"
else
    echo "✗ 数据库完整性检查失败"
    exit 1
fi

echo "[4/5] 验证数据..."
USER_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM users;")
QUESTION_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM questions;")
echo "用户数: $USER_COUNT"
echo "题目数: $QUESTION_COUNT"

echo "[5/5] 恢复完成！"
echo "请重启应用并进行功能测试。"
```

### B. 监控和告警

建议设置以下监控指标：

1. **备份成功率**: 每日备份是否成功
2. **备份文件大小**: 是否异常增长或减少
3. **最近备份时间**: 是否超过 24 小时
4. **磁盘空间**: 备份目录剩余空间

可以通过管理员界面的"备份统计"查看这些指标。

---

**最后更新**: 2026-05-17  
**版本**: 1.0  
**维护者**: 付刷开发团队
