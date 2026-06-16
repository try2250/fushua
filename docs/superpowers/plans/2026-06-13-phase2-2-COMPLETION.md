# Plan 2.2 完成总结

**完成日期**: 2026-06-16
**实际工时**: ~2.5 小时

## 验收清单

- [x] `test_badges.py` — 10/10 ✅（模型 + badge_service + 集成触发 + API）
- [x] `test_onboarding.py` — 5/5 ✅（模型 + API get/advance）
- [x] `test_chapter_map.py` — 1/1 ✅（chapter-map API）
- [x] `test_route_audit.py` — passed ✅（/api/v1/badges + /api/v1/onboarding 白名单）
- [x] `scripts/seed_badges.py` — 10 个 Badge 可写入 DB
- [x] 小程序成就页、章节地图页、新手引导组件已创建

## 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models.py` | 修改 | +Badge, UserBadge, OnboardingState |
| `alembic/versions/` | 新建 | migration for 3 models |
| `app/services/badge_service.py` | **新建** | 徽章触发逻辑（answer_submit + streak_change） |
| `scripts/seed_badges.py` | **新建** | 10 个 Badge seed |
| `app/api/v1/badges.py` | **新建** | GET /api/v1/badges/me |
| `app/api/v1/onboarding.py` | **新建** | GET state + POST advance |
| `app/api/v1/practice.py` | 修改 | +/chapter-map 端点 |
| `app/services/record_service.py` | 修改 | +badge 触发 |
| `app/services/checkin_service.py` | 修改 | +streak badge 触发 |
| `app/main.py` | 修改 | +badges + onboarding router |
| `tests/test_route_audit.py` | 修改 | +badges + onboarding 白名单 |
| `tests/test_badges.py` | **新建** | 10 tests |
| `tests/test_onboarding.py` | **新建** | 5 tests |
| `tests/test_chapter_map.py` | **新建** | 1 test |
| `miniprogram/pages/badges/*` | **新建** | 成就页（4 文件） |
| `miniprogram/pages/chapter-map/*` | **新建** | 章节地图页（4 文件） |
| `miniprogram/components/onboarding/*` | **新建** | 新手引导组件（4 文件） |
| `miniprogram/app.json` | 修改 | +2 pages |

## 10 个 Badge

| code | name | 触发 |
|------|------|------|
| opening | 开门红 | 首次答题 |
| streak_3 | 三日连击 | 连续 3 天打卡 |
| streak_7 | 七日不缀 | 连续 7 天 |
| streak_30 | 三十日大师 | 连续 30 天 |
| hundred | 百题成就 | 累计 100 题 |
| thousand | 千题成就 | 累计 1000 题 |
| perfect_set | 满分组 | 10 题全对 |
| subject_math | 数学开光 | 数学 >=80% + >=50 题 |
| subject_physics | 物理开光 | 同上 |
| subject_chinese | 语文开光 | 同上 |

## 测试覆盖

```
test_badges.py          10 passed
test_onboarding.py       5 passed
test_chapter_map.py       1 passed
test_route_audit.py       1 passed
────────────────────────────────
Total new tests          17 passed
```

## Phase 2 进度

| Plan | 内容 | 测试 | 状态 |
|------|------|------|------|
| 2.1 | 答题循环 + 打卡 + 排行 | 24 tests | ✅ |
| 2.2 | 徽章 + 章节地图 + 引导 | 17 tests | ✅ |
| 2.3 | 推送 dryrun + 通知中心 + 埋点 | - | 待启动 |
