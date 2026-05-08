# 付刷生产交付上线实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将"付刷"项目从开发状态推进到可安全、稳定交付上线的生产级状态，覆盖安全加固、数据完整性、错误处理、性能优化、部署基础设施和运维可观测性六大维度。

**Architecture:** FastAPI + Jinja2 SSR + SQLAlchemy + SQLite（生产环境切换 PostgreSQL），通过 Docker 容器化部署，Gunicorn + Uvicorn worker 运行，Alembic 管理数据库迁移，结构化日志输出到 stdout 供日志收集器采集。

**Tech Stack:** FastAPI 0.115, SQLAlchemy 2.0, Alembic, Gunicorn, Uvicorn, PostgreSQL (psycopg2-binary), Docker, slowapi (限流), reportlab

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `app/main.py` | 应用入口，中间件注册，异常处理器，健康检查 |
| `app/database.py` | 数据库连接，支持 SQLite/PostgreSQL 切换，连接池配置 |
| `app/models.py` | 数据模型，增加唯一约束和复合索引 |
| `app/auth.py` | 认证逻辑，增加密码复杂度校验 |
| `app/security.py` | **新建** — 限流配置、CSRF 校验函数、输入清洗工具 |
| `app/routers/auth.py` | 注册/登录，增加限流、密码复杂度、登录失败锁定 |
| `app/routers/teacher.py` | 教师路由，增加输入校验、CSRF 校验 |
| `app/routers/student.py` | 学生路由，增加输入校验、CSRF 校验 |
| `app/routers/assignment.py` | 作业路由，增加输入校验、CSRF 校验 |
| `app/routers/classgroup.py` | 班级路由，增加输入校验、CSRF 校验 |
| `app/routers/pages.py` | 页面路由，增加错误处理 |
| `app/templates/base.html` | 基础模板，增加 CSP meta、favicon、PWA 图标引用 |
| `app/templates/error.html` | **新建** — 通用错误页面 (404/403/500) |
| `app/utils/report.py` | PDF 报告，增加输入清洗 |
| `app/static/icon-192.png` | **新建** — PWA 图标 192x192 |
| `app/static/icon-512.png` | **新建** — PWA 图标 512x512 |
| `app/static/favicon.ico` | **新建** — 网站图标 |
| `alembic.ini` | **新建** — Alembic 配置 |
| `alembic/env.py` | **新建** — Alembic 环境配置 |
| `alembic/versions/` | **新建** — 迁移版本目录 |
| `.env.example` | **新建** — 环境变量示例 |
| `.gitignore` | **新建** — Git 忽略规则 |
| `Dockerfile` | **新建** — Docker 镜像构建 |
| `docker-compose.yml` | **新建** — Docker Compose 编排 |
| `gunicorn.conf.py` | **新建** — Gunicorn 生产配置 |
| `requirements.txt` | 依赖，增加生产依赖 |
| `tests/test_production.py` | **新建** — 生产级测试（CSRF 校验、限流、输入校验、错误页面） |

---

### Task 1: 数据库模型加固 — 唯一约束与复合索引

**Files:**
- Modify: `app/models.py`
- Test: `tests/test_production.py`

- [ ] **Step 1: 写失败测试 — Favorite 唯一约束**

```python
def test_favorite_unique_constraint(client, db_session):
    from tests.conftest import register_and_login, create_test_question, create_test_user
    user = create_test_user(db_session, username="favuser")
    q = create_test_question(db_session, created_by=user.id)
    register_and_login(client, username="favuser2", role="student")
    client.post(f"/student/favorites/{q.id}/add", follow_redirects=True)
    resp = client.post(f"/student/favorites/{q.id}/add", follow_redirects=True)
    favs = db_session.query(Favorite).filter(Favorite.user_id == user.id, Favorite.question_id == q.id).all()
    assert len(favs) <= 1
```

- [ ] **Step 2: 运行测试确认当前行为**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_favorite_unique_constraint -v`
Expected: 可能 PASS（路由已做去重），但数据库层无约束

- [ ] **Step 3: 在 models.py 中添加唯一约束和复合索引**

在 `Favorite` 类中添加 `__table_args__`:
```python
class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_favorite_user_question"),
    )
```

在 `ClassMember` 类中添加:
```python
class ClassMember(Base):
    __tablename__ = "class_members"
    __table_args__ = (
        UniqueConstraint("class_id", "user_id", name="uq_classmember_class_user"),
    )
```

在 `Question` 类中添加复合索引:
```python
class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_subject_semester", "subject", "semester"),
        Index("ix_questions_subject_chapter", "subject", "chapter"),
    )
```

在 `Record` 类中添加复合索引:
```python
class Record(Base):
    __tablename__ = "records"
    __table_args__ = (
        Index("ix_records_user_created", "user_id", "created_at"),
    )
```

需要在文件顶部添加导入: `from sqlalchemy import UniqueConstraint, Index`

- [ ] **Step 4: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_favorite_unique_constraint -v`
Expected: PASS

- [ ] **Step 5: 运行全部测试确认无回归**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v`
Expected: 全部 PASS

---

### Task 2: 数据库连接池与 PostgreSQL 支持

**Files:**
- Modify: `app/database.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 写失败测试 — 数据库连接使用环境变量**

```python
import os
def test_database_url_from_env():
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
    from importlib import reload
    import app.database
    reload(app.database)
    assert "postgresql" in app.database.SQLALCHEMY_DATABASE_URL
    del os.environ["DATABASE_URL"]
    reload(app.database)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_database_url_from_env -v`
Expected: FAIL — 当前硬编码 SQLite

- [ ] **Step 3: 修改 database.py 支持环境变量切换**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./fushua.db"
)

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
    max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "10")),
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: 在 requirements.txt 添加 psycopg2-binary**

在 `requirements.txt` 末尾添加:
```
psycopg2-binary==2.9.9
alembic==1.13.2
gunicorn==22.0.0
slowapi==1.0.1
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_database_url_from_env -v`
Expected: PASS

---

### Task 3: Alembic 数据库迁移

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/` (空目录)

- [ ] **Step 1: 安装 alembic 并初始化**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pip install alembic==1.13.2`

- [ ] **Step 2: 创建 alembic.ini**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = sqlite:///./fushua.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: 创建 alembic/env.py**

```python
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import User, FieldConfig, Question, Record, Favorite, StudyPlan, ClassGroup, ClassMember, Notification, Assignment, AssignmentRecord

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
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
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 创建 alembic/script.py.mako**

```mako
\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 5: 创建 alembic/versions 目录并生成初始迁移**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && mkdir alembic\versions 2>nul & py -m alembic revision --autogenerate -m "initial_schema"`

- [ ] **Step 6: 验证迁移可以执行**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m alembic upgrade head`
Expected: 无报错

---

### Task 4: CSRF 校验强制执行

**Files:**
- Create: `app/security.py`
- Modify: `app/routers/auth.py`
- Modify: `app/routers/teacher.py`
- Modify: `app/routers/student.py`
- Modify: `app/routers/assignment.py`
- Modify: `app/routers/classgroup.py`

- [ ] **Step 1: 写失败测试 — POST 请求缺少 CSRF token 被拒绝**

```python
def test_csrf_required_for_login(client, db_session):
    from tests.conftest import create_test_user
    create_test_user(db_session, username="csrfuser")
    resp = client.post("/login", data={
        "username": "csrfuser",
        "password": "123456",
    }, follow_redirects=False)
    assert resp.status_code in (403, 400)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_csrf_required_for_login -v`
Expected: FAIL — 当前不校验 CSRF token

- [ ] **Step 3: 创建 app/security.py，添加 CSRF 校验函数**

```python
from fastapi import Request, HTTPException


def validate_csrf(request: Request) -> None:
    token = request.session.get("csrf_token", "")
    if not token:
        raise HTTPException(status_code=403, detail="缺少 CSRF token")
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        form_token = None
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            pass
        header_token = request.headers.get("X-CSRF-Token", "")
        if header_token and header_token == token:
            return
    return


async def validate_csrf_async(request: Request) -> None:
    token = request.session.get("csrf_token", "")
    if not token:
        raise HTTPException(status_code=403, detail="缺少 CSRF token")
    if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
        return
    form = await request.form()
    form_token = form.get("_csrf_token", "")
    if not form_token or form_token != token:
        raise HTTPException(status_code=403, detail="CSRF 校验失败")


def sanitize_input(value: str, max_length: int = 500) -> str:
    if not value:
        return value
    value = value.strip()
    if len(value) > max_length:
        value = value[:max_length]
    return value
```

- [ ] **Step 4: 在 auth.py 路由中添加 CSRF 校验**

在 `register` 和 `login` 的 POST 处理函数中，在业务逻辑前添加:
```python
from app.security import validate_csrf_async
```

在 `register` 函数体开头添加:
```python
    await validate_csrf_async(request)
```

在 `login` 函数体开头添加:
```python
    await validate_csrf_async(request)
```

- [ ] **Step 5: 在 teacher.py 所有 POST 路由中添加 CSRF 校验**

在 `create_question`, `edit_question`, `create_field`, `update_field`, `delete_field`, `import_questions`, `delete_question` 函数体开头添加:
```python
    await validate_csrf_async(request)
```

- [ ] **Step 6: 在 student.py 所有 POST 路由中添加 CSRF 校验**

在 `submit_practice`, `add_favorite`, `remove_favorite`, `create_plan`, `delete_plan`, `mark_notification_read`, `mark_all_notifications_read` 函数体开头添加:
```python
    await validate_csrf_async(request)
```

- [ ] **Step 7: 在 assignment.py 所有 POST 路由中添加 CSRF 校验**

在 `create_assignment`, `complete_assignment` 函数体开头添加:
```python
    await validate_csrf_async(request)
```

- [ ] **Step 8: 在 classgroup.py 所有 POST 路由中添加 CSRF 校验**

在 `create_class`, `add_member`, `remove_member`, `delete_class` 函数体开头添加:
```python
    await validate_csrf_async(request)
```

- [ ] **Step 9: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_csrf_required_for_login -v`
Expected: PASS

- [ ] **Step 10: 修复已有测试 — 确保所有测试 POST 请求都携带 _csrf_token**

检查 `tests/conftest.py` 中 `login_as` 和 `register_and_login` 已包含 `_csrf_token`。确认所有测试文件中的 POST 请求都携带了 `_csrf_token`。运行全量测试:

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v`
Expected: 全部 PASS

---

### Task 5: 登录限流与密码复杂度

**Files:**
- Modify: `app/security.py`
- Modify: `app/routers/auth.py`
- Modify: `app/auth.py`

- [ ] **Step 1: 写失败测试 — 连续登录失败后锁定**

```python
def test_login_rate_limit(client, db_session):
    from tests.conftest import create_test_user, get_csrf_token
    create_test_user(db_session, username="ratelimituser")
    for i in range(6):
        csrf = get_csrf_token(client)
        resp = client.post("/login", data={
            "username": "ratelimituser",
            "password": "wrongpass",
            "_csrf_token": csrf,
        }, follow_redirects=False)
    resp = client.post("/login", data={
        "username": "ratelimituser",
        "password": "123456",
        "_csrf_token": get_csrf_token(client),
    }, follow_redirects=False)
    assert resp.status_code == 429
```

- [ ] **Step 2: 写失败测试 — 弱密码注册被拒绝**

```python
def test_weak_password_rejected(client, db_session):
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "weakpwuser",
        "password": "123",
        "role": "student",
        "display_name": "weakpwuser",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "密码" in resp.text or resp.status_code != 303
```

- [ ] **Step 3: 在 security.py 中添加限流和密码校验**

在 `app/security.py` 中添加:
```python
import time
from collections import defaultdict

_login_attempts = defaultdict(list)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


def check_login_rate_limit(username: str) -> None:
    now = time.time()
    attempts = _login_attempts[username]
    attempts[:] = [t for t in attempts if now - t < LOGIN_LOCKOUT_SECONDS]
    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=429,
            detail=f"登录失败次数过多，请{LOGIN_LOCKOUT_SECONDS}秒后重试"
        )


def record_login_attempt(username: str) -> None:
    _login_attempts[username].append(time.time())


def validate_password_strength(password: str) -> str | None:
    if len(password) < 6:
        return "密码长度至少6位"
    if password.isdigit():
        return "密码不能为纯数字"
    return None
```

- [ ] **Step 4: 在 auth.py 路由中集成限流和密码校验**

修改 `register` 函数，在 `existing = ...` 之前添加:
```python
    pw_error = validate_password_strength(password)
    if pw_error:
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": pw_error, "csrf_token": request.session.get("csrf_token", "")}
        )
```

修改 `login` 函数，在 `user = db.query(...)` 之前添加:
```python
    check_login_rate_limit(username)
```

在登录失败时（`if not user or not User.verify_password(...)` 分支）添加:
```python
    record_login_attempt(username)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_login_rate_limit tests/test_production.py::test_weak_password_rejected -v`
Expected: PASS

---

### Task 6: 全局异常处理与错误页面

**Files:**
- Modify: `app/main.py`
- Create: `app/templates/error.html`

- [ ] **Step 1: 写失败测试 — 404 返回友好错误页面**

```python
def test_404_error_page(client):
    resp = client.get("/nonexistent-page-12345", follow_redirects=True)
    assert resp.status_code == 404
    assert "页面未找到" in resp.text or "404" in resp.text
```

```python
def test_500_error_page(client):
    resp = client.get("/teacher/questions", follow_redirects=True)
    assert resp.status_code in (303, 403)
```

- [ ] **Step 2: 创建 app/templates/error.html**

```html
{% extends "base.html" %}
{% block title %}{{ error_title }} - 付刷{% endblock %}
{% block content %}
<div class="card" style="text-align:center;padding:3rem;">
    <h1 style="font-size:4rem;margin-bottom:0.5rem;">{{ error_code }}</h1>
    <h2>{{ error_title }}</h2>
    <p style="color:var(--text-secondary);margin:1rem 0;">{{ error_message }}</p>
    <a href="/" class="btn btn-primary">返回首页</a>
</div>
{% endblock %}
```

- [ ] **Step 3: 在 main.py 中添加全局异常处理器**

在 `app = FastAPI(...)` 之后添加:
```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_map = {
        400: ("请求错误", "您的请求无法被处理"),
        403: ("访问被拒绝", "您没有权限访问此页面"),
        404: ("页面未找到", "您访问的页面不存在"),
        405: ("方法不允许", "该请求方法不被允许"),
        429: ("请求过于频繁", "请稍后再试"),
        500: ("服务器错误", "服务器内部发生错误，请稍后重试"),
    }
    title, message = error_map.get(exc.status_code, ("出错了", str(exc.detail or "")))
    if exc.detail and exc.status_code not in (404, 405):
        message = exc.detail
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": exc.status_code, "error_title": title, "error_message": message},
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": 400, "error_title": "请求错误", "error_message": "提交的数据格式不正确"},
        status_code=400,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("fushua").exception("Unhandled exception")
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": 500, "error_title": "服务器错误", "error_message": "服务器内部发生错误，请稍后重试"},
        status_code=500,
    )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_404_error_page tests/test_production.py::test_500_error_page -v`
Expected: PASS

---

### Task 7: 健康检查端点与结构化日志

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: 写失败测试 — 健康检查端点**

```python
def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_health_check -v`
Expected: FAIL — 404

- [ ] **Step 3: 在 main.py 中添加健康检查端点和日志配置**

在路由注册之前添加:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fushua")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "3.0.0"}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_health_check -v`
Expected: PASS

---

### Task 8: 输入校验与清洗

**Files:**
- Modify: `app/routers/auth.py`
- Modify: `app/routers/teacher.py`
- Modify: `app/routers/student.py`
- Modify: `app/routers/assignment.py`
- Modify: `app/routers/classgroup.py`

- [ ] **Step 1: 写失败测试 — 超长用户名被截断/拒绝**

```python
def test_username_length_limit(client, db_session):
    csrf = get_csrf_token(client)
    long_name = "a" * 200
    resp = client.post("/register", data={
        "username": long_name,
        "password": "password123",
        "role": "student",
        "display_name": "test",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert resp.status_code != 500
```

```python
def test_question_content_required(client, db_session):
    from tests.conftest import register_and_login, create_test_user
    create_test_user(db_session, username="teacher1", role="teacher")
    register_and_login(client, username="teacher1", role="teacher")
    csrf = get_csrf_token(client)
    resp = client.post("/teacher/questions/create", data={
        "subject": "数学",
        "content": "",
        "answer": "",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "必填" in resp.text or resp.status_code == 200
```

- [ ] **Step 2: 在 auth.py 中添加用户名和密码长度校验**

修改 `register` 函数，在 `existing = ...` 之前添加:
```python
    username = sanitize_input(username, max_length=50)
    display_name = sanitize_input(display_name, max_length=100)
    if len(username) < 2:
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": "用户名至少2个字符", "csrf_token": request.session.get("csrf_token", "")}
        )
```

需要在 `auth.py` 路由文件顶部添加:
```python
from app.security import sanitize_input, validate_password_strength
```

- [ ] **Step 3: 在 teacher.py 中添加字段校验**

在 `create_question` 函数中，对 `subject`, `content`, `answer` 进行清洗:
```python
    subject = sanitize_input(subject, max_length=20)
    content = sanitize_input(content, max_length=5000)
    answer = sanitize_input(answer, max_length=200)
```

在 `create_field` 函数中:
```python
    field_key = sanitize_input(field_key, max_length=50)
    field_label = sanitize_input(field_label, max_length=100)
```

需要在 `teacher.py` 顶部添加:
```python
from app.security import sanitize_input
```

- [ ] **Step 4: 在 assignment.py 中添加校验**

在 `create_assignment` 函数中:
```python
    title = sanitize_input(title, max_length=200)
    description = sanitize_input(description, max_length=2000)
    valid_ids = [qid.strip() for qid in question_ids.split(",") if qid.strip().isdigit()]
    if not valid_ids:
        ...
    question_ids = ",".join(valid_ids)
```

- [ ] **Step 5: 在 classgroup.py 中添加校验**

在 `create_class` 函数中:
```python
    name = sanitize_input(name, max_length=100)
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py -v`
Expected: 全部 PASS

---

### Task 9: 安全头完善与 Content-Security-Policy

**Files:**
- Modify: `app/main.py`
- Modify: `app/templates/base.html`

- [ ] **Step 1: 写测试 — 安全头存在性检查**

```python
def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in resp.headers
```

- [ ] **Step 2: 在 SecurityHeadersMiddleware 中添加 CSP 头**

修改 `SecurityHeadersMiddleware`:
```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response
```

- [ ] **Step 3: 在 base.html 中添加 CSP meta 标签作为备用**

在 `<head>` 中添加:
```html
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_security_headers -v`
Expected: PASS

---

### Task 10: PWA 图标与 Favicon

**Files:**
- Create: `app/static/icon-192.png`
- Create: `app/static/icon-512.png`
- Create: `app/static/favicon.ico`
- Modify: `app/templates/base.html`

- [ ] **Step 1: 生成 PWA 图标文件**

使用 Python 生成简单的占位图标（纯色 + 文字）:

```python
from PIL import Image, ImageDraw, ImageFont
import os

static_dir = os.path.join("app", "static")

for size, filename in [(192, "icon-192.png"), (512, "icon-512.png")]:
    img = Image.new("RGBA", (size, size), (67, 97, 238, 255))
    draw = ImageDraw.Draw(img)
    text = "付刷"
    font_size = size // 4
    try:
        font = ImageFont.truetype("msyh.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - font_size * 0.1), text, fill="white", font=font)
    img.save(os.path.join(static_dir, filename))

favicon = Image.new("RGBA", (32, 32), (67, 97, 238, 255))
favicon.save(os.path.join(static_dir, "favicon.ico"), format="ICO")
```

注意: 如果 Pillow 不可用，使用纯色 PNG 替代:
```python
import struct, zlib

def create_png(width, height, r, g, b, filepath):
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    raw = b''
    for y in range(height):
        raw += b'\x00' + bytes([r, g, b]) * width
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    with open(filepath, 'wb') as f:
        f.write(header + ihdr + idat + iend)

create_png(192, 192, 67, 97, 238, "app/static/icon-192.png")
create_png(512, 512, 67, 97, 238, "app/static/icon-512.png")
```

- [ ] **Step 2: 在 base.html 中添加 favicon 和 apple-touch-icon**

在 `<head>` 中添加:
```html
    <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    <link rel="apple-touch-icon" href="/static/icon-192.png">
```

- [ ] **Step 3: 写测试 — PWA 图标可访问**

```python
def test_pwa_icons_accessible(client):
    for path in ["/static/icon-192.png", "/static/icon-512.png", "/static/favicon.ico"]:
        resp = client.get(path)
        assert resp.status_code == 200
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_pwa_icons_accessible -v`
Expected: PASS

---

### Task 11: Docker 容器化部署

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: 创建 Dockerfile**

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
ENV SECRET_KEY=change-me-in-production
ENV HTTPS_ONLY=false

CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
version: "3.8"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/fushua.db
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - HTTPS_ONLY=${HTTPS_ONLY:-false}
    volumes:
      - app_data:/app/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: fushua
      POSTGRES_USER: fushua
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-fushua_dev}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  app_data:
  pg_data:
```

- [ ] **Step 3: 创建 .dockerignore**

```
__pycache__
*.pyc
*.pyo
.pytest_cache
*.db
.git
.env
docs/
*.md
```

- [ ] **Step 4: 创建 gunicorn.conf.py**

```python
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("GUNICORN_WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

- [ ] **Step 5: 验证 Docker 构建**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && docker build -t fushua .`
Expected: 构建成功

---

### Task 12: 环境配置与 .gitignore

**Files:**
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: 创建 .env.example**

```
SECRET_KEY=your-secret-key-here-use-openssl-rand-hex-32
DATABASE_URL=sqlite:///./fushua.db
HTTPS_ONLY=false
GUNICORN_WORKERS=4
PORT=8000
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

POSTGRES_PASSWORD=fushua_dev
```

- [ ] **Step 2: 创建 .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
*.db
*.sqlite3
.env
.venv/
venv/
instance/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
node_modules/
.DS_Store
Thumbs.db
```

- [ ] **Step 3: 确认 .env 不被追踪**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && git status 2>nul || echo "Not a git repo yet"`

---

### Task 13: Logout 改为 POST 方法

**Files:**
- Modify: `app/routers/auth.py`
- Modify: `app/templates/base.html`

- [ ] **Step 1: 写测试 — GET /logout 不再直接退出**

```python
def test_logout_requires_post(client, db_session):
    from tests.conftest import register_and_login
    register_and_login(client, username="logoutuser")
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code in (405, 303)
```

- [ ] **Step 2: 修改 auth.py — 将 logout 改为 POST**

```python
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
```

- [ ] **Step 3: 修改 base.html — 退出链接改为表单**

将 `<a href="/logout" class="nav-link nav-link-logout">退出</a>` 替换为:
```html
                    <form action="/logout" method="POST" style="display:inline;">
                        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                        <button type="submit" class="nav-link nav-link-logout" style="background:none;border:none;cursor:pointer;font:inherit;color:inherit;">退出</button>
                    </form>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_production.py::test_logout_requires_post -v`
Expected: PASS

---

### Task 14: N+1 查询优化

**Files:**
- Modify: `app/routers/pages.py`
- Modify: `app/routers/teacher.py`
- Modify: `app/routers/classgroup.py`

- [ ] **Step 1: 优化 pages.py 的 leaderboard 查询**

将排行榜查询从 N+1 改为聚合查询:
```python
@router.get("/leaderboard")
def leaderboard(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = get_current_user(request)
    logged_in = user_id is not None

    rankings_data = (
        db.query(
            User.id,
            User.username,
            User.display_name,
            sa_func.count(Record.id).label("total"),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
        )
        .outerjoin(Record, Record.user_id == User.id)
        .filter(User.role == "student")
        .group_by(User.id)
        .having(sa_func.count(Record.id) > 0)
        .all()
    )
    rankings = [
        {
            "username": r.username,
            "display_name": r.display_name,
            "total": r.total,
            "correct": int(r.correct or 0),
            "accuracy": round((r.correct or 0) / r.total * 100, 1) if r.total > 0 else 0,
        }
        for r in rankings_data
    ]
    rankings.sort(key=lambda x: (-x["correct"], -x["accuracy"]))

    return request.app.state.templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "logged_in": logged_in, "rankings": rankings},
    )
```

- [ ] **Step 2: 优化 teacher.py 的 stats 查询**

将 `teacher_stats` 中的学生统计从 N+1 改为聚合查询:
```python
    student_records = (
        db.query(
            User.id,
            User.username,
            User.display_name,
            sa_func.count(Record.id).label("total"),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
        )
        .join(Record, Record.user_id == User.id)
        .filter(Record.question_id.in_(question_ids), User.role == "student")
        .group_by(User.id)
        .all()
    ) if question_ids else []
    student_stats = [
        {
            "id": s.id,
            "username": s.username,
            "display_name": s.display_name,
            "total": s.total,
            "correct": int(s.correct or 0),
            "accuracy": round((s.correct or 0) / s.total * 100, 1),
        }
        for s in student_records
    ]
    student_stats.sort(key=lambda x: x["accuracy"])
```

- [ ] **Step 3: 优化 classgroup.py 的 class_detail 查询**

将班级成员统计从 N+1 改为聚合查询:
```python
    member_data = (
        db.query(
            User.id,
            User.username,
            User.display_name,
            sa_func.count(Record.id).label("total"),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
        )
        .join(ClassMember, ClassMember.user_id == User.id)
        .outerjoin(Record, Record.user_id == User.id)
        .filter(ClassMember.class_id == class_id)
        .group_by(User.id)
        .all()
    )
    members = [
        {
            "id": m.id,
            "username": m.username,
            "display_name": m.display_name,
            "total": m.total,
            "correct": int(m.correct or 0),
            "accuracy": round((m.correct or 0) / m.total * 100, 1) if m.total > 0 else 0,
        }
        for m in member_data
    ]
    members.sort(key=lambda x: x["accuracy"])
```

- [ ] **Step 4: 运行全量测试确认无回归**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v`
Expected: 全部 PASS

---

### Task 15: PDF 报告输入清洗

**Files:**
- Modify: `app/utils/report.py`

- [ ] **Step 1: 在 report.py 中添加输入清洗**

在文件顶部添加:
```python
from app.security import sanitize_input
```

修改 `generate_teacher_report` 函数中的参数处理:
```python
def generate_teacher_report(teacher_name, total_questions, total_records, accuracy, per_question, student_stats):
    teacher_name = sanitize_input(str(teacher_name), max_length=100)
```

修改 `generate_student_report` 函数中的参数处理:
```python
def generate_student_report(student_name, total, correct, accuracy, subject_stats, type_stats):
    student_name = sanitize_input(str(student_name), max_length=100)
```

- [ ] **Step 2: 运行测试确认无回归**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_report.py -v`
Expected: PASS

---

### Task 16: 全量测试验证与回归测试

**Files:**
- Modify: `tests/test_production.py` (补充完整)
- All source files

- [ ] **Step 1: 补充完整的 test_production.py**

确保文件包含所有 Task 1-15 中定义的测试，以及一个综合测试:

```python
import os
import pytest
from tests.conftest import (
    client, db_session, create_test_user, create_test_question,
    get_csrf_token, login_as, register_and_login
)
from app.models import Favorite, ClassMember


def test_favorite_unique_constraint(client, db_session):
    user = create_test_user(db_session, username="favuser")
    q = create_test_question(db_session, created_by=user.id)
    register_and_login(client, username="favuser2")
    client.post(f"/student/favorites/{q.id}/add", follow_redirects=True)
    client.post(f"/student/favorites/{q.id}/add", follow_redirects=True)
    favs = db_session.query(Favorite).filter(Favorite.question_id == q.id).all()
    assert len(favs) <= 2


def test_csrf_required_for_login(client, db_session):
    create_test_user(db_session, username="csrfuser")
    resp = client.post("/login", data={
        "username": "csrfuser",
        "password": "123456",
    }, follow_redirects=False)
    assert resp.status_code in (403, 400)


def test_login_rate_limit(client, db_session):
    create_test_user(db_session, username="ratelimituser")
    for i in range(6):
        csrf = get_csrf_token(client)
        client.post("/login", data={
            "username": "ratelimituser",
            "password": "wrongpass",
            "_csrf_token": csrf,
        }, follow_redirects=False)
    resp = client.post("/login", data={
        "username": "ratelimituser",
        "password": "123456",
        "_csrf_token": get_csrf_token(client),
    }, follow_redirects=False)
    assert resp.status_code == 429


def test_weak_password_rejected(client, db_session):
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "weakpwuser",
        "password": "123",
        "role": "student",
        "display_name": "weakpwuser",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "密码" in resp.text


def test_404_error_page(client):
    resp = client.get("/nonexistent-page-12345")
    assert resp.status_code == 404


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in resp.headers


def test_pwa_icons_accessible(client):
    for path in ["/static/icon-192.png", "/static/icon-512.png"]:
        resp = client.get(path)
        assert resp.status_code == 200


def test_logout_requires_post(client, db_session):
    register_and_login(client, username="logoutuser2")
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code in (405, 303)


def test_username_length_limit(client, db_session):
    csrf = get_csrf_token(client)
    long_name = "a" * 200
    resp = client.post("/register", data={
        "username": long_name,
        "password": "password123",
        "role": "student",
        "display_name": "test",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert resp.status_code != 500
```

- [ ] **Step 2: 运行全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 3: 修复任何回归问题**

如果测试失败，逐个排查修复，重新运行直到全部通过。

---

### Task 17: 生产环境启动验证

**Files:**
- All files

- [ ] **Step 1: 删除旧数据库，从迁移重建**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && del fushua.db 2>nul & py -m alembic upgrade head`

- [ ] **Step 2: 使用 Gunicorn 启动验证**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pip install gunicorn && py -m gunicorn app.main:app -c gunicorn.conf.py`

- [ ] **Step 3: 验证健康检查**

Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok","version":"3.0.0"}`

- [ ] **Step 4: 验证核心功能**

手动测试:
1. 注册教师账号 → 出题 → 导入题库
2. 注册学生账号 → 刷题 → 查看错题本
3. 查看排行榜 → 导出 PDF
4. 验证深色模式切换
5. 验证 PWA 安装提示

- [ ] **Step 5: Docker 构建验证**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && docker compose up --build -d`
Expected: 容器正常启动

- [ ] **Step 6: 最终全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v`
Expected: 全部 PASS
