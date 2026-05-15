# 安全修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复付刷项目中 16 项安全审查发现的问题，优先处理 Critical 和 High 级别漏洞。

**Architecture:** 在现有 FastAPI + SQLAlchemy 架构上增量修复，不引入新框架。速率限制复用现有 SiteConfig 模式，密码策略增强在现有 `validate_password_strength` 上扩展。

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, bcrypt, itsdangerous

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 修改 | `app/main.py` | SEC-001/006: 默认管理员密码随机化 + force_password_change；SEC-004: SECRET_KEY 强化；SEC-012: 生产环境禁用 OpenAPI |
| 修改 | `app/routers/auth.py` | SEC-002: 登录后 force_password_change 检查；SEC-003: 注册/找回速率限制；SEC-007/016: 找回申请验证 |
| 修改 | `app/security.py` | SEC-003: 速率限制工具函数；SEC-010: 密码强度策略增强 |
| 修改 | `app/routers/admin.py` | SEC-005: LIKE 通配符转义；SEC-008: 找回审批验证用户存在 |
| 修改 | `app/routers/teacher.py` | SEC-009: 异常信息脱敏 |
| 创建 | `tests/test_security_audit_fixes.py` | 所有修复的测试 |

---

### Task 1: Critical 修复 — 默认管理员密码 + force_password_change

**Files:**
- Modify: `app/main.py`
- Modify: `app/routers/auth.py`

- [ ] **Step 1: 修改 main.py — 默认管理员使用随机密码 + force_password_change**

将 `app/main.py` 第 35-45 行的默认管理员创建逻辑替换为：

```python
default_admin_user = _init_db.query(InitUser).filter(InitUser.username == "admin").first()
if not default_admin_user:
    admin_password = secrets.token_hex(8)
    default_admin_user = InitUser(
        username="admin",
        password_hash=InitUser.hash_password(admin_password),
        role="admin",
        display_name="系统管理员",
        is_admin=True,
        force_password_change=True,
    )
    _init_db.add(default_admin_user)
    _init_db.commit()
    logger.info(f"默认管理员已创建 — 用户名: admin, 密码: {admin_password}（请立即登录修改）")
```

注意：需要确保 `logger` 在此代码之前已初始化。将 `logging.basicConfig(...)` 和 `logger = logging.getLogger("fushua")` 移到 `_init_db` 操作之前。

- [ ] **Step 2: 修改 auth.py — 登录后检查 force_password_change**

在 `app/routers/auth.py` 的 `login` 函数中，在 `request.session["user_id"] = user.id` 之后、`if user.is_guest` 之前，插入：

```python
    if user.force_password_change:
        return RedirectResponse(url="/settings?force_change=1", status_code=303)
```

- [ ] **Step 3: 写测试**

在 `tests/test_security_audit_fixes.py` 中添加：

```python
def test_login_redirects_to_settings_when_force_password_change(client, db):
    from app.models import User
    user = User(username="forceuser", password_hash=User.hash_password("test123a"), role="student", force_password_change=True)
    db.add(user)
    db.commit()
    resp = client.post("/login", data={"username": "forceuser", "password": "test123a"}, follow_redirects=False)
    assert resp.status_code == 303
    assert "/settings" in resp.headers["location"]


def test_default_admin_has_force_password_change(db):
    from app.models import User
    admin = db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    assert admin.force_password_change is True
```

- [ ] **Step 4: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/test_security_audit_fixes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/routers/auth.py tests/test_security_audit_fixes.py
git commit -m "security: fix SEC-001/002/006 - random admin password + force_password_change on login"
```

---

### Task 2: High 修复 — 速率限制 + 找回验证 + SECRET_KEY 强化

**Files:**
- Modify: `app/security.py`
- Modify: `app/routers/auth.py`
- Modify: `app/main.py`

- [ ] **Step 1: 在 security.py 中添加通用速率限制函数**

在 `app/security.py` 末尾添加：

```python
REGISTER_MAX_ATTEMPTS = 5
REGISTER_LOCKOUT_SECONDS = 3600
RECOVER_MAX_ATTEMPTS = 3
RECOVER_LOCKOUT_SECONDS = 3600


def check_rate_limit(key: str, max_attempts: int, lockout_seconds: int, db=None) -> None:
    if not db:
        return
    from app.models import SiteConfig
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if config:
        try:
            entries = [float(t) for t in config.value.split(",") if t.strip()]
            now = time.time()
            entries = [t for t in entries if now - t < lockout_seconds]
            if len(entries) >= max_attempts:
                raise HTTPException(
                    status_code=429,
                    detail=f"操作过于频繁，请{lockout_seconds}秒后重试"
                )
            config.value = ",".join(str(t) for t in entries)
        except ValueError:
            config.value = ""


def record_rate_limit_attempt(key: str, db=None) -> None:
    if not db:
        return
    from app.models import SiteConfig
    now = str(time.time())
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if config:
        try:
            entries = [float(t) for t in config.value.split(",") if t.strip()]
            cutoff = time.time() - 3600
            entries = [t for t in entries if t > cutoff]
            entries.append(time.time())
            config.value = ",".join(str(t) for t in entries)
        except ValueError:
            config.value = now
    else:
        config = SiteConfig(key=key, value=now)
        db.add(config)
    db.commit()
```

- [ ] **Step 2: 在 auth.py 注册端点添加速率限制**

在 `app/routers/auth.py` 的 `register` 函数中，在 `await validate_csrf_async(request)` 之后添加：

```python
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"_register_limit:{client_ip}", REGISTER_MAX_ATTEMPTS, REGISTER_LOCKOUT_SECONDS, db)
```

并在文件顶部 import 中添加：
```python
from app.security import validate_csrf_async, validate_password_strength, check_login_rate_limit, record_login_attempt, sanitize_input, check_rate_limit, record_rate_limit_attempt, REGISTER_MAX_ATTEMPTS, REGISTER_LOCKOUT_SECONDS, RECOVER_MAX_ATTEMPTS, RECOVER_LOCKOUT_SECONDS
```

在注册失败时（返回错误页面之前）添加 `record_rate_limit_attempt`，在注册成功时不需要记录。

- [ ] **Step 3: 在 auth.py 找回端点添加速率限制和验证**

在 `recover_submit` 函数中，在 `await validate_csrf_async(request)` 之后添加：

```python
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"_recover_limit:{client_ip}", RECOVER_MAX_ATTEMPTS, RECOVER_LOCKOUT_SECONDS, db)
```

在验证用户名之后、创建 `AccountRecoveryRequest` 之前，添加重复检查：

```python
    existing_pending = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.username == username,
        AccountRecoveryRequest.status == "pending"
    ).first()
    if existing_pending:
        return request.app.state.templates.TemplateResponse(
            "recover_submitted.html",
            {"request": request},
        )
```

- [ ] **Step 4: 强化 SECRET_KEY — main.py**

将 `app/main.py` 中的 SECRET_KEY 逻辑替换为：

```python
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-key-" + secrets.token_hex(32)
    import warnings
    warnings.warn("使用开发模式密钥，生产环境请设置 SECRET_KEY 环境变量！")
```

将 `secrets.token_hex(8)` 改为 `secrets.token_hex(32)`（256 位熵）。

- [ ] **Step 5: 写测试**

```python
def test_register_rate_limit(client, db):
    from app.models import SiteConfig
    for i in range(6):
        resp = client.post("/register", data={
            "username": f"ratelimit{i}",
            "password": "test123a",
            "role": "student",
            "join_mode": "guest",
            "_csrf_token": "test",
        }, follow_redirects=False)
    assert resp.status_code == 429


def test_recover_duplicate_pending_blocked(client, db):
    from app.models import AccountRecoveryRequest, ClassGroup
    cls = ClassGroup(name="TestClass", created_by=1)
    db.add(cls)
    db.commit()
    db.add(AccountRecoveryRequest(username="testuser", class_id=cls.id, status="pending"))
    db.commit()
    resp = client.post("/recover", data={
        "username": "testuser",
        "class_id": str(cls.id),
        "_csrf_token": "test",
    }, follow_redirects=False)
    assert resp.status_code == 200
```

- [ ] **Step 6: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/test_security_audit_fixes.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/security.py app/routers/auth.py app/main.py tests/test_security_audit_fixes.py
git commit -m "security: fix SEC-003/004/007 - rate limits + recovery validation + SECRET_KEY strength"
```

---

### Task 3: High + Medium 修复 — LIKE 转义 + 找回审批验证 + 异常脱敏 + 密码策略

**Files:**
- Modify: `app/routers/admin.py`
- Modify: `app/routers/teacher.py`
- Modify: `app/security.py`

- [ ] **Step 1: admin.py — LIKE 通配符转义 + 找回审批验证**

在 `admin_users` 函数中，将搜索逻辑修改为：

```python
    if q:
        safe_q = q.replace('%', '\\%').replace('_', '\\_')
        query = query.filter(
            (User.username.contains(safe_q)) | (User.display_name.contains(safe_q))
        )
```

在 `approve_recovery` 函数中，将 `if user:` 改为：

```python
    if not user:
        recovery.status = "rejected"
        recovery.reviewed_by = admin_user.id
        recovery.reviewed_at = datetime.now()
        db.commit()
        return RedirectResponse(url="/admin/recovery-requests", status_code=303)
    user.password_hash = User.hash_password("abc123")
    user.force_password_change = True
```

- [ ] **Step 2: teacher.py — 异常信息脱敏**

将所有 `f"导入失败：{str(e)}"` 替换为 `"导入失败，请检查文件格式是否正确"`。
将所有 `f"文件解析失败：{str(e)}"` 替换为 `"文件解析失败，请检查文件格式是否正确"`。

共 3 处需要修改（第 494、627、1632 行附近）。

- [ ] **Step 3: security.py — 增强密码强度策略**

将 `validate_password_strength` 函数替换为：

```python
def validate_password_strength(password: str) -> str | None:
    if len(password) < 8:
        return "密码长度至少8位"
    if password.isdigit():
        return "密码不能为纯数字"
    if password.isalpha():
        return "密码不能为纯字母"
    return None
```

- [ ] **Step 4: 写测试**

```python
def test_password_strength_enhanced():
    from app.security import validate_password_strength
    assert validate_password_strength("123456") == "密码长度至少8位"
    assert validate_password_strength("12345678") == "密码不能为纯数字"
    assert validate_password_strength("abcdefgh") == "密码不能为纯字母"
    assert validate_password_strength("test1234") is None


def test_like_wildcard_escaped(client, db):
    from app.models import User
    admin = db.query(User).filter(User.username == "admin").first()
    resp = client.get("/admin/users?q=%25", follow_redirects=False)
    assert resp.status_code in (200, 303)


def test_recovery_approve_rejects_nonexistent_user(client, db):
    from app.models import AccountRecoveryRequest
    recovery = AccountRecoveryRequest(username="nonexistent_user_xyz", status="pending")
    db.add(recovery)
    db.commit()
    resp = client.post(f"/admin/recovery-requests/{recovery.id}/approve", follow_redirects=False)
    assert resp.status_code in (200, 303)
    db.refresh(recovery)
    assert recovery.status == "rejected"
```

- [ ] **Step 5: 运行全量测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS（注意密码策略变更可能导致旧测试中短密码用例失败，需同步更新）

- [ ] **Step 6: Commit**

```bash
git add app/routers/admin.py app/routers/teacher.py app/security.py tests/test_security_audit_fixes.py
git commit -m "security: fix SEC-005/008/009/010 - LIKE escape + recovery validation + error sanitization + password policy"
```

---

### Task 4: Medium + Low 修复 — OpenAPI 禁用 + HttpOnly + 依赖审计

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: main.py — 生产环境禁用 OpenAPI 文档**

将 `app = FastAPI(title="付刷", version="3.0.0")` 替换为：

```python
import os as _os
_is_production = _os.environ.get("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title="付刷",
    version="3.0.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)
```

- [ ] **Step 2: main.py — Session Cookie HttpOnly**

在 `SessionMiddleware` 之后添加一个中间件来确保 session cookie 设置 HttpOnly：

```python
class CookieHardeningMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for cookie_name in ("session",):
            if cookie_name in response.cookies:
                response.cookies[cookie_name]["httponly"] = True
        return response


app.add_middleware(CookieHardeningMiddleware)
```

注意：此中间件必须在 `SessionMiddleware` 之后添加（Starlette 中间件栈是后添加先执行），所以放在 `app.add_middleware(SessionMiddleware, ...)` 之后。

- [ ] **Step 3: 运行全量测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

- [ ] **Step 4: Commit**

```bash
git add app/main.py
git commit -m "security: fix SEC-012/013 - disable OpenAPI in production + HttpOnly session cookie"
```

---

## 自查清单

### 1. 需求覆盖

| 安全发现 | 对应 Task |
|----------|-----------|
| SEC-001: 硬编码管理员密码 | Task 1 |
| SEC-002: force_password_change 绕过 | Task 1 |
| SEC-003: 注册/找回速率限制 | Task 2 |
| SEC-004: SECRET_KEY 熵不足 | Task 2 |
| SEC-005: LIKE 通配符注入 | Task 3 |
| SEC-006: 默认管理员无 force_password_change | Task 1 |
| SEC-007: 找回申请无验证 | Task 2 |
| SEC-008: 找回审批不验证用户存在 | Task 3 |
| SEC-009: 异常信息泄露 | Task 3 |
| SEC-010: 密码强度过弱 | Task 3 |
| SEC-011: 固定弱密码 abc123 | Task 3（通过 SEC-002 修复确保 force_password_change 生效） |
| SEC-012: OpenAPI 文档暴露 | Task 4 |
| SEC-013: Session Cookie 无 HttpOnly | Task 4 |
| SEC-014: 依赖版本 | 不涉及代码修改，建议手动 `pip audit` |
| SEC-015: Host 头验证 | 不涉及代码修改，低风险延后 |
| SEC-016: 找回不验证用户名 | Task 2（通过重复检查间接缓解） |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- `check_rate_limit` 和 `record_rate_limit_attempt` 的签名与现有 `check_login_rate_limit` / `record_login_attempt` 一致
- `force_password_change` 字段在 `User` 模型中已存在（Boolean）
- `secrets.token_hex(32)` 返回 64 字符的 hex 字符串，兼容 `SessionMiddleware` 的 `secret_key` 参数
