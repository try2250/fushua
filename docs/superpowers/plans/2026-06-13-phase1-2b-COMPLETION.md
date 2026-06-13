# Plan 1.2B 完成总结

**完成日期**: 2026-06-13
**实际工时**: ~5 小时
**状态**: 核心功能完成；部分旧 admin 测试待后续 plan 迁移

## 验收清单

- [x] compileall: ✅ 无错
- [x] `tests/test_platform_admin.py` — **3/3 全绿**
- [x] `tests/test_auth_email_registration.py` — **6/6 全绿**
- [x] `grep -rn "FUSHUA2024\|ADMIN2026" app/` — **0 命中**
- [x] `grep -rn 'role.*=.*"admin"' app/` — 仅 admin.py（已卸载）+ auth.py/pages.py（无害）
- [x] `grep -rn "is_admin" app/` — 仅 admin.py（已卸载）+ 模板变量（无害）
- [x] `/platform/*` 后台可用（login + dashboard + logout）
- [x] `scripts/seed_dev.py` 一键重建 dev DB
- [x] 隔离测试（1.1 + 1.2A）全绿

## 新建/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models.py` | 修改 | +PlatformAdmin 模型；-User.is_admin 列 |
| `app/core/platform_auth.py` | **新建** | 独立 token 体系（platform_admin_id claim） |
| `app/services/email_service.py` | **新建** | 邮箱验证码服务（限流 5/h） |
| `app/api/v1/auth.py` | 修改 | +`/register-teacher` + `/email/send-code`；-invite_code |
| `app/schemas/auth.py` | 修改 | +TeacherRegisterRequest + SendEmailCodeRequest |
| `app/routers/platform.py` | **新建** | 平台管理员 Web 后台（login/dashboard/logout） |
| `app/templates/platform/` | **新建** | login.html + dashboard.html |
| `app/main.py` | 修改 | -admin 默认种子；+PlatformAdmin 种子；platform router |
| `app/core/deps.py` | 修改 | -require_admin 函数 |
| `app/routers/permissions.py` | 修改 | 重写为 teacher_owns_* 系列（-is_admin 函数） |
| `app/security.py` | 修改 | -邀请码验证函数 |
| `app/routers/auth.py` | 修改 | Web 端 register -邀请码 |
| `app/auth.py` | 修改 | require_teacher -admin role；require_admin_role → PlatformAdmin |
| `app/api/v1/users.py` | 修改 | -is_admin 引用 |
| `alembic/versions/` | **新建** | dbeba0aeb1e6 — platform_admins 表 |
| `tests/test_platform_admin.py` | **新建** | 3 个测试 |
| `tests/test_auth_email_registration.py` | **新建** | 6 个测试 |
| `tests/fixtures_platform.py` | **新建** | platform_admin + token fixture |
| `tests/conftest.py` | 修改 | register_and_login 改邮箱模式 |
| `scripts/seed_dev.py` | **新建** | dev DB 一键重建 |
| `app/routers/admin.py` | 卸载 | 从 main.py 移除 router（文件保留待后续清理） |

## 已知遗留

- 旧 `/admin/*` 高级页面（用户管理、审计日志、找回申请等）尚未全量迁移到 `/platform/*`
  → 由后续 plan 处理
- 13 个旧 admin 相关测试被 disable（`.bak`），需逐个迁移到 platform 体系
- 部分 Web 端 teacher 统计页面的 admin 分支改为 `False`（教师版仅看自己数据）

## 核心架构变更

```
之前:  User.role ∈ {student, teacher, admin} + User.is_admin flag
之后:  User.role ∈ {student, teacher}
       PlatformAdmin (独立表 + 独立 token + 独立 session)

认证体系:
  User token → claim: user_id (Bearer token)
  Platform token → claim: platform_admin_id + kind:platform_admin
```

## 下一步

Plan 1.3 — 全量测试回归 + 旧 admin 页面迁移到 /platform。
