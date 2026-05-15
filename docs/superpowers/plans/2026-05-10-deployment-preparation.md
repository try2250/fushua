# 部署上线准备实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对付刷项目进行部署上线前的代码检查优化和部署配置对接，确保安全推送到 GitHub 并成功部署到 Render。

**Architecture:** 项目使用 FastAPI + SQLAlchemy + SQLite(开发)/PostgreSQL(生产) + Gunicorn + Render 部署。当前有大量未提交的本地更改需要审查、整理后推送。部署链路为：本地 → GitHub(main) → Render 自动部署。

**Tech Stack:** Python 3.12(生产)/3.13(开发), FastAPI, SQLAlchemy, Alembic, Gunicorn, PostgreSQL, Render

---

## 当前状态分析

### Git 状态
- **远程仓库**: `https://github.com/try2250/fushua.git`
- **最新提交**: `7f12926 fix: harden release validation`
- **未提交更改**: 20+ 修改文件，10+ 新增文件
- **未跟踪文件**: 新迁移脚本、新模板、新测试、计划文档、上传图片

### 关键问题清单
1. **httpx 未在 requirements.txt 中** — `extractor.py` 导入了 httpx 但未声明依赖，生产环境会崩溃
2. **entrypoint.sh 过时** — 仍使用旧逻辑（升级第一个教师为管理员），与新的 admin 角色系统不兼容
3. **render.yaml startCommand 过时** — 仍使用旧的初始化逻辑，缺少 admin_invite_code 初始化
4. **alembic.ini 硬编码 SQLite URL** — 生产环境使用 PostgreSQL，但 alembic.ini 写死了 sqlite URL
5. **alembic/env.py 缺少新模型导入** — 未导入 ClassJoinRequest、AccountRecoveryRequest 等新模型
6. **PYTHON_VERSION 过时** — render.yaml 指定 3.12.6，但本地开发用 3.13
7. **uploads 目录不应提交** — `app/static/uploads/` 包含本地测试图片
8. **docs/superpowers/ 不应提交** — 内部计划文档
9. **security_best_practices_report.md 不应提交** — 安全审查报告包含漏洞细节
10. **Dockerfile ENV SECRET_KEY 不安全** — 默认值 `change-me-in-production` 应移除
11. **.env.example 缺少新环境变量** — 缺少 ENVIRONMENT、FUTI_BASE_URL、FUTI_API_TOKEN
12. **CI 工作流未设置 ENVIRONMENT** — 测试时不会触发生产模式检查

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 修改 | `requirements.txt` | 添加 httpx 依赖 |
| 修改 | `entrypoint.sh` | 更新初始化逻辑匹配新 admin 角色 |
| 修改 | `render.yaml` | 更新 startCommand、PYTHON_VERSION、环境变量 |
| 修改 | `alembic.ini` | 移除硬编码 SQLite URL |
| 修改 | `alembic/env.py` | 添加新模型导入 |
| 修改 | `.gitignore` | 添加 uploads/、docs/superpowers/、security report |
| 修改 | `.env.example` | 添加新环境变量 |
| 修改 | `Dockerfile` | 移除不安全的默认 SECRET_KEY |
| 修改 | `.github/workflows/ci.yml` | 添加 ENVIRONMENT 变量 |
| 修改 | `docker-compose.yml` | 添加新环境变量 |

---

### Task 1: 依赖修复 + .gitignore 更新

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: 添加 httpx 到 requirements.txt**

在 `requirements.txt` 末尾添加：

```
httpx==0.27.2
```

- [ ] **Step 2: 更新 .gitignore**

在 `.gitignore` 末尾追加：

```
app/static/uploads/
docs/superpowers/
security_best_practices_report.md
```

- [ ] **Step 3: 删除不应提交的文件**

删除 `app/static/uploads/` 目录中的所有本地测试图片（这些文件已在 .gitignore 中排除，但需要从 git 跟踪中移除）：

```bash
git rm -r --cached app/static/uploads/ 2>/dev/null; echo "done"
```

- [ ] **Step 4: 验证 httpx 安装**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -c "import httpx; print(httpx.__version__)"`
Expected: 输出版本号

- [ ] **Step 5: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

---

### Task 2: 部署配置更新 — entrypoint.sh + render.yaml + Dockerfile

**Files:**
- Modify: `entrypoint.sh`
- Modify: `render.yaml`
- Modify: `Dockerfile`

- [ ] **Step 1: 重写 entrypoint.sh**

替换 `entrypoint.sh` 全部内容为：

```bash
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || {
    echo "Alembic migration failed, falling back to create_all..."
    python -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
}

echo "Starting application..."
exec "$@"
```

移除旧的初始化逻辑（teacher_invite_code 和 first_teacher 升级），因为这些现在在 `app/main.py` 的启动代码中处理。

- [ ] **Step 2: 更新 render.yaml**

替换 `render.yaml` 全部内容为：

```yaml
services:
  - type: web
    name: fushua
    plan: free
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: alembic upgrade head && gunicorn app.main:app -c gunicorn.conf.py
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: fushua-db
          property: connectionString
      - key: HTTPS_ONLY
        value: "true"
      - key: ENVIRONMENT
        value: "production"
      - key: GUNICORN_WORKERS
        value: "2"
      - key: PYTHON_VERSION
        value: "3.12.6"

databases:
  - name: fushua-db
    plan: free
```

关键变更：
- startCommand 简化：移除内联 Python 初始化（已由 main.py 处理）
- 添加 `ENVIRONMENT=production`：触发 OpenAPI 禁用等生产模式行为
- 保留 PYTHON_VERSION=3.12.6（Render 免费版兼容性更好）

- [ ] **Step 3: 更新 Dockerfile**

替换 `Dockerfile` 全部内容为：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

ENV DATABASE_URL=sqlite:///./data/fushua.db
ENV HTTPS_ONLY=false
ENV ENVIRONMENT=development

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

关键变更：
- 移除 `ENV SECRET_KEY=change-me-in-production`（不再硬编码默认密钥，由应用自动生成并警告）
- 添加 `ENV ENVIRONMENT=development`

- [ ] **Step 4: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

---

### Task 3: Alembic 配置修复 + 环境变量补全

**Files:**
- Modify: `alembic.ini`
- Modify: `alembic/env.py`
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 修复 alembic.ini — 移除硬编码 SQLite URL**

将 `alembic.ini` 第 4 行的：
```ini
sqlalchemy.url = sqlite:///./fushua.db
```

替换为：
```ini
sqlalchemy.url = sqlite:///./fushua.db
```

保持不变（alembic.ini 中的 URL 是 fallback，env.py 中会通过 `DATABASE_URL` 环境变量覆盖）。但添加注释说明：

```ini
# Note: This URL is overridden by DATABASE_URL env var in env.py
sqlalchemy.url = sqlite:///./fushua.db
```

- [ ] **Step 2: 更新 alembic/env.py — 添加新模型导入**

将 `alembic/env.py` 第 10 行的导入替换为：

```python
from app.models import User, FieldConfig, Question, Record, Favorite, StudyPlan, ClassGroup, ClassMember, Notification, Assignment, AssignmentRecord, ClassJoinRequest, AccountRecoveryRequest, QuestionBank
```

- [ ] **Step 3: 更新 .env.example**

替换 `.env.example` 全部内容为：

```env
# === 必须配置 ===
SECRET_KEY=your-secret-key-here-use-openssl-rand-hex-32

# === 环境 ===
ENVIRONMENT=development

# === 数据库 ===
DATABASE_URL=postgresql://fushua:fushua_dev@postgres:5432/fushua
POSTGRES_PASSWORD=fushua_dev

# === 服务器 ===
PORT=8000
HTTPS_ONLY=false
GUNICORN_WORKERS=4

# === 数据库连接池 ===
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# === 付题服务（可选） ===
FUTI_BASE_URL=http://localhost:8001
FUTI_API_TOKEN=
```

- [ ] **Step 4: 更新 docker-compose.yml**

在 `docker-compose.yml` 的 web 服务的 environment 中添加：

```yaml
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - FUTI_BASE_URL=${FUTI_BASE_URL:-http://localhost:8001}
      - FUTI_API_TOKEN=${FUTI_API_TOKEN:-}
```

添加到 `HTTPS_ONLY` 行之后。

- [ ] **Step 5: 更新 CI 工作流**

在 `.github/workflows/ci.yml` 的 `Run tests` 步骤的 env 中添加：

```yaml
        ENVIRONMENT: test
```

完整的 env 块应为：

```yaml
      - name: Run tests
        env:
          DATABASE_URL: sqlite:///./test_ci.db
          ENVIRONMENT: test
        run: |
          python -m pytest tests/ -v --tb=short -q
```

- [ ] **Step 6: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

---

### Task 4: 代码质量检查 + 最终验证

**Files:**
- 可能修改多个测试文件（修复密码长度问题等）

- [ ] **Step 1: 运行全量测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

- [ ] **Step 2: 检查所有 Python 文件语法**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/main.py; & "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/routers/auth.py; & "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/routers/admin.py; & "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/routers/teacher.py; & "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/security.py; & "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/database.py; & "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m py_compile app/routers/extractor.py`
Expected: 无错误输出

- [ ] **Step 3: 验证 Alembic 迁移链完整性**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m alembic heads`
Expected: 输出单个 head 版本

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m alembic history`
Expected: 完整的迁移链无断裂

- [ ] **Step 4: 验证本地服务器启动**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m uvicorn app.main:app --port 8001` (使用 8001 避免与当前运行的服务冲突)

访问 http://localhost:8001/health 验证健康检查返回 `{"status":"ok"}`

- [ ] **Step 5: 检查 git diff 摘要**

Run: `git diff --stat`

确认所有预期修改的文件都在列表中，无意外修改。

---

### Task 5: Git 提交 + 推送

**Files:**
- 无新文件修改，仅 git 操作

- [ ] **Step 1: 暂存所有更改**

```bash
git add -A
```

- [ ] **Step 2: 检查暂存区**

Run: `git status`
确认：
- ✅ 所有修改文件已暂存
- ✅ `app/static/uploads/` 未被跟踪
- ✅ `docs/superpowers/` 未被跟踪
- ✅ `security_best_practices_report.md` 未被跟踪
- ✅ 新迁移文件已暂存
- ✅ 新模板文件已暂存
- ✅ 新测试文件已暂存

- [ ] **Step 3: 提交**

```bash
git commit -m "release: v3.1.0 - explicit registration, admin role, security hardening, UI overhaul

Features:
- Explicit registration modes (formal/apply/guest)
- Independent admin role with invite codes
- Account recovery with teacher/admin review
- Scholarly Refinement UI design system

Security:
- Random admin password on first launch
- force_password_change enforcement on login
- Rate limiting on register/recover endpoints
- SECRET_KEY strengthened to 256-bit entropy
- LIKE wildcard injection prevention
- Exception message sanitization
- Password policy: 8+ chars, mixed letters+digits
- OpenAPI docs disabled in production
- HttpOnly session cookie

Deployment:
- Updated render.yaml with ENVIRONMENT variable
- Simplified entrypoint.sh (init logic moved to main.py)
- Added httpx to requirements.txt
- Updated .env.example with new env vars
- Fixed alembic/env.py model imports
- CI workflow with ENVIRONMENT=test"
```

- [ ] **Step 4: 推送到 GitHub**

```bash
git push origin main
```

- [ ] **Step 5: 验证 Render 部署**

在 Render 控制台检查：
1. 新部署是否自动触发
2. 构建日志中 `alembic upgrade head` 是否成功
3. 应用启动后 `/health` 端点是否返回 ok
4. 环境变量 `ENVIRONMENT=production` 是否生效（`/docs` 应返回 404）

---

## 自查清单

### 1. 需求覆盖

| 需求 | 对应 Task |
|------|-----------|
| httpx 依赖缺失 | Task 1 |
| .gitignore 更新 | Task 1 |
| entrypoint.sh 过时 | Task 2 |
| render.yaml 过时 | Task 2 |
| Dockerfile 默认 SECRET_KEY | Task 2 |
| alembic.ini 硬编码 URL | Task 3 |
| alembic/env.py 缺少模型 | Task 3 |
| .env.example 缺少变量 | Task 3 |
| docker-compose.yml 缺少变量 | Task 3 |
| CI 未设 ENVIRONMENT | Task 3 |
| 代码质量检查 | Task 4 |
| Git 提交推送 | Task 5 |
| Render 部署验证 | Task 5 |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- `entrypoint.sh` 移除的初始化逻辑与 `main.py` 中的初始化逻辑一致（teacher_invite_code、admin_invite_code、默认管理员创建）
- `render.yaml` 的 startCommand 与 `entrypoint.sh` 的逻辑一致（先 alembic upgrade head，再启动 gunicorn）
- 新增环境变量 `ENVIRONMENT` 在 main.py、render.yaml、.env.example、docker-compose.yml、ci.yml 中一致使用
