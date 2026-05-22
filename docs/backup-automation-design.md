# 数据备份自动化设计文档

## 1. 概述

### 目标
为付刷系统实现自动化数据备份功能，确保生产环境数据安全，满足灰度试用前的必备要求。

### 核心需求
- 每日自动备份数据库
- 管理员可手动触发备份
- 完整的备份管理界面（查看、下载、删除、验证）
- 备份历史记录和统计
- 备份文件完整性验证
- 恢复演练文档

## 2. 系统架构

### 组件关系
```
Render Cron Job (每日 2:00 UTC)
    ↓ HTTP POST (带内部密钥)
FastAPI 备份端点 (/admin/backup/trigger)
    ↓ 调用
backup_db.sh 脚本
    ↓ 生成
备份文件 (backups/fushua_YYYYMMDD_HHMMSS.db)
    ↓ 记录
backup_logs 表 (元数据)
    ↓ 展示
管理员界面 (/admin/backup)
```

### 技术选型
- **定时调度**: Render Cron Job
- **API 框架**: FastAPI
- **数据库**: SQLAlchemy (新增 `backup_logs` 表)
- **备份脚本**: 现有 `scripts/backup_db.sh`
- **存储方案**: 本地临时存储 + 手动下载（免费版方案）

### 设计决策

**为什么选择 Render Cron Job？**
- ✅ 独立可靠，不受应用休眠影响
- ✅ Render 原生支持，配置简单
- ✅ 失败时有通知
- ✅ 适合生产环境

**为什么选择混合存储（数据库 + 文件系统）？**
- ✅ 数据库记录元数据，便于查询和展示
- ✅ 文件系统存储实际备份文件
- ✅ 分离关注点，符合最佳实践

**为什么选择 API 端点触发？**
- ✅ 统一入口，手动和自动备份都有记录
- ✅ 可以添加认证和权限控制
- ✅ 便于监控和审计

## 3. 数据库设计

### 新增表：backup_logs

```python
class BackupLog(Base):
    __tablename__ = "backup_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'running'
    file_path = Column(String(255), nullable=True)  # 相对路径
    file_size = Column(Integer, nullable=True)  # 字节数
    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(50), default="cron")  # 'cron', 'admin', 'manual'
    duration_seconds = Column(Integer, nullable=True)
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| created_at | DateTime | 备份开始时间 |
| status | String(20) | 备份状态：success/failed/running |
| file_path | String(255) | 备份文件相对路径 |
| file_size | Integer | 文件大小（字节） |
| error_message | Text | 失败时的错误信息 |
| triggered_by | String(50) | 触发来源：cron/admin/manual |
| duration_seconds | Integer | 备份耗时（秒） |

### 索引
- `created_at` - 用于按时间查询
- `status` - 用于统计成功率

## 4. API 端点设计

### 4.1 触发备份

```
POST /admin/backup/trigger
Headers: X-Backup-Secret: <BACKUP_SECRET>
Response: {
  "status": "success",
  "backup_id": 123,
  "file_path": "backups/fushua_20260517_020000.db",
  "file_size": 47185920
}
```

**认证机制**:
- 使用环境变量 `BACKUP_SECRET` 进行认证
- Cron Job 和 Web Service 共享同一密钥
- 防止未授权访问

### 4.2 查看备份列表

```
GET /admin/backup
Response: HTML 页面
```

**权限**: 需要管理员权限 (`require_admin()`)

### 4.3 查看备份统计

```
GET /admin/backup/stats
Response: {
  "total_backups": 30,
  "success_count": 28,
  "failed_count": 2,
  "success_rate": 0.933,
  "total_size_mb": 1024.5,
  "last_backup": {
    "created_at": "2026-05-17T02:00:00",
    "status": "success",
    "file_size": 47185920
  }
}
```

### 4.4 下载备份文件

```
GET /admin/backup/download/{backup_id}
Response: 文件下载（application/octet-stream）
```

**安全检查**:
- 验证管理员权限
- 验证备份 ID 存在
- 验证文件路径安全（防止路径遍历）

### 4.5 删除备份

```
POST /admin/backup/delete/{backup_id}
Body: {"_csrf_token": "..."}
Response: {"status": "success"}
```

**操作**:
- 删除文件系统中的备份文件
- 更新数据库记录状态或删除记录
- 记录到审计日志

### 4.6 配置备份保留天数

```
POST /admin/backup/config
Body: {
  "keep_days": 30,
  "_csrf_token": "..."
}
Response: {"status": "success"}
```

**存储**: 使用 `site_configs` 表存储配置

### 4.7 验证备份完整性

```
POST /admin/backup/verify/{backup_id}
Response: {
  "status": "valid",
  "checks": {
    "file_exists": true,
    "file_size_ok": true,
    "integrity_check": true
  },
  "details": "备份文件完整"
}
```

## 5. 管理员界面设计

### 页面布局

```
┌─────────────────────────────────────────────────┐
│ 数据备份管理                                      │
├─────────────────────────────────────────────────┤
│ 📊 备份统计                                       │
│   总备份数: 30 | 成功率: 95% | 总大小: 1.2 GB    │
│   最后备份: 2026-05-17 02:00 (成功)              │
├─────────────────────────────────────────────────┤
│ ⚙️ 备份配置                                       │
│   保留天数: [30] 天  [保存]                       │
│   [立即备份] [验证最新备份]                        │
├─────────────────────────────────────────────────┤
│ 📋 备份历史                                       │
│ ┌───────────────────────────────────────────┐   │
│ │ 时间              状态   大小    操作      │   │
│ ├───────────────────────────────────────────┤   │
│ │ 2026-05-17 02:00  ✓成功  45MB  [下载][删除]│   │
│ │ 2026-05-16 02:00  ✓成功  44MB  [下载][删除]│   │
│ │ 2026-05-15 02:00  ✗失败   -    [查看日志] │   │
│ │ ...                                        │   │
│ └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 功能模块

#### 5.1 统计面板
- 总备份数
- 成功率（成功数/总数）
- 总大小（所有备份文件大小之和）
- 最后备份时间和状态

#### 5.2 配置面板
- 保留天数设置（默认 30 天）
- 立即备份按钮（手动触发）
- 验证最新备份按钮

#### 5.3 历史列表
- 显示最近 30 天的备份记录
- 状态指示：
  - ✓ 成功（绿色）
  - ✗ 失败（红色）
  - ⏳ 进行中（黄色）
- 操作按钮：
  - 下载（成功的备份）
  - 删除（所有备份）
  - 查看日志（失败的备份）

### 模板文件

**新增**: `templates/admin/backup.html`

**继承**: `templates/base.html`

**样式**: 使用现有的 admin 样式

## 6. Render 配置

### 更新 render.yaml

```yaml
services:
  - type: web
    name: fushua
    plan: free
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: alembic upgrade head && gunicorn app.main:app -c gunicorn.conf.py
    envVars:
      # ... 现有环境变量 ...
      - key: BACKUP_SECRET
        generateValue: true  # Render 自动生成密钥

  - type: cron
    name: fushua-backup
    schedule: "0 2 * * *"  # 每日凌晨 2:00 UTC (北京时间 10:00)
    buildCommand: echo "Backup cron job"
    startCommand: >
      curl -X POST https://fushua.onrender.com/admin/backup/trigger
      -H "X-Backup-Secret: $BACKUP_SECRET"
    envVars:
      - key: BACKUP_SECRET
        sync: false  # 需要手动从 web service 复制密钥

databases:
  - name: fushua-db
    plan: free
```

### 配置步骤

1. 更新 `render.yaml` 文件
2. 提交到 Git 并推送
3. 在 Render Dashboard 中：
   - 找到 web service 的 `BACKUP_SECRET` 值
   - 复制到 cron job 的环境变量中
4. 验证 cron job 配置正确

### 注意事项

- **时区**: Render Cron Job 使用 UTC 时区
  - `0 2 * * *` = UTC 02:00 = 北京时间 10:00
  - 如需凌晨 2:00 北京时间，使用 `0 18 * * *`
- **免费版限制**: 可能限制 cron job 数量和执行频率
- **密钥同步**: `BACKUP_SECRET` 需要手动同步，不能自动共享

## 7. 备份验证机制

### 验证流程

```python
def verify_backup(file_path: str) -> dict:
    """验证备份文件完整性"""
    
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        return {"valid": False, "error": "文件不存在"}
    
    # 2. 检查文件大小（至少 1KB）
    size = os.path.getsize(file_path)
    if size < 1024:
        return {"valid": False, "error": "文件过小，可能损坏"}
    
    # 3. SQLite 完整性检查
    if file_path.endswith('.db'):
        result = subprocess.run(
            ['sqlite3', file_path, 'PRAGMA integrity_check;'],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip() != 'ok':
            return {"valid": False, "error": "数据库完整性检查失败"}
    
    # 4. PostgreSQL 验证（如果是 .sql.gz）
    if file_path.endswith('.sql.gz'):
        result = subprocess.run(
            ['gunzip', '-t', file_path],
            capture_output=True, timeout=30
        )
        if result.returncode != 0:
            return {"valid": False, "error": "压缩文件损坏"}
    
    return {
        "valid": True,
        "size": size,
        "details": "备份文件完整"
    }
```

### 验证时机

1. **备份完成后**: 自动验证新创建的备份
2. **手动触发**: 管理员点击"验证"按钮
3. **定期检查**: 每周验证所有备份（可选）

## 8. 错误处理机制

### 备份执行流程

```python
def execute_backup(triggered_by: str = "cron") -> dict:
    """执行备份并处理错误"""
    
    # 1. 创建备份日志记录
    backup_log = BackupLog(
        status="running",
        triggered_by=triggered_by
    )
    db.add(backup_log)
    db.commit()
    
    start_time = time.time()
    
    try:
        # 2. 执行备份脚本
        result = subprocess.run(
            ['bash', 'scripts/backup_db.sh'],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 3. 处理执行结果
        if result.returncode == 0:
            # 解析输出，提取文件路径和大小
            file_path = extract_file_path(result.stdout)
            file_size = os.path.getsize(file_path)
            
            # 验证备份完整性
            verification = verify_backup(file_path)
            
            if verification["valid"]:
                backup_log.status = "success"
                backup_log.file_path = file_path
                backup_log.file_size = file_size
            else:
                backup_log.status = "failed"
                backup_log.error_message = f"验证失败: {verification['error']}"
        else:
            backup_log.status = "failed"
            backup_log.error_message = result.stderr
            
            # 发送告警
            send_backup_alert("备份失败", result.stderr)
    
    except subprocess.TimeoutExpired:
        backup_log.status = "failed"
        backup_log.error_message = "备份超时（5分钟）"
        send_backup_alert("备份超时", "备份执行超过5分钟")
    
    except Exception as e:
        backup_log.status = "failed"
        backup_log.error_message = str(e)
        send_backup_alert("备份异常", str(e))
    
    finally:
        # 4. 记录耗时
        backup_log.duration_seconds = int(time.time() - start_time)
        db.commit()
    
    return {
        "backup_id": backup_log.id,
        "status": backup_log.status,
        "file_path": backup_log.file_path,
        "file_size": backup_log.file_size
    }
```

### 告警机制

#### 触发条件
- 单次备份失败
- 连续 3 次备份失败
- 备份超时
- 备份验证失败

#### 告警方式
1. **管理员首页警告**
   - 在 `/admin` 首页顶部显示红色警告横幅
   - 显示最近失败的备份信息
   - 提供"查看详情"链接

2. **审计日志记录**
   - 记录到 `audit_logs` 表
   - action: "backup_failed"
   - detail: 错误信息

3. **未来扩展**
   - 邮件通知
   - Slack 通知
   - 短信通知（紧急情况）

### 自动清理

```python
def cleanup_old_backups(keep_days: int = 30):
    """清理超过保留天数的备份"""
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    # 查询需要删除的备份
    old_backups = db.query(BackupLog).filter(
        BackupLog.created_at < cutoff_date,
        BackupLog.status == "success"
    ).all()
    
    for backup in old_backups:
        try:
            # 删除文件
            if backup.file_path and os.path.exists(backup.file_path):
                os.remove(backup.file_path)
            
            # 删除数据库记录
            db.delete(backup)
        except Exception as e:
            logger.error(f"清理备份失败: {backup.id}, {e}")
    
    db.commit()
```

## 9. 恢复演练文档

### 文档位置
`docs/backup-recovery-guide.md`

### 文档内容

#### 9.1 备份文件位置
- **本地**: `backups/fushua_YYYYMMDD_HHMMSS.db` 或 `.sql.gz`
- **下载**: 通过管理员界面下载

#### 9.2 恢复步骤

**SQLite 数据库恢复**:
```bash
# 1. 停止应用
# 2. 备份当前数据库
cp fushua.db fushua.db.backup

# 3. 恢复备份
cp backups/fushua_20260517_020000.db fushua.db

# 4. 运行迁移（如果需要）
alembic upgrade head

# 5. 验证数据
sqlite3 fushua.db "SELECT COUNT(*) FROM users;"

# 6. 重启应用
```

**PostgreSQL 数据库恢复**:
```bash
# 1. 停止应用
# 2. 创建备份
pg_dump $DATABASE_URL > current_backup.sql

# 3. 恢复备份
gunzip -c backups/fushua_20260517_020000.sql.gz | psql $DATABASE_URL

# 4. 运行迁移（如果需要）
alembic upgrade head

# 5. 验证数据
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# 6. 重启应用
```

#### 9.3 验证恢复

**检查清单**:
- [ ] 用户表数据完整
- [ ] 班级表数据完整
- [ ] 题库表数据完整
- [ ] 作业表数据完整
- [ ] 答题记录表数据完整
- [ ] 应用可以正常启动
- [ ] 登录功能正常
- [ ] 核心功能正常

**验证脚本**:
```python
# scripts/verify_restore.py
def verify_restore():
    """验证恢复后的数据完整性"""
    checks = {
        "users": db.query(User).count(),
        "classes": db.query(ClassGroup).count(),
        "questions": db.query(Question).count(),
        "assignments": db.query(Assignment).count(),
        "records": db.query(Record).count()
    }
    
    print("数据完整性检查:")
    for table, count in checks.items():
        print(f"  {table}: {count} 条记录")
    
    return all(count > 0 for count in checks.values())
```

#### 9.4 回滚计划

如果恢复失败或数据不正确:
```bash
# 1. 停止应用
# 2. 恢复到恢复前的备份
cp fushua.db.backup fushua.db

# 3. 重启应用
# 4. 分析失败原因
```

#### 9.5 演练清单

**每月执行一次恢复演练**:
- [ ] 选择最新的备份文件
- [ ] 在测试环境执行恢复
- [ ] 验证数据完整性
- [ ] 测试核心功能
- [ ] 记录演练结果
- [ ] 更新恢复文档（如有问题）

**演练记录模板**:
```markdown
## 恢复演练记录

**日期**: 2026-05-17
**执行人**: 管理员
**备份文件**: fushua_20260517_020000.db
**恢复环境**: 测试环境

**结果**:
- [ ] 恢复成功
- [ ] 数据完整
- [ ] 功能正常

**问题**:
- 无

**改进建议**:
- 无
```

## 10. 文件清单

### 新增文件

1. **数据库迁移**
   - `alembic/versions/XXXX_add_backup_logs_table.py`

2. **模型**
   - `app/models.py` (新增 `BackupLog` 模型)

3. **路由**
   - `app/routers/backup.py` (新增备份路由)

4. **模板**
   - `templates/admin/backup.html`

5. **工具函数**
   - `app/utils/backup.py` (备份执行、验证、清理)

6. **文档**
   - `docs/backup-recovery-guide.md`

### 修改文件

1. **Render 配置**
   - `render.yaml` (新增 cron job)

2. **主应用**
   - `app/main.py` (注册备份路由)

3. **管理员路由**
   - `app/routers/admin.py` (添加备份入口链接)

4. **管理员模板**
   - `templates/admin/index.html` (添加备份管理链接和告警)

## 11. 测试计划

### 单元测试

1. **备份执行测试**
   - 测试成功备份
   - 测试备份失败
   - 测试备份超时

2. **备份验证测试**
   - 测试 SQLite 完整性检查
   - 测试 PostgreSQL 完整性检查
   - 测试损坏文件检测

3. **清理测试**
   - 测试自动清理旧备份
   - 测试保留天数配置

### 集成测试

1. **API 端点测试**
   - 测试触发备份（带密钥）
   - 测试触发备份（无密钥，应失败）
   - 测试查看备份列表
   - 测试下载备份
   - 测试删除备份
   - 测试配置保留天数

2. **权限测试**
   - 测试非管理员访问（应拒绝）
   - 测试管理员访问（应允许）

3. **界面测试**
   - 测试备份列表显示
   - 测试统计数据正确性
   - 测试手动触发备份
   - 测试下载按钮
   - 测试删除按钮

### 端到端测试

1. **完整备份流程**
   - Cron Job 触发 → API 执行 → 文件生成 → 记录保存 → 界面显示

2. **恢复演练**
   - 下载备份 → 恢复到测试环境 → 验证数据 → 测试功能

## 12. 部署清单

### 部署前检查

- [ ] 代码审查通过
- [ ] 所有测试通过
- [ ] 数据库迁移脚本准备好
- [ ] `render.yaml` 更新
- [ ] 环境变量配置文档更新
- [ ] 恢复演练文档完成

### 部署步骤

1. **数据库迁移**
   ```bash
   alembic upgrade head
   ```

2. **更新代码**
   ```bash
   git push origin main
   ```

3. **配置 Render**
   - 在 Render Dashboard 中添加 `BACKUP_SECRET` 环境变量
   - 创建 Cron Job 服务
   - 复制 `BACKUP_SECRET` 到 Cron Job

4. **验证部署**
   - 访问 `/admin/backup` 页面
   - 手动触发一次备份
   - 检查备份文件生成
   - 检查数据库记录

5. **监控**
   - 第二天检查 Cron Job 是否自动执行
   - 检查备份文件是否生成
   - 检查告警机制是否正常

### 部署后验证

- [ ] 管理员界面可访问
- [ ] 手动备份功能正常
- [ ] 备份文件可下载
- [ ] 统计数据正确
- [ ] Cron Job 配置正确
- [ ] 第一次自动备份成功

## 13. 未来改进

### 短期改进（1-3 个月）

1. **持久化存储**
   - 集成 Render Disk 或 S3
   - 自动上传备份到云存储
   - 实现异地备份

2. **增量备份**
   - 实现增量备份策略
   - 减少备份文件大小
   - 加快备份速度

3. **通知增强**
   - 邮件通知
   - Slack 集成
   - 备份报告

### 长期改进（3-6 个月）

1. **自动恢复测试**
   - 定期自动恢复到测试环境
   - 自动验证数据完整性
   - 生成恢复测试报告

2. **备份加密**
   - 加密备份文件
   - 密钥管理
   - 安全传输

3. **多版本保留**
   - 保留多个版本的备份
   - 支持回滚到任意时间点
   - 备份版本管理

## 14. 风险和限制

### 已知限制

1. **Render 免费版限制**
   - 临时文件系统，重启后文件丢失
   - Cron Job 可能有执行频率限制
   - 存储空间有限

2. **备份窗口**
   - 备份期间可能影响性能
   - 大数据库备份时间较长
   - 需要选择低峰时段

3. **恢复时间**
   - 大数据库恢复时间较长
   - 需要停机维护
   - 可能影响服务可用性

### 风险缓解

1. **文件丢失风险**
   - 提醒管理员定期下载重要备份
   - 未来升级到持久化存储
   - 实现异地备份

2. **备份失败风险**
   - 实现告警机制
   - 连续失败时通知管理员
   - 提供手动备份选项

3. **恢复失败风险**
   - 定期执行恢复演练
   - 维护详细的恢复文档
   - 保留多个备份版本

## 15. 总结

本设计文档详细描述了数据备份自动化功能的完整实现方案，包括：

- ✅ 自动化调度（Render Cron Job）
- ✅ 完整的管理界面（查看、下载、删除、验证）
- ✅ 备份历史记录和统计
- ✅ 备份验证机制
- ✅ 错误处理和告警
- ✅ 恢复演练文档

该方案满足灰度试用前的数据安全要求，为生产环境提供可靠的数据保护。

**下一步**: 创建详细的实施计划（使用 writing-plans 技能）
