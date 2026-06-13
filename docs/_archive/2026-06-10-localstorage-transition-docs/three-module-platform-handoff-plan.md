# 付刷三模块教学工具平台交接规划

日期：2026-06-10

本文档用于把当前 `fushua` 项目交接给其他开发工具或开发者继续实现。请先阅读本文，再动代码。

## 1. 项目定位

当前项目应从单一刷题系统升级为三模块教学工具平台：

1. 课堂管理：面向教师课堂现场，承接旧网页工具“课堂伴侣”的随机抽学生、随机抽题、课堂答题、积分、统计、数据备份能力。
2. 刷题训练：面向学生小程序，承接当前已实现的每日刷题、作业、错题本、个人统计能力。
3. 个人题库管理：面向教师 Web 端，提供题库、题目、导入、分类、标签、解析维护能力，并向课堂管理和刷题训练供题。

三模块的核心闭环：

```text
个人题库管理 -> 课堂抽取答题 / 作业发布 -> 学生刷题训练 -> 错题与统计 -> 反哺题库和课堂教学
```

## 2. 当前项目事实

项目根目录：

```text
C:\Users\Windows 10\Desktop\trae\fushua
```

技术栈：

- 后端：FastAPI + SQLAlchemy + Jinja2
- 数据库：PostgreSQL 生产环境，SQLite 可本地开发
- 小程序：原生微信小程序
- Web 教师后台：Jinja2 模板
- 服务器域名：`https://www.fushua.asia`
- 小程序 AppID：`wx86db4c7584917750`

当前核心数据表已存在：

- `users`
- `class_groups`
- `class_members`
- `question_banks`
- `questions`
- `records`
- `assignments`
- `assignment_records`
- `verification_codes`
- `announcements`

当前小程序生产地址已经统一为：

```text
https://www.fushua.asia
```

当前短期产品策略：

- 手机绑定暂时放宽，不强制短信验证码。
- 短信服务后续再接入，不能阻塞当前开发。
- 教师端课堂工具先 Web 化，不急着重写成小程序。

## 3. 旧课堂工具情况

旧工具文件：

```text
C:\Users\Windows 10\Desktop\ClassRoom-v1(1)\apps\copy-of-classroom-companion-(课堂伴侣)\抽取优化版 2.html
```

旧工具是一个 React 单页 HTML，依赖 CDN：

- React 18 UMD
- ReactDOM UMD
- Babel standalone
- Tailwind CDN

旧工具主要视图：

- `DASHBOARD`：首页仪表盘
- `SESSION`：开始上课
- `STUDENTS`：班级学生
- `QUESTIONS`：题库中心
- `STATS`：统计排行
- `DATA`：数据备份与恢复

旧工具主要本地存储键：

- `classroom_companion_data_v2`
- `classroom_companion_snapshots_v2`
- `classroom_draw_history_v3`

旧工具本地状态大致结构：

```json
{
  "classes": [],
  "activeClassId": null,
  "students": [],
  "questions": []
}
```

旧工具已有的课堂能力：

- 多班级切换
- 学生管理
- 题库管理
- 导入题目
- 随机抽学生
- 随机抽题
- 连胜模式
- 学生自主选题模式
- 答题正误反馈
- 积分
- 抽取历史
- 统计排行
- 数据备份和恢复

## 4. 推荐总体路线

不要一开始就大规模重写旧工具。推荐分四阶段：

### 阶段 A：放宽绑定，保证用户能进入系统

目标：开发期不被短信服务阻塞。

要求：

1. 后端增加配置项：

```text
PHONE_BINDING_REQUIRE_SMS=false
```

2. 当该配置为 `false` 时：
   - `/api/v1/auth/wechat/bind` 不校验短信验证码。
   - 仍校验手机号格式。
   - 绑定成功后 `users.phone` 写入手机号。
   - `users.is_phone_verified` 必须写入 `false`。

3. 当该配置为 `true` 时：
   - 恢复当前验证码校验逻辑。
   - 验证成功后 `users.is_phone_verified=true`。

4. 小程序绑定页：
   - 开发期可以隐藏验证码输入和发送验证码按钮，或显示“开发期免验证码绑定”提示。
   - 不能让用户以为已完成短信验证。

验收标准：

- 新微信用户登录后进入绑定页。
- 输入合法手机号即可继续选择身份。
- 学生/教师可以完成绑定。
- 数据库中该用户 `phone` 有值，`is_phone_verified=false`。
- 配置切回 `PHONE_BINDING_REQUIRE_SMS=true` 后，旧验证码逻辑仍可用。

### 阶段 B：课堂工具以 Web 页面接入

目标：最快让教师在当前系统里打开旧课堂工具。

建议路径：

```text
GET /teacher/classroom
```

建议文件位置：

```text
app/templates/teacher/classroom.html
app/routers/classroom.py
```

第一版可以先做“嵌入式迁移”：

1. 把旧 HTML 中的 React 应用迁入 Jinja2 模板。
2. 教师登录后才能访问。
3. 入口加到教师后台导航或首页。
4. 第一版仍允许 localStorage 存储课堂数据。
5. 明确标注这是“课堂工具试用版，本地浏览器数据”。

第一版不要急着做：

- 不要立刻拆成复杂前后端工程。
- 不要立刻把所有 localStorage 数据迁入数据库。
- 不要立刻改造成小程序。
- 不要立刻做多人实时同步。

验收标准：

- 教师登录后能从后台进入课堂工具。
- 原工具的学生管理、题库管理、随机抽取、统计、数据备份恢复能运行。
- 普通学生不能访问该页面。
- 未登录用户访问会跳转登录或返回权限错误。

### 阶段 C：课堂工具服务化

目标：把旧工具从浏览器本地数据逐步接入当前数据库。

优先接入顺序：

1. 班级读取：从 `class_groups` 和 `class_members` 读取当前教师班级。
2. 学生读取：课堂学生列表来自当前系统学生。
3. 题库读取：课堂抽题来自 `question_banks` 和 `questions`。
4. 课堂记录入库：新增课堂会话和课堂答题记录。
5. 统计联动：课堂记录进入学生统计和题目统计。

建议新增模型：

```text
ClassroomSession
- id
- class_id
- teacher_id
- title
- mode
- started_at
- ended_at
- created_at

ClassroomDrawRecord
- id
- session_id
- class_id
- student_id
- question_id
- result
- score_delta
- note
- created_at

ClassroomQuestionSnapshot
- id
- session_id
- question_id
- content_snapshot
- answer_snapshot
- explanation_snapshot
- created_at
```

说明：

- `ClassroomQuestionSnapshot` 用于保留课堂当时题目内容，避免题目后续编辑导致历史记录失真。
- `result` 建议取值：`correct`、`wrong`、`skip`、`manual`。
- `score_delta` 用于课堂积分。

建议新增 API：

```text
GET    /api/v1/classroom/classes
GET    /api/v1/classroom/classes/{class_id}/students
GET    /api/v1/classroom/question-banks
GET    /api/v1/classroom/questions?bank_id=&subject=&chapter=&difficulty=
POST   /api/v1/classroom/sessions
GET    /api/v1/classroom/sessions/{session_id}
POST   /api/v1/classroom/sessions/{session_id}/draws
GET    /api/v1/classroom/sessions/{session_id}/draws
POST   /api/v1/classroom/sessions/{session_id}/finish
```

权限要求：

- 教师只能访问自己创建的班级。
- 教师只能读取自己题库里的题。
- 管理员可跨教师访问，但必须通过管理入口。
- 学生不能访问课堂管理 API。

### 阶段 D：三模块打通

目标：课堂、刷题、题库共用同一套题目和统计。

打通规则：

1. 个人题库是题目来源。
2. 课堂抽题只从教师有权限的题目中选择。
3. 作业发布也从教师有权限的题目中选择。
4. 学生刷题记录写入 `records`。
5. 课堂答题记录写入 `classroom_draw_records`，后续可汇总进学情分析。
6. 题目统计同时展示：
   - 刷题正确率
   - 作业正确率
   - 课堂答题正确率
   - 被抽取次数
   - 最近使用时间

## 5. 三大模块边界

### 5.1 个人题库管理

职责：

- 教师创建题库。
- 教师维护题目。
- 支持导入题目。
- 支持筛选题目。
- 支持把题用于课堂和作业。

不负责：

- 不记录学生答题行为。
- 不管理课堂会话。
- 不决定学生练习推荐策略。

### 5.2 课堂管理

职责：

- 上课现场抽学生。
- 上课现场抽题。
- 记录课堂答题结果。
- 展示课堂积分和排行。
- 输出课堂小结。

不负责：

- 不编辑题目正文，最多跳转到题库编辑。
- 不承担完整作业系统。
- 不替代学生日常刷题。

### 5.3 刷题训练

职责：

- 学生日常练习。
- 作业答题。
- 错题本。
- 个人统计。
- 班级作业完成情况。

不负责：

- 不做课堂现场抽人。
- 不管理教师题库结构。

## 6. 绑定手机号临时放宽的详细要求

后端文件重点：

```text
app/core/config.py
app/api/v1/auth.py
app/services/auth_service.py
tests/test_miniprogram_compat.py 或新增 tests/test_wechat_binding.py
```

小程序文件重点：

```text
miniprogram/pages/bind/bind.js
miniprogram/pages/bind/bind.wxml
miniprogram/pages/bind/bind.wxss
```

开发要求：

1. 增加配置项，默认开发环境可为 `false`，生产是否 `false` 由当前阶段决定。
2. 不删除验证码相关代码，只加开关。
3. 保留 `send_sms` 接口，但接口返回文案要避免误导：
   - 若未接短信服务，可返回“开发期验证码已跳过”。
   - 或者小程序端开发期不展示该按钮。
4. 绑定接口必须仍防止手机号重复绑定。
5. 绑定接口必须仍校验 `openid_token`。
6. 绑定教师身份时，仍应校验教师邀请码或后续设计的教师准入条件。

验收测试：

- `PHONE_BINDING_REQUIRE_SMS=false` 时，验证码为空也可以绑定。
- `PHONE_BINDING_REQUIRE_SMS=false` 时，错误手机号不能绑定。
- `PHONE_BINDING_REQUIRE_SMS=false` 时，重复手机号不能绑定。
- `PHONE_BINDING_REQUIRE_SMS=true` 时，错误验证码不能绑定。
- `PHONE_BINDING_REQUIRE_SMS=true` 时，正确验证码可以绑定。

## 7. 课堂工具迁移要求

第一阶段迁移目标：让旧工具在项目内可打开、可用、受权限保护。

建议操作：

1. 新增路由文件：

```text
app/routers/classroom.py
```

2. 在 `app/main.py` include router：

```python
from app.routers import classroom
app.include_router(classroom.router)
```

3. 新增模板：

```text
app/templates/teacher/classroom.html
```

4. 从旧 HTML 迁入：
   - `<script>` CDN 依赖
   - `<style>`
   - `<div id="root"></div>`
   - React 应用脚本

5. 路由权限：

```python
@router.get("/teacher/classroom", response_class=HTMLResponse)
def classroom_page(request: Request, db: Session = Depends(get_db)):
    require_teacher(request, db)
    return templates.TemplateResponse("teacher/classroom.html", {"request": request})
```

6. 教师后台加入口：
   - 首页功能卡片
   - 或导航链接
   - 文案：“课堂伴侣”

第一阶段验收：

- 教师能打开 `/teacher/classroom`。
- 学生和未登录用户不能打开。
- 页面无 500。
- 浏览器控制台无阻塞性错误。
- localStorage 版学生、题库、抽取、统计可用。

第二阶段服务化目标：

- 旧工具的 `students` 映射到系统班级学生。
- 旧工具的 `questions` 映射到系统题库题目。
- 旧工具的 `drawHistory` 映射到课堂抽取记录表。

## 8. 数据映射建议

旧工具 `class` -> 当前 `ClassGroup`

```text
old.id       -> class_groups.id 或前端临时 id
old.name     -> class_groups.name
teacher_id   -> class_groups.created_by
```

旧工具 `student` -> 当前 `User + ClassMember`

```text
old.id        -> users.id 或前端临时 id
old.name      -> users.display_name / users.nickname / users.username
old.classId   -> class_members.class_id
old.score     -> classroom 聚合字段，不建议直接写 users
old.history   -> classroom_draw_records
```

旧工具 `question` -> 当前 `Question`

```text
old.id        -> questions.id 或前端临时 id
old.text      -> questions.content
old.answer    -> questions.answer
old.type      -> questions.q_type
old.options   -> option_a/b/c/d 或 extra_data
old.category  -> chapter / tags
```

旧工具 `drawHistory` -> 新增 `ClassroomDrawRecord`

```text
studentId   -> student_id
questionId  -> question_id
result      -> result
score       -> score_delta
time        -> created_at
```

## 9. 开发顺序建议

推荐给接手工具按以下顺序做：

1. 创建新分支或至少先确认当前 git dirty 状态，不要回滚已有改动。
2. 实现手机号绑定开关。
3. 写绑定开关测试。
4. 将课堂工具以 Web 页面接入。
5. 给教师后台加入口。
6. 做页面访问权限测试。
7. 做手动浏览器验证。
8. 再开始设计课堂服务化数据表和 API。

不要一开始做：

- 不要大改小程序结构。
- 不要删除旧短信验证码逻辑。
- 不要把旧 HTML 改成复杂构建项目。
- 不要绕过现有 `require_teacher` 权限体系。
- 不要让课堂记录直接污染 `records`，应先独立建课堂记录表。

## 10. 验证命令

本项目常用窄验证：

```powershell
python -m compileall -q app tests
python -m pytest tests/test_backup.py -q --tb=short
python -c "from app.main import app; print('import ok')"
node tests/miniprogram_request_url.test.js
node tests/miniprogram_ui_theme.test.js
node tests/miniprogram_product_design_pages.test.js
```

全量测试需要更长时间：

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m pytest tests/ -q --tb=short --disable-warnings --maxfail=1
```

注意：

- 全量测试可能超过 3 分钟。
- 不要把短 timeout 当作测试失败。
- 当前工作区可能已有大量未提交改动，不要擅自 revert。

## 11. 交接给其他工具时的提示词建议

可把下面这段直接交给另一个工具：

```text
你接手的是 C:\Users\Windows 10\Desktop\trae\fushua 项目。请先阅读 docs/three-module-platform-handoff-plan.md。

目标不是重做项目，而是在现有 FastAPI + Jinja2 + 微信小程序基础上推进三模块平台：
1. 课堂管理：先把旧 HTML 课堂伴侣作为教师 Web 工具接入，再逐步服务化。
2. 刷题训练：保留当前小程序刷题/作业/错题能力。
3. 个人题库管理：作为课堂和刷题共同题源。

当前优先任务：
1. 实现 PHONE_BINDING_REQUIRE_SMS 开关，开发期允许免验证码绑定手机号，但 is_phone_verified=false。
2. 把旧课堂工具 C:\Users\Windows 10\Desktop\ClassRoom-v1(1)\apps\copy-of-classroom-companion-(课堂伴侣)\抽取优化版 2.html 接入到 /teacher/classroom，仅教师可访问。
3. 不要删除短信逻辑，不要重写小程序，不要回滚现有改动。
4. 每步都配测试和验证命令。

请先查看 git status，再阅读相关文件，遵循项目现有模式小步修改。
```

## 12. 风险和决策

### 风险 1：旧课堂工具依赖 CDN

短期可接受。正式产品应考虑本地化依赖或改成构建产物，避免 CDN 不稳定。

### 风险 2：localStorage 数据无法多设备同步

第一阶段可接受。服务化阶段必须把班级、题库、课堂记录入库。

### 风险 3：课堂积分与刷题统计混淆

不要直接把课堂答题写进 `records`。课堂记录先独立建表，后续统计时再聚合。

### 风险 4：免验证码绑定带来手机号真实性问题

开发期可接受，但必须用 `is_phone_verified=false` 区分。后续短信接入后再升级验证状态。

### 风险 5：三模块同时开发容易失控

必须按阶段推进：先进系统，再接课堂工具，再服务化，再打通统计。

## 13. 最小可交付版本定义

MVP-1：

- 微信用户可免验证码完成绑定。
- 教师可登录 Web 后台。
- 教师可打开课堂伴侣页面。
- 课堂伴侣页面保留原本 localStorage 功能。
- 学生小程序刷题不受影响。

MVP-2：

- 课堂伴侣能读取真实班级学生。
- 课堂伴侣能读取教师个人题库。
- 课堂答题记录可保存到数据库。

MVP-3：

- 教师题库、课堂记录、学生刷题记录在统计页打通。
- 教师能看到班级、学生、题目、知识点维度分析。

