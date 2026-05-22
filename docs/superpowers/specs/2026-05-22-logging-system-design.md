# 日志与错误追踪系统设计文档

**设计日期**: 2026-05-22  
**目标版本**: v3.2.0  
**优先级**: 🟡 P1（重要）

---

## 1. 设计目标

### 1.1 核心目标
- 生产环境问题可追溯：能够快速定位500错误、业务异常的根本原因
- 关键操作可审计：记录用户的重要操作，便于问题排查和安全审计
- 性能问题可诊断：记录请求耗时，识别慢查询和性能瓶颈
- 为未来扩展预留接口：支持后续接入Sentry等专业监控服务

### 1.2 非目标
- 不做实时告警（第一版）
- 不做日志聚合分析（依赖Render Logs）
- 不做日志持久化存储（依赖Render平台）

---

## 2. 架构设计

### 2.1 组件结构

```
app/
├── utils/
│   ├── logger.py          # 统一日志服务（核心模块）
│   └── error_monitor.py   # 错误监控（预留Sentry接口）
├── middleware/
│   └── logging.py         # 请求日志中间件
└── main.py                # 注册中间件和异常处理器
```

### 2.2 数据流

```
HTTP请求
    ↓
[日志中间件] → 生成request_id，提取user_id
    ↓
[路由处理器] → 业务逻辑，手动记录关键操作
    ↓
[异常处理器] → 捕获500错误，记录完整堆栈
    ↓
[日志中间件] → 记录响应状态码和耗时
    ↓
输出到stdout（Render Logs）
```

### 2.3 日志输出目标

- **开发环境**：控制台输出，带颜色高亮
- **生产环境**：JSON格式输出到stdout，由Render收集
- **未来扩展**：通过error_monitor.py发送到Sentry

---

## 3. 日志格式设计

### 3.1 标准日志格式（JSON）

```json
{
  "timestamp": "2026-05-22T10:30:45.123Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "user_id": 42,
  "user_role": "teacher",
  "action": "import_questions",
  "path": "/teacher/questions/import",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 234,
  "ip_address": "192.168.1.100",
  "details": {
    "bank_id": 5,
    "questions_count": 50,
    "success_count": 48,
    "failed_count": 2,
    "errors": ["第3行：选项格式错误", "第7行：答案不能为空"]
  }
}
```

### 3.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | string | 是 | ISO 8601格式时间戳 |
| level | string | 是 | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| request_id | string | 是 | 请求唯一标识，格式：req_{uuid} |
| user_id | int | 否 | 当前用户ID（未登录为null） |
| user_role | string | 否 | 用户角色：admin/teacher/student/guest |
| action | string | 是 | 操作类型（见3.3） |
| path | string | 是 | 请求路径 |
| method | string | 是 | HTTP方法 |
| status_code | int | 是 | HTTP状态码 |
| duration_ms | int | 是 | 请求处理耗时（毫秒） |
| ip_address | string | 否 | 客户端IP地址 |
| details | object | 否 | 操作详细信息（结构化数据） |
| error | object | 否 | 错误信息（包含message、traceback） |

### 3.3 操作类型（action）

**认证相关**：
- `login_success` / `login_failed`
- `register`
- `logout`

**权限相关**：
- `permission_denied`
- `cross_class_access_attempt`

**数据操作**：
- `import_questions`
- `import_students`
- `create_class`
- `delete_class`
- `create_assignment`
- `delete_assignment`
- `delete_question_bank`

**错误追踪**：
- `http_500_error`
- `database_error`
- `validation_error`

---

## 4. 日志级别策略

### 4.1 级别定义

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 开发调试 | SQL查询、函数调用栈 |
| INFO | 正常业务操作 | 登录成功、导入完成、作业创建 |
| WARNING | 需要注意但不影响功能 | 权限拒绝、输入验证失败、重复操作 |
| ERROR | 业务错误 | 导入失败、数据库查询失败、文件读取失败 |
| CRITICAL | 系统级错误 | 数据库连接失败、500错误、配置错误 |

### 4.2 生产环境级别

- 默认级别：**INFO**
- 通过环境变量 `LOG_LEVEL` 可调整
- DEBUG级别仅在开发环境启用

---

## 5. 核心模块设计

### 5.1 logger.py（统一日志服务）

**功能**：
- 提供统一的日志记录接口
- 自动注入请求上下文（request_id、user_id）
- 支持结构化日志输出
- 提供便捷的日志方法

**主要接口**：
```python
# 初始化日志系统
def setup_logging(log_level: str = "INFO", json_format: bool = True)

# 获取日志记录器
def get_logger(name: str) -> Logger

# 记录业务操作
def log_operation(
    action: str,
    level: str = "INFO",
    user_id: Optional[int] = None,
    details: Optional[dict] = None
)

# 记录错误
def log_error(
    error: Exception,
    action: str,
    user_id: Optional[int] = None,
    details: Optional[dict] = None
)
```

### 5.2 middleware/logging.py（请求日志中间件）

**功能**：
- 为每个请求生成唯一request_id
- 从session提取user_id和user_role
- 记录请求开始时间
- 请求结束时记录状态码和耗时
- 自动捕获异常

**实现要点**：
```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # 1. 生成request_id
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # 2. 提取用户信息
    user_id = request.session.get("user_id")
    user_role = request.session.get("role")
    
    # 3. 注入上下文
    contextvars.request_id.set(request_id)
    contextvars.user_id.set(user_id)
    
    # 4. 记录请求开始
    start_time = time.time()
    
    # 5. 处理请求
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 6. 记录请求完成
        log_request(request, response.status_code, duration_ms)
        
        return response
    except Exception as e:
        # 7. 记录异常
        log_error(e, action="http_request", ...)
        raise
```

### 5.3 error_monitor.py（错误监控）

**功能**：
- 统一的错误上报接口
- 预留Sentry集成
- 错误分类和过滤

**主要接口**：
```python
# 初始化错误监控（可选Sentry DSN）
def init_error_monitor(sentry_dsn: Optional[str] = None)

# 上报错误
def report_error(
    error: Exception,
    context: dict,
    level: str = "error"
)

# 捕获异常装饰器
def capture_exceptions(func)
```

---

## 6. 关键操作日志记录点

### 6.1 认证模块（app/routers/auth.py）

**登录成功**：
```python
log_operation(
    action="login_success",
    level="INFO",
    user_id=user.id,
    details={
        "username": user.username,
        "role": user.role,
        "ip_address": request.client.host
    }
)
```

**登录失败**：
```python
log_operation(
    action="login_failed",
    level="WARNING",
    details={
        "username": username,
        "reason": "invalid_password",
        "ip_address": request.client.host
    }
)
```

### 6.2 权限检查（app/routers/permissions.py）

**权限拒绝**：
```python
log_operation(
    action="permission_denied",
    level="WARNING",
    user_id=teacher_id,
    details={
        "resource_type": "student",
        "resource_id": student_id,
        "reason": "not_in_teacher_class"
    }
)
```

### 6.3 数据导入（app/routers/teacher.py）

**题目导入**：
```python
log_operation(
    action="import_questions",
    level="INFO" if success_count > 0 else "ERROR",
    user_id=teacher_id,
    details={
        "bank_id": bank_id,
        "total_count": total_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": error_messages[:10]  # 只记录前10条错误
    }
)
```

### 6.4 异常处理（app/main.py）

**500错误**：
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(
        error=exc,
        action="http_500_error",
        user_id=request.session.get("user_id"),
        details={
            "path": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params),
            "traceback": traceback.format_exc()
        }
    )
    
    # 上报到Sentry（如果已配置）
    report_error(exc, context={...})
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## 7. 性能考虑

### 7.1 日志性能优化

- 使用异步日志写入（避免阻塞请求）
- 限制details字段大小（最大10KB）
- 错误堆栈截断（最多100行）
- 敏感信息脱敏（密码、token）

### 7.2 日志采样（未来优化）

- 正常请求（2xx）：100%记录
- 客户端错误（4xx）：100%记录
- 服务器错误（5xx）：100%记录
- 静态资源请求：可选择性关闭

---

## 8. 安全和隐私

### 8.1 敏感信息脱敏

**需要脱敏的字段**：
- 密码：完全不记录
- Session token：只记录前8位
- 用户真实姓名：可选脱敏（生产环境建议开启）
- IP地址：记录但不用于用户画像

**脱敏实现**：
```python
def sanitize_log_data(data: dict) -> dict:
    """脱敏敏感信息"""
    sensitive_keys = ["password", "token", "secret"]
    for key in sensitive_keys:
        if key in data:
            data[key] = "***REDACTED***"
    return data
```

### 8.2 日志访问控制

- 日志仅管理员可查看
- Render Logs访问需要平台权限
- 不在前端暴露详细日志

---

## 9. 测试策略

### 9.1 单元测试

**测试文件**：`tests/test_logging.py`

**测试用例**：
- 日志格式正确性
- request_id生成和传递
- 用户上下文注入
- 敏感信息脱敏
- 错误堆栈记录

### 9.2 集成测试

**测试文件**：`tests/test_logging_integration.py`

**测试场景**：
- 完整请求的日志记录
- 异常捕获和记录
- 中间件正确注入上下文
- 多个请求的request_id隔离

---

## 10. 部署和配置

### 10.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| LOG_LEVEL | INFO | 日志级别 |
| LOG_FORMAT | json | 日志格式：json/text |
| SENTRY_DSN | None | Sentry DSN（可选） |
| SENTRY_ENVIRONMENT | production | Sentry环境标识 |

### 10.2 Render配置

在Render Dashboard添加环境变量：
```
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 10.3 查看日志

**Render平台**：
1. 进入服务页面
2. 点击"Logs"标签
3. 使用搜索过滤：`level:ERROR` 或 `action:login_failed`

**本地开发**：
```bash
# 启动应用
uvicorn app.main:app --reload

# 查看日志（带颜色）
# 日志会直接输出到控制台
```

---

## 11. 未来扩展

### 11.1 Sentry集成（Phase 2）

**实现步骤**：
1. 安装依赖：`pip install sentry-sdk`
2. 在 `error_monitor.py` 中初始化Sentry
3. 配置环境变量 `SENTRY_DSN`
4. 自动上报500错误和业务异常

**预期效果**：
- 实时错误告警
- 错误聚合和趋势分析
- 用户影响范围统计
- 错误自动分配和跟踪

### 11.2 日志查询界面（Phase 3）

**功能**：
- 管理员后台日志查询页面
- 按时间、用户、操作类型筛选
- 错误日志高亮显示
- 导出日志功能

### 11.3 性能监控（Phase 4）

**功能**：
- 慢查询检测（>1秒）
- API响应时间统计
- 数据库连接池监控
- 内存使用监控

---

## 12. 实施计划

### Phase 1：基础日志系统（本次实施）

**预计时间**：3-4小时

**任务清单**：
- [ ] 实现 `app/utils/logger.py`
- [ ] 实现 `app/utils/error_monitor.py`（预留Sentry接口）
- [ ] 实现 `app/middleware/logging.py`
- [ ] 在 `app/main.py` 注册中间件和异常处理器
- [ ] 在关键操作点添加日志记录
  - [ ] 登录/登出（auth.py）
  - [ ] 权限拒绝（permissions.py）
  - [ ] 题目导入（teacher.py）
  - [ ] 学生导入（teacher.py）
  - [ ] 作业创建/删除（assignment.py）
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 更新文档

### Phase 2：Sentry集成（可选）

**预计时间**：1-2小时

**任务清单**：
- [ ] 注册Sentry账号
- [ ] 配置Sentry DSN
- [ ] 测试错误上报
- [ ] 配置告警规则

---

## 13. 验收标准

### 13.1 功能验收

- [ ] 所有HTTP请求都有日志记录
- [ ] 日志包含request_id、user_id、耗时
- [ ] 500错误记录完整堆栈
- [ ] 关键操作有详细日志
- [ ] 敏感信息已脱敏
- [ ] 日志格式为JSON（生产环境）

### 13.2 测试验收

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 手动测试各种场景

### 13.3 文档验收

- [ ] 设计文档完成
- [ ] 代码注释清晰
- [ ] 部署文档更新

### 13.4 性能验收

- [ ] 日志记录不影响请求响应时间（<10ms）
- [ ] 无内存泄漏
- [ ] 日志文件大小可控

---

## 14. 风险和缓解

### 14.1 风险识别

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 日志量过大 | 存储成本增加 | 中 | 设置日志保留期限，采样策略 |
| 性能影响 | 请求变慢 | 低 | 异步日志，限制字段大小 |
| 敏感信息泄露 | 隐私问题 | 中 | 严格脱敏，访问控制 |
| 日志丢失 | 问题无法追溯 | 低 | 依赖Render平台可靠性 |

### 14.2 回滚方案

如果日志系统导致问题：
1. 通过环境变量关闭详细日志：`LOG_LEVEL=ERROR`
2. 移除中间件注册（注释掉 `app.add_middleware`）
3. 回滚到上一个稳定版本

---

## 15. 参考资料

- [Python logging文档](https://docs.python.org/3/library/logging.html)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [FastAPI中间件](https://fastapi.tiangolo.com/tutorial/middleware/)
- [结构化日志最佳实践](https://www.structlog.org/)

---

**文档版本**: v1.0  
**最后更新**: 2026-05-22  
**负责人**: 开发团队  
**审核状态**: 待审核
