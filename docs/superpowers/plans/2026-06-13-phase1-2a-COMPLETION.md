# Plan 1.2A 完成总结

**完成日期**: 2026-06-13
**实际工时**: ~3 小时
**commit 范围**: 来自 1.1 之后的新增

## 验收清单

- [x] `tests/test_tenant_isolation_class.py` — **9/9 全绿**
- [x] `tests/test_tenant_isolation_assignment.py` — **9/9 全绿**
- [x] `tests/test_route_audit.py` — classes/assignments 进入 COVERED；余下 users/records/announcements/classroom xfail
- [x] 全量 `tests/` — **592 passed, 1 xfailed**（0 新 fail）

## 新建/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `tests/test_tenant_isolation_class.py` | **新建** | 9 个 Class 隔离测试 |
| `tests/test_tenant_isolation_assignment.py` | **新建** | 9 个 Assignment 隔离测试 |
| `app/services/class_service.py` | 修改 | +`get_classes_for_tenant`, `get_class_by_id_for_tenant` |
| `app/services/assignment_service.py` | 修改 | +`get_assignments_for_tenant`, `get_assignment_by_id_for_tenant` |
| `app/api/v1/classes.py` | 修改 | 7 个端点接入 `TenantContext`；/join 保留 `get_current_user` |
| `app/api/v1/assignments.py` | 修改 | 8 个端点接入 `TenantContext` |
| `tests/test_route_audit.py` | 修改 | COVERED 扩到 questions+classes+assignments；加 EXACT_PATHS 白名单 |
| `tests/test_assignments_api.py` | 修改 | 适配 student 测试（补 class_id + membership） |
| `tests/test_classes_api.py` | 修改 | 适配 student 测试 |
| `tests/test_miniprogram_compat.py` | 修改 | 适配 student 测试 |

## 模式确认

1.1 模式（`_for_tenant` 命名 + `TenantContext` 依赖 + audit 收口）成功复用到 Class 和 Assignment 资源。
后续资源（Records / Users / Announcements / Classroom）按相同流程处理即可。

## 跨租户入口模式

`/api/v1/classes/{class_id}/join` 是唯一跨租户入口（学生主动加入任意班级），
保留 `get_current_user`，通过 audit 精确路径白名单豁免。

## 下一步

Plan 1.2B — Records / Users / Announcements / Classroom 接入 tenant。
