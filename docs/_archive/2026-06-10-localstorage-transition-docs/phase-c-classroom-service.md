# 阶段 C 实现文档：课堂工具服务化

实施日期：2026-06-10  
状态：✅ 已完成

## 实施目标

根据 `docs/three-module-platform-handoff-plan.md` 阶段 C 要求，将课堂工具从 localStorage 数据存储升级为后端数据库服务化。

## 已完成的工作

### 1. 数据模型设计（`app/models.py`）

新增三个课堂管理模型：

#### ClassroomSession（课堂会话）
```python
- id: 主键
- class_id: 班级 ID（外键）
- teacher_id: 教师 ID（外键）
- title: 课堂标题
- mode: 课堂模式（normal/streak/self_select）
- started_at: 开始时间
- ended_at: 结束时间（可选）
- created_at: 创建时间
```

**索引：**
- `idx_classroom_sessions_teacher_created`（teacher_id, created_at）
- `idx_classroom_sessions_class_created`（class_id, created_at）

#### ClassroomDrawRecord（课堂抽取记录）
```python
- id: 主键
- session_id: 会话 ID（外键）
- class_id: 班级 ID（外键）
- student_id: 学生 ID（外键）
- question_id: 题目 ID（外键，可选）
- result: 结果（correct/wrong/skip/manual）
- score_delta: 积分变化
- note: 备注
- created_at: 创建时间
```

**索引：**
- `idx_classroom_draw_session_created`（session_id, created_at）
- `idx_classroom_draw_student_created`（student_id, created_at）

#### ClassroomQuestionSnapshot（课堂题目快照）
```python
- id: 主键
- session_id: 会话 ID（外键）
- question_id: 题目 ID（外键）
- content_snapshot: 题目内容快照
- answer_snapshot: 答案快照
- explanation_snapshot: 解析快照
- extra_snapshot: 额外信息快照（JSON）
- created_at: 创建时间
```

**索引：**
- `idx_classroom_snapshot_session_question`（session_id, question_id）

**设计亮点：**
- **独立记录表**：课堂记录不污染 `records` 表
- **题目快照**：保留课堂当时的题目内容，避免后续编辑影响历史
- **关联设计**：通过外键关联班级、学生、题目

### 2. 数据库迁移（`migrations/002_classroom_tables.py`）

创建迁移脚本，支持：
- `upgrade`：创建三张表和索引
- `downgrade`：删除三张表

**执行结果：**
```bash
python migrations/002_classroom_tables.py upgrade
# Migration completed successfully!
```

### 3. API Schema 设计（`app/schemas/classroom.py`）

定义 Pydantic 模型：

**请求模型：**
- `ClassroomSessionCreate` - 创建课堂会话
- `ClassroomDrawCreate` - 创建抽取记录
- `ClassroomSessionFinish` - 结束课堂

**响应模型：**
- `ClassroomSessionResponse` - 课堂会话响应
- `ClassroomDrawResponse` - 抽取记录响应
- `ClassroomStudentResponse` - 学生响应
- `ClassroomClassResponse` - 班级响应
- `ClassroomQuestionBankResponse` - 题库响应
- `ClassroomQuestionResponse` - 题目响应

### 4. 课堂 API 接口（`app/api/v1/classroom.py`）

实现完整的 RESTful API：

#### 班级和学生

```
GET /api/v1/classroom/classes
- 获取教师的班级列表
- 返回：班级列表，包含学生数量

GET /api/v1/classroom/classes/{class_id}/students
- 获取班级学生列表
- 权限：仅班级创建者可访问
- 返回：学生列表（id, username, display_name, phone）
```

#### 题库和题目

```
GET /api/v1/classroom/question-banks
- 获取教师的题库列表
- 返回：题库列表，包含题目数量

GET /api/v1/classroom/questions
- 获取教师的题目列表（用于课堂抽题）
- 查询参数：bank_id, subject, chapter, difficulty, limit
- 返回：题目列表（最多 50 题）
```

#### 课堂会话管理

```
POST /api/v1/classroom/sessions
- 创建课堂会话
- 请求体：class_id, title, mode
- 返回：会话详情

GET /api/v1/classroom/sessions/{session_id}
- 获取课堂会话详情
- 权限：仅会话创建者可访问
- 返回：会话详情

POST /api/v1/classroom/sessions/{session_id}/finish
- 结束课堂会话
- 设置 ended_at 时间
- 返回：更新后的会话详情
```

#### 抽取记录管理

```
POST /api/v1/classroom/sessions/{session_id}/draws
- 创建课堂抽取记录
- 请求体：student_id, question_id, result, score_delta, note
- 自动创建题目快照（如果有题目）
- 返回：抽取记录详情

GET /api/v1/classroom/sessions/{session_id}/draws
- 获取课堂会话的抽取记录
- 按创建时间排序
- 返回：抽取记录列表
```

**权限控制：**
- 所有接口需要教师身份（teacher/admin）
- 教师只能访问自己创建的班级和会话
- 使用 `get_current_teacher` 依赖注入

**题目快照逻辑：**
- 抽取时自动创建题目快照
- 同一会话中的同一题目只创建一次快照
- 快照包含：题目内容、答案、解析、选项等

### 5. 路由注册（`app/main.py`）

将课堂 API 注册到主应用：

```python
from app.api.v1 import classroom as api_classroom
app.include_router(api_classroom.router, prefix="/api/v1")
```

**API 路径前缀：** `/api/v1/classroom`

## 验收结果

✅ 所有文档要求的验收标准已达成：

**数据层：**
- [x] 课堂数据表已创建
- [x] 表结构符合设计要求
- [x] 索引已正确创建
- [x] 迁移脚本可正常运行

**API 层：**
- [x] 班级和学生读取接口
- [x] 题库和题目读取接口
- [x] 课堂会话管理接口
- [x] 抽取记录保存接口
- [x] 权限控制正常
- [x] 应用可正常导入启动

## 文件清单

### 新增的文件

```
app/models.py                                 # 添加 3 个模型
app/schemas/classroom.py                      # 课堂 Schema（9 个类）
app/api/v1/classroom.py                       # 课堂 API（10 个接口）
migrations/002_classroom_tables.py            # 数据库迁移脚本
docs/phase-c-classroom-service.md             # 本文档
```

### 修改的文件

```
app/main.py                                   # 注册课堂 API 路由
```

## API 设计说明

### 认证方式

使用现有的 JWT 认证体系：
- 请求头：`Authorization: Bearer <token>`
- 依赖注入：`Depends(get_current_user)`
- 教师过滤：`get_current_teacher` 包装

### 响应格式

统一使用 `ResponseModel`：
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

错误响应：
```json
{
  "detail": "错误信息"
}
```

### 数据隔离

- 教师只能访问自己创建的班级
- 教师只能访问自己的题库和题目
- 教师只能访问自己创建的课堂会话
- 管理员拥有全部权限

### 性能优化

- 使用索引优化查询
- 限制题目列表返回数量（默认 50）
- 题目快照避免重复创建

## 题目快照机制

### 为什么需要快照？

课堂结束后，教师可能会编辑题目内容。如果不保存快照，历史课堂记录中的题目会显示修改后的内容，导致记录失真。

### 快照创建时机

当创建抽取记录且包含题目时，自动创建快照：

```python
if request.question_id:
    # 检查是否已有快照
    snapshot = db.query(ClassroomQuestionSnapshot).filter(
        ClassroomQuestionSnapshot.session_id == session_id,
        ClassroomQuestionSnapshot.question_id == request.question_id
    ).first()
    
    if not snapshot:
        # 创建新快照
        snapshot = ClassroomQuestionSnapshot(...)
        db.add(snapshot)
```

### 快照内容

```json
{
  "content_snapshot": "题目内容",
  "answer_snapshot": "答案",
  "explanation_snapshot": "解析",
  "extra_snapshot": {
    "subject": "数学",
    "q_type": "choice",
    "option_a": "选项A",
    "option_b": "选项B",
    "option_c": "选项C",
    "option_d": "选项D"
  }
}
```

## 数据映射规则

### 旧工具 localStorage → 新系统数据库

**班级（class）：**
```
old.id        → class_groups.id（前端临时 ID）
old.name      → class_groups.name
old.teacher   → class_groups.created_by
```

**学生（student）：**
```
old.id        → users.id（前端临时 ID）
old.name      → users.display_name
old.classId   → class_members.class_id
old.score     → 聚合计算（sum(score_delta)）
old.history   → classroom_draw_records
```

**题目（question）：**
```
old.id        → questions.id（前端临时 ID）
old.text      → questions.content
old.answer    → questions.answer
old.type      → questions.q_type
old.options   → option_a/b/c/d
```

**抽取历史（drawHistory）：**
```
old.studentId  → classroom_draw_records.student_id
old.questionId → classroom_draw_records.question_id
old.result     → classroom_draw_records.result
old.score      → classroom_draw_records.score_delta
old.time       → classroom_draw_records.created_at
```

## 前端对接指南

### 步骤 1：获取数据

替换 localStorage 读取为 API 调用：

```javascript
// 旧代码
const classes = JSON.parse(localStorage.getItem('classroom_data_v2')).classes;

// 新代码
const response = await get('/classroom/classes');
const classes = response.data;
```

### 步骤 2：创建课堂会话

开始上课时创建会话：

```javascript
const session = await post('/classroom/sessions', {
  class_id: selectedClassId,
  title: '数学课-第3章',
  mode: 'normal'
});
```

### 步骤 3：记录抽取

每次抽取时保存记录：

```javascript
await post(`/classroom/sessions/${sessionId}/draws`, {
  student_id: drawnStudent.id,
  question_id: drawnQuestion?.id,
  result: 'correct',
  score_delta: 10,
  note: ''
});
```

### 步骤 4：结束课堂

课堂结束时调用：

```javascript
await post(`/classroom/sessions/${sessionId}/finish`);
```

### 错误处理

```javascript
try {
  const result = await post('/classroom/sessions', data);
} catch (error) {
  if (error.status === 403) {
    alert('权限不足');
  } else if (error.status === 404) {
    alert('班级不存在');
  } else {
    alert('网络错误，请重试');
  }
}
```

## 测试验证

### 验证命令

```bash
# 语法检查
python -m compileall -q app

# 应用导入检查
python -c "from app.main import app; print('import ok')"

# 启动应用
uvicorn app.main:app --reload --port 8000
```

### API 测试清单

使用 curl 或 Postman 测试：

```bash
# 1. 获取班级列表
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/classroom/classes

# 2. 获取班级学生
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/classroom/classes/1/students

# 3. 获取题库
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/classroom/question-banks

# 4. 获取题目
curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/v1/classroom/questions?bank_id=1&limit=10"

# 5. 创建课堂会话
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"class_id":1,"title":"测试课堂","mode":"normal"}' \
  http://localhost:8000/api/v1/classroom/sessions

# 6. 创建抽取记录
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"student_id":1,"question_id":1,"result":"correct","score_delta":10}' \
  http://localhost:8000/api/v1/classroom/sessions/1/draws

# 7. 获取抽取记录
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/classroom/sessions/1/draws

# 8. 结束课堂
curl -X POST -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/classroom/sessions/1/finish
```

## 下一步工作

根据交接文档，接下来应该进入：

**阶段 D：三模块打通**

主要任务：
1. **统计联动**
   - 课堂答题记录进入学生统计
   - 题目统计同时展示课堂/作业/刷题数据
   - 学情分析整合多维度数据

2. **前端改造**
   - 替换课堂工具的 localStorage 为 API 调用
   - 保持原有 UI 和交互不变
   - 添加加载状态和错误处理
   - 提供 localStorage 数据导入功能（可选）

3. **数据打通**
   - 课堂记录 → 学生统计
   - 课堂记录 → 题目统计
   - 课堂记录 → 知识点分析
   - 跨模块数据聚合查询

## 风险和注意事项

### 风险 1：API 性能

**影响**：大班级（100+ 学生）查询可能较慢

**缓解**：
- 已添加数据库索引
- 限制题目列表数量
- 可考虑添加 Redis 缓存

### 风险 2：快照存储空间

**影响**：每个题目每个会话都保存快照，可能占用较多空间

**缓解**：
- 只在首次使用时创建快照
- 定期清理旧会话的快照（可选）
- 快照表独立，便于管理

### 风险 3：前端改造工作量

**影响**：旧课堂工具 1874 行代码，改造需要时间

**缓解**：
- 逐步改造，先核心功能
- 保留 localStorage 作为降级方案
- 提供数据迁移工具

## 交接建议

给下一位开发者（codex 或其他工具）的提示：

1. ✅ 阶段 C 已完成，课堂 API 已就绪
2. 📍 当前位置：准备开始阶段 D（三模块打通）
3. 🎯 下一步目标：
   - 前端改造：替换 localStorage 为 API 调用
   - 统计联动：课堂记录进入学生和题目统计
   - 数据打通：跨模块聚合查询
4. ⚠️ 注意事项：
   - 先改造核心流程（创建会话、抽取记录）
   - 保留 localStorage 作为降级方案
   - 添加完善的错误处理
   - 提供数据导入工具（可选）

## 参考文档

- 主交接文档：`docs/three-module-platform-handoff-plan.md`
- 阶段 A 文档：`docs/phase-a-phone-binding-implementation.md`
- 阶段 B 文档：`docs/phase-b-classroom-web-integration.md`
- API 代码：`app/api/v1/classroom.py`
- 模型定义：`app/models.py`（第 404-485 行）

---

**文档版本：** 1.0  
**最后更新：** 2026-06-10  
**实施者：** Claude (Kiro)  
**审核状态：** 待审核
