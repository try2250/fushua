# 数据备份自动化实施计划

## 概述

本计划基于 [backup-automation-design.md](../backup-automation-design.md) 设计文档，将数据备份自动化功能分解为可执行的任务。

## 任务分解

### 阶段 1：数据库模型和迁移（1-2小时）

**任务 1.1：创建 BackupLog 模型**
- 文件：`app/models/backup.py`（新建）
- 内容：
  - 定义 `BackupLog` 类
  - 字段：id, created_at, status, file_path, file_size, error_message, triggered_by, duration_seconds
  - 添加索引：created_at, status
  - 添加 `__repr__` 方法便于调试

**任务 1.2：创建数据库迁移**
- 文件：`alembic/versions/xxx_add_backup_logs.py`（新建）
- 内容：
  - 创建 `backup_logs` 表
  - 添加索引
  - 提供 downgrade 方法

**任务 1.3：更新模型导入**
- 文件：`app/models/__init__.py`
- 内容：添加 `from .backup import BackupLog`

**验证步骤**：
```bash
# 运行迁移
alembic upgrade head

# 验证表创建
psql $DATABASE_URL -c "\d backup_logs"
```

---

### 阶段 2：备份核心逻辑（2-3小时）

**任务 2.1：创建备份服务模块**
- 文件：`app/services/backup_service.py`（新建）
- 内容：
  - `trigger_backup()` - 主备份函数
    - 创建 BackupLog 记录（status='running'）
    - 调用 `scripts/backup_db.sh`
    - 记录文件路径、大小、耗时
    - 更新状态为 'success' 或 'failed'
    - 错误处理和超时控制（5分钟）
  - `validate_backup(backup_id)` - 验证备份完整性
    - 检查文件存在性
    - 检查文件大小（>100KB）
    - SQLite: PRAGMA integrity_check
    - PostgreSQL: gunzip -t
  - `cleanup_old_backups(keep_days)` - 清理旧备份
    - 查询超过保留天数的备份
    - 删除文件和数据库记录
  - `get_backup_stats()` - 获取统计信息
    - 总备份数、成功数、失败数
    - 成功率、总大小
    - 最近一次备份信息

**任务 2.2：更新 backup_db.sh 脚本**
- 文件：`scripts/backup_db.sh`
- 内容：
  - 确保脚本可执行（chmod +x）
  - 添加错误处理（set -e）
  - 输出备份文件路径到 stdout
  - 返回正确的退出码

**验证步骤**：
```python
# 单元测试
pytest tests/test_backup_service.py -v

# 手动测试
python -c "from app.services.backup_service import trigger_backup; trigger_backup('manual')"
```

---

### 阶段 3：API 端点（2-3小时）

**任务 3.1：创建备份路由**
- 文件：`app/routers/backup.py`（新建）
- 内容：
  - `POST /admin/backup/trigger` - 触发备份
    - 验证 X-Backup-Secret header
    - 调用 `trigger_backup('cron' or 'admin')`
    - 返回备份 ID 和文件信息
  - `GET /admin/backup` - 备份管理页面
    - 需要管理员权限
    - 渲染 Jinja2 模板
  - `GET /admin/backup/logs` - 获取备份列表（JSON）
    - 分页支持（page, page_size）
    - 按时间倒序
  - `GET /admin/backup/stats` - 获取统计信息
    - 调用 `get_backup_stats()`
  - `GET /admin/backup/download/{backup_id}` - 下载备份
    - 验证管理员权限
    - 验证备份存在
    - 防止路径遍历攻击
    - 返回 FileResponse
  - `POST /admin/backup/delete/{backup_id}` - 删除备份
    - 验证 CSRF token
    - 删除文件和数据库记录
  - `POST /admin/backup/validate/{backup_id}` - 验证备份
    - 调用 `validate_backup()`
  - `POST /admin/backup/cleanup` - 清理旧备份
    - 验证 CSRF token
    - 调用 `cleanup_old_backups()`

**任务 3.2：注册路由**
- 文件：`app/main.py`
- 内容：
  - 导入 `backup` 路由
  - 添加 `app.include_router(backup.router)`

**验证步骤**：
```bash
# 启动服务
uvicorn app.main:app --reload

# 测试端点
curl -X POST http://localhost:8000/admin/backup/trigger \
  -H "X-Backup-Secret: test_secret"

# 集成测试
pytest tests/test_backup_api.py -v
```

---

### 阶段 4：管理员界面（2-3小时）

**任务 4.1：创建 Jinja2 模板**
- 文件：`app/templates/admin/backup.html`（新建）
- 内容：
  - 继承 `base.html`
  - 备份历史表格
    - 列：时间、状态、触发方式、文件大小、操作
    - 操作按钮：下载、验证、删除
  - 手动触发按钮
  - 统计面板
    - 总备份数、成功率、总大小
    - 最近一次备份信息
  - 配置区域
    - 保留天数设置
    - 清理旧备份按钮
  - JavaScript 交互
    - AJAX 调用 API
    - 实时更新状态
    - 确认对话框（删除操作）

**任务 4.2：更新导航菜单**
- 文件：`app/templates/base.html`
- 内容：
  - 在管理员菜单中添加"数据备份"链接
  - 仅对管理员可见

**验证步骤**：
- 访问 http://localhost:8000/admin/backup
- 测试所有按钮和交互
- 验证权限控制（非管理员无法访问）

---

### 阶段 5：Render 配置（30分钟）

**任务 5.1：更新 render.yaml**
- 文件：`render.yaml`
- 内容：
  - 添加 Cron Job 配置
    ```yaml
    - type: cronjob
      name: fushua-backup
      env: docker
      schedule: "0 2 * * *"  # 每日 2:00 UTC
      dockerCommand: >
        curl -X POST https://fushua.onrender.com/admin/backup/trigger
        -H "X-Backup-Secret: $BACKUP_SECRET"
        -H "Content-Type: application/json"
      envVars:
        - key: BACKUP_SECRET
          sync: false  # 手动设置
    ```
  - 在 Web Service 中添加 `BACKUP_SECRET` 环境变量

**任务 5.2：生成并配置密钥**
- 在 Render Dashboard 中：
  - 生成随机密钥：`openssl rand -hex 32`
  - 在 Web Service 和 Cron Job 中设置 `BACKUP_SECRET`

**验证步骤**：
- 部署到 Render
- 手动触发 Cron Job 测试
- 检查 Cron Job 日志

---

### 阶段 6：测试（2-3小时）

**任务 6.1：单元测试**
- 文件：`tests/test_backup_service.py`（新建）
- 测试用例：
  - `test_trigger_backup_success` - 成功备份
  - `test_trigger_backup_failure` - 备份失败处理
  - `test_validate_backup_valid` - 验证有效备份
  - `test_validate_backup_invalid` - 验证无效备份
  - `test_cleanup_old_backups` - 清理旧备份
  - `test_get_backup_stats` - 统计信息

**任务 6.2：API 集成测试**
- 文件：`tests/test_backup_api.py`（新建）
- 测试用例：
  - `test_trigger_backup_with_valid_secret` - 有效密钥触发
  - `test_trigger_backup_with_invalid_secret` - 无效密钥拒绝
  - `test_backup_list_requires_admin` - 权限控制
  - `test_download_backup` - 下载备份
  - `test_delete_backup` - 删除备份
  - `test_validate_backup_api` - 验证 API

**任务 6.3：端到端测试**
- 文件：`tests/test_backup_e2e.py`（新建）
- 测试场景：
  - 完整备份流程（触发 → 验证 → 下载 → 删除）
  - Cron Job 模拟（调用 trigger 端点）
  - 管理员界面交互（使用 Playwright）

**验证步骤**：
```bash
# 运行所有测试
pytest tests/test_backup*.py -v --cov=app.services.backup_service --cov=app.routers.backup

# 检查覆盖率（目标 >80%）
pytest --cov-report=html
```

---

### 阶段 7：文档和部署（1小时）

**任务 7.1：创建恢复演练文档**
- 文件：`docs/backup-recovery-guide.md`（新建）
- 内容：
  - 备份文件位置
  - SQLite 恢复步骤
  - PostgreSQL 恢复步骤
  - 验证方法
  - 回滚计划
  - 每月演练清单

**任务 7.2：更新 README**
- 文件：`README.md`
- 内容：
  - 添加"数据备份"章节
  - 说明自动备份机制
  - 管理员操作指南

**任务 7.3：部署清单**
- [ ] 运行数据库迁移：`alembic upgrade head`
- [ ] 更新 `render.yaml` 并推送
- [ ] 在 Render Dashboard 配置 `BACKUP_SECRET`
- [ ] 创建 Cron Job
- [ ] 手动触发测试备份
- [ ] 验证备份文件生成
- [ ] 测试管理员界面
- [ ] 设置监控告警（可选）

---

## 文件清单

### 新建文件
1. `app/models/backup.py` - BackupLog 模型
2. `app/services/backup_service.py` - 备份核心逻辑
3. `app/routers/backup.py` - API 端点
4. `app/templates/admin/backup.html` - 管理界面
5. `alembic/versions/xxx_add_backup_logs.py` - 数据库迁移
6. `tests/test_backup_service.py` - 单元测试
7. `tests/test_backup_api.py` - API 测试
8. `tests/test_backup_e2e.py` - 端到端测试
9. `docs/backup-recovery-guide.md` - 恢复指南

### 修改文件
1. `app/models/__init__.py` - 导入 BackupLog
2. `app/main.py` - 注册备份路由
3. `app/templates/base.html` - 添加导航链接
4. `render.yaml` - 添加 Cron Job 配置
5. `README.md` - 添加备份文档
6. `scripts/backup_db.sh` - 增强错误处理

---

## 时间估算

| 阶段 | 预计时间 | 依赖 |
|------|---------|------|
| 1. 数据库模型和迁移 | 1-2小时 | 无 |
| 2. 备份核心逻辑 | 2-3小时 | 阶段1 |
| 3. API 端点 | 2-3小时 | 阶段2 |
| 4. 管理员界面 | 2-3小时 | 阶段3 |
| 5. Render 配置 | 30分钟 | 阶段3 |
| 6. 测试 | 2-3小时 | 阶段2-4 |
| 7. 文档和部署 | 1小时 | 阶段1-6 |
| **总计** | **11-16小时** | |

---

## 风险和缓解措施

### 风险 1：备份脚本执行失败
- **影响**：无法生成备份文件
- **缓解**：
  - 在 `backup_service.py` 中添加详细错误日志
  - 设置超时机制（5分钟）
  - 失败时发送告警（连续3次失败）

### 风险 2：Render 免费版存储限制
- **影响**：备份文件占用磁盘空间
- **缓解**：
  - 实现自动清理机制（默认保留30天）
  - 提供手动下载功能
  - 在管理界面显示存储使用情况

### 风险 3：Cron Job 调用失败
- **影响**：自动备份不执行
- **缓解**：
  - 在 Render Dashboard 监控 Cron Job 状态
  - 设置失败通知
  - 提供手动触发备份功能

### 风险 4：备份文件损坏
- **影响**：无法恢复数据
- **缓解**：
  - 实现完整性验证机制
  - 每月进行恢复演练
  - 保留多个历史备份

---

## 成功标准

- [ ] 每日自动备份成功执行
- [ ] 管理员可以查看备份历史
- [ ] 管理员可以手动触发备份
- [ ] 管理员可以下载备份文件
- [ ] 管理员可以验证备份完整性
- [ ] 管理员可以删除旧备份
- [ ] 所有测试通过（覆盖率 >80%）
- [ ] 恢复演练文档完整
- [ ] Render Cron Job 配置正确

---

## 下一步行动

1. **立即开始**：阶段1（数据库模型和迁移）
2. **并行任务**：可以在等待代码审查时编写测试用例
3. **部署前检查**：完成所有测试后再部署到 Render

---

## 参考文档

- [设计文档](../backup-automation-design.md)
- [Render Cron Jobs 文档](https://render.com/docs/cronjobs)
- [FastAPI 文件上传/下载](https://fastapi.tiangolo.com/tutorial/request-files/)
- [SQLAlchemy 模型定义](https://docs.sqlalchemy.org/en/14/orm/tutorial.html)
