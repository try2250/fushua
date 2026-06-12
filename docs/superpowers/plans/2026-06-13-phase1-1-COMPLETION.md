# Plan 1.1 完成总结

**完成日期**：2026-06-13
**实际工时**：~4 小时
**commit 范围**：`deff7d2..8c72df7`（11 个 commit）

## 验收清单

- [x] `pytest tests/test_tenant_isolation.py -v` — **15/15 全绿**
- [x] `pytest tests/test_route_audit.py -v` — questions 路由通过（其他 xfail）
- [x] `pytest tests/` 总体 — 573 passed, 2 failed（1 个修复后通过，1 个已有 miniprogram compat 问题），1 xfailed

## Commit 清单

| Commit | 内容 |
|--------|------|
| `deff7d2` | feat(tenant): add TenantContext dataclass scaffolding |
| `2dc44bc` | feat(tenant): resolve teacher tenant from bearer token |
| `5c6c2d7` | feat(tenant): resolve student tenant via class_id query param |
| `94ee5a3` | feat(tenant): add tenant_filter query helper |
| `92ee404` | feat(question): add tenant-aware service queries |
| `97c3e50` | feat(api/questions): enforce tenant isolation on list and detail |
| `6cdb391` | feat(api/questions): enforce tenant isolation on write ops |
| `2c731bd` | feat(api/questions): scope random endpoint to tenant |
| `532703c` | test(tenant): extract multi-tenant fixtures |
| `cdcba9b` | test(audit): add route scanner for tenant dependency |
| `8c72df7` | test: adapt existing tests for tenant isolation |

## 新建/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/tenant.py` | **新建** | TenantContext + get_tenant_context + tenant_filter |
| `app/services/question_service.py` | 修改 | +`get_questions_for_tenant`, `get_question_by_id_for_tenant`, `get_random_questions_for_tenant` |
| `app/api/v1/questions.py` | 修改 | 全部 6 个端点接入 `get_tenant_context` |
| `tests/test_tenant_isolation.py` | **新建** | 15 个隔离测试 |
| `tests/test_route_audit.py` | **新建** | API 路由 tenant 依赖审计 |
| `tests/fixtures_tenant.py` | **新建** | teacher_a/b + token + class_b_with_student |
| `tests/conftest.py` | 修改 | 注册多租户 fixture |
| `tests/test_questions_api.py` | 修改 | 适配 student create test |

## 模式总结（供 Plan 1.2 复用）

1. **依赖注入**：路由的 `current_user` 参数换成 `tenant: TenantContext = Depends(get_tenant_context)`
2. **service 层**：为每个查询方法增加 `_for_tenant` 版本，接受 `tenant_id` 参数
3. **白名单**：登录/注册/微信认证等不需要 tenant 的路径加入 `WHITELIST_PATH_PREFIXES`
4. **xfail 收口**：Plan 1.2 完成时移除 audit 测试里 questions 之外的 xfail 分支

## 已知问题

- `test_miniprogram_practice_record_aliases` — 已有问题，与 tenant 变更无关（未修改 practice-records 端点）
