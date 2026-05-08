# 付刷（Fushua）安全审查报告

**审查日期**: 2026-05-08  
**技术栈**: Python 3.x + FastAPI + SQLAlchemy + Jinja2 + SQLite  
**审查范围**: 全部应用代码（app/ 目录）

---

## 执行摘要

本次安全审查基于 FastAPI 安全最佳实践规范，对"付刷"项目进行了全面扫描。共发现 **8 个安全问题**，其中 **2 个严重（Critical）**、**3 个高危（High）**、**2 个中危（Medium）**、**1 个低危（Low）**。最紧迫的问题是密码哈希使用 SHA256（快速哈希）而非 bcrypt/Argon2，以及 Session 密钥硬编码在源码中。

---

## 严重（Critical）

### SEC-001: 密码哈希使用 SHA256 而非专用密码哈希算法

- **规则**: FASTAPI-AUTH-003
- **位置**: `app/models.py` 第 34-35 行
- **证据**:
  ```python
  @staticmethod
  def hash_password(password: str, salt: str) -> str:
      return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
  ```
- **影响**: SHA256 是快速哈希算法，攻击者可以每秒尝试数十亿次密码。即使加了 salt，暴力破解仍然非常高效。专用密码哈希（如 bcrypt、Argon2id）通过迭代/内存消耗使暴力破解成本提高数万倍。
- **修复**: 使用 `bcrypt` 或 `argon2-cffi` 替代 SHA256。示例：
  ```python
  import bcrypt

  @staticmethod
  def hash_password(password: str) -> str:
      return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

  @staticmethod
  def verify_password(stored_hash: str, password: str) -> bool:
      return bcrypt.checkpw(password.encode(), stored_hash.encode())
  ```
- **迁移**: 需要添加 re-hash-on-login 升级路径，兼容旧 SHA256 哈希。

### SEC-002: Session 密钥硬编码在源码中

- **规则**: FASTAPI-SESS-001 / FASTAPI-SESS-002
- **位置**: `app/main.py` 第 14 行
- **证据**:
  ```python
  app.add_middleware(SessionMiddleware, secret_key="fushua-secret-key-change-in-production")
  ```
- **影响**: 硬编码的密钥意味着任何能看到源码的人都能伪造 session cookie，冒充任意用户（包括教师）。此密钥用于签名 session 数据，泄露即等同于认证绕过。
- **修复**: 从环境变量读取密钥：
  ```python
  import os
  SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
  if SECRET_KEY == "dev-only-insecure-key":
      import warnings
      warnings.warn("使用默认密钥，请设置 SECRET_KEY 环境变量！")
  app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
  ```

---

## 高危（High）

### SEC-003: Session Cookie 缺少安全属性（SameSite、HttpsOnly）

- **规则**: FASTAPI-SESS-001
- **位置**: `app/main.py` 第 14 行
- **证据**:
  ```python
  app.add_middleware(SessionMiddleware, secret_key="fushua-secret-key-change-in-production")
  ```
  未设置 `same_site`、`https_only` 参数。
- **影响**: Session Cookie 默认 `SameSite=Lax`（Starlette 默认），但未显式设置 `https_only=True`。在生产 HTTPS 环境下，cookie 可通过 HTTP 连接被截获。
- **修复**:
  ```python
  app.add_middleware(
      SessionMiddleware,
      secret_key=SECRET_KEY,
      same_site="lax",
      https_only=os.environ.get("HTTPS_ONLY", "false").lower() == "true",
  )
  ```

### SEC-004: 缺少 CSRF 保护

- **规则**: FASTAPI-CSRF-001
- **位置**: 所有 POST 路由（`app/routers/auth.py`、`app/routers/teacher.py`、`app/routers/student.py`）
- **证据**: 项目使用 Cookie-based Session 认证，但所有状态变更端点（注册、登录、出题、删题、提交答案等）均无 CSRF Token 验证。
- **影响**: 攻击者可以构造恶意页面，诱导已登录用户在不知情的情况下提交表单（如删除题目、修改密码等）。
- **修复**: 添加 CSRF 中间件（如 `starlette-csrf` 或自定义 CSRF Token 机制），在所有 POST 表单中嵌入并验证 CSRF Token。

### SEC-005: Session 中存储敏感角色信息

- **规则**: FASTAPI-SESS-002
- **位置**: `app/routers/auth.py` 第 43-46 行、第 69-72 行
- **证据**:
  ```python
  request.session["user_id"] = user.id
  request.session["username"] = user.username
  request.session["role"] = user.role
  request.session["display_name"] = user.display_name
  ```
- **影响**: Starlette SessionMiddleware 使用签名 cookie（非加密），客户端可读取 cookie 内容。`role` 字段存储在客户端可读的 cookie 中，攻击者虽不能篡改（有签名），但可以了解系统结构。更重要的是，如果密钥泄露（见 SEC-002），攻击者可以伪造 `role=teacher` 提权。
- **修复**: Session 中仅存储 `user_id`，其他信息（role、display_name）从数据库实时查询。

---

## 中危（Medium）

### SEC-006: 缺少安全响应头

- **规则**: FASTAPI-HEADERS-001
- **位置**: `app/main.py` — 无安全头中间件
- **证据**: 项目未设置 `X-Content-Type-Options`、`X-Frame-Options`、`Content-Security-Policy` 等安全头。
- **影响**: 缺少 `X-Frame-Options` 使页面可被 iframe 嵌入（Clickjacking）；缺少 `X-Content-Type-Options: nosniff` 可能导致 MIME 嗅探攻击。
- **修复**: 添加安全头中间件：
  ```python
  from starlette.middleware.base import BaseHTTPMiddleware

  class SecurityHeadersMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request, call_next):
          response = await call_next(request)
          response.headers["X-Content-Type-Options"] = "nosniff"
          response.headers["X-Frame-Options"] = "DENY"
          response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
          return response

  app.add_middleware(SecurityHeadersMiddleware)
  ```

### SEC-007: 文件上传缺少类型和大小验证

- **规则**: FASTAPI-UPLOAD-001
- **位置**: `app/routers/teacher.py` 第 155-199 行
- **证据**:
  ```python
  filename = file.filename or ""
  content_bytes = await file.read()
  ```
  仅通过文件扩展名（`.json`/`.csv`）判断类型，未验证文件内容，未限制文件大小。
- **影响**: 恶意用户可上传超大文件导致内存耗尽（DoS），或上传伪装扩展名的恶意文件。
- **修复**:
  - 添加文件大小限制（如 5MB）
  - 验证文件内容是否为合法 JSON/CSV
  - 使用 `io.BytesIO` 限制读取大小

---

## 低危（Low）

### SEC-008: 缺少 Host 头验证

- **规则**: FASTAPI-HOST-001
- **位置**: `app/main.py` — 无 TrustedHostMiddleware
- **影响**: 在反向代理部署时，可能遭受 Host 头注入。当前项目未使用 Host 头构建外部 URL，风险较低。
- **修复**: 生产部署时添加 `TrustedHostMiddleware`。

---

## 已确认安全的部分

| 检查项 | 状态 | 说明 |
|--------|------|------|
| SQL 注入 | ✅ 安全 | 全部使用 SQLAlchemy ORM，无原始 SQL 拼接 |
| 命令注入 | ✅ 安全 | 无 `subprocess`、`os.system` 调用 |
| XSS（模板） | ✅ 安全 | Jinja2 默认自动转义，未使用 `\|safe` 过滤器 |
| SSTI | ✅ 安全 | 模板均为静态文件，无用户控制的模板字符串 |
| 开放重定向 | ✅ 安全 | 所有 `RedirectResponse` 使用硬编码 URL |
| CORS | ✅ 安全 | 未启用 CORS（纯服务端渲染，无需跨域） |
| OpenAPI 暴露 | ⚠️ 注意 | FastAPI 默认启用 `/docs`，生产环境应关闭 |

---

## 修复优先级建议

1. **立即修复**: SEC-001（密码哈希）、SEC-002（密钥硬编码）
2. **尽快修复**: SEC-003（Cookie 安全属性）、SEC-004（CSRF 保护）、SEC-005（Session 最小化）
3. **计划修复**: SEC-006（安全头）、SEC-007（上传验证）
4. **部署时处理**: SEC-008（Host 验证）
