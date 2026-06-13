# Plan 1.3 完成总结

**完成日期**: 2026-06-13
**实际工时**: ~2 小时

## 验收清单

- [x] `tests/test_logging.py` 1/1 passed（无需重写，已使用 TestClient）
- [x] 小程序 tabbar 5 张 PNG 图标生成 + app.json 更新
- [x] `/platform/users` 用户管理（list/search/reset-password/toggle-disable/delete）
- [x] `/platform/recovery-requests` 找回审核（approve/reject）
- [x] `/platform/classes` 班级总览（跨租户）
- [x] `/platform/audit-log` 审计日志 + CSV 导出
- [x] `/platform/announcements` 公告 CRUD 全套
- [x] `/platform/data-export` 4 类数据导出
- [x] `app/routers/admin.py` 已物理删除
- [x] `app/templates/admin/` 已物理删除
- [x] `app/templates/base.html` admin 链接改为 /platform/*
- [x] 全量测试: **426 passed**（比 1.2B 多 19 个通过）

## 新建文件

| 文件 | 说明 |
|------|------|
| `app/routers/platform_users.py` | 用户管理（_require_platform 共享依赖） |
| `app/routers/platform_recovery.py` | 找回申请 |
| `app/routers/platform_classes.py` | 班级总览 |
| `app/routers/platform_audit.py` | 审计日志 + CSV 导出 |
| `app/routers/platform_announcements.py` | 公告 CRUD |
| `app/routers/platform_export.py` | 数据导出（users/classes/questions/stats） |
| `app/templates/platform/users.html` | 用户列表 |
| `app/templates/platform/user_detail.html` | 用户详情 |
| `app/templates/platform/recovery_requests.html` | 找回审核 |
| `app/templates/platform/classes.html` | 班级总览 |
| `app/templates/platform/audit_log.html` | 审计日志 |
| `app/templates/platform/announcements.html` + `announcement_form.html` | 公告 |
| `app/templates/platform/data_export.html` | 导出页 |
| `tests/test_platform_users.py` | 4 tests |
| `tests/test_platform_recovery.py` | 2 tests |
| `tests/test_platform_classes.py` | 1 test |
| `tests/test_platform_audit.py` | 3 tests |
| `tests/test_platform_announcements.py` | 4 tests |
| `tests/test_platform_export.py` | 1 test |
| `miniprogram/images/tabbar/` | 10 张 PNG 图标 |

## 删除文件

- `app/routers/admin.py`
- `app/templates/admin/`（13 个文件）

## 核心架构

```
/platform/*
  ├── login / logout / dashboard       (platform.py)
  ├── /users / users/{id}/*            (platform_users.py)
  ├── /recovery-requests/*             (platform_recovery.py)
  ├── /classes                         (platform_classes.py)
  ├── /audit-log / audit-log/export    (platform_audit.py)
  ├── /announcements / create/edit/toggle/delete (platform_announcements.py)
  └── /data-export / export/*           (platform_export.py)

认证: session.platform_admin_id → PlatformAdmin 表
共享依赖: _require_platform (request, db=Depends(get_db))
```

## 下一步

Plan 1.4 — 可观察性 + tenant 推广到 users/records/announcements。
