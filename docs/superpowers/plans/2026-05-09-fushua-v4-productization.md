# 付刷 V4 产品化升级 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将付刷从功能原型升级为可投入真实教学场景的产品，补全教师端批量管理、学生端学习体验、管理员后台和数据导出等关键能力。

**Architecture:** 在现有 FastAPI + Jinja2 + SQLAlchemy + SQLite 架构上扩展。新增模型字段和表用 Alembic 迁移；新功能以路由模块形式挂载；模板复用 base.html 布局。批量操作使用临时文件 + 事务保证原子性；统计查询使用 SQLAlchemy 聚合函数避免 N+1。

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2, SQLite/PostgreSQL, openpyxl (Excel 读写), reportlab (PDF), python-csv (标准库)

---

## 文件结构

### 新增文件
| 文件 | 职责 |
|------|------|
| `app/routers/admin.py` | 管理员后台路由 |
| `app/templates/teacher/student_import.html` | 学生批量导入页 |
| `app/templates/teacher/assignment_detail.html` | 作业完成看板 |
| `app/templates/teacher/batch_edit.html` | 题目批量管理页 |
| `app/templates/teacher/class_stats.html` | 班级维度统计 |
| `app/templates/teacher/import_preview.html` | 题库导入预览 |
| `app/templates/student/dashboard.html` | 今日学习页 |
| `app/templates/admin/index.html` | 管理员后台首页 |
| `app/templates/admin/users.html` | 用户管理页 |
| `app/templates/help.html` | 帮助中心 |
| `app/templates/teacher/parent_report.html` | 家长报告 |

### 修改文件
| 文件 | 变更 |
|------|------|
| `app/models.py` | 新增 MasteryRecord 模型；Assignment 增加 class_id 字段；User 增加 streak/achievement 字段 |
| `app/routers/teacher.py` | 新增批量导入、作业看板、批量管理、班级统计、导入预览、未完成提醒路由 |
| `app/routers/student.py` | 新增今日学习页、错题掌握状态、个性化推荐、学习成就路由 |
| `app/routers/assignment.py` | 新增作业完成详情、答案提交逻辑 |
| `app/routers/pages.py` | 新增帮助中心、反馈入口 |
| `app/main.py` | 注册 admin 路由、全局模板变量增加 feedback |
| `app/templates/base.html` | 导航增加帮助/反馈入口、管理员入口 |
| `requirements.txt` | 新增 openpyxl |

---

## Task 1: 学生批量导入

**Files:**
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/student_import.html`
- Test: `tests/test_student_import.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_student_import.py
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User, ClassGroup, ClassMember


class TestStudentImport:
    def test_import_csv_students(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher", "teacher")
        cls = ClassGroup(name="导入班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher", "teacher")
        csrf = get_csrf_token(client)
        csv_content = "username,display_name\nstu1,学生1\nstu2,学生2"
        resp = client.post(f"/teacher/classes/{cls.id}/import-students", data={
            "_csrf_token": csrf,
            "csv_data": csv_content,
        }, follow_redirects=True)
        assert "成功导入" in resp.text
        count = db_session.query(User).filter(User.role == "student", User.username.in_(["stu1", "stu2"])).count()
        assert count == 2

    def test_import_csv_duplicate_skipped(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher2", "teacher")
        create_test_user(db_session, "dupstu", "student")
        cls = ClassGroup(name="导入班2", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher2", "teacher")
        csrf = get_csrf_token(client)
        csv_content = "username,display_name\ndupstu,重复学生\nnewstu,新学生"
        resp = client.post(f"/teacher/classes/{cls.id}/import-students", data={
            "_csrf_token": csrf,
            "csv_data": csv_content,
        }, follow_redirects=True)
        assert "1" in resp.text  # 只导入1个
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_student_import.py -v`
Expected: FAIL

- [ ] **Step 3: 实现导入路由**

在 `app/routers/teacher.py` 添加：

```python
@router.get("/classes/{class_id}/import-students")
def import_students_page(request: Request, class_id: int, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        raise HTTPException(status_code=404)
    return request.app.state.templates.TemplateResponse(
        "teacher/student_import.html",
        {"request": request, "cls": cls},
    )


@router.post("/classes/{class_id}/import-students")
async def import_students(class_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        raise HTTPException(status_code=404)
    form = await request.form()
    csv_data = form.get("csv_data", "")
    import csv
    import io
    reader = csv.DictReader(io.StringIO(csv_data))
    imported = 0
    skipped = 0
    for row in reader:
        username = row.get("username", "").strip()
        display_name = row.get("display_name", "").strip()
        if not username:
            continue
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            skipped += 1
            if not existing.class_id:
                existing.class_id = cls.id
                existing.is_guest = False
                existing.guest_expires_at = None
                member_exists = db.query(ClassMember).filter(ClassMember.class_id == cls.id, ClassMember.user_id == existing.id).first()
                if not member_exists:
                    db.add(ClassMember(class_id=cls.id, user_id=existing.id))
            continue
        default_pwd = "abc123"
        user = User(
            username=username,
            password_hash=User.hash_password(default_pwd),
            role="student",
            display_name=display_name or username,
            class_id=cls.id,
        )
        db.add(user)
        db.flush()
        db.add(ClassMember(class_id=cls.id, user_id=user.id))
        imported += 1
    db.commit()
    return request.app.state.templates.TemplateResponse(
        "teacher/student_import.html",
        {"request": request, "cls": cls, "imported": imported, "skipped": skipped},
    )
```

- [ ] **Step 4: 创建导入页面模板**

创建 `app/templates/teacher/student_import.html`，包含 CSV 文本框、格式说明、导入结果展示。

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_student_import.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: 学生批量CSV导入"
```

---

## Task 2: 作业完成看板

**Files:**
- Modify: `app/routers/assignment.py`
- Create: `app/templates/teacher/assignment_detail.html`
- Test: `tests/test_assignment_dashboard.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_assignment_dashboard.py
from tests.conftest import create_test_user, create_test_question, get_csrf_token, register_and_login
from app.models import Assignment, AssignmentRecord


class TestAssignmentDashboard:
    def test_assignment_detail_shows_stats(self, client, db_session):
        teacher = create_test_user(db_session, "dashteacher", "teacher")
        student = create_test_user(db_session, "dashstudent", "student")
        q = create_test_question(db_session, created_by=teacher.id)
        assignment = Assignment(title="看板作业", question_ids=str(q.id), created_by=teacher.id)
        db_session.add(assignment)
        db_session.commit()
        register_and_login(client, "dashteacher", "teacher")
        resp = client.get(f"/teacher/assignments/{assignment.id}", follow_redirects=True)
        assert resp.status_code == 200
        assert "看板作业" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_assignment_dashboard.py -v`
Expected: FAIL

- [ ] **Step 3: 添加 Assignment.class_id 字段到模型**

在 `app/models.py` 的 Assignment 类中添加：
```python
class_id = Column(Integer, nullable=True, index=True)
```
同时修改创建作业时自动设置 class_id。

- [ ] **Step 4: 实现作业看板路由**

在 `app/routers/assignment.py` 添加：

```python
@router.get("/teacher/assignments/{assignment_id}")
def assignment_detail(assignment_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.created_by == user_id).first()
    if not assignment:
        raise HTTPException(status_code=404)
    q_ids = [int(x) for x in assignment.question_ids.split(",") if x.strip().isdigit()]
    questions = db.query(Question).filter(Question.id.in_(q_ids)).all()
    q_map = {q.id: q for q in questions}

    if assignment.class_id:
        members = db.query(User).join(ClassMember).filter(ClassMember.class_id == assignment.class_id).all()
    else:
        members = []
    member_ids = [m.id for m in members]

    completed_records = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id,
        AssignmentRecord.completed == True,
    ).all()
    completed_user_ids = set(r.user_id for r in completed_records)
    completed_count = len(completed_user_ids & set(member_ids)) if member_ids else len(completed_user_ids)
    total_count = len(members) if members else 0

    all_records = db.query(Record).filter(
        Record.question_id.in_(q_ids),
        Record.user_id.in_(member_ids) if member_ids else Record.user_id > 0,
    ).all()

    q_stats = {}
    for qid in q_ids:
        q_records = [r for r in all_records if r.question_id == qid]
        correct = sum(1 for r in q_records if r.is_correct)
        q_stats[qid] = {"total": len(q_records), "correct": correct, "rate": round(correct / len(q_records) * 100, 1) if q_records else 0}

    avg_rate = 0
    if q_stats:
        rates = [s["rate"] for s in q_stats.values()]
        avg_rate = round(sum(rates) / len(rates), 1)

    high_error = sorted(q_stats.items(), key=lambda x: x[1]["rate"])[:5]

    return request.app.state.templates.TemplateResponse(
        "teacher/assignment_detail.html",
        {
            "request": request,
            "assignment": assignment,
            "questions": questions,
            "q_map": q_map,
            "completed_count": completed_count,
            "total_count": total_count,
            "avg_rate": avg_rate,
            "high_error": high_error,
            "q_stats": q_stats,
            "completed_user_ids": completed_user_ids,
            "members": members,
        },
    )
```

- [ ] **Step 5: 创建看板模板**

创建 `app/templates/teacher/assignment_detail.html`，展示完成人数/未完成人数/平均正确率/高频错题/学生完成列表。

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_assignment_dashboard.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: 作业完成看板"
```

---

## Task 3: 未完成提醒

**Files:**
- Modify: `app/routers/assignment.py`
- Test: `tests/test_assignment_reminder.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_assignment_reminder.py
from tests.conftest import create_test_user, create_test_question, get_csrf_token, register_and_login
from app.models import Assignment, Notification


class TestAssignmentReminder:
    def test_send_reminder_creates_notifications(self, client, db_session):
        teacher = create_test_user(db_session, "remindteacher", "teacher")
        student = create_test_user(db_session, "remindstudent", "student")
        q = create_test_question(db_session, created_by=teacher.id)
        assignment = Assignment(title="提醒作业", question_ids=str(q.id), created_by=teacher.id)
        db_session.add(assignment)
        db_session.commit()
        register_and_login(client, "remindteacher", "teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/assignments/{assignment.id}/remind", data={
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        notif = db_session.query(Notification).filter(Notification.user_id == student.id).first()
        assert notif is not None
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现提醒路由**

在 `app/routers/assignment.py` 添加：

```python
@router.post("/teacher/assignments/{assignment_id}/remind")
async def send_reminder(assignment_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.created_by == user_id).first()
    if not assignment:
        raise HTTPException(status_code=404)
    completed_records = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id, AssignmentRecord.completed == True
    ).all()
    completed_user_ids = set(r.user_id for r in completed_records)
    if assignment.class_id:
        members = db.query(User).join(ClassMember).filter(ClassMember.class_id == assignment.class_id).all()
    else:
        members = []
    reminded = 0
    for m in members:
        if m.id not in completed_user_ids:
            db.add(Notification(
                user_id=m.id,
                title="作业提醒",
                content=f"您有一份作业「{assignment.title}」尚未完成，请尽快完成。",
            ))
            reminded += 1
    db.commit()
    return request.app.state.templates.TemplateResponse(
        "teacher/assignment_detail.html",
        {"request": request, "assignment": assignment, "questions": [], "q_map": {},
         "completed_count": 0, "total_count": len(members), "avg_rate": 0,
         "high_error": [], "q_stats": {}, "completed_user_ids": completed_user_ids,
         "members": members, "reminded": reminded},
    )
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: 作业未完成站内提醒"
```

---

## Task 4: 题库导入预览

**Files:**
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/import_preview.html`
- Test: `tests/test_import_preview.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_import_preview.py
from tests.conftest import create_test_user, get_csrf_token, register_and_login


class TestImportPreview:
    def test_preview_shows_rows_and_errors(self, client, db_session):
        teacher = create_test_user(db_session, "prevteacher", "teacher")
        register_and_login(client, "prevteacher", "teacher")
        csrf = get_csrf_token(client)
        csv_content = "subject,q_type,content,answer\n数学,choice,1+1=,2\n,choice,缺科目,A\n数学,choice,重复题,2"
        resp = client.post("/teacher/questions/import-preview", data={
            "_csrf_token": csrf,
            "csv_data": csv_content,
        }, follow_redirects=True)
        assert "1+1=" in resp.text
        assert "缺科目" in resp.text or "错误" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现预览路由**

在 `app/routers/teacher.py` 添加 `/teacher/questions/import-preview` POST 路由，解析 CSV 前N行，校验必填字段（subject/content/answer），标记错误行和重复题，返回预览数据。

- [ ] **Step 4: 创建预览模板**

创建 `app/templates/teacher/import_preview.html`，展示前20行预览、错误行标红、重复题提示、确认导入按钮。

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: 题库导入预览"
```

---

## Task 5: 题目批量管理

**Files:**
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/batch_edit.html`
- Test: `tests/test_batch_edit.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_batch_edit.py
from tests.conftest import create_test_user, create_test_question, get_csrf_token, register_and_login
from app.models import Question


class TestBatchEdit:
    def test_batch_change_difficulty(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher", "teacher")
        q1 = create_test_question(db_session, content="Q1", difficulty=1, created_by=teacher.id)
        q2 = create_test_question(db_session, content="Q2", difficulty=1, created_by=teacher.id)
        register_and_login(client, "batchteacher", "teacher")
        csrf = get_csrf_token(client)
        resp = client.post("/teacher/questions/batch-edit", data={
            "_csrf_token": csrf,
            "question_ids": f"{q1.id},{q2.id}",
            "action": "difficulty",
            "value": "3",
        }, follow_redirects=True)
        db_session.expire_all()
        assert db_session.query(Question).filter(Question.id == q1.id).first().difficulty == 3
        assert db_session.query(Question).filter(Question.id == q2.id).first().difficulty == 3

    def test_batch_delete(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher2", "teacher")
        q1 = create_test_question(db_session, content="D1", created_by=teacher.id)
        q2 = create_test_question(db_session, content="D2", created_by=teacher.id)
        register_and_login(client, "batchteacher2", "teacher")
        csrf = get_csrf_token(client)
        resp = client.post("/teacher/questions/batch-edit", data={
            "_csrf_token": csrf,
            "question_ids": f"{q1.id},{q2.id}",
            "action": "delete",
        }, follow_redirects=True)
        assert db_session.query(Question).filter(Question.id.in_([q1.id, q2.id])).count() == 0
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现批量操作路由**

在 `app/routers/teacher.py` 添加 `/teacher/questions/batch-edit` POST 路由，支持 action: difficulty/semester/chapter/bank/move/delete，对选中的 question_ids 批量更新。

- [ ] **Step 4: 修改题目列表模板**

在 `app/templates/teacher/questions.html` 添加复选框和批量操作栏。

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: 题目批量管理"
```

---

## Task 6: 班级维度统计

**Files:**
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/class_stats.html`
- Test: `tests/test_class_stats.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_class_stats.py
from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import ClassGroup, ClassMember, Record


class TestClassStats:
    def test_class_stats_accessible(self, client, db_session):
        teacher = create_test_user(db_session, "statsteacher", "teacher")
        cls = ClassGroup(name="统计班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "statsteacher", "teacher")
        resp = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=True)
        assert resp.status_code == 200
        assert "统计班" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现班级统计路由**

在 `app/routers/teacher.py` 添加 `/teacher/classes/{class_id}/stats` GET 路由，查询班级成员的答题记录聚合：正确率趋势（按天）、薄弱章节（按 subject+chapter 聚合正确率最低）、学生排名（按正确率）、进步榜（对比前后半段正确率）、未练习名单。

- [ ] **Step 4: 创建统计模板**

创建 `app/templates/teacher/class_stats.html`，展示正确率趋势图（简单 CSS 柱状图）、薄弱章节列表、学生排名表、进步榜、未练习名单。

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: 班级维度统计"
```

---

## Task 7: 今日学习页（学生首页）

**Files:**
- Modify: `app/routers/student.py`
- Create: `app/templates/student/dashboard.html`
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dashboard.py
from tests.conftest import create_test_user, register_and_login


class TestDashboard:
    def test_dashboard_accessible(self, client, db_session):
        student = create_test_user(db_session, "dashstu", "student")
        register_and_login(client, "dashstu", "student")
        resp = client.get("/student/dashboard", follow_redirects=True)
        assert resp.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现今日学习页路由**

在 `app/routers/student.py` 添加 `/student/dashboard` GET 路由，聚合：今日作业（未完成的 Assignment）、推荐练习（薄弱科目题目）、错题复习数量、今日完成进度（今日 Record 数 / StudyPlan.daily_goal）。

- [ ] **Step 4: 创建今日学习模板**

创建 `app/templates/student/dashboard.html`，卡片式布局展示：今日作业、推荐练习、错题复习、完成进度。

- [ ] **Step 5: 修改首页重定向**

在 `app/routers/pages.py` 中，登录学生访问 `/` 时重定向到 `/student/dashboard`。

- [ ] **Step 6: 运行测试确认通过**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: 学生今日学习页"
```

---

## Task 8: 错题掌握状态

**Files:**
- Modify: `app/models.py` (新增 MasteryRecord)
- Modify: `app/routers/student.py`
- Modify: `app/templates/student/mistakes.html`
- Test: `tests/test_mastery.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_mastery.py
from tests.conftest import create_test_user, create_test_question
from app.models import MasteryRecord


class TestMastery:
    def test_mastery_record_model(self, client, db_session):
        student = create_test_user(db_session, "maststu", "student")
        q = create_test_question(db_session)
        m = MasteryRecord(user_id=student.id, question_id=q.id, status="unmastered", consecutive_correct=0)
        db_session.add(m)
        db_session.commit()
        assert m.id is not None
        assert m.status == "unmastered"
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 新增 MasteryRecord 模型**

在 `app/models.py` 添加：

```python
class MasteryRecord(Base):
    __tablename__ = "mastery_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    status = Column(String(20), default="unmastered")  # unmastered / reviewing / mastered
    consecutive_correct = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_mastery_user_question"),
    )
```

- [ ] **Step 4: 在答题时更新掌握状态**

修改 `app/routers/student.py` 中的 `submit_practice` 路由，答题后更新 MasteryRecord：答对 consecutive_correct+1，连续3次答对转 mastered；答错重置为 unmastered。

- [ ] **Step 5: 修改错题本展示**

修改 `app/templates/student/mistakes.html`，按掌握状态分组展示（未掌握/复习中/已掌握），支持筛选。

- [ ] **Step 6: 运行测试确认通过**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: 错题掌握状态"
```

---

## Task 9: 个性化推荐

**Files:**
- Modify: `app/routers/student.py`

- [ ] **Step 1: 增强推荐算法**

修改 `_smart_select` 函数，优先推荐：未掌握错题 > 薄弱章节（正确率<60%）> 适合难度（根据历史正确率调整）> 随机补充。权重分配：错题40%、薄弱30%、难度适配20%、随机10%。

- [ ] **Step 2: 在今日学习页展示推荐**

在 `/student/dashboard` 路由中调用增强后的推荐函数，展示推荐题目列表。

- [ ] **Step 3: 提交**

```bash
git add -A && git commit -m "feat: 个性化推荐算法"
```

---

## Task 10: 学习成就

**Files:**
- Modify: `app/models.py` (User 新增字段)
- Modify: `app/routers/student.py`
- Modify: `app/templates/student/profile.html`
- Test: `tests/test_achievement.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_achievement.py
from tests.conftest import create_test_user, register_and_login


class TestAchievement:
    def test_profile_shows_streak(self, client, db_session):
        student = create_test_user(db_session, "achiestu", "student")
        register_and_login(client, "achiestu", "student")
        resp = client.get("/student/profile", follow_redirects=True)
        assert resp.status_code == 200
```

- [ ] **Step 2: 运行测试确认通过**（应已通过，确保不破坏）

- [ ] **Step 3: 在 profile 路由中添加成就数据**

在 `/student/profile` 路由中计算：连续学习天数（已有 streak 逻辑）、今日完成目标（今日 Record 数 vs daily_goal）、正确率提升（对比前后半段）、章节徽章（正确率>80%的章节）。

- [ ] **Step 4: 修改 profile 模板**

在 `app/templates/student/profile.html` 中添加成就展示区域：连续学习天数、今日目标进度条、正确率变化、章节徽章。

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: 学习成就展示"
```

---

## Task 11: 管理员后台

**Files:**
- Create: `app/routers/admin.py`
- Create: `app/templates/admin/index.html`
- Create: `app/templates/admin/users.html`
- Modify: `app/main.py`
- Test: `tests/test_admin.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_admin.py
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User


class TestAdmin:
    def test_admin_page_requires_admin(self, client, db_session):
        teacher = create_test_user(db_session, "nonadmin", "teacher")
        register_and_login(client, "nonadmin", "teacher")
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code in (303, 403)

    def test_admin_can_reset_password(self, client, db_session):
        admin = create_test_user(db_session, "admintest", "teacher", is_admin=True)
        student = create_test_user(db_session, "resetstu", "student")
        register_and_login(client, "admintest", "teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{student.id}/reset-password", data={
            "_csrf_token": csrf,
            "new_password": "newpass123",
        }, follow_redirects=True)
        db_session.expire_all()
        u = db_session.query(User).filter(User.username == "resetstu").first()
        assert User.verify_password(u.password_hash, "newpass123")
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 创建管理员路由**

创建 `app/routers/admin.py`，包含：
- `GET /admin` — 管理员首页（用户数、班级数、题目数概览）
- `GET /admin/users` — 用户列表（搜索、按角色筛选）
- `POST /admin/users/{id}/reset-password` — 重置密码
- `POST /admin/users/{id}/toggle-disable` — 禁用/启用账号（User 新增 is_disabled 字段）
- `POST /admin/cleanup-guests` — 清理过期游客

- [ ] **Step 4: User 模型新增 is_disabled 字段**

在 `app/models.py` 的 User 类添加：
```python
is_disabled = Column(Boolean, default=False)
```

- [ ] **Step 5: 在 main.py 注册 admin 路由**

```python
from app.routers import admin
app.include_router(admin.router)
```

- [ ] **Step 6: 创建管理员模板**

创建 `app/templates/admin/index.html` 和 `app/templates/admin/users.html`。

- [ ] **Step 7: 在 base.html 添加管理员入口**

在导航栏中，`is_admin` 为 True 时显示"管理"链接。

- [ ] **Step 8: 运行测试确认通过**

- [ ] **Step 9: 提交**

```bash
git add -A && git commit -m "feat: 管理员后台"
```

---

## Task 12: 反馈入口

**Files:**
- Modify: `app/models.py` (新增 Feedback)
- Modify: `app/main.py`
- Modify: `app/templates/base.html`
- Test: `tests/test_feedback.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_feedback.py
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import Feedback


class TestFeedback:
    def test_submit_feedback(self, client, db_session):
        student = create_test_user(db_session, "fbstu", "student")
        register_and_login(client, "fbstu", "student")
        csrf = get_csrf_token(client)
        resp = client.post("/feedback", data={
            "_csrf_token": csrf,
            "content": "这个功能很好用",
        }, follow_redirects=True)
        assert resp.status_code == 200
        fb = db_session.query(Feedback).first()
        assert fb is not None
        assert fb.content == "这个功能很好用"
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 新增 Feedback 模型**

```python
class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    role = Column(String(10), default="")
    page_path = Column(String(500), default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 添加反馈路由**

在 `app/main.py` 或新建 `app/routers/feedback.py` 添加 `POST /feedback` 路由，自动附带 user_id、role、page_path。

- [ ] **Step 5: 在 base.html 添加反馈入口**

在页面底部添加"反馈问题"按钮，点击弹出简单表单（content 文本框 + 提交）。

- [ ] **Step 6: 运行测试确认通过**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: 反馈入口"
```

---

## Task 13: 帮助中心

**Files:**
- Modify: `app/routers/pages.py`
- Create: `app/templates/help.html`

- [ ] **Step 1: 添加帮助中心路由**

在 `app/routers/pages.py` 添加 `GET /help` 路由。

- [ ] **Step 2: 创建帮助中心模板**

创建 `app/templates/help.html`，按角色展示：教师帮助（建班、导入题目、布置作业、看统计、处理学生忘记密码）、学生帮助（注册、做题、查看错题）。

- [ ] **Step 3: 在 base.html 添加帮助链接**

在导航栏添加"帮助"链接。

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: 帮助中心"
```

---

## Task 14: 数据导出

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `requirements.txt` (新增 openpyxl)
- Test: `tests/test_export.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_export.py
from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import ClassGroup, ClassMember, Record


class TestExport:
    def test_export_class_report(self, client, db_session):
        teacher = create_test_user(db_session, "expteacher", "teacher")
        cls = ClassGroup(name="导出班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "expteacher", "teacher")
        resp = client.get(f"/teacher/classes/{cls.id}/export/excel", follow_redirects=False)
        assert resp.status_code == 200
        assert "spreadsheet" in resp.headers.get("content-type", "") or "xlsx" in resp.headers.get("content-disposition", "")
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 添加 openpyxl 依赖**

在 `requirements.txt` 添加 `openpyxl==3.1.5`。

- [ ] **Step 4: 实现导出路由**

在 `app/routers/teacher.py` 添加：
- `GET /teacher/classes/{class_id}/export/excel` — 班级报告 Excel
- `GET /teacher/students/{student_id}/export/excel` — 学生报告 Excel
- `GET /teacher/questions/export` — 题库导出 Excel
- `GET /teacher/assignments/{assignment_id}/export/excel` — 作业完成情况 Excel

使用 openpyxl 生成 xlsx 文件，StreamingResponse 返回。

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: 数据导出Excel"
```

---

## Task 15: 家长报告

**Files:**
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/parent_report.html`

- [ ] **Step 1: 添加家长报告路由**

在 `app/routers/teacher.py` 添加 `GET /teacher/students/{student_id}/parent-report` 路由，聚合：本周做题数、正确率、薄弱点（正确率<60%的章节）、建议练习方向。

- [ ] **Step 2: 创建家长报告模板**

创建 `app/templates/teacher/parent_report.html`，简洁卡片式布局，适合打印。

- [ ] **Step 3: 添加 PDF 导出**

复用 reportlab 生成 PDF 版家长报告。

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: 家长报告"
```

---

## 执行顺序

按依赖关系和优先级排序：

1. **Task 1** — 学生批量导入（教师端最急需）
2. **Task 4** — 题库导入预览（防止导入错误数据）
3. **Task 5** — 题目批量管理（管理效率）
4. **Task 2** — 作业完成看板（教学反馈）
5. **Task 3** — 未完成提醒（作业管理闭环）
6. **Task 6** — 班级维度统计（教学分析）
7. **Task 7** — 今日学习页（学生体验核心）
8. **Task 8** — 错题掌握状态（学习效果追踪）
9. **Task 9** — 个性化推荐（智能学习）
10. **Task 10** — 学习成就（激励）
11. **Task 11** — 管理员后台（运维）
12. **Task 12** — 反馈入口（产品迭代）
13. **Task 13** — 帮助中心（用户引导）
14. **Task 14** — 数据导出（数据利用）
15. **Task 15** — 家长报告（家校沟通）
