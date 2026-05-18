# 付刷项目微信小程序化架构设计

**设计日期**: 2026-05-18  
**当前版本**: v3.1.0  
**目标版本**: v4.0.0 (微信小程序化完成版)

---

## 一、项目背景与目标

### 1.1 当前状态

付刷项目目前是基于 FastAPI + Jinja2 模板的 Web 应用，已完成：
- 基础刷题功能
- 题库管理
- 班级管理
- 作业系统
- 错题本
- 统计分析
- 权限隔离
- 部署配置

### 1.2 转型目标

**核心目标**: 将付刷转型为以微信小程序为主要用户入口的教育平台

**用户定位**:
- 学生：主要通过微信小程序使用
- 教师：主要通过微信小程序使用
- 管理员：通过 Web 管理后台

**技术目标**:
- 完全前后端分离架构
- RESTful API 设计
- 微信生态集成
- 手机号认证体系

---

## 二、整体架构设计

### 2.1 系统架构图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  微信小程序      │     │   Web 管理后台   │     │   Web 学生端     │
│  (学生+教师)     │     │   (管理员)       │     │   (可选)         │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                          HTTPS/JSON
                                 │
                    ┌────────────▼────────────┐
                    │   FastAPI RESTful API   │
                    │   - JWT 认证             │
                    │   - 权限中间件           │
                    │   - 业务逻辑层           │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   数据访问层 (SQLAlchemy)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   PostgreSQL 数据库      │
                    └─────────────────────────┘
```

### 2.2 技术栈

**后端**:
- FastAPI - RESTful API 框架
- SQLAlchemy - ORM
- Alembic - 数据库迁移
- Pydantic - 数据验证
- PyJWT - JWT 认证
- Python 3.12+

**前端**:
- 微信小程序 - 主要用户入口
- Vue 3 + Element Plus - Web 管理后台（推荐）
- 或 Jinja2 模板 + API 调用（过渡方案）

**基础设施**:
- PostgreSQL - 主数据库
- Redis - 缓存/Session（可选，后期）
- 对象存储 - 图片/文件（可选，后期）
- 短信服务 - 验证码（阿里云/腾讯云）

---

## 三、认证与授权设计

### 3.1 认证方案

#### 3.1.1 微信小程序登录流程

```
1. 小程序调用 wx.login() 获取临时 code
2. 小程序发送 code 到后端 POST /api/v1/auth/wechat/login
3. 后端用 code 调用微信服务器换取 openid 和 session_key
4. 后端查询数据库：
   - 如果 openid 已存在 → 返回 JWT token
   - 如果 openid 不存在 → 返回 need_bind=true
5. 用户绑定手机号：
   - 输入手机号
   - 发送验证码 POST /api/v1/auth/sms/send
   - 提交验证码 + 选择角色/班级 POST /api/v1/auth/wechat/bind
6. 后端创建用户，返回 JWT token
7. 小程序存储 token，后续请求携带 Authorization: Bearer <token>
```

#### 3.1.2 Web 端登录流程

```
1. 用户输入用户名/密码或手机号/密码
2. POST /api/v1/auth/login
3. 后端验证密码
4. 返回 JWT token
5. 前端存储 token（localStorage/sessionStorage）
6. 后续请求携带 Authorization: Bearer <token>
```

#### 3.1.3 已有账号绑定微信

```
1. 小程序登录，检测到 openid 未绑定
2. 提示"已有账号？绑定手机号"
3. 输入手机号 + 验证码
4. POST /api/v1/auth/wechat/bind-existing
5. 后端验证手机号和验证码
6. 将 openid 绑定到现有账号
7. 返回 JWT token
```

### 3.2 JWT Token 设计

**Token Payload**:
```json
{
  "user_id": 123,
  "role": "student",
  "openid": "oXXXX",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Token 配置**:
- Access Token 有效期: 7天
- Refresh Token: 30天（可选，后期实现）
- 算法: HS256
- Secret: 环境变量配置

### 3.3 权限控制

**角色定义**:
- `student` - 学生
- `teacher` - 教师
- `admin` - 管理员

**权限装饰器**:
```python
@require_auth()           # 需要登录
@require_role("teacher")  # 需要教师角色
@require_role("admin")    # 需要管理员角色
```

**权限规则**:
- 学生只能访问自己班级的数据
- 教师只能管理自己创建的班级/题库/作业
- 管理员可以跨教师查看数据（需审计）

---

## 四、数据库设计调整

### 4.1 users 表调整

**新增字段**:
```sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20) UNIQUE;
ALTER TABLE users ADD COLUMN openid VARCHAR(100) UNIQUE;
ALTER TABLE users ADD COLUMN is_phone_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN nickname VARCHAR(100);
ALTER TABLE users ADD COLUMN wechat_unionid VARCHAR(100);

CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_openid ON users(openid);
```

**字段说明**:
- `phone`: 手机号，用于登录和绑定
- `openid`: 微信小程序 openid
- `is_phone_verified`: 手机号是否验证
- `avatar_url`: 微信头像
- `nickname`: 微信昵称
- `wechat_unionid`: 微信 unionid（后期支持多小程序）

### 4.2 新增表

#### verification_codes - 验证码表

```sql
CREATE TABLE verification_codes (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    code VARCHAR(6) NOT NULL,
    purpose VARCHAR(20) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone_expires (phone, expires_at)
);
```

**purpose 枚举**:
- `register` - 注册
- `bind` - 绑定
- `reset` - 重置密码
- `login` - 登录验证

#### refresh_tokens - 刷新令牌表（可选）

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_token (token)
);
```

---

## 五、API 接口设计

### 5.1 API 版本和路由结构

**基础路径**: `/api/v1`

**路由结构**:

```
/api/v1/
├── auth/                    # 认证相关
│   ├── POST /login          # Web 登录
│   ├── POST /register       # Web 注册
│   ├── POST /logout         # 登出
│   ├── POST /wechat/login   # 微信登录
│   ├── POST /wechat/bind    # 绑定手机号
│   ├── POST /wechat/bind-existing  # 绑定已有账号
│   ├── POST /sms/send       # 发送验证码
│   └── POST /sms/verify     # 验证验证码
│
├── users/                   # 用户管理
│   ├── GET /me              # 获取当前用户信息
│   ├── PUT /me              # 更新个人信息
│   ├── PUT /me/password     # 修改密码
│   └── GET /{user_id}       # 获取用户详情（权限控制）
│
├── classes/                 # 班级管理
│   ├── GET /                # 班级列表（教师：自己的班级）
│   ├── POST /               # 创建班级（教师）
│   ├── GET /{class_id}      # 班级详情
│   ├── PUT /{class_id}      # 更新班级
│   ├── DELETE /{class_id}   # 删除班级
│   ├── GET /{class_id}/members      # 班级成员
│   ├── POST /{class_id}/members     # 添加成员
│   └── DELETE /{class_id}/members/{user_id}  # 移除成员
│
├── banks/                   # 题库管理
│   ├── GET /                # 题库列表（教师：自己的）
│   ├── POST /               # 创建题库
│   ├── GET /{bank_id}       # 题库详情
│   ├── PUT /{bank_id}       # 更新题库
│   ├── DELETE /{bank_id}    # 删除题库
│   └── POST /{bank_id}/import  # 批量导入题目
│
├── questions/               # 题目管理
│   ├── GET /                # 题目列表（支持筛选）
│   ├── POST /               # 创建题目
│   ├── GET /{question_id}   # 题目详情
│   ├── PUT /{question_id}   # 更新题目
│   ├── DELETE /{question_id}# 删除题目
│   └── POST /batch          # 批量创建
│
├── assignments/             # 作业管理
│   ├── GET /                # 作业列表（学生：本班，教师：自己创建的）
│   ├── POST /               # 创建作业（教师）
│   ├── GET /{assignment_id} # 作业详情
│   ├── PUT /{assignment_id} # 更新作业
│   ├── DELETE /{assignment_id} # 删除作业
│   ├── GET /{assignment_id}/stats  # 作业统计（教师）
│   └── POST /{assignment_id}/submit # 提交作业（学生）
│
├── practice/                # 刷题相关
│   ├── GET /daily           # 每日刷题（学生）
│   ├── POST /submit         # 提交答案
│   ├── GET /records         # 答题记录
│   └── GET /mistakes        # 错题本
│
├── stats/                   # 统计分析
│   ├── GET /student/{student_id}  # 学生统计（教师查看）
│   ├── GET /class/{class_id}      # 班级统计
│   ├── GET /my                    # 我的统计（学生）
│   └── GET /export/pdf            # 导出 PDF
│
└── admin/                   # 管理员接口
    ├── GET /users           # 用户管理
    ├── GET /classes         # 所有班级
    ├── POST /invite-code    # 生成邀请码
    └── GET /audit-logs      # 审计日志
```

### 5.2 统一响应格式

**成功响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误响应**:
```json
{
  "code": 40001,
  "message": "用户不存在",
  "data": null
}
```

**分页响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 5.3 错误码设计

```
# 通用错误 (10000-19999)
10000 - 系统错误
10001 - 参数错误
10002 - 数据不存在
10003 - 操作失败

# 认证错误 (20000-29999)
20001 - 未登录
20002 - Token 无效
20003 - Token 过期
20004 - 权限不足
20005 - 验证码错误
20006 - 验证码过期
20007 - 手机号已注册
20008 - 用户名或密码错误

# 业务错误 (30000-39999)
30001 - 班级不存在
30002 - 题库不存在
30003 - 作业不存在
30004 - 学生不属于该班级
30005 - 教师无权访问该资源
```

### 5.4 核心接口详细设计

#### 5.4.1 微信登录接口

**POST /api/v1/auth/wechat/login**

请求:
```json
{
  "code": "wx_login_code"
}
```

响应（已注册）:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "eyJhbGc...",
    "user": {
      "id": 123,
      "nickname": "张三",
      "avatar_url": "https://...",
      "role": "student",
      "phone": "138****1234"
    }
  }
}
```

响应（未注册）:
```json
{
  "code": 0,
  "message": "need_bind",
  "data": {
    "need_bind": true,
    "openid_token": "temp_token_for_bind"
  }
}
```

#### 5.4.2 绑定手机号接口

**POST /api/v1/auth/wechat/bind**

请求:
```json
{
  "openid_token": "temp_token_for_bind",
  "phone": "13800138000",
  "code": "123456",
  "role": "student",
  "class_id": 1,
  "invite_code": "TEACHER123"
}
```

响应:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "eyJhbGc...",
    "user": {
      "id": 124,
      "phone": "138****0000",
      "role": "student",
      "class_id": 1
    }
  }
}
```

#### 5.4.3 发送验证码接口

**POST /api/v1/auth/sms/send**

请求:
```json
{
  "phone": "13800138000",
  "purpose": "register"
}
```

响应:
```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": {
    "expires_in": 300
  }
}
```

---

## 六、项目目录结构重构

### 6.1 后端目录结构

```
app/
├── api/                      # API 路由层（新增）
│   └── v1/
│       ├── __init__.py
│       ├── auth.py           # 认证接口
│       ├── users.py          # 用户接口
│       ├── classes.py        # 班级接口
│       ├── banks.py          # 题库接口
│       ├── questions.py      # 题目接口
│       ├── assignments.py    # 作业接口
│       ├── practice.py       # 刷题接口
│       ├── stats.py          # 统计接口
│       └── admin.py          # 管理员接口
│
├── core/                     # 核心配置（新增）
│   ├── __init__.py
│   ├── config.py             # 配置管理
│   ├── security.py           # JWT/加密
│   ├── deps.py               # 依赖注入
│   └── middleware.py         # 中间件
│
├── schemas/                  # Pydantic 模型（新增）
│   ├── __init__.py
│   ├── auth.py               # 认证相关 schema
│   ├── user.py               # 用户 schema
│   ├── class_group.py        # 班级 schema
│   ├── question.py           # 题目 schema
│   ├── assignment.py         # 作业 schema
│   └── common.py             # 通用 schema
│
├── services/                 # 业务逻辑层（新增）
│   ├── __init__.py
│   ├── auth_service.py       # 认证服务
│   ├── wechat_service.py     # 微信服务
│   ├── sms_service.py        # 短信服务
│   ├── user_service.py       # 用户服务
│   ├── class_service.py      # 班级服务
│   ├── question_service.py   # 题目服务
│   └── assignment_service.py # 作业服务
│
├── models/                   # 数据模型（保留）
│   ├── __init__.py
│   ├── user.py
│   ├── question.py
│   ├── assignment.py
│   └── ...
│
├── routers/                  # Web 路由（保留，逐步废弃）
│   ├── auth.py
│   ├── teacher.py
│   ├── student.py
│   └── ...
│
├── templates/                # Jinja2 模板（保留，管理后台用）
│   └── ...
│
├── utils/                    # 工具函数（保留）
│   ├── __init__.py
│   ├── security.py
│   └── validators.py
│
└── main.py                   # 应用入口
```

### 6.2 微信小程序目录结构

```
miniprogram/
├── pages/                    # 页面
│   ├── index/                # 首页
│   ├── login/                # 登录/绑定
│   ├── practice/             # 刷题
│   ├── assignments/          # 作业列表
│   ├── assignment-detail/    # 作业详情
│   ├── mistakes/             # 错题本
│   ├── stats/                # 统计
│   ├── profile/              # 个人中心
│   ├── class-manage/         # 班级管理（教师）
│   ├── question-manage/      # 题目管理（教师）
│   └── student-detail/       # 学生详情（教师）
│
├── components/               # 组件
│   ├── question-card/        # 题目卡片
│   ├── answer-sheet/         # 答题卡
│   └── stats-chart/          # 统计图表
│
├── utils/                    # 工具
│   ├── request.js            # API 请求封装
│   ├── auth.js               # 认证管理
│   └── storage.js            # 本地存储
│
├── app.js                    # 小程序入口
├── app.json                  # 小程序配置
└── app.wxss                  # 全局样式
```

---

## 七、迁移策略

### 7.1 数据迁移

**阶段 1：Schema 迁移**

创建 Alembic 迁移脚本:
```python
# alembic/versions/xxxx_add_wechat_phone_fields.py

def upgrade():
    # 添加新字段
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('openid', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('is_phone_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('nickname', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('wechat_unionid', sa.String(100), nullable=True))
    
    # 创建唯一索引
    op.create_unique_constraint('uq_users_phone', 'users', ['phone'])
    op.create_unique_constraint('uq_users_openid', 'users', ['openid'])
    op.create_index('idx_users_phone', 'users', ['phone'])
    op.create_index('idx_users_openid', 'users', ['openid'])
    
    # 创建验证码表
    op.create_table(
        'verification_codes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('purpose', sa.String(20), nullable=False),
        sa.Column('is_used', sa.Boolean(), default=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_verification_codes_phone', 'verification_codes', ['phone', 'expires_at'])
```

**阶段 2：现有用户处理**
- 现有用户保持 username/password 登录
- 首次使用小程序时引导绑定手机号和微信
- 提供"账号合并"功能

### 7.2 代码迁移策略

**并行运行期（1-2个月）**:
```
/api/v1/*        → 新 API（小程序使用）
/teacher/*       → 旧 Web 路由（继续可用）
/student/*       → 旧 Web 路由（继续可用）
/admin/*         → 旧 Web 路由（继续可用）
```

**过渡完成后**:
```
/api/v1/*        → 所有客户端使用
/admin/*         → Web 管理后台（Vue 重写或保留 Jinja2）
其他旧路由       → 废弃
```

---

## 八、部署架构

### 8.1 Render 部署配置

```yaml
# render.yaml
services:
  - type: web
    name: fushua-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: |
      alembic upgrade head && 
      gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: fushua-db
          property: connectionString
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: WECHAT_APP_ID
        sync: false
      - key: WECHAT_APP_SECRET
        sync: false
      - key: SMS_ACCESS_KEY
        sync: false
      - key: SMS_SECRET_KEY
        sync: false
      - key: CORS_ORIGINS
        value: "*"

databases:
  - name: fushua-db
    databaseName: fushua
    plan: starter
```

### 8.2 环境变量配置

```bash
# .env.example

# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/fushua

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080  # 7天

# 微信小程序
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your-wechat-app-secret

# 短信服务（阿里云示例）
SMS_ACCESS_KEY=your-aliyun-access-key
SMS_SECRET_KEY=your-aliyun-secret-key
SMS_SIGN_NAME=付刷
SMS_TEMPLATE_CODE=SMS_123456

# CORS
CORS_ORIGINS=["https://your-domain.com","https://servicewechat.com"]

# 其他
ENVIRONMENT=production  # development/production
DEBUG=False
LOG_LEVEL=INFO
```

---

## 九、开发优先级和里程碑

### Phase 1：后端 API 基础（2-3周）

**Week 1：核心架构**
- 项目结构重构
- JWT 认证实现
- 数据库迁移
- 统一响应格式
- 错误处理中间件
- CORS 配置

**Week 2：核心 API**
- 认证接口（登录/注册/微信登录）
- 用户接口
- 班级接口
- 题目接口
- 短信服务集成

**Week 3：业务 API**
- 作业接口
- 刷题接口
- 统计接口
- 权限控制完善
- API 文档（Swagger）

### Phase 2：微信小程序开发（3-4周）

**Week 4-5：学生端**
- 微信登录/绑定流程
- 每日刷题功能
- 作业列表/详情
- 答题界面
- 错题本
- 个人统计

**Week 6-7：教师端**
- 班级管理
- 题库管理
- 题目导入
- 作业布置
- 学生统计查看

### Phase 3：Web 管理后台（2-3周）

**Week 8-9：管理后台**
- Vue 3 项目搭建（或保留 Jinja2 + API）
- 用户管理
- 班级管理
- 数据统计
- 系统配置
- 审计日志

### Phase 4：测试和优化（1-2周）

**Week 10-11：**
- 集成测试
- 性能优化
- 安全审计
- 文档完善
- 灰度发布

---

## 十、风险评估与应对

### 10.1 技术风险

**风险 1：微信登录集成复杂度**
- 影响：开发周期延长
- 应对：提前申请小程序账号，熟悉微信开发文档
- 备选：先实现手机号登录，微信登录后期补充

**风险 2：前后端分离后性能下降**
- 影响：用户体验变差
- 应对：合理设计 API，减少请求次数，使用缓存
- 监控：添加性能监控，及时发现问题

**风险 3：数据迁移失败**
- 影响：现有用户无法使用
- 应对：充分测试迁移脚本，保留回滚方案
- 备份：迁移前完整备份数据库

### 10.2 业务风险

**风险 1：用户不接受小程序**
- 影响：转型失败
- 应对：保留 Web 端作为备选，灰度发布
- 调研：提前调研目标用户使用习惯

**风险 2：手机号绑定流程复杂**
- 影响：用户流失
- 应对：简化流程，提供清晰引导
- 优化：支持一键授权手机号（微信能力）

### 10.3 时间风险

**风险 1：开发周期超预期**
- 影响：延迟上线
- 应对：分阶段发布，优先核心功能
- 调整：根据实际进度动态调整计划

---

## 十一、成功标准

### 11.1 功能完整性

- [ ] 微信登录/绑定流程完整
- [ ] 学生端核心功能可用（刷题/作业/错题）
- [ ] 教师端核心功能可用（班级/题库/作业管理）
- [ ] 管理后台基本可用
- [ ] 现有 Web 端功能不受影响

### 11.2 性能指标

- [ ] API 响应时间 < 500ms (P95)
- [ ] 小程序首屏加载 < 2s
- [ ] 支持 1000+ 并发用户
- [ ] 数据库查询优化（无 N+1 问题）

### 11.3 安全标准

- [ ] JWT 认证正确实现
- [ ] 权限控制完整
- [ ] 敏感数据加密
- [ ] SQL 注入防护
- [ ] XSS 防护
- [ ] CSRF 防护

### 11.4 用户体验

- [ ] 登录流程顺畅（< 3 步）
- [ ] 界面友好，符合微信设计规范
- [ ] 错误提示清晰
- [ ] 加载状态明确
- [ ] 离线提示友好

---

## 十二、后续优化方向

### 12.1 短期优化（3个月内）

- Redis 缓存集成
- 图片上传到对象存储
- 消息推送（模板消息/订阅消息）
- 数据统计优化
- 性能监控

### 12.2 中期优化（6个月内）

- 多小程序支持（unionid）
- 家长端小程序
- 学习报告优化
- AI 推荐题目
- 社交功能（班级排行榜）

### 12.3 长期规划（1年内）

- 微信支付集成
- 会员体系
- 内容商城
- 数据分析平台
- 开放 API

---

## 十三、附录

### 13.1 参考文档

- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [JWT 最佳实践](https://tools.ietf.org/html/rfc7519)
- [RESTful API 设计指南](https://restfulapi.net/)

### 13.2 相关资源

**必需资源**:
- 微信小程序 AppID: 需在微信公众平台申请
- 短信服务账号: 推荐阿里云或腾讯云短信服务
- SSL 证书: Render 自动提供

**可选资源**:
- 对象存储: 用于图片/文件存储，初期可使用本地存储
- 域名备案: 如需在中国大陆提供服务则必需，否则可选
- Redis: 用于缓存，初期可不使用

---

**文档版本**: v1.0  
**最后更新**: 2026-05-18  
**负责人**: 开发团队  
**审核状态**: 待审核
