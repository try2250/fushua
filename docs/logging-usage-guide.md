# 日志系统使用指南

## 概述

项目使用统一的日志系统记录关键操作和错误,便于生产环境问题追溯。

## 日志级别

- **INFO**: 正常业务操作(登录成功、导入完成)
- **WARNING**: 需要注意的情况(权限拒绝、验证失败)
- **ERROR**: 业务错误(导入失败、数据库错误)
- **CRITICAL**: 系统级错误(500错误、配置错误)

## 使用方法

### 记录INFO日志

```python
from app.utils.logger import log_info

log_info(
    "Operation successful",
    request=request,  # 可选,自动提取request_id和user_id
    operation_type="create_assignment",
    assignment_id=123
)
```

### 记录WARNING日志

```python
from app.utils.logger import log_warning

log_warning(
    "Permission denied",
    request=request,
    resource_type="student",
    resource_id=456
)
```

### 记录ERROR日志

```python
from app.utils.logger import log_error

log_error(
    "Import failed",
    request=request,
    exc_info=True,  # 包含异常堆栈
    error_message=str(e),
    details={"bank_id": 789}
)
```

## 查看日志

### 本地开发

日志直接输出到控制台,带颜色高亮。

### Render生产环境

1. 登录Render Dashboard
2. 进入服务页面
3. 点击"Logs"标签
4. 使用搜索过滤:
   - `level:ERROR` - 查看所有错误
   - `login_failed` - 查看登录失败
   - `req:abc123` - 按request_id查询

## 敏感信息保护

日志系统自动过滤以下敏感字段:
- password, password_hash
- token, secret, api_key
- session, csrf_token

## 最佳实践

1. **关键操作必须记录日志**:登录、权限检查、数据修改
2. **错误必须记录上下文**:包含user_id、resource_id等
3. **避免记录敏感信息**:不要手动记录密码、token
4. **使用结构化数据**:通过extra参数传递字典,便于搜索
