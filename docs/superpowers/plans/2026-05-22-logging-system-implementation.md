# 日志与错误追踪系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强现有日志系统，添加请求日志中间件、关键操作日志记录点、全局异常处理器，实现生产环境问题可追溯

**Architecture:** 基于现有的 `app/utils/logger.py` 和 `app/utils/error_monitor.py`，增强 `app/middleware/request_tracking.py` 添加请求日志记录，在 `app/main.py` 注册全局异常处理器，在关键路由（auth.py, teacher.py, permissions.py）添加日志记录点

**Tech Stack:** FastAPI, Python logging, Starlette middleware

---

## 现状分析

**已存在的组件**：
- ✅ `app/utils/logger.py` - 基础日志工具（AppLogger, 敏感信息过滤）
- ✅ `app/utils/error_monitor.py` - 内存错误监控器
- ✅ `app/middleware/request_tracking.py` - 请求ID和用户ID追踪
- ✅ `app/main.py` - 已导入日志工具

**需要增强的部分**：
- ❌ 请求日志中间件未记录请求开始/结束、耗时
- ❌ 缺少全局异常处理器记录500错误
- ❌ 关键操作（登录、权限拒绝、导入）未添加日志
- ❌ 缺少测试覆盖

---

## 文件结构

**修改的文件**：
- `app/middleware/request_tracking.py` - 增强请求日志记录
- `app/main.py` - 添加全局异常处理器
- `app/routers/auth.py` - 添加登录/注册日志
- `app/routers/permissions.py` - 添加权限拒绝日志
- `app/routers/teacher.py` - 添加导入操作日志

**新增的文件**：
- `tests/test_logging.py` - 日志系统单元测试
- `tests/test_logging_integration.py` - 日志系统集成测试

---

## Task 1: 增强请求日志中间件

**Files:**
- Modify: `app/middleware/request_tracking.py`
- Test: `tests/test_logging.py`

- [ ] **Step 1: 写失败测试 - 验证请求日志记录**

在 `tests/test_logging.py` 创建测试：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_request_logging_records_duration(caplog):
    """测试请求日志记录耗时"""
    client = TestClient(app)
    
    with caplog.at_level("INFO"):
        response = client.get("/health")
    
    assert response.status_code == 200
    # 验证日志包含请求信息
    log_records = [r for r in caplog.records if "GET /health" in r.message]
    assert len(log_records) > 0
    # 验证包含耗时信息
    assert "duration_ms" in log_records[0].message or "ms" in log_records[0].message
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_logging.py::test_request_logging_records_duration -v
```

预期输出：FAIL - 日志中没有耗时信息

- [ ] **Step 3: 增强请求日志中间件**

修改 `app/middleware/request_tracking.py`：

```python
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.utils.logger import log_info, log_error


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """为每个请求生成唯一的 request_id，并从 session 中提取 user_id，记录请求日志"""

    async def dispatch(self, request: Request, call_next):
        # 生成request_id
        request.state.request_id = str(uuid.uuid4())
        request.state.user_id = request.session.get("user_id")
        request.state.user_role = request.session.get("role")
        
        # 记录请求开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录请求日志
            log_info(
                f"{request.method} {request.url.path}",
                request=request,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request.state.request_id
            
            return response
            
        except Exception as e:
            # 记录异常
            duration_ms = int((time.time() - start_time) * 1000)
            log_error(
                f"Request failed: {request.method} {request.url.path}",
                request=request,
                exc_info=True,
                error=str(e),
                duration_ms=duration_ms
            )
            raise

```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_logging.py::test_request_logging_records_duration -v
```

预期输出：PASS

- [ ] **Step 5: 提交**

```bash
git add app/middleware/request_tracking.py tests/test_logging.py
git commit -m "feat: enhance request logging middleware with duration tracking"
```

---

## Task 2: 添加全局异常处理器

**Files:**
- Modify: `app/main.py:200-250`
- Test: `tests/test_logging_integration.py`

- [ ] **Step 1: 写失败测试 - 验证500错误日志**

创建 `tests/test_logging_integration.py`：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

def test_global_exception_handler_logs_500_errors(caplog):
    """测试全局异常处理器记录500错误"""
    client = TestClient(app)
    
    # 模拟一个会抛出异常的端点
    with patch("app.routers.pages.router") as mock_router:
        mock_router.get.side_effect = Exception("Test error")
        
        with caplog.at_level("ERROR"):
            response = client.get("/")
        
        # 验证返回500
        assert response.status_code == 500
        
        # 验证错误日志
        error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_logs) > 0
        assert "Test error" in error_logs[0].message
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_logging_integration.py::test_global_exception_handler_logs_500_errors -v
```

预期输出：FAIL - 没有全局异常处理器

- [ ] **Step 3: 在main.py添加全局异常处理器**

在 `app/main.py` 的路由注册之后添加：

```python
# 在 app.include_router(...) 之后添加

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，记录所有未捕获的异常"""
    from app.utils.logger import log_error
    from app.utils.error_monitor import error_monitor
    import traceback
    
    # 记录错误日志
    log_error(
        f"Unhandled exception: {type(exc).__name__}",
        request=request,
        exc_info=True,
        error_message=str(exc),
        traceback=traceback.format_exc()
    )
    
    # 添加到错误监控器
    error_monitor.add_error(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=getattr(request.state, "user_id", None),
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
        status_code=500
    )
    
    # 返回通用错误响应
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_logging_integration.py::test_global_exception_handler_logs_500_errors -v
```

预期输出：PASS

- [ ] **Step 5: 提交**

```bash
git add app/main.py tests/test_logging_integration.py
git commit -m "feat: add global exception handler with error logging"
```

---

## Task 3: 添加登录操作日志

**Files:**
- Modify: `app/routers/auth.py:32-100`
- Test: `tests/test_logging_integration.py`

- [ ] **Step 1: 写失败测试 - 验证登录日志**

在 `tests/test_logging_integration.py` 添加：

```python
def test_login_success_logs_operation(client, db, caplog):
    """测试登录成功记录日志"""
    from app.models import User
    
    # 创建测试用户
    user = User(
        username="testuser",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test User"
    )
    db.add(user)
    db.commit()
    
    with caplog.at_level("INFO"):
        response = client.post("/login", data={
            "username": "testuser",
            "password": "Test123!@#",
            "csrf_token": client.cookies.get("csrf_token", "")
        })
    
    assert response.status_code == 302  # 重定向
    
    # 验证日志
    login_logs = [r for r in caplog.records if "login_success" in r.message]
    assert len(login_logs) > 0

def test_login_failure_logs_warning(client, caplog):
    """测试登录失败记录警告日志"""
    with caplog.at_level("WARNING"):
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "wrongpass",
            "csrf_token": ""
        })
    
    # 验证警告日志
    warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warning_logs) > 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_logging_integration.py::test_login_success_logs_operation -v
pytest tests/test_logging_integration.py::test_login_failure_logs_warning -v
```

预期输出：FAIL - 没有登录日志

- [ ] **Step 3: 在auth.py添加登录日志**

修改 `app/routers/auth.py` 的登录路由：

```python
# 在文件顶部添加导入
from app.utils.logger import log_info, log_warning

# 在登录成功处添加（找到 request.session["user_id"] = user.id 附近）
@router.post("/login")
async def login(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    # ... 现有验证逻辑 ...
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.verify_password(password):
        # 记录登录失败
        log_warning(
            "Login failed",
            request=request,
            username=username,
            reason="invalid_credentials",
            ip_address=client_ip
        )
        # ... 现有错误处理 ...
    
    # 登录成功
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    
    # 记录登录成功
    log_info(
        "Login successful",
        request=request,
        username=username,
        user_id=user.id,
        role=user.role,
        ip_address=client_ip
    )
    
    # ... 现有重定向逻辑 ...
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_logging_integration.py::test_login_success_logs_operation -v
pytest tests/test_logging_integration.py::test_login_failure_logs_warning -v
```

预期输出：PASS

- [ ] **Step 5: 提交**

```bash
git add app/routers/auth.py tests/test_logging_integration.py
git commit -m "feat: add login operation logging"
```

---

## Task 4: 添加权限拒绝日志

**Files:**
- Modify: `app/routers/permissions.py`
- Test: `tests/test_logging_integration.py`

- [ ] **Step 1: 写失败测试 - 验证权限拒绝日志**

在 `tests/test_logging_integration.py` 添加：

```python
def test_permission_denied_logs_warning(client, db, caplog):
    """测试权限拒绝记录警告日志"""
    from app.models import User, ClassGroup
    
    # 创建两个教师和两个班级
    teacher1 = User(username="teacher1", password_hash=User.hash_password("Test123!@#"), role="teacher", display_name="Teacher 1")
    teacher2 = User(username="teacher2", password_hash=User.hash_password("Test123!@#"), role="teacher", display_name="Teacher 2")
    db.add_all([teacher1, teacher2])
    db.commit()
    
    class1 = ClassGroup(name="Class 1", created_by=teacher1.id)
    class2 = ClassGroup(name="Class 2", created_by=teacher2.id)
    db.add_all([class1, class2])
    db.commit()
    
    # 教师1登录
    client.post("/login", data={"username": "teacher1", "password": "Test123!@#"})
    
    with caplog.at_level("WARNING"):
        # 尝试访问教师2的班级
        response = client.get(f"/teacher/classes/{class2.id}")
    
    # 验证权限拒绝日志
    permission_logs = [r for r in caplog.records if "permission_denied" in r.message.lower()]
    assert len(permission_logs) > 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_logging_integration.py::test_permission_denied_logs_warning -v
```

预期输出：FAIL - 没有权限拒绝日志

- [ ] **Step 3: 在permissions.py添加权限拒绝日志**

修改 `app/routers/permissions.py`：

```python
# 在文件顶部添加导入
from app.utils.logger import log_warning

# 修改 teacher_owns_class 函数
def teacher_owns_class(db: Session, teacher_id: int, class_id: int) -> bool:
    """检查班级是否属于该教师"""
    from fastapi import Request
    from contextvars import ContextVar
    
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not cls:
        return False
    
    is_owner = cls.created_by == teacher_id
    
    if not is_owner:
        # 记录权限拒绝
        log_warning(
            "Permission denied: teacher does not own class",
            teacher_id=teacher_id,
            class_id=class_id,
            resource_type="class"
        )
    
    return is_owner

# 类似地修改其他权限检查函数：teacher_owns_student, teacher_owns_bank
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_logging_integration.py::test_permission_denied_logs_warning -v
```

预期输出：PASS

- [ ] **Step 5: 提交**

```bash
git add app/routers/permissions.py tests/test_logging_integration.py
git commit -m "feat: add permission denied logging"
```

---

## Task 5: 添加题目导入日志

**Files:**
- Modify: `app/routers/teacher.py` (导入题目相关函数)
- Test: `tests/test_logging_integration.py`

- [ ] **Step 1: 写失败测试 - 验证导入日志**

在 `tests/test_logging_integration.py` 添加：

```python
def test_question_import_logs_operation(client, db, caplog):
    """测试题目导入记录日志"""
    from app.models import User, QuestionBank
    
    # 创建教师和题库
    teacher = User(username="teacher", password_hash=User.hash_password("Test123!@#"), role="teacher", display_name="Teacher")
    db.add(teacher)
    db.commit()
    
    bank = QuestionBank(name="Test Bank", created_by=teacher.id)
    db.add(bank)
    db.commit()
    
    # 教师登录
    client.post("/login", data={"username": "teacher", "password": "Test123!@#"})
    
    # 准备CSV数据
    csv_content = "题目,选项A,选项B,选项C,选项D,答案,难度\n测试题,A,B,C,D,A,1"
    
    with caplog.at_level("INFO"):
        response = client.post(
            f"/teacher/questions/import",
            data={"bank_id": bank.id, "csv_text": csv_content}
        )
    
    # 验证导入日志
    import_logs = [r for r in caplog.records if "import" in r.message.lower()]
    assert len(import_logs) > 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_logging_integration.py::test_question_import_logs_operation -v
```

预期输出：FAIL - 没有导入日志

- [ ] **Step 3: 在teacher.py添加导入日志**

找到题目导入函数（通常在 `app/routers/teacher.py` 中），添加日志：

```python
# 在文件顶部添加导入
from app.utils.logger import log_info, log_error

# 在导入函数中添加（找到CSV解析和保存逻辑）
@router.post("/questions/import")
async def import_questions(request: Request, db: Session = Depends(get_db)):
    # ... 现有验证逻辑 ...
    
    success_count = 0
    failed_count = 0
    errors = []
    
    # ... CSV解析和保存逻辑 ...
    
    # 记录导入结果
    if failed_count > 0:
        log_error(
            "Question import completed with errors",
            request=request,
            bank_id=bank_id,
            total_count=success_count + failed_count,
            success_count=success_count,
            failed_count=failed_count,
            errors=errors[:10]  # 只记录前10条错误
        )
    else:
        log_info(
            "Question import successful",
            request=request,
            bank_id=bank_id,
            total_count=success_count,
            success_count=success_count
        )
    
    # ... 返回响应 ...
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_logging_integration.py::test_question_import_logs_operation -v
```

预期输出：PASS

- [ ] **Step 5: 提交**

```bash
git add app/routers/teacher.py tests/test_logging_integration.py
git commit -m "feat: add question import logging"
```

---

## Task 6: 运行完整测试套件

**Files:**
- Test: `tests/test_logging.py`, `tests/test_logging_integration.py`

- [ ] **Step 1: 运行所有日志相关测试**

```bash
pytest tests/test_logging.py tests/test_logging_integration.py -v
```

预期输出：所有测试通过

- [ ] **Step 2: 运行完整测试套件**

```bash
$env:PYTHONIOENCODING='utf-8'; python -m pytest tests/ -q --tb=short --disable-warnings
```

预期输出：所有测试通过，无回归

- [ ] **Step 3: 检查测试覆盖率（可选）**

```bash
pytest tests/test_logging.py tests/test_logging_integration.py --cov=app.utils.logger --cov=app.middleware.request_tracking --cov-report=term-missing
```

预期输出：覆盖率 > 80%

---

## Task 7: 更新文档

**Files:**
- Create: `docs/logging-usage-guide.md`

- [ ] **Step 1: 创建日志使用指南**

创建 `docs/logging-usage-guide.md`：

```markdown
# 日志系统使用指南

## 概述

项目使用统一的日志系统记录关键操作和错误，便于生产环境问题追溯。

## 日志级别

- **INFO**: 正常业务操作（登录成功、导入完成）
- **WARNING**: 需要注意的情况（权限拒绝、验证失败）
- **ERROR**: 业务错误（导入失败、数据库错误）
- **CRITICAL**: 系统级错误（500错误、配置错误）

## 使用方法

### 记录INFO日志

\`\`\`python
from app.utils.logger import log_info

log_info(
    "Operation successful",
    request=request,  # 可选，自动提取request_id和user_id
    operation_type="create_assignment",
    assignment_id=123
)
\`\`\`

### 记录WARNING日志

\`\`\`python
from app.utils.logger import log_warning

log_warning(
    "Permission denied",
    request=request,
    resource_type="student",
    resource_id=456
)
\`\`\`

### 记录ERROR日志

\`\`\`python
from app.utils.logger import log_error

log_error(
    "Import failed",
    request=request,
    exc_info=True,  # 包含异常堆栈
    error_message=str(e),
    details={"bank_id": 789}
)
\`\`\`

## 查看日志

### 本地开发

日志直接输出到控制台，带颜色高亮。

### Render生产环境

1. 登录Render Dashboard
2. 进入服务页面
3. 点击"Logs"标签
4. 使用搜索过滤：
   - `level:ERROR` - 查看所有错误
   - `login_failed` - 查看登录失败
   - `req:abc123` - 按request_id查询

## 敏感信息保护

日志系统自动过滤以下敏感字段：
- password, password_hash
- token, secret, api_key
- session, csrf_token

## 最佳实践

1. **关键操作必须记录日志**：登录、权限检查、数据修改
2. **错误必须记录上下文**：包含user_id、resource_id等
3. **避免记录敏感信息**：不要手动记录密码、token
4. **使用结构化数据**：通过extra参数传递字典，便于搜索
\`\`\`

- [ ] **Step 2: 提交文档**

```bash
git add docs/logging-usage-guide.md
git commit -m "docs: add logging system usage guide"
```

---

## Task 8: 手动验证

**Files:**
- N/A (手动测试)

- [ ] **Step 1: 启动应用并验证日志输出**

```bash
uvicorn app.main:app --reload
```

在浏览器中执行以下操作，观察控制台日志：
1. 访问首页 - 应看到请求日志
2. 登录成功 - 应看到 "Login successful"
3. 登录失败 - 应看到 "Login failed"
4. 访问无权限资源 - 应看到 "Permission denied"

- [ ] **Step 2: 验证日志格式**

检查日志输出是否包含：
- request_id (格式: req:xxxxxxxx)
- user_id (登录后)
- 操作类型
- 耗时信息 (duration_ms)

- [ ] **Step 3: 验证错误监控器**

访问 `/admin` (如果有错误监控页面) 或检查 `error_monitor.get_recent_errors()` 是否记录了错误。

---

## 验收标准

### 功能验收
- [ ] 所有HTTP请求都有日志记录（包含request_id、耗时）
- [ ] 500错误记录完整堆栈
- [ ] 登录成功/失败有日志
- [ ] 权限拒绝有日志
- [ ] 题目导入有日志
- [ ] 敏感信息已脱敏

### 测试验收
- [ ] 所有新增测试通过
- [ ] 完整测试套件无回归
- [ ] 测试覆盖率 > 80%

### 文档验收
- [ ] 日志使用指南完成
- [ ] 代码注释清晰

### 性能验收
- [ ] 日志记录不影响请求响应时间（增加 < 10ms）
- [ ] 无内存泄漏

---

## 后续优化（可选）

### Phase 2: Sentry集成
1. 注册Sentry账号
2. 安装 `sentry-sdk`
3. 在 `app/utils/error_monitor.py` 添加Sentry初始化
4. 配置环境变量 `SENTRY_DSN`

### Phase 3: 日志查询界面
1. 创建管理员日志查询页面
2. 按时间、用户、操作类型筛选
3. 错误日志高亮显示

---

## 注意事项

1. **项目文件组织规则**：
   - 真实项目文件放在 `fushua/` 根目录
   - 临时测试脚本、调试日志放在项目外的 `backup/debug/` 文件夹

2. **提交规范**：
   - 每个任务完成后立即提交
   - 提交信息格式：`feat: 功能描述` 或 `test: 测试描述`

3. **测试策略**：
   - 先写测试，再写实现（TDD）
   - 每个步骤都要验证测试通过

4. **代码风格**：
   - 遵循现有代码风格
   - 使用类型提示
   - 添加必要的注释
