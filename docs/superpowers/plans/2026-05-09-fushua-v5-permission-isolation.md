# 付刷 V5 权限隔离与运维基线 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复正式上线前最关键的安全问题——多教师数据隔离、作业班级化、输入校验、审计日志和 CI 基线——使产品具备进入真实班级灰度试用的安全基础。

**Architecture:** 在现有 FastAPI + Jinja2 + SQLAlchemy 架构上修补权限漏洞。新增权限 helper 函数统一校验逻辑；新增 AuditLog 模型记录关键操作；新增 GitHub Actions CI 配置文件。所有改动沿用现有路由结构和模板风格。

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2, SQLite/PostgreSQL, GitHub Actions (CI), pytest

---

## 现状差距分析

| 路线图阶段 | 要求 | 当前状态 |
|-----------|------|---------|
| 1.2 教师跨班越权 | 教师只能查看本班学生 | ❌ `/teacher/students/{id}` 无班级校验 |
| 1.3 作业班级化 | 学生只看本班作业 | ❌ 学生作业列表未按 class_id 过滤 |
| 1.3 作业提交校验 | 学生只能提交本班作业 | ❌ 提交作业无班级校验 |
| 1.4 题库删除校验 | 删除题库需校验归属 | ❌ 删除题库未检查 created_by |
| 1.5 班级成员一致性 | users.class_id 与 class_members 同步 | ❌ 移出班级未清空 class_id |
| 1.6 输入校验 | 非法数字不触发 500 | ❌ 多处直接 int() 无异常处理 |
| 2.3 健康检查增强 | /health 反映数据库状态 | ❌ 只返回 {"status":"ok"} |
| 2.4 GitHub Actions CI | push 自动跑测试 | ❌ 无 CI 配置 |
| 3.3 操作审计 | 关键操作可追溯 | ❌ 无 AuditLog 模型 |

---

## 文件结构

### 新增文件
| 文件 | 职责 |
|------|------|
| `app/routers/permissions.py` | 权限 helper 函数（teacher_owns_student, teacher_owns_bank 等） |
| `app/utils/validation.py` | 输入校验 helper（parse_int, parse_float） |
| `.github/workflows/ci.yml` | GitHub Actions CI 配置 |
| `tests/test_permissions.py` | 权限隔离测试 |
| `tests/test_input_validation.py` | 输入校验测试 |
| `tests/test_audit.py` | 审计日志测试 |

### 修改文件
| 文件 | 变更 |
|------|------|
| `app/models.py` | 新增 AuditLog 模型 |
| `app/routers/teacher.py` | 引用权限 helper；修复删除题库校验；替换直接 int() 调用 |
| `app/routers/assignment.py` | 学生作业列表按 class_id 过滤；提交作业校验班级归属 |
| `app/routers/classgroup.py` | 移出学生时同步清空 users.class_id |
| `app/routers/admin.py` | 关键操作写审计日志 |
| `app/main.py` | /health 增加数据库连接检查 |
| `app/routers/student.py` | 替换直接 int() 调用 |

---

## Task 1: 权限 Helper 函数

**Files:**
- Create: `app/routers/permissions.py`
- Test: `tests/test_permissions.py`

- [ ] **Step 1: 写失败测试**

```python
from tests.conftest import create_test_user, register_and_login
from app.models import ClassGroup, ClassMember, User, Question, QuestionBank


class TestPermissionHelpers:
    def test_teacher_owns_student_same_class(self, client, db_session):
        teacher = create_test_user(db_session, "ownteacher1", "teacher")
        student = create_test_user(db_session, "ownstu1", "student")
        cls = ClassGroup(name="归属班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()
        from app.routers.permissions import teacher_owns_student
        assert teacher_owns_student(db_session, teacher.id, student.id) is True

    def test_teacher_owns_student_different_class(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacherA1", "teacher")
        teacher_b = create_test_user(db_session, "teacherB1", "teacher")
        student = create_test_user(db_session, "otherstu1", "student")
        cls_b = ClassGroup(name="B班", created_by=teacher_b.id)
        db_session.add(cls_b)
        db_session.commit()
        student.class_id = cls_b.id
        db_session.add(ClassMember(class_id=cls_b.id, user_id=student.id))
        db_session.commit()
        from app.routers.permissions import teacher_owns_student
        assert teacher_owns_student(db_session, teacher_a.id, student.id) is False

    def test_teacher_owns_bank(self, client, db_session):
        teacher = create_test_user(db_session, "bankteacher1", "teacher")
        bank = QuestionBank(name="我的题库", created_by=teacher.id)
        db_session.add(bank)
        db_session.commit()
        from app.routers.permissions import teacher_owns_bank
        assert teacher_owns_bank(db_session, teacher.id, bank.id) is True

    def test_teacher_owns_bank_not_owner(self, client, db_session):
        teacher_a = create_test_user(db_session, "bankA1", "teacher")
        teacher_b = create_test_user(db_session, "bankB1", "teacher")
        bank = QuestionBank(name="B的题库", created_by=teacher_b.id)
        db_session.add(bank)
        db_session.commit()
        from app.routers.permissions import teacher_owns_bank
        assert teacher_owns_bank(db_session, teacher_a.id, bank.id) is False

    def test_teacher_owns_class(self, client, db_session):
        teacher = create_test_user(db_session, "classteacher1", "teacher")
        cls = ClassGroup(name="我的班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        from app.routers.permissions import teacher_owns_class
        assert teacher_owns_class(db_session, teacher.id, cls.id) is True

    def test_teacher_owns_class_not_owner(self, client, db_session):
        teacher_a = create_test_user(db_session, "clsA1", "teacher")
        teacher_b = create_test_user(db_session, "clsB1", "teacher")
        cls = ClassGroup(name="B的班", created_by=teacher_b.id)
        db_session.add(cls)
        db_session.commit()
        from app.routers.permissions import teacher_owns_class
        assert teacher_owns_class(db_session, teacher_a.id, cls.id) is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_permissions.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: 实现权限 helper**

创建 `app/routers/permissions.py`：

```python
from sqlalchemy.orm import Session
from app.models import ClassGroup, ClassMember, QuestionBank, User


def teacher_owns_student(db: Session, teacher_id: int, student_id: int) -> bool:
    teacher_classes = db.query(ClassGroup.id).filter(ClassGroup.created_by == teacher_id).subquery()
    return db.query(ClassMember).filter(
        ClassMember.class_id.in_(teacher_classes),
        ClassMember.user_id == student_id,
    ).first() is not None


def teacher_owns_bank(db: Session, teacher_id: int, bank_id: int) -> bool:
    return db.query(QuestionBank).filter(
        QuestionBank.id == bank_id,
        QuestionBank.created_by == teacher_id,
    ).first() is not None


def teacher_owns_class(db: Session, teacher_id: int, class_id: int) -> bool:
    return db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.created_by == teacher_id,
    ).first() is not None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_permissions.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: 权限helper函数(teacher_owns_student/bank/class)"
```

---

## Task 2: 修复教师跨班查看学生越权

**Files:**
- Modify: `app/routers/teacher.py` (学生详情路由)
- Modify: `app/routers/teacher.py` (学生PDF导出路由)
- Modify: `app/routers/teacher.py` (家长报告路由)
- Test: `tests/test_permissions.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_permissions.py` 追加：

```python
class TestTeacherStudentAccess:
    def test_teacher_cannot_view_other_class_student(self, client, db_session):
        teacher_a = create_test_user(db_session, "viewA1", "teacher")
        teacher_b = create_test_user(db_session, "viewB1", "teacher")
        student = create_test_user(db_session, "viewstu1", "student")
        cls_b = ClassGroup(name="B班学生", created_by=teacher_b.id)
        db_session.add(cls_b)
        db_session.commit()
        student.class_id = cls_b.id
        db_session.add(ClassMember(class_id=cls_b.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "viewA1", "teacher")
        resp = client.get(f"/teacher/students/{student.id}", follow_redirects=False)
        assert resp.status_code in (403, 404)

    def test_teacher_can_view_own_class_student(self, client, db_session):
        teacher = create_test_user(db_session, "viewOwn1", "teacher")
        student = create_test_user(db_session, "ownViewStu1", "student")
        cls = ClassGroup(name="我的班学生", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "viewOwn1", "teacher")
        resp = client.get(f"/teacher/students/{student.id}", follow_redirects=True)
        assert resp.status_code == 200

    def test_teacher_cannot_export_other_class_pdf(self, client, db_session):
        teacher_a = create_test_user(db_session, "pdfA1", "teacher")
        teacher_b = create_test_user(db_session, "pdfB1", "teacher")
        student = create_test_user(db_session, "pdfstu1", "student")
        cls_b = ClassGroup(name="B班PDF", created_by=teacher_b.id)
        db_session.add(cls_b)
        db_session.commit()
        student.class_id = cls_b.id
        db_session.add(ClassMember(class_id=cls_b.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "pdfA1", "teacher")
        resp = client.get(f"/teacher/students/{student.id}/export/pdf", follow_redirects=False)
        assert resp.status_code in (403, 404)

    def test_teacher_cannot_view_other_class_parent_report(self, client, db_session):
        teacher_a = create_test_user(db_session, "prA1", "teacher")
        teacher_b = create_test_user(db_session, "prB1", "teacher")
        student = create_test_user(db_session, "prstu1", "student")
        cls_b = ClassGroup(name="B班报告", created_by=teacher_b.id)
        db_session.add(cls_b)
        db_session.commit()
        student.class_id = cls_b.id
        db_session.add(ClassMember(class_id=cls_b.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "prA1", "teacher")
        resp = client.get(f"/teacher/students/{student.id}/parent-report", follow_redirects=False)
        assert resp.status_code in (403, 404)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_permissions.py::TestTeacherStudentAccess -v`
Expected: FAIL (teacher can currently view any student)

- [ ] **Step 3: 修改教师路由添加权限校验**

在 `app/routers/teacher.py` 中，找到学生详情路由（`/teacher/students/{student_id}`），在查询学生后添加：

```python
from app.routers.permissions import teacher_owns_student
```

在获取 student 对象后添加校验：

```python
if not teacher_owns_student(db, user_id, student_id):
    raise HTTPException(status_code=404)
```

同样修改：
- `/teacher/students/{student_id}/export/pdf` 路由
- `/teacher/students/{student_id}/parent-report` 路由
- `/teacher/students/{student_id}/parent-report/pdf` 路由
- `/teacher/students/{student_id}/export/excel` 路由

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_permissions.py::TestTeacherStudentAccess -v`
Expected: PASS

- [ ] **Step 5: 运行全量测试确认无回归**

Run: `pytest -v --tb=short -q`
Expected: ALL PASS

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "fix: 教师只能查看本班学生详情/PDF/报告"
```

---

## Task 3: 学生作业列表班级过滤

**Files:**
- Modify: `app/routers/assignment.py` (学生作业列表路由)
- Modify: `app/routers/assignment.py` (学生提交作业路由)
- Test: `tests/test_permissions.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_permissions.py` 追加：

```python
from app.models import Assignment


class TestAssignmentClassFilter:
    def test_student_only_sees_own_class_assignments(self, client, db_session):
        teacher_a = create_test_user(db_session, "asgnA1", "teacher")
        teacher_b = create_test_user(db_session, "asgnB1", "teacher")
        student = create_test_user(db_session, "asgnstu1", "student")
        cls_a = ClassGroup(name="A班作业", created_by=teacher_a.id)
        cls_b = ClassGroup(name="B班作业", created_by=teacher_b.id)
        db_session.add_all([cls_a, cls_b])
        db_session.commit()
        student.class_id = cls_a.id
        db_session.add(ClassMember(class_id=cls_a.id, user_id=student.id))
        db_session.commit()
        asgn_a = Assignment(title="A班作业", question_ids="1", created_by=teacher_a.id, class_id=cls_a.id)
        asgn_b = Assignment(title="B班作业", question_ids="1", created_by=teacher_b.id, class_id=cls_b.id)
        db_session.add_all([asgn_a, asgn_b])
        db_session.commit()
        register_and_login(client, "asgnstu1", "student")
        resp = client.get("/student/assignments", follow_redirects=True)
        assert "A班作业" in resp.text
        assert "B班作业" not in resp.text

    def test_student_cannot_submit_other_class_assignment(self, client, db_session):
        teacher_a = create_test_user(db_session, "subA1", "teacher")
        teacher_b = create_test_user(db_session, "subB1", "teacher")
        student = create_test_user(db_session, "substu1", "student")
        cls_a = ClassGroup(name="A班提交", created_by=teacher_a.id)
        cls_b = ClassGroup(name="B班提交", created_by=teacher_b.id)
        db_session.add_all([cls_a, cls_b])
        db_session.commit()
        student.class_id = cls_a.id
        db_session.add(ClassMember(class_id=cls_a.id, user_id=student.id))
        db_session.commit()
        from tests.conftest import create_test_question, get_csrf_token
        q = create_test_question(db_session, created_by=teacher_b.id)
        asgn_b = Assignment(title="B班提交作业", question_ids=str(q.id), created_by=teacher_b.id, class_id=cls_b.id)
        db_session.add(asgn_b)
        db_session.commit()
        register_and_login(client, "substu1", "student")
        csrf = get_csrf_token(client)
        resp = client.post(f"/student/assignments/{asgn_b.id}/complete", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code in (403, 404)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_permissions.py::TestAssignmentClassFilter -v`
Expected: FAIL

- [ ] **Step 3: 修改学生作业列表路由**

在 `app/routers/assignment.py` 中找到学生作业列表路由，添加 class_id 过滤：

```python
if user.class_id:
    assignments = db.query(Assignment).filter(
        Assignment.class_id == user.class_id
    ).order_by(Assignment.created_at.desc()).all()
else:
    assignments = db.query(Assignment).filter(
        Assignment.class_id.is_(None)
    ).order_by(Assignment.created_at.desc()).all()
```

- [ ] **Step 4: 修改学生提交作业路由**

在学生完成作业路由中，提交前校验学生属于该作业班级：

```python
if assignment.class_id:
    member = db.query(ClassMember).filter(
        ClassMember.class_id == assignment.class_id,
        ClassMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_permissions.py::TestAssignmentClassFilter -v`
Expected: PASS

- [ ] **Step 6: 运行全量测试确认无回归**

Run: `pytest -v --tb=short -q`
Expected: ALL PASS

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "fix: 学生只能查看和提交本班作业"
```

---

## Task 4: 题库删除归属校验

**Files:**
- Modify: `app/routers/teacher.py` (删除题库路由)
- Test: `tests/test_permissions.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_permissions.py` 追加：

```python
class TestBankDeletePermission:
    def test_teacher_cannot_delete_other_bank(self, client, db_session):
        teacher_a = create_test_user(db_session, "delA1", "teacher")
        teacher_b = create_test_user(db_session, "delB1", "teacher")
        bank = QuestionBank(name="B的题库删除", created_by=teacher_b.id)
        db_session.add(bank)
        db_session.commit()
        register_and_login(client, "delA1", "teacher")
        from tests.conftest import get_csrf_token
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/banks/{bank.id}/delete", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code in (403, 404)
        db_session.expire_all()
        assert db_session.query(QuestionBank).filter(QuestionBank.id == bank.id).first() is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_permissions.py::TestBankDeletePermission -v`
Expected: FAIL

- [ ] **Step 3: 修改删除题库路由**

在 `app/routers/teacher.py` 中找到删除题库路由，添加归属校验：

```python
from app.routers.permissions import teacher_owns_bank

bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
if not bank or not teacher_owns_bank(db, user_id, bank_id):
    raise HTTPException(status_code=404)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_permissions.py::TestBankDeletePermission -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "fix: 删除题库校验归属"
```

---

## Task 5: 班级成员一致性修复

**Files:**
- Modify: `app/routers/classgroup.py` (移出学生路由)
- Modify: `app/routers/classgroup.py` (添加学生路由)
- Test: `tests/test_permissions.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_permissions.py` 追加：

```python
class TestClassMembershipConsistency:
    def test_remove_student_clears_class_id(self, client, db_session):
        teacher = create_test_user(db_session, "removeteacher1", "teacher")
        student = create_test_user(db_session, "removestu1", "student")
        cls = ClassGroup(name="移出班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "removeteacher1", "teacher")
        from tests.conftest import get_csrf_token
        csrf = get_csrf_token(client)
        resp = client.post(f"/classes/{cls.id}/members/{student.id}/remove", data={
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        db_session.expire_all()
        s = db_session.query(User).filter(User.id == student.id).first()
        assert s.class_id is None

    def test_cannot_add_student_already_in_other_class(self, client, db_session):
        teacher_a = create_test_user(db_session, "addA1", "teacher")
        teacher_b = create_test_user(db_session, "addB1", "teacher")
        student = create_test_user(db_session, "addstu1", "student")
        cls_a = ClassGroup(name="A班添加", created_by=teacher_a.id)
        cls_b = ClassGroup(name="B班添加", created_by=teacher_b.id)
        db_session.add_all([cls_a, cls_b])
        db_session.commit()
        student.class_id = cls_a.id
        db_session.add(ClassMember(class_id=cls_a.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "addB1", "teacher")
        from tests.conftest import get_csrf_token
        csrf = get_csrf_token(client)
        resp = client.post(f"/classes/{cls_b.id}/members/add", data={
            "_csrf_token": csrf,
            "username": "addstu1",
        }, follow_redirects=True)
        db_session.expire_all()
        s = db_session.query(User).filter(User.id == student.id).first()
        assert s.class_id == cls_a.id
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_permissions.py::TestClassMembershipConsistency -v`
Expected: FAIL (class_id not cleared on remove)

- [ ] **Step 3: 修改移出学生路由**

在 `app/routers/classgroup.py` 中找到移出学生路由，在删除 ClassMember 后添加：

```python
student = db.query(User).filter(User.id == member.user_id).first()
if student and student.class_id == class_id:
    student.class_id = None
```

- [ ] **Step 4: 修改添加学生路由**

在添加学生路由中，检查学生是否已有其他班级：

```python
if student.class_id and student.class_id != class_id:
    return request.app.state.templates.TemplateResponse(
        "teacher/class_detail.html",
        {"request": request, "cls": cls, "error": f"学生 {username} 已在其他班级，请先移出原班级"},
    )
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_permissions.py::TestClassMembershipConsistency -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "fix: 班级成员一致性-移出清空class_id/添加检查已有班级"
```

---

## Task 6: 输入校验 Helper

**Files:**
- Create: `app/utils/validation.py`
- Test: `tests/test_input_validation.py`

- [ ] **Step 1: 写失败测试**

```python
from app.utils.validation import parse_int, parse_float


class TestParseInt:
    def test_valid_integer(self):
        assert parse_int("5") == 5

    def test_valid_integer_with_default(self):
        assert parse_int("abc", default=0) == 0

    def test_valid_integer_with_min(self):
        assert parse_int("0", min_value=1, default=1) == 1

    def test_valid_integer_with_max(self):
        assert parse_int("10", max_value=5, default=5) == 5

    def test_none_returns_default(self):
        assert parse_int(None, default=3) == 3

    def test_empty_string_returns_default(self):
        assert parse_int("", default=2) == 2

    def test_float_string_returns_default(self):
        assert parse_int("3.5", default=0) == 0

    def test_valid_range(self):
        assert parse_int("3", min_value=1, max_value=5) == 3


class TestParseFloat:
    def test_valid_float(self):
        assert parse_float("3.5") == 3.5

    def test_invalid_float(self):
        assert parse_float("abc", default=0.0) == 0.0

    def test_none_returns_default(self):
        assert parse_float(None, default=1.0) == 1.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_input_validation.py -v`
Expected: FAIL

- [ ] **Step 3: 实现校验 helper**

创建 `app/utils/validation.py`：

```python
def parse_int(value, default=None, min_value=None, max_value=None):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    try:
        result = int(value)
    except (ValueError, TypeError):
        return default
    if min_value is not None and result < min_value:
        return default
    if max_value is not None and result > max_value:
        return default
    return result


def parse_float(value, default=None, min_value=None, max_value=None):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    try:
        result = float(value)
    except (ValueError, TypeError):
        return default
    if min_value is not None and result < min_value:
        return default
    if max_value is not None and result > max_value:
        return default
    return result
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_input_validation.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: 输入校验helper(parse_int/parse_float)"
```

---

## Task 7: 替换直接 int() 调用

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `app/routers/assignment.py`
- Modify: `app/routers/student.py`
- Test: `tests/test_input_validation.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_input_validation.py` 追加：

```python
from tests.conftest import create_test_user, register_and_login, get_csrf_token


class TestInputValidationInRoutes:
    def test_invalid_difficulty_no_500(self, client, db_session):
        teacher = create_test_user(db_session, "valteacher1", "teacher")
        register_and_login(client, "valteacher1", "teacher")
        csrf = get_csrf_token(client)
        resp = client.post("/teacher/questions/new", data={
            "_csrf_token": csrf,
            "subject": "数学",
            "content": "测试题",
            "answer": "A",
            "q_type": "choice",
            "difficulty": "abc",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert "500" not in resp.text

    def test_invalid_daily_goal_no_500(self, client, db_session):
        student = create_test_user(db_session, "valstu1", "student")
        register_and_login(client, "valstu1", "student")
        csrf = get_csrf_token(client)
        resp = client.post("/student/study-plan", data={
            "_csrf_token": csrf,
            "daily_goal": "xyz",
            "subject": "数学",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert "500" not in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_input_validation.py::TestInputValidationInRoutes -v`
Expected: FAIL (500 error)

- [ ] **Step 3: 替换 teacher.py 中的直接 int() 调用**

在 `app/routers/teacher.py` 顶部添加：

```python
from app.utils.validation import parse_int
```

逐一替换以下模式：

| 原代码 | 替换为 |
|--------|--------|
| `int(form.get("difficulty", "2"))` | `parse_int(form.get("difficulty"), default=2, min_value=1, max_value=5)` |
| `int(form.get("sort_order", "0"))` | `parse_int(form.get("sort_order"), default=0)` |
| `int(bank_id)` | `parse_int(bank_id, default=None)` |
| `int(bank_id_val) if bank_id_val else None` | `parse_int(bank_id_val, default=None)` |
| `int(class_id)` | `parse_int(class_id, default=None)` |

- [ ] **Step 4: 替换 assignment.py 中的直接 int() 调用**

在 `app/routers/assignment.py` 顶部添加：

```python
from app.utils.validation import parse_int
```

替换 `int(x.strip())` 为带异常处理的版本：

```python
q_ids = []
for x in assignment.question_ids.split(","):
    val = parse_int(x.strip())
    if val is not None:
        q_ids.append(val)
```

- [ ] **Step 5: 替换 student.py 中的直接 int() 调用**

在 `app/routers/student.py` 顶部添加：

```python
from app.utils.validation import parse_int
```

替换 `int(qid_str)` 为 `parse_int(qid_str, default=None)`，跳过 None 值。

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_input_validation.py -v`
Expected: PASS

- [ ] **Step 7: 运行全量测试确认无回归**

Run: `pytest -v --tb=short -q`
Expected: ALL PASS

- [ ] **Step 8: 提交**

```bash
git add -A && git commit -m "fix: 替换直接int()为parse_int防止500错误"
```

---

## Task 8: 审计日志模型

**Files:**
- Modify: `app/models.py`
- Test: `tests/test_audit.py`

- [ ] **Step 1: 写失败测试**

```python
from app.models import AuditLog


class TestAuditLog:
    def test_create_audit_log(self, db_session):
        log = AuditLog(
            actor_id=1,
            action="reset_password",
            target_type="user",
            target_id=2,
            detail="重置用户密码",
        )
        db_session.add(log)
        db_session.commit()
        assert log.id is not None
        assert log.action == "reset_password"

    def test_query_audit_logs_by_action(self, db_session):
        log1 = AuditLog(actor_id=1, action="reset_password", target_type="user", target_id=2)
        log2 = AuditLog(actor_id=1, action="toggle_disable", target_type="user", target_id=3)
        db_session.add_all([log1, log2])
        db_session.commit()
        results = db_session.query(AuditLog).filter(AuditLog.action == "reset_password").all()
        assert len(results) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_audit.py -v`
Expected: FAIL

- [ ] **Step 3: 新增 AuditLog 模型**

在 `app/models.py` 中添加：

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50), default="")
    target_id = Column(Integer, nullable=True)
    detail = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_audit.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: AuditLog审计日志模型"
```

---

## Task 9: 管理员操作写审计日志

**Files:**
- Modify: `app/routers/admin.py`
- Test: `tests/test_audit.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_audit.py` 追加：

```python
from tests.conftest import create_test_user, register_and_login, get_csrf_token


class TestAdminAuditLog:
    def test_reset_password_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "auditadmin1", "teacher", is_admin=True)
        student = create_test_user(db_session, "auditstu1", "student")
        register_and_login(client, "auditadmin1", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/admin/users/{student.id}/reset-password", data={
            "_csrf_token": csrf,
        }, follow_redirects=True)
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "reset_password",
            AuditLog.target_id == student.id,
        ).first()
        assert log is not None
        assert log.actor_id == admin.id

    def test_toggle_disable_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "auditadmin2", "teacher", is_admin=True)
        student = create_test_user(db_session, "auditstu2", "student")
        register_and_login(client, "auditadmin2", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/admin/users/{student.id}/toggle-disable", data={
            "_csrf_token": csrf,
        }, follow_redirects=True)
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "toggle_disable",
            AuditLog.target_id == student.id,
        ).first()
        assert log is not None

    def test_cleanup_guests_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "auditadmin3", "teacher", is_admin=True)
        register_and_login(client, "auditadmin3", "teacher")
        csrf = get_csrf_token(client)
        client.post("/admin/cleanup-guests", data={
            "_csrf_token": csrf,
        }, follow_redirects=True)
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "cleanup_guests",
        ).first()
        assert log is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_audit.py::TestAdminAuditLog -v`
Expected: FAIL

- [ ] **Step 3: 在 admin.py 中添加审计日志写入**

在 `app/routers/admin.py` 中添加导入：

```python
from app.models import AuditLog
```

在以下操作完成后写入审计日志：

- 重置密码：`db.add(AuditLog(actor_id=admin_id, action="reset_password", target_type="user", target_id=user_id, detail="管理员重置密码"))`
- 禁用/启用：`db.add(AuditLog(actor_id=admin_id, action="toggle_disable", target_type="user", target_id=user_id, detail=f"{'禁用' if user.is_disabled else '启用'}账号"))`
- 清理游客：`db.add(AuditLog(actor_id=admin_id, action="cleanup_guests", target_type="system", detail=f"清理了{count}个过期游客"))`

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_audit.py::TestAdminAuditLog -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: 管理员操作写审计日志"
```

---

## Task 10: 健康检查增强

**Files:**
- Modify: `app/main.py` (/health 路由)
- Test: `tests/test_input_validation.py` (追加)

- [ ] **Step 1: 写失败测试**

在 `tests/test_input_validation.py` 追加：

```python
class TestHealthCheck:
    def test_health_returns_db_status(self, client, db_session):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data
        assert data["db"] in ("ok", "error")

    def test_health_db_status_includes_user_count(self, client, db_session):
        resp = client.get("/health")
        data = resp.json()
        assert "user_count" in data
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_input_validation.py::TestHealthCheck -v`
Expected: FAIL

- [ ] **Step 3: 增强 /health 路由**

在 `app/main.py` 中修改 `/health` 路由：

```python
@app.get("/health")
def health_check():
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        return {"status": "ok", "db": "ok", "user_count": user_count}
    except Exception as e:
        return {"status": "degraded", "db": "error", "error": str(e)}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_input_validation.py::TestHealthCheck -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: 健康检查增加数据库状态"
```

---

## Task 11: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: 创建 CI 配置**

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: sqlite:///./test_ci.db
        run: |
          pytest tests/ -v --tb=short -q

      - name: Run Alembic migration
        run: |
          alembic upgrade head
```

- [ ] **Step 2: 验证 YAML 语法**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
Expected: no error

- [ ] **Step 3: 提交**

```bash
git add -A && git commit -m "ci: GitHub Actions自动测试和迁移"
```

---

## 执行顺序

按风险优先级排序：

1. **Task 1** — 权限 Helper 函数（基础设施）
2. **Task 2** — 教师跨班查看学生越权（最高风险安全漏洞）
3. **Task 3** — 学生作业列表班级过滤（数据隔离）
4. **Task 4** — 题库删除归属校验（数据安全）
5. **Task 5** — 班级成员一致性（数据一致性）
6. **Task 6** — 输入校验 Helper（基础设施）
7. **Task 7** — 替换直接 int() 调用（防 500 错误）
8. **Task 8** — 审计日志模型（基础设施）
9. **Task 9** — 管理员操作写审计日志（可追溯性）
10. **Task 10** — 健康检查增强（运维能力）
11. **Task 11** — GitHub Actions CI（自动化基线）

---

## 验收标准

完成所有 Task 后，以下条件必须同时满足：

- [ ] 教师 A 无法查看教师 B 班级学生详情/PDF/报告
- [ ] 学生只能看到本班作业，无法提交其他班级作业
- [ ] 教师无法删除其他教师的题库
- [ ] 移出班级后 users.class_id 清空
- [ ] 已在其他班的学生不能被直接添加到新班级
- [ ] 非法数字输入不触发 500 错误
- [ ] 管理员关键操作有审计日志
- [ ] /health 反映数据库连接状态
- [ ] GitHub Actions CI 配置就绪
- [ ] 全量 247+ 测试通过
