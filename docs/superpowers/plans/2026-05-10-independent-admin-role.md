# 独立管理员账户与权限后台 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将管理员从教师角色的 `is_admin` 标记拆分为独立的 `admin` 角色，拥有专属注册流程（管理员邀请码）、独立导航栏、独立后台界面，与教师权限彻底分离。

**Architecture:** User 模型的 `role` 字段新增 `"admin"` 取值，废弃 `is_admin` 布尔字段（保留但不再作为主要判断依据）。注册页面新增管理员角色选项（需管理员邀请码）。导航栏为 admin 角色展示专属后台入口。`require_admin` 函数改为检查 `role == "admin"`。管理员后台增加教师邀请码管理、班级全局管理、系统配置等功能。

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2, bcrypt, SQLite

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 修改 | `app/models.py` | 无结构变更，`is_admin` 保留但不再主要使用 |
| 修改 | `app/auth.py` | 新增 `require_admin_role` 函数，基于 `role == "admin"` |
| 修改 | `app/routers/auth.py` | 注册支持 `role=admin`，需管理员邀请码 |
| 修改 | `app/templates/register.html` | 新增管理员注册选项 |
| 修改 | `app/templates/base.html` | 导航栏为 admin 角色展示专属入口 |
| 修改 | `app/main.py` | 初始化时创建默认管理员；`_global_template_vars` 适配 admin 角色 |
| 修改 | `app/routers/admin.py` | `require_admin` 改用 `role == "admin"`；增加管理员专属功能 |
| 修改 | `app/templates/admin/index.html` | 增强管理后台首页 |
| 修改 | `app/templates/admin/users.html` | 用户管理支持 admin 角色筛选和操作 |
| 修改 | `app/routers/teacher.py` | 移除 teacher.py 中的 `require_admin` 函数（已有 admin.py 的版本） |
| 修改 | `tests/conftest.py` | 适配 admin 角色注册 |
| 新建 | `tests/test_admin_role.py` | 独立管理员角色测试 |

---

### Task 1: 新增 `require_admin_role` 函数和注册支持 admin 角色

**Files:**
- Modify: `app/auth.py`
- Modify: `app/routers/auth.py`
- Modify: `app/templates/register.html`
- Test: `tests/test_admin_role.py`

- [ ] **Step 1: 写失败测试 — admin 角色注册和权限**

```python
# tests/test_admin_role.py
import pytest
from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal, register_and_login
from app.models import User, SiteConfig


class TestAdminRole:
    def test_register_admin_with_invite_code(self, client, db_session):
        config = SiteConfig(key="admin_invite_code", value="ADMIN2026")
        db_session.add(config)
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "admin_user",
            "password": "admin123",
            "role": "admin",
            "display_name": "管理员",
            "invite_code": "ADMIN2026",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "admin_user").first()
        assert user is not None
        assert user.role == "admin"

    def test_register_admin_without_invite_code_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_code_admin",
            "password": "admin123",
            "role": "admin",
            "display_name": "无码管理员",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "邀请码" in resp.text

    def test_register_admin_with_wrong_invite_code_is_error(self, client, db_session):
        config = SiteConfig(key="admin_invite_code", value="ADMIN2026")
        db_session.add(config)
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "wrong_code_admin",
            "password": "admin123",
            "role": "admin",
            "display_name": "错码管理员",
            "invite_code": "WRONG",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "邀请码无效" in resp.text

    def test_require_admin_role_allows_admin(self, client, db_session):
        from app.auth import require_admin_role
        from fastapi import Request
        admin = create_test_user(db_session, username="role_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="role_admin", role="admin")
        user_id = client.cookies.get("session") is not None or True
        request = type("Request", (), {"session": {"user_id": admin.id}})()
        result = require_admin_role(request, db_session)
        assert result == admin.id

    def test_require_admin_role_rejects_teacher(self, client, db_session):
        from app.auth import require_admin_role
        from fastapi import HTTPException
        teacher = create_test_user(db_session, username="not_admin_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        request = type("Request", (), {"session": {"user_id": teacher.id}})()
        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(request, db_session)
        assert exc_info.value.status_code == 403

    def test_require_admin_role_rejects_student(self, client, db_session):
        from app.auth import require_admin_role
        from fastapi import HTTPException
        student = create_test_user(db_session, username="not_admin_student", role="student")
        db_session.commit()
        request = type("Request", (), {"session": {"user_id": student.id}})()
        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(request, db_session)
        assert exc_info.value.status_code == 403

    def test_admin_can_access_admin_panel(self, client, db_session):
        admin = create_test_user(db_session, username="panel_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="panel_admin", role="admin")
        resp = client.get("/admin", follow_redirects=True)
        assert resp.status_code == 200

    def test_teacher_cannot_access_admin_panel(self, client, db_session):
        teacher = create_test_user(db_session, username="no_panel_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        register_and_login(client, username="no_panel_teacher", role="teacher")
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code == 403
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_admin_role.py -v`
Expected: FAIL — `require_admin_role` 不存在，admin 角色注册不支持

- [ ] **Step 3: 在 auth.py 中添加 `require_admin_role` 函数**

在 `app/auth.py` 末尾添加：

```python
def require_admin_role(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return user_id
```

- [ ] **Step 4: 修改 auth.py 路由支持 admin 角色注册**

在 `app/routers/auth.py` 的 `register` 函数中，在 `if role == "teacher":` 代码块（约第50-62行）之后，添加 admin 角色的邀请码验证：

```python
    if role == "admin":
        invite_code = form.get("invite_code", "").strip()
        if not invite_code:
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "管理员注册需要邀请码", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
            )
        from app.security import verify_admin_invite_code
        if not verify_admin_invite_code(invite_code, db):
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "邀请码无效", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
            )
```

- [ ] **Step 5: 在 security.py 中添加 `verify_admin_invite_code` 函数**

在 `app/security.py` 末尾添加：

```python
def verify_admin_invite_code(code: str, db) -> bool:
    from app.models import SiteConfig
    if not code:
        return False
    config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
    if not config or not config.value:
        return False
    codes = [c.strip() for c in config.value.split(",") if c.strip()]
    return code in codes
```

- [ ] **Step 6: 修改注册模板，添加管理员选项**

在 `app/templates/register.html` 的角色选择区域（第25-33行），添加管理员选项：

将角色选择改为：

```html
        <div class="form-group">
            <label>我是</label>
            <div class="role-select" style="display:flex;gap:1rem;flex-wrap:wrap;">
                <label style="cursor:pointer;">
                    <input type="radio" name="role" value="student" checked onchange="toggleFields()"> 🎓 学生
                </label>
                <label style="cursor:pointer;">
                    <input type="radio" name="role" value="teacher" onchange="toggleFields()"> 👨‍🏫 教师
                </label>
                <label style="cursor:pointer;">
                    <input type="radio" name="role" value="admin" onchange="toggleFields()"> 🛡️ 管理员
                </label>
            </div>
        </div>
```

修改 `inviteCodeGroup` 的显示逻辑和标签，使其同时支持教师和管理员邀请码：

```html
        <div class="form-group" id="inviteCodeGroup" style="display:none;">
            <label for="invite_code">邀请码 *</label>
            <input type="text" id="invite_code" name="invite_code" placeholder="请输入邀请码">
            <small id="inviteCodeHint" style="color:var(--text-secondary);">教师注册需要邀请码，请联系管理员获取</small>
        </div>
```

修改 `toggleFields` JavaScript 函数：

```javascript
function toggleFields() {
    var role = document.querySelector('input[name="role"]:checked').value;
    var inviteGroup = document.getElementById('inviteCodeGroup');
    var studentGroup = document.getElementById('studentModeGroup');
    var hint = document.getElementById('inviteCodeHint');
    if (role === 'teacher') {
        inviteGroup.style.display = 'block';
        hint.textContent = '教师注册需要邀请码，请联系管理员获取';
    } else if (role === 'admin') {
        inviteGroup.style.display = 'block';
        hint.textContent = '管理员注册需要管理员邀请码';
    } else {
        inviteGroup.style.display = 'none';
    }
    studentGroup.style.display = role === 'student' ? 'block' : 'none';
}
```

- [ ] **Step 7: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_admin_role.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add app/auth.py app/routers/auth.py app/security.py app/templates/register.html tests/test_admin_role.py
git commit -m "feat: independent admin role with invite code registration"
```

---

### Task 2: 修改 admin.py 使用 `require_admin_role`，增强管理后台

**Files:**
- Modify: `app/routers/admin.py`
- Modify: `app/routers/teacher.py`
- Modify: `app/templates/admin/index.html`
- Modify: `app/templates/admin/users.html`
- Test: `tests/test_admin_role.py`

- [ ] **Step 1: 写失败测试 — admin 后台权限控制**

在 `tests/test_admin_role.py` 中追加：

```python
class TestAdminPanelAccess:
    def test_admin_panel_shows_admin_features(self, client, db_session):
        admin = create_test_user(db_session, username="feat_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="feat_admin", role="admin")
        resp = client.get("/admin", follow_redirects=True)
        assert resp.status_code == 200
        assert "管理后台" in resp.text

    def test_admin_can_manage_invite_codes(self, client, db_session):
        admin = create_test_user(db_session, username="invite_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="invite_admin", role="admin")
        resp = client.get("/admin/invite", follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_can_set_teacher_admin_flag(self, client, db_session):
        admin = create_test_user(db_session, username="flag_admin", role="admin")
        teacher = create_test_user(db_session, username="flag_teacher", role="teacher")
        db_session.commit()
        register_and_login(client, username="flag_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{teacher.id}/toggle-admin", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(teacher)
        assert teacher.is_admin is True

    def test_admin_users_page_shows_admin_role(self, client, db_session):
        admin = create_test_user(db_session, username="list_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="list_admin", role="admin")
        resp = client.get("/admin/users?role=admin", follow_redirects=True)
        assert resp.status_code == 200
        assert "管理员" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_admin_role.py::TestAdminPanelAccess -v`
Expected: FAIL — 路由不存在

- [ ] **Step 3: 修改 admin.py 的 `require_admin` 使用 `require_admin_role`**

替换 `app/routers/admin.py` 的 `require_admin` 函数：

```python
from app.auth import require_admin_role


def require_admin(request: Request, db: Session):
    return require_admin_role(request, db)
```

同时删除旧的 `require_admin` 函数体（第15-22行），替换为上述代码。

- [ ] **Step 4: 修改 teacher.py 中的 `require_admin` 函数**

在 `app/routers/teacher.py` 中，替换 `require_admin` 函数（第41-46行）：

```python
def require_admin(request: Request, db: Session) -> int:
    from app.auth import require_admin_role
    return require_admin_role(request, db)
```

- [ ] **Step 5: 在 admin.py 中添加邀请码管理和 toggle-admin 路由**

在 `app/routers/admin.py` 末尾添加：

```python
@router.get("/admin/invite")
def admin_invite_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    teacher_config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    admin_config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
    teacher_codes = teacher_config.value if teacher_config else ""
    admin_codes = admin_config.value if admin_config else ""
    return request.app.state.templates.TemplateResponse(
        "admin/invite.html",
        {"request": request, "teacher_codes": teacher_codes, "admin_codes": admin_codes, "csrf_token": request.session.get("csrf_token", "")},
    )


@router.post("/admin/invite/update")
async def admin_invite_update(request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    teacher_codes = sanitize_input(form.get("teacher_codes", "").strip(), max_length=500)
    admin_codes = sanitize_input(form.get("admin_codes", "").strip(), max_length=500)
    teacher_config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    if not teacher_config:
        teacher_config = SiteConfig(key="teacher_invite_code", value=teacher_codes)
        db.add(teacher_config)
    else:
        teacher_config.value = teacher_codes
    admin_config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
    if not admin_config:
        admin_config = SiteConfig(key="admin_invite_code", value=admin_codes)
        db.add(admin_config)
    else:
        admin_config.value = admin_codes
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="update_invite_codes",
        target_type="system",
        detail="管理员更新邀请码配置"
    ))
    db.commit()
    return RedirectResponse(url="/admin/invite", status_code=303)


@router.post("/admin/users/{user_id}/toggle-admin")
async def toggle_admin(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="不能修改管理员角色的 is_admin 标记")
    user.is_admin = not user.is_admin
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="toggle_admin",
        target_type="user",
        target_id=user_id,
        detail=f"{'授予' if user.is_admin else '撤销'}用户 {user.username} 的教师管理权限"
    ))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)
```

需要在 admin.py 顶部添加 import：

```python
from app.security import validate_csrf_async, sanitize_input
from app.models import SiteConfig
```

- [ ] **Step 6: 更新 admin/index.html — 增强管理后台首页**

替换 `app/templates/admin/index.html`：

```html
{% extends "base.html" %}

{% block title %}管理后台 - 付刷{% endblock %}

{% block content %}
<h1>🛡️ 管理后台</h1>

<div class="stats-row">
    <div class="stat-card">
        <div class="stat-number">{{ user_count }}</div>
        <div class="stat-label">用户数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ class_count }}</div>
        <div class="stat-label">班级数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ question_count }}</div>
        <div class="stat-label">题目数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ teacher_count }}</div>
        <div class="stat-label">教师数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ guest_count }}</div>
        <div class="stat-label">游客数</div>
    </div>
</div>

<div class="card">
    <h2>用户与权限</h2>
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
        <a href="/admin/users" class="btn">用户管理</a>
        <a href="/admin/invite" class="btn">邀请码管理</a>
        <a href="/admin/recovery-requests" class="btn">找回申请</a>
    </div>
</div>

<div class="card">
    <h2>系统维护</h2>
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
        <form action="/admin/cleanup-guests" method="POST" style="display:inline;">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
            <button type="submit" class="btn btn-outline" onclick="return confirm('确定清理所有过期游客？')">清理过期游客</button>
        </form>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 7: 更新 admin/users.html — 支持 admin 角色筛选和操作**

修改 `app/templates/admin/users.html`，在角色筛选下拉框中添加管理员选项：

将第14行附近的 `<option value="teacher"` 之后添加：

```html
            <option value="admin" {% if role == 'admin' %}selected{% endif %}>管理员</option>
```

在角色显示列中（第42-49行），添加管理员角色显示：

```html
                <td>
                    {% if u.role == 'admin' %}
                        <span class="badge badge-correct">管理员</span>
                    {% elif u.role == 'teacher' %}
                        <span class="badge badge-subject">教师</span>
                    {% else %}
                        <span class="badge">学生</span>
                    {% endif %}
                    {% if u.is_admin and u.role != 'admin' %}
                        <span class="badge badge-correct">管理权限</span>
                    {% endif %}
                </td>
```

在操作列中（第54-64行），为非 admin 用户添加 toggle-admin 按钮：

```html
                <td>
                    {% if u.role != 'admin' %}
                        <form action="/admin/users/{{ u.id }}/reset-password" method="POST" style="display:inline;">
                            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                            <button type="submit" class="btn btn-outline btn-sm" onclick="return confirm('确定重置密码为 abc123？')">重置密码</button>
                        </form>
                        <form action="/admin/users/{{ u.id }}/toggle-disable" method="POST" style="display:inline;">
                            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                            <button type="submit" class="btn btn-outline btn-sm">{% if u.is_disabled %}启用{% else %}禁用{% endif %}</button>
                        </form>
                        {% if u.role == 'teacher' %}
                        <form action="/admin/users/{{ u.id }}/toggle-admin" method="POST" style="display:inline;">
                            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                            <button type="submit" class="btn btn-outline btn-sm">{% if u.is_admin %}撤销管理权限{% else %}授予管理权限{% endif %}</button>
                        </form>
                        {% endif %}
                    {% endif %}
                </td>
```

- [ ] **Step 8: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_admin_role.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add app/routers/admin.py app/routers/teacher.py app/templates/admin/index.html app/templates/admin/users.html tests/test_admin_role.py
git commit -m "feat: admin panel with require_admin_role, invite management, toggle-admin"
```

---

### Task 3: 导航栏和全局模板适配 admin 角色

**Files:**
- Modify: `app/templates/base.html`
- Modify: `app/main.py`
- Test: `tests/test_admin_role.py`

- [ ] **Step 1: 写失败测试 — 导航栏显示管理员入口**

在 `tests/test_admin_role.py` 中追加：

```python
class TestAdminNavigation:
    def test_admin_sees_admin_nav(self, client, db_session):
        admin = create_test_user(db_session, username="nav_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="nav_admin", role="admin")
        resp = client.get("/", follow_redirects=True)
        assert "管理后台" in resp.text or "/admin" in resp.text

    def test_teacher_no_admin_nav(self, client, db_session):
        teacher = create_test_user(db_session, username="nav_teacher", role="teacher")
        db_session.commit()
        register_and_login(client, username="nav_teacher", role="teacher")
        resp = client.get("/", follow_redirects=True)
        text = resp.text
        has_admin_link = 'href="/admin"' in text
        assert not has_admin_link or "管理后台" not in text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_admin_role.py::TestAdminNavigation -v`
Expected: FAIL — 导航栏未为 admin 角色显示专属入口

- [ ] **Step 3: 修改 base.html 导航栏**

在 `app/templates/base.html` 的导航栏中，在 `{% elif role == 'teacher' %}` 代码块之后（约第55行 `{% endif %}` 之前），添加 admin 角色的导航：

```html
                    {% elif role == 'admin' %}
                        <a href="/admin" class="nav-link">管理后台</a>
                        <a href="/admin/users" class="nav-link">用户</a>
                        <a href="/admin/invite" class="nav-link">邀请码</a>
                        <a href="/admin/recovery-requests" class="nav-link">找回</a>
                        <a href="/browse" class="nav-link">题库</a>
                        <a href="/help" class="nav-link">帮助</a>
                        <a href="/settings" class="nav-link">设置</a>
```

同时移除教师导航栏中的 `{% if is_admin %}<a href="/admin" class="nav-link">管理</a>{% endif %}` 和 `{% if is_admin %}<a href="/teacher/invite" class="nav-link">邀请码</a>{% endif %}`，因为管理员功能已独立。

- [ ] **Step 4: 修改 main.py 初始化逻辑**

修改 `app/main.py` 的初始化部分（第21-30行），添加默认管理员创建和管理员邀请码初始化：

```python
from app.models import SiteConfig, User as InitUser
_init_db = SessionLocal()
if not _init_db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first():
    _init_db.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    _init_db.commit()
if not _init_db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first():
    _init_db.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    _init_db.commit()
first_admin = _init_db.query(InitUser).filter(InitUser.role == "admin").first()
if not first_admin:
    first_teacher = _init_db.query(InitUser).filter(InitUser.role == "teacher").first()
    if first_teacher and first_teacher.is_admin:
        first_teacher.role = "admin"
        _init_db.commit()
    else:
        default_admin = InitUser(
            username="admin",
            password_hash=InitUser.hash_password("admin123"),
            role="admin",
            display_name="系统管理员",
            is_admin=True,
        )
        _init_db.add(default_admin)
        _init_db.commit()
_init_db.close()
```

- [ ] **Step 5: 修改 main.py 的 `_global_template_vars` 函数**

在 `_global_template_vars` 函数中（约第116-147行），修改 `is_admin` 的判断逻辑，使其基于 `role == "admin"`：

```python
        is_admin = user.role == "admin"
```

替换原来的：

```python
        is_admin = user.is_admin
```

- [ ] **Step 6: 修改 conftest.py 适配 admin 角色注册**

在 `tests/conftest.py` 的 `register_and_login` 函数中，添加 admin 角色的注册支持：

在 `if role == "teacher":` 代码块之后添加：

```python
    if role == "admin":
        db = TestingSessionLocal()
        try:
            config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
            if not config:
                config = SiteConfig(key="admin_invite_code", value="ADMIN2026")
                db.add(config)
            else:
                config.value = "ADMIN2026"
            db.commit()
        finally:
            db.close()
        data["invite_code"] = "ADMIN2026"
```

- [ ] **Step 7: 运行测试确认通过**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/test_admin_role.py -v`
Expected: PASS

- [ ] **Step 8: 运行全量测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 全部 PASS（可能需要修复因 `require_admin` 变更导致的回归）

- [ ] **Step 9: Commit**

```bash
git add app/templates/base.html app/main.py tests/conftest.py tests/test_admin_role.py
git commit -m "feat: admin navigation, default admin init, global template vars"
```

---

### Task 4: 全量回归测试和收尾

**Files:**
- All modified files
- Test: `tests/` (full suite)

- [ ] **Step 1: 运行全部测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 2: 修复回归问题**

重点检查：
- `tests/test_admin.py` — 旧测试可能依赖 `is_admin` 布尔字段，需要确保 `require_admin` 在 admin.py 中使用 `require_admin_role`
- `tests/test_admin_audit_log.py` — 同上
- `tests/test_teacher_cross_class.py` — teacher.py 中的 `require_admin` 引用

如果旧测试中创建管理员用的是 `is_admin=True` 的教师，需要改为 `role="admin"` 或确保 `require_admin` 在 admin.py 中正确使用 `require_admin_role`。

- [ ] **Step 3: 最终 Commit**

```bash
git add -A
git commit -m "feat: independent admin role and backend - complete"
```

---

## 自查清单

### 1. 需求覆盖

| 需求 | 对应 Task |
|------|-----------|
| 独立管理员账户（admin 角色） | Task 1 (role="admin" 注册) |
| 管理员专属邀请码 | Task 1 (admin_invite_code) |
| 管理员独立后台 | Task 2 (require_admin_role + 增强后台) |
| 邀请码管理（教师+管理员） | Task 2 (/admin/invite) |
| 教师 is_admin 标记管理 | Task 2 (toggle-admin) |
| 管理员专属导航栏 | Task 3 (base.html) |
| 默认管理员初始化 | Task 3 (main.py) |
| 与教师权限彻底分离 | Task 2-3 (require_admin_role) |

### 2. 占位符扫描

无 TBD/TODO/实现后补等占位符。

### 3. 类型一致性

- `role` 字段取值：`"student"` / `"teacher"` / `"admin"`
- `require_admin_role` 在 `app/auth.py` 中定义，在 `app/routers/admin.py` 和 `app/routers/teacher.py` 中通过 `require_admin` 包装调用
- `admin_invite_code` 在 `SiteConfig` 中存储，格式与 `teacher_invite_code` 一致（逗号分隔）
- 默认管理员邀请码：`ADMIN2026`，默认管理员账户：`admin` / `admin123`
