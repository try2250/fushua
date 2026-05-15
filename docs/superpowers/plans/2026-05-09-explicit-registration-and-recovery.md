# 注册明确模式 + 账号找回 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将学生注册从隐式游客模式改为三种明确选项（正式加入班级/申请加入班级/临时游客），并增加基于用户名+班级/姓名校验的账号找回功能。

**Architecture:** 在现有 User 模型上新增 `join_mode` 字段区分注册方式；新增 `ClassJoinRequest` 模型存储入班申请；新增 `AccountRecoveryRequest` 模型存储找回申请。注册页面改为三步式明确选择；登录页面增加找回入口；教师/管理员后台增加审批入口。

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2, bcrypt, SQLite

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 修改 | `app/models.py` | 新增 `join_mode` 字段、`ClassJoinRequest` 模型、`AccountRecoveryRequest` 模型 |
| 修改 | `app/routers/auth.py` | 重写注册逻辑为三种模式；新增找回页面和提交路由 |
| 修改 | `app/auth.py` | 更新 `is_guest_expired` 以兼容 `join_mode` |
| 修改 | `app/templates/register.html` | 重写为三种明确注册模式 |
| 修改 | `app/templates/login.html` | 增加"找回账号"链接 |
| 新建 | `app/templates/recover.html` | 账号找回表单页面 |
| 新建 | `app/templates/recover_submitted.html` | 找回申请提交成功页面 |
| 修改 | `app/routers/teacher.py` | 新增入班申请审批和找回申请审批路由 |
| 修改 | `app/templates/teacher/students.html` | 增加入班申请审批区域和找回申请审批区域 |
| 修改 | `app/routers/admin.py` | 新增管理员处理找回申请路由 |
| 修改 | `app/templates/admin/index.html` | 增加找回申请入口 |
| 新建 | `app/templates/admin/recovery_requests.html` | 管理员查看找回申请列表 |
| 修改 | `tests/conftest.py` | 更新 `register_and_login` 辅助函数适配新注册模式 |
| 新建 | `tests/test_explicit_registration.py` | 注册明确模式测试 |
| 新建 | `tests/test_account_recovery.py` | 账号找回测试 |
| 新建 | `alembic/versions/20260509_join_mode_and_recovery.py` | 数据库迁移 |

---

### Task 1: 新增数据库模型和字段

**Files:**
- Modify: `app/models.py:24-51`
- Create: `alembic/versions/20260509_join_mode_and_recovery.py`
- Test: `tests/test_explicit_registration.py`

- [ ] **Step 1: 写失败测试 — 验证 User 模型有 join_mode 字段**

```python
# tests/test_explicit_registration.py
import pytest
from app.models import User, ClassJoinRequest, AccountRecoveryRequest


def test_user_has_join_mode_field():
    user = User(
        username="testjoin",
        password_hash="hash",
        role="student",
        join_mode="formal",
    )
    assert user.join_mode == "formal"


def test_user_join_mode_default_is_empty():
    user = User(username="defaultjoin", password_hash="hash", role="student")
    assert user.join_mode == ""


def test_class_join_request_model():
    req = ClassJoinRequest(
        user_id=1,
        class_id=2,
        display_name="张三",
        status="pending",
    )
    assert req.status == "pending"
    assert req.display_name == "张三"


def test_account_recovery_request_model():
    req = AccountRecoveryRequest(
        username="lostuser",
        class_id=1,
        display_name="李四",
        status="pending",
    )
    assert req.status == "pending"
    assert req.username == "lostuser"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_explicit_registration.py -v`
Expected: FAIL — `ClassJoinRequest` 和 `AccountRecoveryRequest` 未定义，`join_mode` 属性不存在

- [ ] **Step 3: 在 models.py 中添加 join_mode 字段和两个新模型**

在 `User` 模型的 `is_guest` 字段之前添加 `join_mode` 字段，并在文件末尾添加 `ClassJoinRequest` 和 `AccountRecoveryRequest` 模型：

```python
# app/models.py — User 类中新增字段（在 is_guest 之前）
    join_mode = Column(String(20), default="")
```

```python
# app/models.py — 文件末尾新增模型

class ClassJoinRequest(Base):
    __tablename__ = "class_join_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    display_name = Column(String(100), default="")
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "class_id", name="uq_join_request_user_class"),
    )


class AccountRecoveryRequest(Base):
    __tablename__ = "account_recovery_requests"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)
    display_name = Column(String(100), default="")
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    new_password_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_explicit_registration.py -v`
Expected: PASS

- [ ] **Step 5: 创建数据库迁移脚本**

```python
# alembic/versions/20260509_join_mode_and_recovery.py
"""add join_mode and recovery models

Revision ID: 20260509_join_mode
Revises: 20260509_productization_schema
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = "20260509_join_mode"
down_revision = "20260509_productization_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("join_mode", sa.String(20), server_default="", nullable=True))
    op.create_table(
        "class_join_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=False),
        sa.Column("display_name", sa.String(100), server_default=""),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "class_id", name="uq_join_request_user_class"),
    )
    op.create_index("ix_class_join_requests_user_id", "class_join_requests", ["user_id"])
    op.create_index("ix_class_join_requests_class_id", "class_join_requests", ["class_id"])
    op.create_table(
        "account_recovery_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=True),
        sa.Column("display_name", sa.String(100), server_default=""),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("new_password_hash", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_recovery_username", "account_recovery_requests", ["username"])


def downgrade():
    op.drop_table("account_recovery_requests")
    op.drop_table("class_join_requests")
    op.drop_column("users", "join_mode")
```

- [ ] **Step 6: Commit**

```bash
git add app/models.py alembic/versions/20260509_join_mode_and_recovery.py tests/test_explicit_registration.py
git commit -m "feat: add join_mode field, ClassJoinRequest and AccountRecoveryRequest models"
```

---

### Task 2: 重写注册页面为三种明确模式

**Files:**
- Modify: `app/templates/register.html`
- Test: `tests/test_explicit_registration.py`

- [ ] **Step 1: 写失败测试 — 注册三种模式的路由行为**

在 `tests/test_explicit_registration.py` 中追加：

```python
from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal
from app.models import ClassGroup, ClassMember, ClassJoinRequest


class TestExplicitRegistration:
    def test_register_formal_join(self, client, db_session):
        cls = ClassGroup(name="测试班", created_by=0)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "formal_student",
            "password": "abc123",
            "role": "student",
            "display_name": "正式生",
            "join_mode": "formal",
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "formal_student").first()
        assert user is not None
        assert user.join_mode == "formal"
        assert user.is_guest is False
        assert user.class_id == cls.id
        member = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == user.id
        ).first()
        assert member is not None

    def test_register_apply_join(self, client, db_session):
        cls = ClassGroup(name="申请班", created_by=0)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "apply_student",
            "password": "abc123",
            "role": "student",
            "display_name": "申请生",
            "join_mode": "apply",
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "apply_student").first()
        assert user is not None
        assert user.join_mode == "apply"
        assert user.is_guest is True
        assert user.class_id is None
        req = db_session.query(ClassJoinRequest).filter(
            ClassJoinRequest.user_id == user.id, ClassJoinRequest.class_id == cls.id
        ).first()
        assert req is not None
        assert req.status == "pending"

    def test_register_guest(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "guest_student",
            "password": "abc123",
            "role": "student",
            "display_name": "游客生",
            "join_mode": "guest",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "guest_student").first()
        assert user is not None
        assert user.join_mode == "guest"
        assert user.is_guest is True
        assert user.guest_expires_at is not None
        assert user.class_id is None

    def test_register_formal_without_class_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_class_student",
            "password": "abc123",
            "role": "student",
            "display_name": "无班生",
            "join_mode": "formal",
            "class_id": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "请选择班级" in resp.text or "选择班级" in resp.text

    def test_register_apply_without_class_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_class_apply",
            "password": "abc123",
            "role": "student",
            "display_name": "无班申请",
            "join_mode": "apply",
            "class_id": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "请选择班级" in resp.text or "选择班级" in resp.text

    def test_register_no_join_mode_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_mode_student",
            "password": "abc123",
            "role": "student",
            "display_name": "无模式",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "请选择注册方式" in resp.text or "注册方式" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_explicit_registration.py::TestExplicitRegistration -v`
Expected: FAIL — 路由尚未处理 `join_mode` 参数

- [ ] **Step 3: 重写注册路由逻辑**

修改 `app/routers/auth.py` 的 `register` 函数，将第 71-93 行的学生注册逻辑替换为基于 `join_mode` 的明确模式：

```python
# app/routers/auth.py — 替换第 71-93 行
    from datetime import datetime, timedelta
    is_guest = False
    class_id = None
    guest_expires_at = None
    join_mode = ""

    if role == "student":
        join_mode = form.get("join_mode", "").strip()
        if join_mode not in ("formal", "apply", "guest"):
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "请选择注册方式", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
            )

        if join_mode == "formal":
            class_id_str = form.get("class_id", "").strip()
            if not class_id_str:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "正式加入班级请选择班级", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )
            class_id = parse_int(class_id_str, min_value=1)
            if class_id is None:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "所选班级不存在，请重新选择", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )
            cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if not cls:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "所选班级不存在，请重新选择", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )

        elif join_mode == "apply":
            class_id_str = form.get("class_id", "").strip()
            if not class_id_str:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "申请加入班级请选择班级", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )
            class_id = parse_int(class_id_str, min_value=1)
            if class_id is None:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "所选班级不存在，请重新选择", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )
            cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if not cls:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "所选班级不存在，请重新选择", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )
            is_guest = True
            guest_expires_at = datetime.now() + timedelta(hours=24)
            class_id = None

        elif join_mode == "guest":
            is_guest = True
            guest_expires_at = datetime.now() + timedelta(hours=1)
```

同时在创建 User 对象时加上 `join_mode`：

```python
# app/routers/auth.py — 创建 User 对象时增加 join_mode
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        display_name=display_name or username,
        is_guest=is_guest,
        guest_expires_at=guest_expires_at,
        class_id=class_id,
        join_mode=join_mode,
    )
```

在注册成功后，如果是 `apply` 模式，需要创建 `ClassJoinRequest`：

```python
# app/routers/auth.py — 在 db.refresh(user) 之后，class_id 判断之前插入
    if join_mode == "apply":
        apply_class_id_str = form.get("class_id", "").strip()
        apply_class_id = parse_int(apply_class_id_str, min_value=1)
        if apply_class_id:
            from app.models import ClassJoinRequest
            existing_req = db.query(ClassJoinRequest).filter(
                ClassJoinRequest.user_id == user.id, ClassJoinRequest.class_id == apply_class_id
            ).first()
            if not existing_req:
                db.add(ClassJoinRequest(
                    user_id=user.id,
                    class_id=apply_class_id,
                    display_name=display_name or username,
                    status="pending",
                ))
                db.commit()
```

- [ ] **Step 4: 重写注册模板**

将 `app/templates/register.html` 完整替换为：

```html
{% extends "base.html" %}
{% block title %}注册 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>注册</h1>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <form action="/register" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required placeholder="请输入用户名">
        </div>
        <div class="form-group">
            <label for="display_name">昵称</label>
            <input type="text" id="display_name" name="display_name" placeholder="显示名称（可选）">
        </div>
        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required placeholder="请输入密码（至少6位，非纯数字）">
        </div>
        <div class="form-group">
            <label>我是</label>
            <div class="role-select" style="display:flex;gap:1rem;">
                <label style="cursor:pointer;">
                    <input type="radio" name="role" value="student" checked onchange="toggleFields()"> 🎓 学生
                </label>
                <label style="cursor:pointer;">
                    <input type="radio" name="role" value="teacher" onchange="toggleFields()"> 👨‍🏫 教师
                </label>
            </div>
        </div>
        <div id="studentModeGroup">
            <div class="form-group">
                <label>注册方式</label>
                <div style="display:flex;flex-direction:column;gap:0.75rem;margin-top:0.5rem;">
                    <label style="cursor:pointer;padding:0.75rem;border:2px solid var(--border-color);border-radius:8px;transition:all 0.2s;" class="join-mode-option" data-mode="formal">
                        <input type="radio" name="join_mode" value="formal" onchange="toggleJoinMode()" style="margin-right:0.5rem;">
                        <strong>✅ 正式加入班级</strong>
                        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem;">选择班级后立即加入，可使用全部功能</div>
                    </label>
                    <label style="cursor:pointer;padding:0.75rem;border:2px solid var(--border-color);border-radius:8px;transition:all 0.2s;" class="join-mode-option" data-mode="apply">
                        <input type="radio" name="join_mode" value="apply" onchange="toggleJoinMode()" style="margin-right:0.5rem;">
                        <strong>📝 申请加入班级</strong>
                        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem;">提交申请，等待教师审核通过后正式加入</div>
                    </label>
                    <label style="cursor:pointer;padding:0.75rem;border:2px solid var(--border-color);border-radius:8px;transition:all 0.2s;" class="join-mode-option" data-mode="guest">
                        <input type="radio" name="join_mode" value="guest" onchange="toggleJoinMode()" style="margin-right:0.5rem;">
                        <strong>👀 临时游客</strong>
                        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem;">无需选择班级，仅可体验1小时，数据不保留</div>
                    </label>
                </div>
            </div>
            <div class="form-group" id="classSelectGroup" style="display:none;">
                <label for="class_id">选择班级</label>
                <select name="class_id" id="class_id">
                    <option value="">请选择班级</option>
                    {% for c in classes %}
                    <option value="{{ c.id }}" {{ 'selected' if c.id|string == preselected_class else '' }}>{{ c.name }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>
        <div class="form-group" id="inviteCodeGroup" style="display:none;">
            <label for="invite_code">教师邀请码 *</label>
            <input type="text" id="invite_code" name="invite_code" placeholder="请输入管理员提供的邀请码">
            <small style="color:var(--text-secondary);">教师注册需要邀请码，请联系管理员获取</small>
        </div>
        <button type="submit" class="btn btn-primary btn-block">注册</button>
    </form>
    <p class="auth-switch">已有账号？<a href="/login">去登录</a></p>
</div>
<script>
function toggleFields() {
    var role = document.querySelector('input[name="role"]:checked').value;
    document.getElementById('inviteCodeGroup').style.display = role === 'teacher' ? 'block' : 'none';
    document.getElementById('studentModeGroup').style.display = role === 'student' ? 'block' : 'none';
}
function toggleJoinMode() {
    var mode = document.querySelector('input[name="join_mode"]:checked');
    var classGroup = document.getElementById('classSelectGroup');
    var options = document.querySelectorAll('.join-mode-option');
    options.forEach(function(opt) {
        opt.style.borderColor = 'var(--border-color)';
        opt.style.background = '';
    });
    if (mode) {
        var selected = document.querySelector('.join-mode-option[data-mode="' + mode.value + '"]');
        if (selected) {
            selected.style.borderColor = 'var(--primary-color, #4361ee)';
            selected.style.background = 'var(--primary-bg, rgba(67,97,238,0.05))';
        }
        if (mode.value === 'formal' || mode.value === 'apply') {
            classGroup.style.display = 'block';
        } else {
            classGroup.style.display = 'none';
        }
    } else {
        classGroup.style.display = 'none';
    }
}
document.addEventListener('DOMContentLoaded', function() {
    toggleFields();
    toggleJoinMode();
});
</script>
{% endblock %}
```

- [ ] **Step 5: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_explicit_registration.py -v`
Expected: PASS

- [ ] **Step 6: 运行全部现有测试确认无回归**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 所有测试 PASS（可能需要更新 conftest.py 中的 `register_and_login` 函数）

- [ ] **Step 7: 更新 conftest.py 中的 register_and_login**

修改 `tests/conftest.py` 的 `register_and_login` 函数，为学生注册添加 `join_mode`：

```python
# tests/conftest.py — 修改 register_and_login 函数
def register_and_login(client, username="testuser", role="student", password="abc123"):
    if role == "teacher":
        db = TestingSessionLocal()
        try:
            config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
            if not config:
                config = SiteConfig(key="teacher_invite_code", value="FUSHUA2024")
                db.add(config)
            else:
                config.value = "FUSHUA2024"
            db.commit()
        finally:
            db.close()
    csrf = get_csrf_token(client)
    data = {
        "username": username,
        "password": password,
        "role": role,
        "display_name": username,
        "_csrf_token": csrf,
    }
    if role == "teacher":
        data["invite_code"] = "FUSHUA2024"
    if role == "student":
        data["join_mode"] = "guest"
    client.post("/register", data=data, follow_redirects=True)
    return login_as(client, username, password)
```

- [ ] **Step 8: 再次运行全部测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 所有测试 PASS

- [ ] **Step 9: Commit**

```bash
git add app/routers/auth.py app/templates/register.html tests/test_explicit_registration.py tests/conftest.py
git commit -m "feat: explicit registration mode - formal/apply/guest"
```

---

### Task 3: 增加入班申请审批功能

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `app/templates/teacher/students.html`
- Test: `tests/test_explicit_registration.py`

- [ ] **Step 1: 写失败测试 — 教师审批入班申请**

在 `tests/test_explicit_registration.py` 中追加：

```python
class TestJoinRequestApproval:
    def test_teacher_can_see_pending_requests(self, client, db_session):
        from tests.conftest import register_and_login
        teacher = create_test_user(db_session, username="req_teacher", role="teacher")
        cls = ClassGroup(name="审批班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="req_teacher", role="teacher")
        student = User(
            username="req_student",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="申请生",
            is_guest=True,
            join_mode="apply",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        req = ClassJoinRequest(user_id=student.id, class_id=cls.id, display_name="申请生", status="pending")
        db_session.add(req)
        db_session.commit()
        resp = client.get("/teacher/students", follow_redirects=True)
        assert resp.status_code == 200
        assert "申请生" in resp.text or "req_student" in resp.text

    def test_teacher_approve_join_request(self, client, db_session):
        teacher = create_test_user(db_session, username="approve_teacher", role="teacher")
        cls = ClassGroup(name="批准班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="approve_teacher", role="teacher")
        student = User(
            username="approve_student",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="批准生",
            is_guest=True,
            join_mode="apply",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        req = ClassJoinRequest(user_id=student.id, class_id=cls.id, display_name="批准生", status="pending")
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/join-requests/{req.id}/approve", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.is_guest is False
        assert student.class_id == cls.id
        assert student.join_mode == "formal"
        db_session.refresh(req)
        assert req.status == "approved"

    def test_teacher_reject_join_request(self, client, db_session):
        teacher = create_test_user(db_session, username="reject_teacher", role="teacher")
        cls = ClassGroup(name="拒绝班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="reject_teacher", role="teacher")
        student = User(
            username="reject_student",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="拒绝生",
            is_guest=True,
            join_mode="apply",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        req = ClassJoinRequest(user_id=student.id, class_id=cls.id, display_name="拒绝生", status="pending")
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/join-requests/{req.id}/reject", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(req)
        assert req.status == "rejected"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_explicit_registration.py::TestJoinRequestApproval -v`
Expected: FAIL — 路由不存在

- [ ] **Step 3: 在 teacher.py 中添加审批路由**

在 `app/routers/teacher.py` 的 import 中添加 `ClassJoinRequest`：

```python
# app/routers/teacher.py — 修改 import 行（第17行）
from app.models import Question, User, Record, FieldConfig, QuestionBank, SiteConfig, ClassGroup, ClassMember, Notification, Favorite, Assignment, AssignmentRecord, ClassJoinRequest, QUESTION_TYPES, SEMESTERS, SUBJECTS, BUILTIN_FIELDS, FIELD_TYPE_CHOICES
```

在 `student_management` 路由（约第1340行）中，查询待审批的入班申请并传入模板。修改 `student_management` 函数：

```python
# app/routers/teacher.py — 在 student_management 函数的 return 之前添加
    pending_join_requests = (
        db.query(ClassJoinRequest)
        .filter(ClassJoinRequest.class_id.in_(class_ids), ClassJoinRequest.status == "pending")
        .all()
    )
    join_request_data = []
    for jr in pending_join_requests:
        jr_user = db.query(User).filter(User.id == jr.user_id).first()
        jr_class = db.query(ClassGroup).filter(ClassGroup.id == jr.class_id).first()
        if jr_user and jr_class:
            join_request_data.append({
                "id": jr.id,
                "user_id": jr_user.id,
                "username": jr_user.username,
                "display_name": jr.display_name or jr_user.display_name,
                "class_name": jr_class.name,
                "class_id": jr_class.id,
                "created_at": jr.created_at,
            })
```

修改 return 中的模板上下文，添加 `join_request_data` 和 `csrf_token`：

```python
# app/routers/teacher.py — 修改 student_management 的 return
    return request.app.state.templates.TemplateResponse(
        "teacher/students.html",
        {"request": request, "class_data": class_data, "guest_data": guest_data, "join_request_data": join_request_data, "csrf_token": request.session.get("csrf_token", "")},
    )
```

添加审批和拒绝路由：

```python
# app/routers/teacher.py — 在 approve_student 路由之后添加

@router.post("/join-requests/{request_id}/approve")
async def approve_join_request(request_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    join_req = db.query(ClassJoinRequest).filter(ClassJoinRequest.id == request_id, ClassJoinRequest.status == "pending").first()
    if not join_req:
        return RedirectResponse(url="/teacher/students", status_code=303)
    cls = db.query(ClassGroup).filter(ClassGroup.id == join_req.class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        return RedirectResponse(url="/teacher/students", status_code=303)
    student = db.query(User).filter(User.id == join_req.user_id).first()
    if not student:
        return RedirectResponse(url="/teacher/students", status_code=303)
    existing_member = db.query(ClassMember).filter(ClassMember.class_id == cls.id, ClassMember.user_id == student.id).first()
    if not existing_member:
        db.add(ClassMember(class_id=cls.id, user_id=student.id))
    student.is_guest = False
    student.guest_expires_at = None
    student.class_id = cls.id
    student.join_mode = "formal"
    join_req.status = "approved"
    join_req.reviewed_by = user_id
    from datetime import datetime
    join_req.reviewed_at = datetime.now()
    db.add(Notification(
        user_id=student.id,
        title="入班申请已通过",
        content=f"您申请加入班级「{cls.name}」已通过审核，现在可以正常使用所有功能。",
    ))
    db.commit()
    return RedirectResponse(url="/teacher/students", status_code=303)


@router.post("/join-requests/{request_id}/reject")
async def reject_join_request(request_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    join_req = db.query(ClassJoinRequest).filter(ClassJoinRequest.id == request_id, ClassJoinRequest.status == "pending").first()
    if not join_req:
        return RedirectResponse(url="/teacher/students", status_code=303)
    cls = db.query(ClassGroup).filter(ClassGroup.id == join_req.class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        return RedirectResponse(url="/teacher/students", status_code=303)
    join_req.status = "rejected"
    join_req.reviewed_by = user_id
    from datetime import datetime
    join_req.reviewed_at = datetime.now()
    student = db.query(User).filter(User.id == join_req.user_id).first()
    if student:
        db.add(Notification(
            user_id=student.id,
            title="入班申请未通过",
            content=f"您申请加入班级「{cls.name}」未通过审核，请选择其他班级或以游客身份体验。",
        ))
    db.commit()
    return RedirectResponse(url="/teacher/students", status_code=303)
```

- [ ] **Step 4: 更新学生管理模板，增加入班申请审批区域**

在 `app/templates/teacher/students.html` 的待审核游客区域之前，插入入班申请审批区域：

```html
{% if join_request_data %}
<div class="card" style="margin-bottom:1.5rem;border-left:4px solid #3b82f6;">
    <h2>入班申请 ({{ join_request_data|length }})</h2>
    <p style="color:var(--text-secondary);">以下学生申请加入您的班级，请审核。</p>
    <table class="table">
        <thead><tr><th>用户名</th><th>昵称</th><th>申请班级</th><th>申请时间</th><th>操作</th></tr></thead>
        <tbody>
        {% for jr in join_request_data %}
        <tr>
            <td>{{ jr.username }}</td>
            <td>{{ jr.display_name }}</td>
            <td>{{ jr.class_name }}</td>
            <td>{{ jr.created_at.strftime('%m-%d %H:%M') if jr.created_at else '' }}</td>
            <td>
                <form action="/teacher/join-requests/{{ jr.id }}/approve" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-primary btn-sm">通过</button>
                </form>
                <form action="/teacher/join-requests/{{ jr.id }}/reject" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-outline btn-sm" onclick="return confirm('确定拒绝该申请？')">拒绝</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}
```

- [ ] **Step 5: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_explicit_registration.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/routers/teacher.py app/templates/teacher/students.html tests/test_explicit_registration.py
git commit -m "feat: teacher approval for class join requests"
```

---

### Task 4: 增加账号找回功能

**Files:**
- Modify: `app/routers/auth.py`
- Modify: `app/templates/login.html`
- Create: `app/templates/recover.html`
- Create: `app/templates/recover_submitted.html`
- Test: `tests/test_account_recovery.py`

- [ ] **Step 1: 写失败测试 — 账号找回流程**

```python
# tests/test_account_recovery.py
import pytest
from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal
from app.models import User, ClassGroup, ClassMember, AccountRecoveryRequest


class TestAccountRecovery:
    def test_recover_page_renders(self, client):
        resp = client.get("/recover", follow_redirects=True)
        assert resp.status_code == 200
        assert "找回" in resp.text

    def test_recover_submit_creates_request(self, client, db_session):
        cls = ClassGroup(name="找回班", created_by=0)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        user = create_test_user(db_session, username="recover_user")
        db_session.add(ClassMember(class_id=cls.id, user_id=user.id))
        user.class_id = cls.id
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/recover", data={
            "username": "recover_user",
            "class_id": str(cls.id),
            "display_name": user.display_name,
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        req = db_session.query(AccountRecoveryRequest).filter(
            AccountRecoveryRequest.username == "recover_user"
        ).first()
        assert req is not None
        assert req.status == "pending"
        assert req.class_id == cls.id

    def test_recover_nonexistent_user_still_submits(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/recover", data={
            "username": "nonexistent_user",
            "class_id": "",
            "display_name": "某人",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_recover_empty_username_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/recover", data={
            "username": "",
            "class_id": "",
            "display_name": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "用户名" in resp.text

    def test_login_page_has_recover_link(self, client):
        resp = client.get("/login", follow_redirects=True)
        assert "找回" in resp.text or "recover" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_account_recovery.py -v`
Expected: FAIL — `/recover` 路由不存在

- [ ] **Step 3: 在 auth.py 中添加找回路由**

在 `app/routers/auth.py` 的 import 中添加 `AccountRecoveryRequest`：

```python
# app/routers/auth.py — 修改 import 行（第7行）
from app.models import User, ClassGroup, Notification, AccountRecoveryRequest
```

在文件末尾添加找回相关路由：

```python
# app/routers/auth.py — 末尾追加

@router.get("/recover")
def recover_page(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
    return request.app.state.templates.TemplateResponse(
        "recover.html",
        {"request": request, "error": None, "csrf_token": request.session.get("csrf_token", ""), "classes": classes},
    )


@router.post("/recover")
async def recover_submit(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    await validate_csrf_async(request)
    form = await request.form()
    username = sanitize_input(form.get("username", "").strip(), max_length=50)
    class_id_str = form.get("class_id", "").strip()
    display_name = sanitize_input(form.get("display_name", "").strip(), max_length=100)

    if not username:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return request.app.state.templates.TemplateResponse(
            "recover.html",
            {"request": request, "error": "请输入用户名", "csrf_token": request.session.get("csrf_token", ""), "classes": classes},
        )

    class_id = None
    if class_id_str:
        class_id = parse_int(class_id_str, min_value=1)

    recovery = AccountRecoveryRequest(
        username=username,
        class_id=class_id,
        display_name=display_name,
        status="pending",
    )
    db.add(recovery)
    db.commit()

    return request.app.state.templates.TemplateResponse(
        "recover_submitted.html",
        {"request": request},
    )
```

- [ ] **Step 4: 创建找回页面模板**

```html
<!-- app/templates/recover.html -->
{% extends "base.html" %}
{% block title %}找回账号 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>找回账号</h1>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <p style="color:var(--text-secondary);margin-bottom:1rem;">请填写以下信息，提交后由教师或管理员审核并重置密码。</p>
    <form action="/recover" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label for="username">用户名 *</label>
            <input type="text" id="username" name="username" required placeholder="请输入注册时的用户名">
        </div>
        <div class="form-group">
            <label for="class_id">所在班级</label>
            <select name="class_id" id="class_id">
                <option value="">请选择（可选）</option>
                {% for c in classes %}
                <option value="{{ c.id }}">{{ c.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="display_name">姓名/昵称</label>
            <input type="text" id="display_name" name="display_name" placeholder="您的真实姓名或昵称（帮助老师确认身份）">
        </div>
        <button type="submit" class="btn btn-primary btn-block">提交找回申请</button>
    </form>
    <p class="auth-switch"><a href="/login">返回登录</a></p>
</div>
{% endblock %}
```

```html
<!-- app/templates/recover_submitted.html -->
{% extends "base.html" %}
{% block title %}找回申请已提交 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>申请已提交</h1>
    <div class="alert alert-success" style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);padding:1rem;border-radius:8px;">
        <p>✅ 您的账号找回申请已提交！</p>
        <p style="margin-top:0.5rem;">教师或管理员审核通过后，您的密码将被重置为默认密码，届时请登录后及时修改。</p>
    </div>
    <p class="auth-switch"><a href="/login">返回登录</a></p>
</div>
{% endblock %}
```

- [ ] **Step 5: 在登录页面添加找回链接**

修改 `app/templates/login.html`，在登录按钮之后、"还没有账号"之前添加找回链接：

```html
<!-- app/templates/login.html — 在 </button> 和 <p class="auth-switch"> 之间插入 -->
    <p style="text-align:center;margin-top:0.5rem;"><a href="/recover" style="color:var(--text-secondary);font-size:0.9rem;">忘记密码？找回账号</a></p>
```

- [ ] **Step 6: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_account_recovery.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/routers/auth.py app/templates/recover.html app/templates/recover_submitted.html app/templates/login.html tests/test_account_recovery.py
git commit -m "feat: account recovery request submission"
```

---

### Task 5: 管理员/教师审批找回申请

**Files:**
- Modify: `app/routers/admin.py`
- Modify: `app/routers/teacher.py`
- Create: `app/templates/admin/recovery_requests.html`
- Modify: `app/templates/admin/index.html`
- Test: `tests/test_account_recovery.py`

- [ ] **Step 1: 写失败测试 — 管理员审批找回申请**

在 `tests/test_account_recovery.py` 中追加：

```python
from tests.conftest import register_and_login


class TestRecoveryApproval:
    def test_admin_can_see_recovery_requests(self, client, db_session):
        admin = create_test_user(db_session, username="rec_admin", role="teacher", password="abc123")
        admin.is_admin = True
        db_session.commit()
        recovery = AccountRecoveryRequest(username="lost_student", display_name="丢失生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        register_and_login(client, username="rec_admin", role="teacher")
        resp = client.get("/admin/recovery-requests", follow_redirects=True)
        assert resp.status_code == 200
        assert "lost_student" in resp.text

    def test_admin_approve_recovery_resets_password(self, client, db_session):
        admin = create_test_user(db_session, username="reset_admin", role="teacher", password="abc123")
        admin.is_admin = True
        db_session.commit()
        student = create_test_user(db_session, username="reset_student")
        old_hash = student.password_hash
        recovery = AccountRecoveryRequest(username="reset_student", display_name="重置生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        db_session.refresh(recovery)
        register_and_login(client, username="reset_admin", role="teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/recovery-requests/{recovery.id}/approve", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.password_hash != old_hash
        assert User.verify_password(student.password_hash, "abc123")
        db_session.refresh(recovery)
        assert recovery.status == "approved"

    def test_admin_reject_recovery(self, client, db_session):
        admin = create_test_user(db_session, username="rej_admin", role="teacher", password="abc123")
        admin.is_admin = True
        db_session.commit()
        recovery = AccountRecoveryRequest(username="rej_student", display_name="拒绝生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        db_session.refresh(recovery)
        register_and_login(client, username="rej_admin", role="teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/recovery-requests/{recovery.id}/reject", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(recovery)
        assert recovery.status == "rejected"

    def test_teacher_can_see_class_recovery_requests(self, client, db_session):
        teacher = create_test_user(db_session, username="cls_rec_teacher", role="teacher")
        cls = ClassGroup(name="找回审批班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="cls_rec_teacher", role="teacher")
        recovery = AccountRecoveryRequest(username="cls_lost_student", class_id=cls.id, display_name="班级找回生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        resp = client.get("/teacher/students", follow_redirects=True)
        assert resp.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_account_recovery.py::TestRecoveryApproval -v`
Expected: FAIL — `/admin/recovery-requests` 路由不存在

- [ ] **Step 3: 在 admin.py 中添加找回申请管理路由**

修改 `app/routers/admin.py` 的 import：

```python
# app/routers/admin.py — 修改 import 行（第8行）
from app.models import User, ClassGroup, Question, ClassMember, AuditLog, AccountRecoveryRequest
```

在文件末尾添加路由：

```python
# app/routers/admin.py — 末尾追加

@router.get("/admin/recovery-requests")
def recovery_requests_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    pending = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.status == "pending"
    ).order_by(AccountRecoveryRequest.created_at.desc()).all()
    processed = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.status != "pending"
    ).order_by(AccountRecoveryRequest.reviewed_at.desc()).limit(50).all()
    return request.app.state.templates.TemplateResponse(
        "admin/recovery_requests.html",
        {
            "request": request,
            "pending": pending,
            "processed": processed,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.post("/admin/recovery-requests/{request_id}/approve")
async def approve_recovery(request_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    recovery = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.id == request_id, AccountRecoveryRequest.status == "pending"
    ).first()
    if not recovery:
        return RedirectResponse(url="/admin/recovery-requests", status_code=303)
    user = db.query(User).filter(User.username == recovery.username).first()
    if user:
        user.password_hash = User.hash_password("abc123")
        db.add(AuditLog(
            actor_id=admin_user.id,
            action="approve_recovery",
            target_type="user",
            target_id=user.id,
            detail=f"管理员批准找回申请，重置用户 {user.username} 的密码"
        ))
    recovery.status = "approved"
    recovery.reviewed_by = admin_user.id
    recovery.reviewed_at = datetime.now()
    db.commit()
    return RedirectResponse(url="/admin/recovery-requests", status_code=303)


@router.post("/admin/recovery-requests/{request_id}/reject")
async def reject_recovery(request_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    recovery = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.id == request_id, AccountRecoveryRequest.status == "pending"
    ).first()
    if not recovery:
        return RedirectResponse(url="/admin/recovery-requests", status_code=303)
    recovery.status = "rejected"
    recovery.reviewed_by = admin_user.id
    recovery.reviewed_at = datetime.now()
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="reject_recovery",
        target_type="recovery_request",
        target_id=request_id,
        detail=f"管理员拒绝找回申请：{recovery.username}"
    ))
    db.commit()
    return RedirectResponse(url="/admin/recovery-requests", status_code=303)
```

- [ ] **Step 4: 创建找回申请管理页面模板**

```html
<!-- app/templates/admin/recovery_requests.html -->
{% extends "base.html" %}
{% block title %}找回申请管理 - 付刷{% endblock %}
{% block content %}
<h1>账号找回申请</h1>

{% if pending %}
<div class="card" style="margin-bottom:1.5rem;border-left:4px solid #f59e0b;">
    <h2>待处理 ({{ pending|length }})</h2>
    <table class="table">
        <thead><tr><th>用户名</th><th>班级ID</th><th>姓名/昵称</th><th>申请时间</th><th>操作</th></tr></thead>
        <tbody>
        {% for r in pending %}
        <tr>
            <td>{{ r.username }}</td>
            <td>{{ r.class_id or '未填写' }}</td>
            <td>{{ r.display_name or '未填写' }}</td>
            <td>{{ r.created_at.strftime('%m-%d %H:%M') if r.created_at else '' }}</td>
            <td>
                <form action="/admin/recovery-requests/{{ r.id }}/approve" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-primary btn-sm" onclick="return confirm('确定通过？密码将重置为 abc123')">通过（重置密码）</button>
                </form>
                <form action="/admin/recovery-requests/{{ r.id }}/reject" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-outline btn-sm" onclick="return confirm('确定拒绝？')">拒绝</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% else %}
<div class="card" style="margin-bottom:1.5rem;">
    <p style="color:var(--text-secondary);">暂无待处理的找回申请。</p>
</div>
{% endif %}

{% if processed %}
<div class="card">
    <h2>已处理</h2>
    <table class="table">
        <thead><tr><th>用户名</th><th>姓名</th><th>状态</th><th>处理时间</th></tr></thead>
        <tbody>
        {% for r in processed %}
        <tr>
            <td>{{ r.username }}</td>
            <td>{{ r.display_name or '未填写' }}</td>
            <td>{% if r.status == 'approved' %}<span class="badge badge-success">已通过</span>{% else %}<span class="badge badge-wrong">已拒绝</span>{% endif %}</td>
            <td>{{ r.reviewed_at.strftime('%m-%d %H:%M') if r.reviewed_at else '' }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

<a href="/admin" class="btn btn-outline" style="margin-top:1rem;">返回管理首页</a>
{% endblock %}
```

- [ ] **Step 5: 在管理后台首页添加找回申请入口**

修改 `app/templates/admin/index.html`，在快捷操作区域添加链接：

```html
<!-- app/templates/admin/index.html — 在 <a href="/admin/users" class="btn">用户管理</a> 之后添加 -->
        <a href="/admin/recovery-requests" class="btn">找回申请</a>
```

- [ ] **Step 6: 在教师学生管理页面也展示班级相关的找回申请**

修改 `app/routers/teacher.py` 的 `student_management` 函数，在 return 之前添加：

```python
# app/routers/teacher.py — student_management 函数中 return 之前添加
    from app.models import AccountRecoveryRequest
    class_recovery_requests = (
        db.query(AccountRecoveryRequest)
        .filter(AccountRecoveryRequest.class_id.in_(class_ids), AccountRecoveryRequest.status == "pending")
        .all()
    ) if class_ids else []
    recovery_data = []
    for rr in class_recovery_requests:
        rr_class = db.query(ClassGroup).filter(ClassGroup.id == rr.class_id).first()
        recovery_data.append({
            "id": rr.id,
            "username": rr.username,
            "display_name": rr.display_name,
            "class_name": rr_class.name if rr_class else "",
            "created_at": rr.created_at,
        })
```

修改 return 的模板上下文：

```python
# app/routers/teacher.py — student_management 的 return 修改
    return request.app.state.templates.TemplateResponse(
        "teacher/students.html",
        {"request": request, "class_data": class_data, "guest_data": guest_data, "join_request_data": join_request_data, "recovery_data": recovery_data, "csrf_token": request.session.get("csrf_token", "")},
    )
```

在 `app/templates/teacher/students.html` 中，在入班申请区域之后、班级列表之前添加：

```html
{% if recovery_data %}
<div class="card" style="margin-bottom:1.5rem;border-left:4px solid #8b5cf6;">
    <h2>账号找回申请 ({{ recovery_data|length }})</h2>
    <p style="color:var(--text-secondary);">以下学生申请找回账号，请核实身份后由管理员处理。</p>
    <table class="table">
        <thead><tr><th>用户名</th><th>姓名</th><th>所在班级</th><th>申请时间</th></tr></thead>
        <tbody>
        {% for rr in recovery_data %}
        <tr>
            <td>{{ rr.username }}</td>
            <td>{{ rr.display_name or '未填写' }}</td>
            <td>{{ rr.class_name }}</td>
            <td>{{ rr.created_at.strftime('%m-%d %H:%M') if rr.created_at else '' }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    <p style="color:var(--text-secondary);font-size:0.85rem;">找回申请需由管理员在管理后台处理，教师可核实信息后联系管理员。</p>
</div>
{% endif %}
```

- [ ] **Step 7: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_account_recovery.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add app/routers/admin.py app/routers/teacher.py app/templates/admin/recovery_requests.html app/templates/admin/index.html app/templates/teacher/students.html tests/test_account_recovery.py
git commit -m "feat: admin/teacher approval for account recovery requests"
```

---

### Task 6: 全量回归测试和收尾

**Files:**
- All modified files
- Test: `tests/` (full suite)

- [ ] **Step 1: 运行全部测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 所有测试 PASS

- [ ] **Step 2: 修复任何回归问题**

如果出现因 `join_mode` 字段缺失导致的测试失败，检查是否所有创建 User 的地方都需要适配。特别关注：
- `tests/conftest.py` 的 `create_test_user` 函数（无需修改，因为 `join_mode` 有默认值 `""`）
- `app/routers/teacher.py` 的 `import_students` 函数（批量导入学生时 `join_mode` 默认为 `""`，等同于正式学生）

- [ ] **Step 3: 验证注册页面渲染**

手动检查注册页面是否正确显示三种模式选择，以及登录页面是否有找回链接。

- [ ] **Step 4: 最终 Commit**

```bash
git add -A
git commit -m "feat: explicit registration mode + account recovery - complete"
```

---

## 自查清单

### 1. 需求覆盖

| 需求 | 对应 Task |
|------|-----------|
| 正式加入班级 | Task 2 (join_mode="formal") |
| 申请加入班级 | Task 2 (join_mode="apply") + Task 3 (审批) |
| 临时游客（明确选择） | Task 2 (join_mode="guest") |
| 避免误注册1小时账号 | Task 2 (必须显式选择 join_mode) |
| 输入用户名+班级/姓名校验 | Task 4 (recover 表单) |
| 提交找回申请 | Task 4 (创建 AccountRecoveryRequest) |
| 老师/管理员重置 | Task 5 (admin/teacher 审批) |

### 2. 占位符扫描

无 TBD/TODO/实现后补等占位符。所有代码步骤均包含完整实现。

### 3. 类型一致性

- `join_mode` 在 User 模型、注册路由、审批路由中均为 `String(20)`，取值为 `"formal"` / `"apply"` / `"guest"` / `""`
- `ClassJoinRequest.status` 和 `AccountRecoveryRequest.status` 均为 `String(20)`，取值为 `"pending"` / `"approved"` / `"rejected"`
- 所有路由路径一致：`/teacher/join-requests/{id}/approve`、`/teacher/join-requests/{id}/reject`、`/admin/recovery-requests`、`/admin/recovery-requests/{id}/approve`、`/admin/recovery-requests/{id}/reject`
