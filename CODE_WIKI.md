# 付刷 (FuShua) — Code Wiki

> **版本**: 3.0.0
> **技术栈**: Python 3.12 / FastAPI / SQLAlchemy / Jinja2 / SQLite & PostgreSQL
> **定位**: 中学在线刷题与教学管理平台

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [目录结构](#3-目录结构)
4. [核心模块详解](#4-核心模块详解)
   - 4.1 [应用入口 — app/main.py](#41-应用入口--appmainpy)
   - 4.2 [数据模型 — app/models.py](#42-数据模型--appmodelspy)
   - 4.3 [数据库层 — app/database.py](#43-数据库层--appdatabasepy)
   - 4.4 [认证与授权 — app/auth.py](#44-认证与授权--appauthpy)
   - 4.5 [安全工具 — app/security.py](#45-安全工具--appsecuritypy)
   - 4.6 [路由模块 — app/routers/](#46-路由模块--approuters)
   - 4.7 [工具模块 — app/utils/](#47-工具模块--apputils)
5. [数据模型关系图](#5-数据模型关系图)
6. [路由与页面映射](#6-路由与页面映射)
7. [依赖关系](#7-依赖关系)
8. [项目运行方式](#8-项目运行方式)
9. [数据库迁移](#9-数据库迁移)
10. [测试体系](#10-测试体系)
11. [部署方案](#11-部署方案)
12. [安全机制](#12-安全机制)
13. [PWA 支持](#13-pwa-支持)
14. [CI/CD 流水线](#14-cicd-流水线)

---

## 1. 项目概述

**付刷** 是一个面向中学教育的在线刷题与教学管理平台，支持三种用户角色：

| 角色 | 说明 |
|------|------|
| **学生 (student)** | 在线刷题、错题本、收藏夹、学习计划、薄弱分析、作业完成 |
| **教师 (teacher)** | 题目管理（CRUD/导入/导出）、题库管理、班级管理、作业布置与统计、学生报告 |
| **管理员 (admin)** | 用户管理、系统配置、邀请码管理、账号找回审核、审计日志 |

核心功能包括：

- **智能刷题**：自适应难度、错题复习、薄弱章节推荐、随机补充
- **题目管理**：支持选择题/多选题/填空题/判断题，JSON/CSV/Excel 导入导出
- **班级系统**：班级创建、成员管理、学生批量导入、班级统计
- **作业系统**：作业布置、完成跟踪、催交提醒、完成率统计
- **学习分析**：分科目/章节/题型统计、薄弱知识点识别、家长周报
- **掌握度追踪**：连续答对3题标记为"已掌握"，错题重置为"未掌握"
- **外部付题服务**：通过 httpx 代理对接付题(FuTi)服务，跨系统导入题目
- **PDF 报告**：教师统计报告、学生学习报告、家长周报
- **PWA 支持**：可安装为桌面/移动应用，离线缓存基础资源

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     客户端 (浏览器)                       │
│           Jinja2 模板渲染 + HTMX 局部更新                 │
│           Service Worker (PWA 离线缓存)                   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI 应用层                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  pages   │ │   auth   │ │ teacher  │ │ student  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │assignment│ │classgroup│ │  admin   │               │
│  └──────────┘ └──────────┘ └──────────┘ ┌──────────┐   │
│                                          │extractor │   │
│  ┌──────────────┐  ┌───────────────┐    └──────────┘   │
│  │  permissions │  │   security    │                    │
│  └──────────────┘  └───────────────┘                    │
│  ┌──────────────┐  ┌───────────────┐                    │
│  │    auth      │  │    utils      │                    │
│  └──────────────┘  └───────────────┘                    │
├─────────────────────────────────────────────────────────┤
│               中间件层 (Middleware)                       │
│  CSRFSessionMiddleware → SecurityHeadersMiddleware       │
│  SessionMiddleware → CookieHardeningMiddleware            │
├─────────────────────────────────────────────────────────┤
│              数据访问层 (SQLAlchemy ORM)                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │  15 个 ORM 模型  ·  SQLite / PostgreSQL          │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│              外部服务 (可选)                               │
│  付题服务 (FUTI) — httpx 异步调用                         │
└─────────────────────────────────────────────────────────┘
```

**架构特点**：

- **服务端渲染 (SSR)**：采用 Jinja2 模板 + HTMX 的传统 Web 应用模式，无前端构建步骤
- **会话认证**：基于 Starlette SessionMiddleware 的 Cookie-Session 机制
- **多数据库支持**：开发环境用 SQLite，生产环境用 PostgreSQL，通过环境变量切换
- **中间件栈**：CSRF 保护 → 安全响应头 → 会话管理 → Cookie 加固
- **渐进式 Web 应用**：通过 manifest.json 和 Service Worker 支持 PWA 安装

---

## 3. 目录结构

```
付刷/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # 应用入口、中间件注册、路由挂载
│   ├── models.py                 # SQLAlchemy ORM 模型定义（15个表）
│   ├── database.py               # 数据库引擎与会话管理
│   ├── auth.py                   # 认证与授权守卫函数
│   ├── security.py               # 安全工具（CSRF/XSS/限流/密码校验）
│   ├── routers/                  # 路由模块
│   │   ├── __init__.py
│   │   ├── pages.py              # 公共页面（首页/浏览/排行榜/帮助/反馈）
│   │   ├── auth.py               # 认证路由（注册/登录/登出/设置/找回）
│   │   ├── teacher.py            # 教师功能（题目/题库/字段/导入导出/统计/学生管理）
│   │   ├── student.py            # 学生功能（刷题/错题/分析/收藏/计划/通知/档案）
│   │   ├── assignment.py         # 作业系统（布置/完成/详情/催交）
│   │   ├── classgroup.py         # 班级管理（创建/详情/成员/删除）
│   │   ├── admin.py              # 管理后台（用户/邀请码/找回/审计）
│   │   ├── extractor.py          # 付题服务代理（跨系统导入题目）
│   │   └── permissions.py        # 权限校验辅助函数
│   ├── utils/                    # 工具模块
│   │   ├── __init__.py
│   │   ├── report.py             # PDF 报告生成（教师/学生/家长周报）
│   │   └── validation.py         # 输入解析与分页（parse_int/parse_float/paginate）
│   ├── static/                   # 静态资源
│   │   ├── style.css             # 全局样式
│   │   ├── favicon.ico
│   │   ├── icon-192.png / icon-512.png
│   │   ├── manifest.json         # PWA 清单
│   │   └── sw.js                 # Service Worker
│   └── templates/                # Jinja2 模板
│       ├── base.html             # 基础布局模板
│       ├── index.html            # 首页
│       ├── login.html / register.html / recover.html
│       ├── browse.html / leaderboard.html / help.html
│       ├── settings.html / error.html
│       ├── partials/             # 模板片段
│       │   └── _pagination.html  # 分页组件
│       ├── admin/                # 管理员模板（6个）
│       ├── teacher/              # 教师模板（17个）
│       ├── student/              # 学生模板（13个）
│       └── extractor_proxy/      # 付题代理模板（3个）
├── alembic/                      # 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                 # 迁移脚本（6个版本）
├── tests/                        # 测试目录（40+ 测试文件）
│   ├── conftest.py               # 测试配置与 fixtures
│   └── test_*.py                 # 各模块测试
├── docs/                         # 项目文档
│   └── superpowers/plans/        # 开发计划与设计文档
├── scripts/                      # 运维脚本
│   ├── backup_db.sh              # 数据库备份
│   └── restore_db.sh             # 数据库恢复
├── .github/workflows/ci.yml      # GitHub Actions CI 配置
├── requirements.txt              # Python 依赖
├── Dockerfile                    # Docker 镜像定义
├── docker-compose.yml            # Docker Compose 编排
├── gunicorn.conf.py              # Gunicorn 生产服务器配置
├── alembic.ini                   # Alembic 配置
├── pytest.ini                    # Pytest 配置
├── render.yaml                   # Render 平台部署配置
├── entrypoint.sh                 # Docker 入口脚本
├── .env.example                  # 环境变量模板
├── 启动.bat                      # Windows 一键启动
├── 启动.sh                       # Linux/Mac 一键启动
└── sample_questions.json         # 示例题目数据
```

---

## 4. 核心模块详解

### 4.1 应用入口 — app/main.py

**职责**：FastAPI 应用创建、中间件注册、路由挂载、全局初始化

**关键流程**：

1. **数据库初始化**：非 PostgreSQL 环境下自动 `create_all` 创建表
2. **默认数据种子**：
   - 创建默认教师邀请码 `FUSHUA2024` 和管理员邀请码 `ADMIN2026`
   - 自动将首个 `is_admin=True` 的教师提升为 admin 角色
   - 创建默认管理员账号 `admin`（随机密码，首次登录强制修改）
3. **中间件栈**（按注册顺序，执行为洋葱模型）：
   - `CSRFSessionMiddleware` — 为每个会话生成 CSRF Token
   - `SecurityHeadersMiddleware` — 注入安全响应头（CSP/X-Frame-Options 等）
   - `SessionMiddleware` — Starlette 会话中间件（Cookie-Based）
   - `CookieHardeningMiddleware` — 为 Session Cookie 添加 HttpOnly 标记
4. **模板全局变量注入**：通过覆盖 `templates.TemplateResponse`，自动向所有模板注入 `logged_in`、`role`、`display_name`、`is_guest`、`is_admin`、`unread_count`、`csrf_token`
5. **全局异常处理**：HTTP 异常 → 自定义错误页面；验证错误 → 400 页面；未捕获异常 → 500 页面
6. **健康检查端点**：`GET /health`，检测数据库连接状态并返回用户/题目/班级/作业计数

**关键类与函数**：

| 名称 | 类型 | 说明 |
|------|------|------|
| `app` | `FastAPI` | 应用实例，title="付刷"，version="3.0.0" |
| `CSRFSessionMiddleware` | `BaseHTTPMiddleware` | 自动生成 CSRF Token |
| `SecurityHeadersMiddleware` | `BaseHTTPMiddleware` | 注入 CSP/X-Frame-Options 等安全头 |
| `CookieHardeningMiddleware` | `Middleware` | 确保 Session Cookie 有 HttpOnly |
| `_global_template_vars()` | `function` | 提取全局模板变量（用户信息/角色/未读通知数） |
| `_get_session_factory()` | `function` | 获取数据库会话工厂，支持依赖覆盖 |
| `health_check()` | `endpoint` | 健康检查端点，返回数据库状态和统计 |

---

### 4.2 数据模型 — app/models.py

**职责**：定义全部 15 个 ORM 模型及业务常量

**业务常量**：

| 常量 | 值 | 说明 |
|------|------|------|
| `QUESTION_TYPES` | `{"choice": "选择题", "multi_choice": "多选题", "fill": "填空题", "judge": "判断题"}` | 题型映射 |
| `SEMESTERS` | `["七年级上册", ..., "九年级下册"]` | 学期列表（6项） |
| `SUBJECTS` | `["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]` | 科目列表（9项） |
| `BUILTIN_FIELDS` | `["subject", "semester", "chapter", "q_type", "difficulty", "content", "option_a", "option_b", "option_c", "option_d", "answer", "explanation"]` | 内置字段名（12项） |
| `FIELD_TYPE_CHOICES` | `["text", "select", "number"]` | 自定义字段类型 |

**数据模型一览**：

| 模型 | 表名 | 说明 | 关键字段 |
|------|------|------|----------|
| `User` | `users` | 用户 | username, password_hash, role, display_name, join_mode, is_guest, guest_expires_at, class_id, is_admin, is_disabled, force_password_change |
| `FieldConfig` | `field_configs` | 自定义字段配置 | field_key, field_label, field_type, required, visible, options, sort_order |
| `Question` | `questions` | 题目 | subject, semester, chapter, difficulty, q_type, content, options A-D, answer, explanation, image_url, extra_data, bank_id, created_by |
| `Record` | `records` | 答题记录 | user_id, question_id, user_answer, is_correct |
| `Favorite` | `favorites` | 收藏 | user_id, question_id (联合唯一) |
| `StudyPlan` | `study_plans` | 学习计划 | user_id, subject, semester, daily_goal, active |
| `ClassGroup` | `class_groups` | 班级 | name, created_by |
| `ClassMember` | `class_members` | 班级成员 | class_id, user_id (联合唯一) |
| `Notification` | `notifications` | 通知 | user_id, title, content, is_read |
| `QuestionBank` | `question_banks` | 题库 | name, subject, semester, description, bank_type, visibility, access_code, created_by |
| `MasteryRecord` | `mastery_records` | 掌握度记录 | user_id, question_id, status, consecutive_correct (联合唯一) |
| `SiteConfig` | `site_configs` | 站点配置 | key, value |
| `Assignment` | `assignments` | 作业 | title, description, question_ids, created_by, deadline, class_id |
| `AssignmentRecord` | `assignment_records` | 作业完成记录 | assignment_id, user_id, completed, completed_at |
| `Feedback` | `feedbacks` | 用户反馈 | user_id, role, page_path, content |
| `AuditLog` | `audit_logs` | 审计日志 | actor_id, action, target_type, target_id, detail |
| `ClassJoinRequest` | `class_join_requests` | 入班申请 | user_id, class_id, display_name, status, reviewed_by, reviewed_at |
| `AccountRecoveryRequest` | `account_recovery_requests` | 账号找回申请 | username, class_id, display_name, status, reviewed_by, reviewed_at, new_password_hash |

**User 模型关键方法**：

- `User.hash_password(password)` — bcrypt 哈希
- `User.verify_password(stored_hash, password)` — bcrypt 验证

**Question 模型关键属性**：

- `type_label` — 题型中文标签（property）
- `extra` / `extra_data` — JSON 扩展字段（getter/setter）
- `get_extra_field(key)` / `set_extra_field(key, value)` — 扩展字段读写

**Question 数据库索引**：

- `ix_questions_subject_semester` — (subject, semester) 复合索引
- `ix_questions_subject_chapter` — (subject, chapter) 复合索引

**QuestionBank 可见性**：

- `public` — 公开，所有学生可见
- `private` — 私有，仅教师所建班级的学生可见
- `code` — 访问码，输入正确访问码后解锁

**MasteryRecord 掌握度状态**：

- `unmastered` — 未掌握
- `reviewing` — 复习中（答对1-2次）
- `mastered` — 已掌握（连续答对3次）

---

### 4.3 数据库层 — app/database.py

**职责**：数据库引擎创建与会话管理

**关键组件**：

| 名称 | 说明 |
|------|------|
| `SQLALCHEMY_DATABASE_URL` | 从 `DATABASE_URL` 环境变量读取，默认 `sqlite:///./fushua.db` |
| `engine` | SQLAlchemy 引擎，SQLite 时禁用 `check_same_thread`，启用 `pool_pre_ping` |
| `SessionLocal` | 会话工厂，autocommit=False, autoflush=False |
| `Base` | `DeclarativeBase` 基类，所有模型继承 |
| `get_db()` | FastAPI 依赖注入生成器，提供数据库会话 |

**连接池配置**：

- `DB_POOL_SIZE` — 默认 5
- `DB_MAX_OVERFLOW` — 默认 10

---

### 4.4 认证与授权 — app/auth.py

**职责**：基于 Session 的认证守卫函数

| 函数 | 说明 | 返回 |
|------|------|------|
| `get_current_user(request, db)` | 获取当前用户 ID，未登录返回 None；禁用用户自动清除 Session | `int \| None` |
| `get_current_user_info(request, db)` | 获取用户对象、角色、昵称 | `(User, role, display_name)` |
| `require_login(request, db)` | 要求登录，否则 303 → /login | `user_id` |
| `require_teacher(request, db)` | 要求教师或管理员角色，否则 403 | `user_id` |
| `require_admin_role(request, db)` | 要求管理员角色，否则 403 | `user_id` |
| `require_non_guest(request, db)` | 要求非过期游客，否则 303 → /student/guest-expired | `user_id` |
| `is_guest_expired(user)` | 判断游客是否过期（无过期时间视为已过期） | `bool` |

**认证流程**：

1. 从 `request.session["user_id"]` 获取用户 ID
2. 查询数据库验证用户存在且未被禁用
3. 禁用用户自动清除 Session
4. 根据角色要求进行权限检查
5. 游客用户检查 `guest_expires_at` 是否过期

---

### 4.5 安全工具 — app/security.py

**职责**：输入净化、CSRF 防护、速率限制、密码策略、邀请码验证

| 函数/常量 | 说明 |
|-----------|------|
| `sanitize_input(value, max_length)` | HTML 转义 + 去除 `javascript:` 和 `on*=` 事件 + 截断 |
| `validate_password_strength(password)` | 密码强度校验（≥8位、非纯数字、非纯字母） |
| `validate_csrf_async(request)` | 异步 CSRF 校验，POST/PUT/DELETE/PATCH 时验证表单 `_csrf_token` |
| `check_login_rate_limit(username, db)` | 登录限流（5次/300秒） |
| `record_login_attempt(username, db)` | 记录登录失败 |
| `check_rate_limit(key, max_attempts, lockout_seconds, db)` | 通用限流检查 |
| `record_rate_limit_attempt(key, db)` | 记录限流尝试 |
| `verify_invite_code(code, db, key)` | 验证邀请码（支持逗号分隔多码） |
| `verify_teacher_invite_code(code, db)` | 验证教师邀请码 |
| `verify_admin_invite_code(code, db)` | 验证管理员邀请码 |
| `LOGIN_MAX_ATTEMPTS = 5` | 登录最大尝试次数 |
| `LOGIN_LOCKOUT_SECONDS = 300` | 登录锁定秒数 |
| `REGISTER_MAX_ATTEMPTS = 5` | 注册最大尝试次数 |
| `REGISTER_LOCKOUT_SECONDS = 3600` | 注册锁定秒数 |
| `RECOVER_MAX_ATTEMPTS = 3` | 找回最大尝试次数 |
| `RECOVER_LOCKOUT_SECONDS = 3600` | 找回锁定秒数 |

**限流实现**：利用 `SiteConfig` 表存储时间戳列表，按 key 前缀区分场景（`_login_fail:`、`_register_limit:`、`_recover_limit:`）。每次检查时先清理过期条目，再判断是否超限。

---

### 4.6 路由模块 — app/routers/

#### 4.6.1 pages.py — 公共页面路由

**前缀**: 无

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页，按角色重定向；未登录显示题库概览 |
| `/browse` | GET | 题库浏览，支持按科目/学期/章节/题库筛选，访问码解锁 |
| `/leaderboard` | GET | 排行榜，按正确数和正确率排序（排除游客） |
| `/help` | GET | 帮助页面 |
| `/feedback` | POST | 提交反馈（JSON 响应） |
| `/browse/unlock-bank` | POST | 解锁访问码题库 |

**题库浏览可见性逻辑**：
- `public` 题库：所有学生可见
- `private` 题库：仅教师所建班级的学生可见（通过班级成员关系判断）
- `code` 题库：输入正确访问码后存入 Session `unlocked_banks` 列表

#### 4.6.2 auth.py — 认证路由

**前缀**: 无

| 端点 | 方法 | 说明 |
|------|------|------|
| `/register` | GET/POST | 注册页面/处理（支持正式/申请/游客三种加入方式） |
| `/login` | GET/POST | 登录页面/处理 |
| `/logout` | POST | 登出（清除 Session） |
| `/settings` | GET | 个人设置页 |
| `/settings/password` | POST | 修改密码 |
| `/settings/profile` | POST | 修改昵称 |
| `/recover` | GET/POST | 账号找回页面/提交申请 |

**注册模式**：

- `formal` — 正式加入班级（需选择班级，直接成为班级成员）
- `apply` — 申请加入班级（临时游客身份，24小时有效，提交入班申请待审核）
- `guest` — 游客体验（1小时有效，无需班级）

**登录后路由**：

- 管理员 → `/admin`
- 教师 → `/teacher/questions`
- 学生 → `/`（首页/仪表盘）
- 强制改密用户 → `/settings?force_change=1`
- 过期游客 → `/student/guest-expired`

#### 4.6.3 teacher.py — 教师路由

**前缀**: `/teacher`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/questions` | GET | 题目管理列表（分页，支持科目/题型筛选） |
| `/questions/create` | GET/POST | 创建题目 |
| `/questions/{id}/edit` | GET/POST | 编辑题目 |
| `/questions/{id}/delete` | POST | 删除题目（级联删除记录/收藏/作业引用） |
| `/questions/batch-edit` | POST | 批量编辑（删除/改难度/改学期/改章节/改题库） |
| `/questions/import` | GET/POST | 导入题目（JSON/CSV） |
| `/questions/import-preview` | POST | 导入预览（校验必填/去重） |
| `/questions/import-confirm` | POST | 确认导入（基于 token 的临时存储） |
| `/questions/import/template/{fmt}` | GET | 下载导入模板（json/csv） |
| `/questions/export/{fmt}` | GET | 导出题目（json/csv/excel） |
| `/banks` | GET | 题库列表（含题目计数） |
| `/banks/create` | GET/POST | 创建题库 |
| `/banks/{id}/delete` | POST | 删除题库（题目 bank_id 置空） |
| `/fields` | GET | 自定义字段管理 |
| `/fields/create` | POST | 创建自定义字段 |
| `/fields/{id}/update` | POST | 更新自定义字段 |
| `/fields/{id}/delete` | POST | 删除自定义字段 |
| `/stats` | GET | 教师数据统计（总题数/答题次数/正确率/学生排名） |
| `/stats/export/pdf` | GET | 导出教师统计 PDF |
| `/students` | GET | 学生管理（班级成员/游客/入班申请/找回申请） |
| `/students/{id}` | GET | 学生详情（分科目/题型/章节统计） |
| `/students/{id}/export/pdf` | GET | 学生报告 PDF |
| `/students/{id}/parent-report` | GET | 家长周报（本周数据/薄弱点/建议） |
| `/students/{id}/parent-report/pdf` | GET | 家长周报 PDF |
| `/students/{id}/approve` | POST | 审核通过游客（转正+通知） |
| `/invite` | GET | 邀请码管理（需管理员） |
| `/invite/update` | POST | 更新邀请码（需管理员） |
| `/classes/{id}/import-students` | GET/POST | 批量导入学生（CSV 格式） |
| `/classes/{id}/stats` | GET | 班级统计（趋势/薄弱章节/排名/进步榜） |
| `/classes/{id}/export/excel` | GET | 导出班级 Excel |
| `/assignments/{id}/export/excel` | GET | 导出作业完成情况 Excel |

**关键内部函数**：

| 函数 | 说明 |
|------|------|
| `_parse_owned_bank_id()` | 解析并验证题库归属当前教师 |
| `_build_question_from_dict()` | 从字典构建 Question 对象（区分内置/自定义字段） |
| `_import_json()` / `_import_csv()` | 文件导入处理 |
| `_parse_file_content()` | 解析上传文件内容为行列表 |
| `_validate_rows()` | 校验行数据必填字段 |
| `_check_duplicates()` | 检查与已有题目的重复（content+answer 匹配） |

**导入预览流程**：

1. 上传文件 → `_parse_file_content()` 解析
2. `_validate_rows()` 校验必填字段 → 分离 valid_rows / error_rows
3. `_check_duplicates()` 去重 → 分离 unique_rows / duplicate_rows
4. 生成 `import_token`，存入内存字典 `_pending_imports`
5. 用户确认 → `_pending_imports.pop(token)` 取出数据写入数据库

> **注意**：`_pending_imports` 是进程内字典，服务重启后丢失，适用于单实例部署。

#### 4.6.4 student.py — 学生路由

**前缀**: `/student`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/dashboard` | GET | 学生仪表盘（待做作业/推荐题目/错题数/每日目标进度） |
| `/practice` | GET | 刷题页面（smart/adaptive/random 模式） |
| `/practice/submit` | POST | 提交答案，更新掌握度 |
| `/mistakes` | GET | 错题本（按科目/掌握状态筛选） |
| `/mistakes/retry` | GET | 重做未掌握错题 |
| `/analysis` | GET | 薄弱分析（分科目/章节/题型） |
| `/profile` | GET | 学习档案（统计/连续天数/成就/趋势/周对比） |
| `/records` | GET | 答题记录（分页） |
| `/favorites` | GET | 收藏夹 |
| `/favorites/{id}/add` | POST | 添加收藏（支持 HTMX 局部更新） |
| `/favorites/{id}/remove` | POST | 取消收藏（支持 HTMX 局部更新） |
| `/plans` | GET | 学习计划列表 |
| `/plans/create` | POST | 创建学习计划 |
| `/plans/{id}/delete` | POST | 删除学习计划 |
| `/notifications` | GET | 通知列表 |
| `/notifications/{id}/read` | POST | 标记已读 |
| `/notifications/read-all` | POST | 全部已读 |
| `/guest-expired` | GET | 游客过期提示页 |

**智能选题算法 `_smart_select()`**：

1. **40% 未掌握题** — 从 `MasteryRecord.status == "unmastered"` 中选取
2. **30% 薄弱章节题** — 从正确率 < 60% 的章节中选取
3. **20% 难度适配题** — 根据用户整体正确率选取对应难度
4. **10% 随机补充** — 随机选取
5. 不足部分从全量题目随机补充

**自适应模式 `_smart_select(mode="adaptive")`**：

- 根据最近 10 题正确率动态调整难度上限
- 正确率 < 40% → 难度 1；< 70% → 难度 1-2；≥ 70% → 难度 1-3

**答案判定逻辑 `check_answer()`**：

| 题型 | 判定规则 |
|------|----------|
| `choice` | 选项字母大写比较 |
| `multi_choice` | 排序后字母序列比较 |
| `judge` | 精确匹配 |
| `fill` | 去空格后小写比较 |

**掌握度更新逻辑**：

- 答对：`consecutive_correct += 1`，连续 3 次答对 → `status = "mastered"`
- 答错：`consecutive_correct = 0`，`status = "unmastered"`
- 中间状态：`status = "reviewing"`

**学习档案统计项**：

- 总答题数/正确数/正确率
- 学习天数/活跃天数
- 今日答题数/连续打卡天数
- 14天每日趋势
- 分科目统计
- 未掌握错题数
- 每日目标完成百分比
- 近7天 vs 前7天正确率变化
- 章节成就徽章（正确率 > 80%）

#### 4.6.5 assignment.py — 作业路由

**前缀**: 无

| 端点 | 方法 | 说明 |
|------|------|------|
| `/teacher/assignments` | GET | 教师作业列表（分页） |
| `/assignments/create` | GET/POST | 创建作业（必须绑定班级） |
| `/teacher/assignments/{id}` | GET | 作业详情（完成率/题目正确率/未完成名单） |
| `/teacher/assignments/{id}/remind` | POST | 催交（给未完成学生发通知） |
| `/teacher/assignments/{id}/delete` | POST | 删除作业（管理员可删所有） |
| `/student/assignments` | GET | 学生作业列表（仅显示本班作业） |
| `/assignments/{id}/complete` | POST | 学生标记作业完成 |

**作业创建约束**：

- 必须选择班级（`class_id` 必填）
- 题目必须属于当前教师
- 班级必须属于当前教师

#### 4.6.6 classgroup.py — 班级路由

**前缀**: 无

| 端点 | 方法 | 说明 |
|------|------|------|
| `/teacher/classes` | GET | 教师班级列表 |
| `/classes/create` | POST | 创建班级 |
| `/classes/{id}` | GET | 班级详情（成员列表及正确率，按正确率升序） |
| `/classes/{id}/members/add` | POST | 添加成员（按用户名查找） |
| `/classes/{id}/members/{mid}/remove` | POST | 移除成员（记录审计日志） |
| `/classes/{id}/delete` | POST | 删除班级（级联清除成员关系和用户 class_id） |

#### 4.6.7 admin.py — 管理后台路由

**前缀**: 无

| 端点 | 方法 | 说明 |
|------|------|------|
| `/admin` | GET | 管理后台首页（统计概览：用户/班级/题目/教师/游客/管理员数） |
| `/admin/users` | GET | 用户管理（搜索/角色筛选/重置密码/禁用/启用） |
| `/admin/users/{id}/reset-password` | POST | 重置用户密码为 `abc12345`（强制下次修改） |
| `/admin/users/{id}/toggle-disable` | POST | 切换用户禁用状态（不能禁用管理员） |
| `/admin/users/{id}/toggle-admin` | POST | 切换教师管理权限（is_admin 标记） |
| `/admin/cleanup-guests` | POST | 清理过期游客（级联删除成员关系） |
| `/admin/recovery-requests` | GET | 找回申请列表（待处理 + 已处理） |
| `/admin/recovery-requests/{id}/approve` | POST | 批准找回（重置密码为 abc12345） |
| `/admin/recovery-requests/{id}/reject` | POST | 拒绝找回 |
| `/admin/invite` | GET | 邀请码管理（教师 + 管理员邀请码） |
| `/admin/invite/update` | POST | 更新邀请码 |
| `/admin/classes` | GET | 班级管理（含成员数和创建者信息） |
| `/admin/audit-log` | GET | 审计日志（分页，按操作类型筛选） |
| `/admin/audit-log/export` | GET | 导出审计日志 CSV（最多5000条） |

#### 4.6.8 extractor.py — 付题服务代理路由

**前缀**: `/extractor`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 付题服务首页（检测连通性） |
| `/import` | GET/POST | 从付题服务导入题目 |
| `/questions` | GET | 浏览付题服务题目列表 |

**外部服务通信**：通过 `httpx` 异步 HTTP 客户端调用付题服务 API（`FUTI_BASE_URL`），支持 API Token 认证（`X-API-Token` 请求头）。

**连通性检测**：`_check_futi()` 通过 `httpx.get(f"{FUTI_BASE_URL}/api/health")` 同步检测服务状态。

#### 4.6.9 permissions.py — 权限校验

| 函数 | 说明 |
|------|------|
| `is_admin(db, user_id)` | 检查用户是否是管理员（role=admin 或 is_admin=True） |
| `teacher_owns_student(db, teacher_id, student_id)` | 学生是否属于教师创建的班级（管理员可查看所有） |
| `teacher_owns_bank(db, teacher_id, bank_id)` | 题库是否属于教师（管理员可查看所有） |
| `teacher_owns_class(db, teacher_id, class_id)` | 班级是否属于教师（管理员可查看所有） |
| `teacher_owns_question(db, teacher_id, question_id)` | 题目是否属于教师（管理员可查看所有） |

**权限模型**：管理员拥有全局访问权限，教师仅能操作自己创建的资源（题目/题库/班级/作业），学生仅能访问自己班级的作业和公开题库。

---

### 4.7 工具模块 — app/utils/

#### validation.py

| 函数 | 说明 |
|------|------|
| `parse_int(value, default, min_value, max_value)` | 安全整数解析，支持范围校验和默认值 |
| `parse_float(value, default, min_value, max_value)` | 安全浮点数解析，支持范围校验和默认值 |
| `paginate(query, page, per_page)` | SQLAlchemy 查询分页，返回 items/page/total/total_pages/has_prev/has_next |

#### report.py

| 函数 | 说明 |
|------|------|
| `generate_teacher_report(teacher_name, total_questions, total_records, accuracy, per_question, student_stats)` | 生成教师数据报告 PDF |
| `generate_parent_report(student_name, week_total, week_correct, week_accuracy, weak_points, suggestions, week_start, today)` | 生成家长周报 PDF |
| `generate_student_report(student_name, total, correct, accuracy, subject_stats, type_stats)` | 生成学生学习报告 PDF |

使用 `reportlab` 库生成 A4 格式 PDF，包含统计表格和样式。所有报告函数均对输入调用 `sanitize_input()` 防止注入。

---

## 5. 数据模型关系图

```
User ─────────────────────────────────────────────────────
  │ 1:N  Record          (用户答题记录)
  │ 1:N  Favorite        (用户收藏)
  │ 1:N  StudyPlan       (用户学习计划)
  │ 1:N  Notification    (用户通知)
  │ 1:N  MasteryRecord   (用户掌握度)
  │ 1:N  ClassGroup      (教师创建的班级, created_by)
  │ 1:N  Question        (教师创建的题目, created_by)
  │ 1:N  QuestionBank    (教师创建的题库, created_by)
  │ 1:N  Assignment      (教师布置的作业, created_by)
  │ 1:N  AssignmentRecord(学生作业完成记录)
  │ 1:N  ClassJoinRequest(入班申请)
  │ 1:N  AccountRecoveryRequest(账号找回, reviewed_by)
  │
  └── ClassMember ──── ClassGroup  (多对多: 用户-班级)

Question ──────────────────────────────────────────────────
  │ 1:N  Record          (题目答题记录)
  │ 1:N  Favorite        (题目收藏)
  │ 1:N  MasteryRecord   (题目掌握度)
  │ N:1  QuestionBank    (题目所属题库, bank_id)
  │ N:1  User            (题目创建者, created_by)

Assignment ────────────────────────────────────────────────
  │ 1:N  AssignmentRecord(作业完成记录, cascade delete)
  │ N:1  ClassGroup      (作业所属班级, class_id)
  │ N:1  User            (作业创建者, created_by)

ClassGroup ────────────────────────────────────────────────
  │ 1:N  ClassMember     (班级成员)
  │ 1:N  ClassJoinRequest(入班申请)
  │ N:1  User            (班级创建者, created_by)

SiteConfig ──── 键值对存储 (邀请码/限流计数等)
AuditLog ────── 审计日志 (操作者/动作/目标)
Feedback ────── 用户反馈
FieldConfig ─── 自定义字段配置
```

---

## 6. 路由与页面映射

### 学生端

| 页面 | 路由 | 模板 |
|------|------|------|
| 仪表盘 | `/student/dashboard` | `student/dashboard.html` |
| 刷题 | `/student/practice` | `student/practice.html` |
| 答题结果 | (POST) `/student/practice/submit` | `student/result.html` |
| 错题本 | `/student/mistakes` | `student/mistakes.html` |
| 薄弱分析 | `/student/analysis` | `student/analysis.html` |
| 学习档案 | `/student/profile` | `student/profile.html` |
| 答题记录 | `/student/records` | `student/records.html` |
| 收藏夹 | `/student/favorites` | `student/favorites.html` |
| 学习计划 | `/student/plans` | `student/plans.html` |
| 通知 | `/student/notifications` | `student/notifications.html` |
| 作业列表 | `/student/assignments` | `student/assignments.html` |
| 游客过期 | `/student/guest-expired` | `student/guest_expired.html` |
| 无题目 | (条件渲染) | `student/no_questions.html` |

### 教师端

| 页面 | 路由 | 模板 |
|------|------|------|
| 题目管理 | `/teacher/questions` | `teacher/questions.html` |
| 创建/编辑题目 | `/teacher/questions/create` 或 `.../edit` | `teacher/question_form.html` |
| 导入题目 | `/teacher/questions/import` | `teacher/import.html` |
| 导入预览 | (POST) `/teacher/questions/import-preview` | `teacher/import_preview.html` |
| 题库管理 | `/teacher/banks` | `teacher/banks.html` |
| 创建题库 | `/teacher/banks/create` | `teacher/bank_form.html` |
| 自定义字段 | `/teacher/fields` | `teacher/fields.html` |
| 数据统计 | `/teacher/stats` | `teacher/stats.html` |
| 学生管理 | `/teacher/students` | `teacher/students.html` |
| 学生详情 | `/teacher/students/{id}` | `teacher/student_detail.html` |
| 家长周报 | `/teacher/students/{id}/parent-report` | `teacher/parent_report.html` |
| 班级列表 | `/teacher/classes` | `teacher/classes.html` |
| 班级详情 | `/classes/{id}` | `teacher/class_detail.html` |
| 班级统计 | `/teacher/classes/{id}/stats` | `teacher/class_stats.html` |
| 批量导入学生 | `/teacher/classes/{id}/import-students` | `teacher/student_import.html` |
| 作业列表 | `/teacher/assignments` | `teacher/assignments.html` |
| 创建作业 | `/assignments/create` | `teacher/assignment_form.html` |
| 作业详情 | `/teacher/assignments/{id}` | `teacher/assignment_detail.html` |
| 邀请码管理 | `/teacher/invite` | `teacher/invite.html` |

### 管理员端

| 页面 | 路由 | 模板 |
|------|------|------|
| 管理首页 | `/admin` | `admin/index.html` |
| 用户管理 | `/admin/users` | `admin/users.html` |
| 班级管理 | `/admin/classes` | `admin/classes.html` |
| 找回申请 | `/admin/recovery-requests` | `admin/recovery_requests.html` |
| 邀请码 | `/admin/invite` | `admin/invite.html` |
| 审计日志 | `/admin/audit-log` | `admin/audit_log.html` |

### 公共页面

| 页面 | 路由 | 模板 |
|------|------|------|
| 首页 | `/` | `index.html` |
| 题库浏览 | `/browse` | `browse.html` |
| 排行榜 | `/leaderboard` | `leaderboard.html` |
| 帮助 | `/help` | `help.html` |
| 登录 | `/login` | `login.html` |
| 注册 | `/register` | `register.html` |
| 设置 | `/settings` | `settings.html` |
| 找回密码 | `/recover` | `recover.html` |
| 找回提交成功 | (POST) `/recover` | `recover_submitted.html` |
| 错误页 | (异常处理) | `error.html` |

---

## 7. 依赖关系

### Python 包依赖

| 包 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.115.0 | Web 框架 |
| `uvicorn` | 0.30.0 | ASGI 服务器 |
| `sqlalchemy` | 2.0.35 | ORM |
| `jinja2` | 3.1.4 | 模板引擎 |
| `python-multipart` | 0.0.9 | 表单数据解析 |
| `itsdangerous` | 2.2.0 | 数据签名 |
| `bcrypt` | 4.2.0 | 密码哈希 |
| `reportlab` | 4.2.2 | PDF 生成 |
| `psycopg2-binary` | 2.9.9 | PostgreSQL 驱动 |
| `alembic` | 1.13.2 | 数据库迁移 |
| `gunicorn` | 22.0.0 | 生产 WSGI/ASGI 服务器 |
| `openpyxl` | 3.1.5 | Excel 读写 |
| `pyyaml` | 6.0.2 | YAML 解析 |
| `httpx` | 0.27.2 | 异步 HTTP 客户端（付题服务） |

### 模块间依赖关系

```
app/main.py
  ├── app/database.py (engine, Base, SessionLocal, get_db)
  ├── app/models.py (User, Notification, SiteConfig)
  ├── app/routers/pages.py
  ├── app/routers/auth.py
  ├── app/routers/teacher.py
  │     ├── app/routers/permissions.py
  │     └── app/utils/report.py
  ├── app/routers/student.py
  ├── app/routers/assignment.py
  │     └── app/routers/permissions.py
  ├── app/routers/classgroup.py
  ├── app/routers/admin.py
  └── app/routers/extractor.py
        └── app/routers/permissions.py

所有路由模块共同依赖:
  ├── app/database.py → get_db
  ├── app/models.py → ORM 模型
  ├── app/auth.py → 认证守卫
  └── app/security.py → CSRF/净化/限流
```

---

## 8. 项目运行方式

### 方式一：一键启动脚本

**Windows**：
```bash
启动.bat
```

**Linux/Mac**：
```bash
chmod +x 启动.sh
./启动.sh
```

脚本自动执行：安装依赖 → 初始化数据库 → 启动 uvicorn 服务器（`0.0.0.0:8000`）

### 方式二：手动启动

```bash
pip install -r requirements.txt
python -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 方式三：Docker Compose

```bash
docker-compose up -d
```

包含两个服务：
- `web` — 付刷应用（Gunicorn + Uvicorn Worker），依赖 postgres 健康检查
- `postgres` — PostgreSQL 16 Alpine 数据库

### 方式四：Render 云平台

使用 `render.yaml` 配置，自动构建部署。

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `SECRET_KEY` | 生产必填 | 开发模式随机 | 会话加密密钥 |
| `DATABASE_URL` | 否 | `sqlite:///./fushua.db` | 数据库连接串 |
| `ENVIRONMENT` | 否 | `development` | 环境标识（production 时隐藏 API 文档） |
| `PORT` | 否 | `8000` | 服务端口 |
| `HTTPS_ONLY` | 否 | `false` | Cookie Secure 标记 |
| `GUNICORN_WORKERS` | 否 | `4` | Gunicorn Worker 数 |
| `DB_POOL_SIZE` | 否 | `5` | 数据库连接池大小 |
| `DB_MAX_OVERFLOW` | 否 | `10` | 连接池最大溢出 |
| `FUTI_BASE_URL` | 否 | `http://localhost:8001` | 付题服务地址 |
| `FUTI_API_TOKEN` | 否 | 空 | 付题服务 API Token |
| `POSTGRES_PASSWORD` | Docker | `fushua_dev` | PostgreSQL 密码 |

---

## 9. 数据库迁移

使用 Alembic 管理数据库迁移：

```bash
# 执行迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "description"

# 查看当前版本
alembic current
```

**已有迁移版本**：

| 迁移文件 | 说明 |
|----------|------|
| `877cbf3c862e_initial_schema.py` | 初始表结构 |
| `11186769213b_add_question_bank_siteconfig_guest.py` | 添加题库/站点配置/游客 |
| `20260509_productization_schema.py` | 产品化 Schema |
| `20260509_join_mode_and_recovery.py` | 加入模式与账号找回 |
| `20260510_force_password_change.py` | 强制修改密码 |
| `20260511_bank_visibility.py` | 题库可见性 |

Docker 入口脚本 `entrypoint.sh` 会自动执行 `alembic upgrade head`，失败时回退到 `create_all`。

---

## 10. 测试体系

**框架**：pytest

**配置**：`pytest.ini`

```ini
testpaths = tests
python_files = test_*.py
```

**测试配置**：`tests/conftest.py` 定义测试 fixtures（数据库会话、测试客户端、测试用户等）

**测试文件清单**（40+ 文件）：

| 测试文件 | 覆盖模块 |
|----------|----------|
| `test_account_recovery.py` | 账号找回流程 |
| `test_achievement.py` | 成就系统 |
| `test_adaptive.py` | 自适应刷题 |
| `test_admin.py` / `test_admin_e2e.py` / `test_admin_role.py` / `test_admin_audit_log.py` / `test_admin_permissions.py` | 管理后台 |
| `test_assignment.py` / `test_assignment_class_required.py` / `test_assignment_delete.py` / `test_assignment_reminder.py` | 作业系统 |
| `test_audit_log.py` | 审计日志 |
| `test_bank_delete_permission.py` | 题库删除权限 |
| `test_batch_edit.py` | 批量编辑 |
| `test_class_stats.py` / `test_classgroup.py` / `test_class_membership_consistency.py` | 班级系统 |
| `test_dashboard.py` | 学生仪表盘 |
| `test_dark_mode.py` | 暗色模式 |
| `test_explicit_registration.py` | 注册流程 |
| `test_export.py` | 导出功能 |
| `test_favorites.py` | 收藏功能 |
| `test_feedback.py` | 反馈系统 |
| `test_flow_optimization.py` | 流程优化 |
| `test_health_check.py` | 健康检查 |
| `test_help.py` | 帮助页面 |
| `test_htmx.py` | HTMX 交互 |
| `test_image_upload.py` | 图片上传 |
| `test_import_preview.py` | 导入预览 |
| `test_input_validation.py` | 输入验证 |
| `test_latex.py` | LaTeX 渲染 |
| `test_leaderboard.py` | 排行榜 |
| `test_logic_fixes.py` / `test_logic_regression.py` | 逻辑修复 |
| `test_mastery.py` | 掌握度系统 |
| `test_no_class_student.py` | 无班级学生 |
| `test_notification.py` | 通知系统 |
| `test_parent_report.py` | 家长周报 |
| `test_parse_int_coverage.py` | parse_int 覆盖率 |
| `test_permissions.py` | 权限系统 |
| `test_production.py` | 生产环境 |
| `test_pwa.py` | PWA |
| `test_report.py` | 报告生成 |
| `test_security_fixes.py` / `test_security_audit_fixes.py` | 安全修复 |
| `test_smart_recommend.py` | 智能推荐 |
| `test_student_assignment_filter.py` / `test_student_import.py` | 学生相关 |
| `test_study_plan.py` | 学习计划 |
| `test_teacher_cross_class.py` / `test_teacher_bank_visibility.py` | 教师相关 |
| `test_ui_polish.py` | UI 优化 |
| `test_acceptance_all_phases.py` | 全阶段验收测试 |
| `test_ci_config.py` | CI 配置验证 |

**运行测试**：

```bash
pytest
```

---

## 11. 部署方案

### Docker 部署（推荐）

```bash
# 1. 创建 .env 文件
cp .env.example .env
# 编辑 SECRET_KEY 等必填项

# 2. 启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f web
```

**Dockerfile 关键配置**：

- 基础镜像：`python:3.12-slim`
- 安装 `libpq5`（PostgreSQL 客户端库）
- 默认数据库：SQLite（`/app/data/fushua.db`）
- 入口脚本：自动执行 Alembic 迁移
- 生产命令：`gunicorn app.main:app -c gunicorn.conf.py`

**Gunicorn 配置**（`gunicorn.conf.py`）：

- 绑定：`0.0.0.0:{PORT}`
- Worker 类：`uvicorn.workers.UvicornWorker`
- Worker 数：4（可通过 `GUNICORN_WORKERS` 调整）
- 超时：120 秒
- Keep-alive：5 秒
- 访问日志/错误日志：stdout

**Docker Compose 服务**：

- `web`：付刷应用，依赖 postgres 健康检查，自动重启，挂载 `app_data` 卷
- `postgres`：PostgreSQL 16 Alpine，挂载 `pg_data` 卷，暴露 5432 端口

### Render 云平台

使用 `render.yaml` 一键部署，自动配置 PostgreSQL 数据库、生成 SECRET_KEY、启用 HTTPS。

**Render 配置**：

- 运行时：Python
- 构建命令：`pip install -r requirements.txt`
- 启动命令：`alembic upgrade head && gunicorn app.main:app -c gunicorn.conf.py`
- Python 版本：3.12.6
- Gunicorn Workers：2（免费计划）

### 本地开发

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API 文档（仅开发环境）：`http://localhost:8000/docs`

### 数据库备份与恢复

```bash
# 备份
bash scripts/backup_db.sh

# 恢复
bash scripts/restore_db.sh
```

---

## 12. 安全机制

| 机制 | 实现方式 | 位置 |
|------|----------|------|
| **密码存储** | bcrypt 哈希 | `app/models.py` → `User.hash_password()` |
| **CSRF 防护** | 双重提交 Cookie（Session Token + 表单 Token） | `app/security.py` → `validate_csrf_async()` |
| **XSS 防护** | HTML 转义 + `javascript:` / `on*=` 过滤 | `app/security.py` → `sanitize_input()` |
| **CSP** | Content-Security-Policy 响应头 | `app/main.py` → `SecurityHeadersMiddleware` |
| **Clickjacking** | X-Frame-Options: DENY | `app/main.py` → `SecurityHeadersMiddleware` |
| **Cookie 安全** | HttpOnly + SameSite=Lax + 可选 Secure | `app/main.py` → 中间件配置 |
| **登录限流** | 5次/300秒（基于 SiteConfig 存储） | `app/security.py` → `check_login_rate_limit()` |
| **注册限流** | 5次/3600秒（基于 IP） | `app/security.py` → `check_rate_limit()` |
| **找回限流** | 3次/3600秒（基于 IP） | `app/security.py` → `check_rate_limit()` |
| **邀请码** | 教师/管理员注册需邀请码（支持逗号分隔多码） | `app/security.py` → `verify_*_invite_code()` |
| **密码策略** | ≥8位、非纯数字、非纯字母 | `app/security.py` → `validate_password_strength()` |
| **强制改密** | 首次登录/密码重置后强制修改 | `User.force_password_change` |
| **权限隔离** | 教师只能操作自己创建的资源 | `app/routers/permissions.py` |
| **审计日志** | 管理员操作记录（重置密码/禁用用户/删除资源等） | `app/models.py` → `AuditLog` |
| **API 文档隐藏** | 生产环境关闭 /docs /redoc /openapi.json | `app/main.py` |
| **输入长度限制** | 所有 sanitize_input 调用带 max_length | 全局 |
| **文件大小限制** | 导入文件最大 5MB | `app/routers/teacher.py` → `MAX_UPLOAD_SIZE` |
| **Referrer 策略** | strict-origin-when-cross-origin | `app/main.py` → `SecurityHeadersMiddleware` |
| **权限策略** | 禁用 camera/microphone/geolocation | `app/main.py` → `SecurityHeadersMiddleware` |

---

## 13. PWA 支持

项目支持渐进式 Web 应用（PWA），允许用户将应用安装到桌面或移动设备：

| 文件 | 说明 |
|------|------|
| `app/static/manifest.json` | PWA 清单，定义应用名称/图标/主题色 |
| `app/static/sw.js` | Service Worker，实现离线缓存 |
| `app/static/icon-192.png` | 192x192 应用图标 |
| `app/static/icon-512.png` | 512x512 应用图标 |

---

## 14. CI/CD 流水线

**平台**：GitHub Actions

**配置文件**：`.github/workflows/ci.yml`

**触发条件**：push 到 main 分支 / PR 到 main 分支

**流水线步骤**：

1. **检出代码** — `actions/checkout@v4`
2. **设置 Python** — `actions/setup-python@v5`，Python 3.12
3. **安装依赖** — `pip install -r requirements.txt`
4. **运行测试** — `pytest tests/ -v --tb=short -q`，使用 SQLite 测试数据库
5. **数据库迁移** — `alembic upgrade head`

**测试环境变量**：

- `DATABASE_URL=sqlite:///./test_ci.db`
- `ENVIRONMENT=test`
