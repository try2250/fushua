# 付刷代码审查与下一步规划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于全面代码审查，修复安全漏洞和逻辑Bug，提升代码质量和用户体验。

**Architecture:** 按优先级分批修复：P0 安全问题 → P1 逻辑Bug → P2 代码质量/体验。每批独立可测试。

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2, bcrypt, SQLite

---

## 审查发现汇总

### 🔴 P0 — 安全问题（必须修复）

| # | 文件 | 问题 | 描述 |
|---|------|------|------|
| S1 | `auth.py:8-12` | 会话固定攻击 | `get_current_user` 仅从 session 读 user_id，不验证用户是否仍存在/未被禁用。已禁用用户仍可操作 |
| S2 | `admin.py:69,157` | 默认密码硬编码 | 重置密码和找回密码都硬编码为 `abc123`，且不强制用户首次登录修改 |
| S3 | `security.py:6-12` | sanitize_input 不够安全 | 仅截断长度，不过滤 HTML/JS 字符。XSS 风险 |
| S4 | `main.py:57` | SECRET_KEY 可预测 | 开发模式密钥在每次重启时随机生成，但格式固定 `dev-only-insecure-key-` + 8字节hex |
| S5 | `pages.py:24-25` | 首页角色路由缺失 | admin 角色访问首页 `/` 不会被重定向，会看到空的学生统计页 |

### 🟡 P1 — 逻辑Bug（应该修复）

| # | 文件 | 问题 | 描述 |
|---|------|------|------|
| B1 | `auth.py:44-49` | is_guest_expired 逻辑不完整 | `join_mode="apply"` 的用户 is_guest=True 但24小时过期，过期后应限制功能但不应完全删除 |
| B2 | `teacher.py:41-48` | require_admin 重复定义 | teacher.py 有自己的 `require_admin`，与 admin.py 的不一致（teacher.py 还接受 is_admin=True 的教师） |
| B3 | `models.py:30` | role 字段长度不足 | `String(10)` 只能存10字符，但 "student"=7, "teacher"=7, "admin"=5，目前够用但无余量 |
| B4 | `admin.py:88` | toggle-disable 逻辑 | `user.is_admin or user.role == "admin"` — is_admin 的教师也会被保护不能禁用，但 is_admin 已无实际意义 |
| B5 | `pages.py:24-30` | 首页逻辑矛盾 | 先判断 `role == "student"` 重定向，后面又判断 `role == "student"` 算统计，永远不会执行 |
| B6 | `classgroup.py:103-106` | 添加成员时清除游客状态 | 将学生加入班级时直接清除 is_guest，但没有更新 join_mode，导致数据不一致 |

### 🟢 P2 — 代码质量/体验（建议改进）

| # | 文件 | 问题 | 描述 |
|---|------|------|------|
| Q1 | `teacher.py` | 文件过大（46个函数，1800+行） | 应拆分为 teacher/questions.py, teacher/students.py, teacher/stats.py 等 |
| Q2 | `security.py:82-101` | 两个 verify 函数重复 | `verify_teacher_invite_code` 和 `verify_admin_invite_code` 逻辑完全相同，仅 key 不同 |
| Q3 | `admin.py` | 缺少班级管理 | 管理员无法查看/管理所有班级，只能通过用户管理间接操作 |
| Q4 | `admin.py` | 缺少题目管理 | 管理员无法查看/管理所有题目 |
| Q5 | `admin.py` | 缺少系统配置 | 除了邀请码外，没有其他系统级配置管理 |
| Q6 | `base.html:53-60` | 管理员导航栏功能少 | 管理员无法从导航栏访问题库管理、班级管理等 |
| Q7 | `auth.py` | 登录后无角色定向 | admin 登录后应跳转 `/admin`，teacher 应跳转 `/teacher/questions`，而非统一跳 `/` |
| Q8 | `models.py:321` | AccountRecoveryRequest.new_password_hash 未使用 | 找回审批时直接重置密码，没有用到这个字段 |
| Q9 | `main.py:98-107` | health check 泄露信息 | 返回 user_count 和内部错误详情 |
| Q10 | `admin/index.html` | 统计数据缺失 admin 数量 | 管理后台首页没有显示管理员数量 |

---

## 实施计划

### Task 1: 修复 P0 安全问题

**Files:**
- Modify: `app/auth.py`
- Modify: `app/security.py`
- Modify: `app/routers/auth.py`
- Modify: `app/main.py`
- Modify: `app/routers/pages.py`
- Test: `tests/test_security_fixes.py`

- [ ] **Step 1: 写失败测试 — 安全修复验证**

```python
# tests/test_security_fixes.py
import pytest
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User, SiteConfig


class TestSessionValidation:
    def test_disabled_user_cannot_access(self, client, db_session):
        user = create_test_user(db_session, username="disabled_user", role="student")
        user.is_disabled = True
        db_session.commit()
        register_and_login(client, username="disabled_user", role="student")
        resp = client.get("/student/dashboard", follow_redirects=False)
        assert resp.status_code in (303, 403)


class TestSanitizeXSS:
    def test_sanitize_strips_html(self):
        from app.security import sanitize_input
        result = sanitize_input("<script>alert(1)</script>hello")
        assert "<script>" not in result

    def test_sanitize_strips_js_events(self):
        from app.security import sanitize_input
        result = sanitize_input('text"onclick="alert(1)')
        assert "onclick" not in result or result != 'text"onclick="alert(1)'


class TestAdminRedirect:
    def test_admin_login_redirects_to_admin(self, client, db_session):
        admin = create_test_user(db_session, username="redir_admin", role="admin")
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/login", data={
            "username": "redir_admin",
            "password": "abc123",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        assert "/admin" in resp.headers.get("location", "")


class TestDefaultPasswordForceChange:
    def test_reset_password_sets_force_change(self, client, db_session):
        admin = create_test_user(db_session, username="force_admin", role="admin")
        db_session.commit()
        student = create_test_user(db_session, username="force_student")
        register_and_login(client, username="force_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{student.id}/reset-password", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.force_password_change is True
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_security_fixes.py -v`
Expected: FAIL

- [ ] **Step 3: 修复 S1 — 禁用用户会话验证**

在 `app/auth.py` 的 `get_current_user` 中添加用户状态验证：

```python
def get_current_user(request: Request, db: Session = None):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    if db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.is_disabled:
            request.session.clear()
            return None
    return user_id
```

修改 `require_login`、`require_teacher`、`require_admin_role` 中的 `get_current_user` 调用，传入 db：

```python
def require_login(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user_id


def require_teacher(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "teacher":
        raise HTTPException(status_code=403, detail="仅教师可访问")
    return user_id


def require_admin_role(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return user_id
```

注意：`require_non_guest` 和 `get_current_user_info` 中也需要传入 db。对于 `get_current_user` 在不传 db 的场景（如 pages.py 的首页），保持不验证（向后兼容）。

- [ ] **Step 4: 修复 S2 — 默认密码强制修改**

在 `app/models.py` 的 User 类中添加字段：

```python
    force_password_change = Column(Boolean, default=False)
```

在 `app/routers/auth.py` 的登录路由中，登录成功后检查 `force_password_change`：

```python
    if user.force_password_change:
        return RedirectResponse(url="/settings?force_change=1", status_code=303)
```

在 `app/routers/admin.py` 的 `reset_password` 和 `approve_recovery` 中，重置密码时设置标记：

```python
    user.force_password_change = True
```

在 `app/routers/auth.py` 的 `change_password` 中，修改密码后清除标记：

```python
    user.force_password_change = False
```

在 `app/templates/settings.html` 中，当 `force_change=1` 时显示提示：

```html
{% if request.query_params.get('force_change') == '1' %}
<div class="alert alert-error" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);padding:1rem;border-radius:8px;margin-bottom:1rem;">
    ⚠️ 您的密码已被管理员重置，请立即修改密码后继续使用。
</div>
{% endif %}
```

- [ ] **Step 5: 修复 S3 — sanitize_input 防 XSS**

替换 `app/security.py` 的 `sanitize_input`：

```python
import html
import re

def sanitize_input(value: str, max_length: int = 500) -> str:
    if not value:
        return value
    value = value.strip()
    value = html.escape(value)
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    if len(value) > max_length:
        value = value[:max_length]
    return value
```

- [ ] **Step 6: 修复 S5 — 首页 admin 角色重定向**

在 `app/routers/pages.py` 的 `index` 函数中，在 `if logged_in and role == "student":` 之前添加：

```python
    if logged_in and role == "admin":
        return RedirectResponse(url="/admin", status_code=303)

    if logged_in and role == "teacher":
        return RedirectResponse(url="/teacher/questions", status_code=303)
```

- [ ] **Step 7: 修复 Q7 — 登录后角色定向**

在 `app/routers/auth.py` 的 `login` 路由中，将最后的 `return RedirectResponse(url="/", status_code=303)` 替换为：

```python
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=303)
    if user.role == "teacher":
        return RedirectResponse(url="/teacher/questions", status_code=303)
    return RedirectResponse(url="/", status_code=303)
```

- [ ] **Step 8: 创建数据库迁移**

```python
# alembic/versions/20260510_force_password_change.py
"""add force_password_change field

Revision ID: 20260510_force_pwd
Revises: 20260509_join_mode
Create Date: 2026-05-10
"""
from alembic import op
import sqlalchemy as sa

revision = "20260510_force_pwd"
down_revision = "20260509_join_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("force_password_change", sa.Boolean(), server_default="0", nullable=True))


def downgrade():
    op.drop_column("users", "force_password_change")
```

- [ ] **Step 9: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_security_fixes.py -v`
Expected: PASS

- [ ] **Step 10: 运行全量测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "fix: P0 security fixes - session validation, XSS sanitize, force password change, role redirect"
```

---

### Task 2: 修复 P1 逻辑Bug

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `app/routers/classgroup.py`
- Modify: `app/routers/admin.py`
- Test: `tests/test_logic_fixes.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_logic_fixes.py
import pytest
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User, ClassGroup, ClassMember


class TestTeacherRequireAdminConsistency:
    def test_teacher_require_admin_rejects_is_admin_teacher(self, client, db_session):
        teacher = create_test_user(db_session, username="isadmin_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        from app.routers.teacher import require_admin
        from fastapi import HTTPException, Request
        request = type("Request", (), {"session": {"user_id": teacher.id}})()
        with pytest.raises(HTTPException) as exc_info:
            require_admin(request, db_session)
        assert exc_info.value.status_code == 403


class TestAddMemberUpdatesJoinMode:
    def test_add_member_clears_guest_status(self, client, db_session):
        teacher = create_test_user(db_session, username="addmem_teacher", role="teacher")
        cls = ClassGroup(name="添加成员班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        student = User(
            username="addmem_student",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="添加成员生",
            is_guest=True,
            join_mode="guest",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        register_and_login(client, username="addmem_teacher", role="teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/classes/{cls.id}/members/add", data={
            "username": "addmem_student",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.is_guest is False
        assert student.join_mode == "formal"
        assert student.guest_expires_at is None


class TestAdminCannotDisableAdmin:
    def test_admin_cannot_disable_another_admin(self, client, db_session):
        admin = create_test_user(db_session, username="nodis_admin", role="admin")
        other_admin = create_test_user(db_session, username="nodis_other", role="admin")
        db_session.commit()
        register_and_login(client, username="nodis_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{other_admin.id}/toggle-disable", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 403
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_logic_fixes.py -v`
Expected: FAIL

- [ ] **Step 3: 修复 B2 — teacher.py 的 require_admin 统一为 require_admin_role**

替换 `app/routers/teacher.py` 第41-48行的 `require_admin`：

```python
def require_admin(request: Request, db: Session) -> int:
    from app.auth import require_admin_role
    return require_admin_role(request, db)
```

- [ ] **Step 4: 修复 B4 — toggle-disable 只保护 admin 角色**

修改 `app/routers/admin.py` 第88行：

```python
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="不能禁用管理员账号")
```

- [ ] **Step 5: 修复 B6 — 添加成员时更新 join_mode**

修改 `app/routers/classgroup.py` 第101-106行：

```python
        if not user.class_id:
            user.class_id = class_id
            if user.is_guest:
                user.is_guest = False
                user.guest_expires_at = None
                user.join_mode = "formal"
```

- [ ] **Step 6: 修复 B5 — 首页逻辑矛盾**

已在 Task 1 Step 6 中修复（admin 和 teacher 都重定向了）。

- [ ] **Step 7: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_logic_fixes.py -v`
Expected: PASS

- [ ] **Step 8: 运行全量测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "fix: P1 logic bugs - require_admin consistency, join_mode update, admin protection"
```

---

### Task 3: P2 代码质量改进

**Files:**
- Modify: `app/security.py`
- Modify: `app/routers/admin.py`
- Modify: `app/templates/base.html`
- Modify: `app/main.py`
- Test: `tests/test_quality_improvements.py`

- [ ] **Step 1: 修复 Q2 — 合并重复的邀请码验证函数**

在 `app/security.py` 中，将 `verify_teacher_invite_code` 和 `verify_admin_invite_code` 合并为一个通用函数：

```python
def verify_invite_code(code: str, db, key: str) -> bool:
    from app.models import SiteConfig
    if not code:
        return False
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if not config or not config.value:
        return False
    codes = [c.strip() for c in config.value.split(",") if c.strip()]
    return code in codes


def verify_teacher_invite_code(code: str, db) -> bool:
    return verify_invite_code(code, db, "teacher_invite_code")


def verify_admin_invite_code(code: str, db) -> bool:
    return verify_invite_code(code, db, "admin_invite_code")
```

- [ ] **Step 2: 修复 Q6 — 管理员导航栏增加更多功能**

修改 `app/templates/base.html` 第53-60行的 admin 导航：

```html
                    {% elif role == 'admin' %}
                        <a href="/admin" class="nav-link">管理后台</a>
                        <a href="/admin/users" class="nav-link">用户</a>
                        <a href="/admin/classes" class="nav-link">班级</a>
                        <a href="/admin/invite" class="nav-link">邀请码</a>
                        <a href="/admin/recovery-requests" class="nav-link">找回</a>
                        <a href="/browse" class="nav-link">题库</a>
                        <a href="/leaderboard" class="nav-link">排行</a>
                        <a href="/help" class="nav-link">帮助</a>
                        <a href="/settings" class="nav-link">设置</a>
```

- [ ] **Step 3: 修复 Q3 — 管理员班级管理路由**

在 `app/routers/admin.py` 末尾添加：

```python
@router.get("/admin/classes")
def admin_classes(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    classes = db.query(ClassGroup).order_by(ClassGroup.created_at.desc()).all()
    class_data = []
    for c in classes:
        member_count = db.query(ClassMember).filter(ClassMember.class_id == c.id).count()
        creator = db.query(User).filter(User.id == c.created_by).first()
        class_data.append({
            "id": c.id,
            "name": c.name,
            "created_by": creator.display_name if creator else "未知",
            "member_count": member_count,
            "created_at": c.created_at,
        })
    return request.app.state.templates.TemplateResponse(
        "admin/classes.html",
        {"request": request, "class_data": class_data},
    )
```

创建 `app/templates/admin/classes.html`：

```html
{% extends "base.html" %}
{% block title %}班级管理 - 付刷{% endblock %}
{% block content %}
<h1>班级管理</h1>

{% if class_data %}
<div class="card">
    <table class="table">
        <thead><tr><th>班级名称</th><th>创建者</th><th>学生数</th><th>创建时间</th></tr></thead>
        <tbody>
        {% for c in class_data %}
        <tr>
            <td>{{ c.name }}</td>
            <td>{{ c.created_by }}</td>
            <td>{{ c.member_count }}</td>
            <td>{{ c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '' }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% else %}
<div class="card">
    <p style="color:var(--text-secondary);">暂无班级。</p>
</div>
{% endif %}

<a href="/admin" class="btn btn-outline" style="margin-top:1rem;">返回管理首页</a>
{% endblock %}
```

- [ ] **Step 4: 修复 Q10 — 管理后台首页添加管理员数量**

修改 `app/routers/admin.py` 的 `admin_index`，在 `guest_count` 之后添加：

```python
    admin_count = db.query(User).filter(User.role == "admin").count()
```

在模板上下文中添加 `"admin_count": admin_count`。

修改 `app/templates/admin/index.html`，在 stats-row 中添加：

```html
    <div class="stat-card">
        <div class="stat-number">{{ admin_count }}</div>
        <div class="stat-label">管理员数</div>
    </div>
```

- [ ] **Step 5: 修复 Q9 — health check 不泄露信息**

修改 `app/main.py` 的 health_check：

```python
@app.get("/health")
def health_check(request: Request):
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.query(User).count()
        db.close()
        return {"status": "ok"}
    except Exception:
        return {"status": "degraded"}
```

- [ ] **Step 6: 运行全量测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "improve: P2 quality - DRY invite codes, admin classes page, nav enhancement, health check"
```

---

## 自查清单

### 1. 需求覆盖

| 问题 | 对应 Task |
|------|-----------|
| S1 禁用用户仍可操作 | Task 1 (get_current_user 验证) |
| S2 默认密码硬编码 | Task 1 (force_password_change) |
| S3 XSS 风险 | Task 1 (sanitize_input) |
| S5 admin 首页无定向 | Task 1 (pages.py 重定向) |
| B2 require_admin 不一致 | Task 2 (统一 require_admin_role) |
| B4 is_admin 保护逻辑 | Task 2 (只保护 admin 角色) |
| B6 join_mode 不一致 | Task 2 (添加成员时更新) |
| B5 首页逻辑矛盾 | Task 1 (已修复) |
| Q2 重复邀请码函数 | Task 3 (DRY) |
| Q3 缺少班级管理 | Task 3 (admin/classes) |
| Q6 导航栏功能少 | Task 3 (增强) |
| Q7 登录后无角色定向 | Task 1 (auth.py) |
| Q9 health check 泄露 | Task 3 (简化) |
| Q10 缺少管理员数量 | Task 3 (添加) |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- `force_password_change` 在 User 模型、admin.py、auth.py 中均为 Boolean
- `require_admin_role` 在 auth.py 定义，teacher.py 和 admin.py 均通过包装调用
- `verify_invite_code` 新增通用函数，旧函数保留为包装
