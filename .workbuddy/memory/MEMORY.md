# 浮刷 (FuShua) 项目记忆

## 多租户基础设施 (Plan 1.1 + 1.2A — 2026-06-13 完成)

### 核心概念
- **TenantContext**: 封装租户上下文，tenant_id = 老师 user.id
- **get_tenant_context**: FastAPI Depends，从 Bearer Token / session / class_id 解析租户
- **tenant_filter**: 对 SQLAlchemy Query 按 created_by 过滤
- Teacher 自动取自己 user.id；Student 通过 class_id 查询参数 → ClassGroup.created_by

### 关键文件
- `app/core/tenant.py` — 基础设施核心
- `app/api/v1/questions.py` — 示范接入（6 个端点全部 tenant-aware）
- `app/api/v1/classes.py` — 7 个端点 tenant-aware（/join 为跨租户入口）
- `app/api/v1/assignments.py` — 8 个端点 tenant-aware
- `tests/test_tenant_isolation.py` — 15 个隔离测试
- `tests/test_tenant_isolation_class.py` — 9 个 Class 隔离测试
- `tests/test_tenant_isolation_assignment.py` — 9 个 Assignment 隔离测试
- `tests/test_route_audit.py` — audit 扫描器（questions/classes/assignments 已覆盖）
- `tests/fixtures_tenant.py` — teacher_a/b token 等 fixture

### 模式复用
其他资源接入 tenant 的步骤：
1. 路由参数 `current_user` → `tenant: TenantContext = Depends(get_tenant_context)`
2. service 层加 `_for_tenant` 方法，接受 `tenant_id`
3. 加入 audit COVERED_PREFIXES
4. 跨租户入口（如 /join）加入 WHITELIST_EXACT_PATHS

### 待接入资源
用户/记录/公告/课堂伴侣 — Plan 1.2B
