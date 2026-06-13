# Plan 1.4 完成总结

**完成日期**: 2026-06-13
**实际工时**: ~2 小时

## 验收清单

- [x] Sentry SDK 初始化（DSN 空安全）
- [x] structlog 配置 + JSON 输出
- [x] RequestContextMiddleware 注入 request_id / user_id
- [x] tenant_id 注入 structlog contextvars
- [x] /health 扩展 db_latency_ms + 5 分钟滚动计数
- [x] /api/v1/client-error 自报端点（小程序 → 后端日志 + Sentry）
- [x] users/me + records + announcements + classroom 加入 USER_OWNED_PATH_PREFIXES 白名单
- [x] /users/{user_id}/* 教师查学生场景接入 tenant 隔离
- [x] **test_route_audit 不再 xfail（assert == []）**
- [x] 全量 pytest: 432 passed（+6 vs 1.3）

## 新建/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/observability.py` | **新建** | Sentry + structlog 初始化入口 |
| `app/core/request_context.py` | **新建** | RequestContextMiddleware（request_id + metrics） |
| `app/core/metrics.py` | **新建** | _RollingCounter（请求/错误 5 分钟窗口） |
| `app/api/v1/client_error.py` | **新建** | 小程序错误上报端点 |
| `tests/test_observability.py` | **新建** | 2 tests |
| `tests/test_client_error.py` | **新建** | 3 tests |
| `tests/test_users_cross_tenant.py` | **新建** | 4 tests（教师查学生跨租户隔离） |
| `app/main.py` | 修改 | +observability init + RequestContextMiddleware + /health 扩展 + client_error router |
| `app/core/tenant.py` | 修改 | +structlog contextvars bind（tenant_id） |
| `app/api/v1/users.py` | 修改 | +_ensure_target_in_tenant + 3 endpoints tenant-scoped |
| `tests/test_route_audit.py` | 修改 | +USER_OWNED_PATH_PREFIXES + 移除 xfail |
| `requirements.txt` | 修改 | +sentry-sdk + structlog |

## 可观察性架构

```
Sentry ← 生产异常
 structlog (JSON) ← 请求日志
    ↑ contextvars (request_id, user_id, tenant_id)
    ↑ RequestContextMiddleware (每个请求注入 + metrics 计数)
 
 /health ← db_latency_ms + request_count_5m + error_count_5m
 /api/v1/client-error ← 小程序 JS 错误 → structlog + Sentry
```

## 审计收口

```
questions        ✅  COVERED_PREFIXES
classes          ✅  COVERED_PREFIXES  
assignments      ✅  COVERED_PREFIXES
users/{id}/*     ✅  COVERED_PREFIXES (Task 7 tenant scope)
users/me         ✅  USER_OWNED_PATH_PREFIXES
records          ✅  USER_OWNED_PATH_PREFIXES
announcements    ✅  USER_OWNED_PATH_PREFIXES
classroom        ✅  USER_OWNED_PATH_PREFIXES
client-error     ✅  USER_OWNED_PATH_PREFIXES
```

**test_route_audit: 0 xfail → passed。**

## 下一步

Plan 1.5（Phase 1 终期）— seed 完善 + E2E + 压测验收。
