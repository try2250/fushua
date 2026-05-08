# 题库自定义 + 注册体系重构 + 游客模式 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构题库管理支持自定义题库（真题/模拟等），重构注册体系实现学生选班注册、教师邀请码注册、游客限时体验，并优化导入流程提供可下载模板。

**Architecture:** 新增 QuestionBank 模型作为题库容器（学科下可创建多个自定义题库），User 模型增加 is_guest/guest_expires_at 字段实现游客模式，新增 SiteConfig 模型存储教师注册邀请码，注册流程按角色分流：学生必须选班级，教师必须输入邀请码，未加入班级的学生降级为游客（1小时体验）。

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Jinja2, HTMX

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `app/models.py` | 新增 QuestionBank, SiteConfig 模型；User 增加 is_guest, guest_expires_at, class_id 字段 |
| `app/auth.py` | 增加 require_guest_check 中间件，游客过期检测 |
| `app/security.py` | 新增邀请码校验函数 |
| `app/routers/auth.py` | 重构注册流程：学生选班、教师邀请码、游客降级 |
| `app/routers/teacher.py` | 题库管理路由、导入模板下载、邀请码管理、学生管理增强 |
| `app/routers/student.py` | 游客过期拦截、题库筛选支持 |
| `app/routers/classgroup.py` | 班级邀请码/加入链接、批量添加学生 |
| `app/routers/pages.py` | 浏览页支持题库维度 |
| `app/templates/register.html` | 重构：学生选班、教师邀请码 |
| `app/templates/teacher/banks.html` | **新建** — 题库管理页 |
| `app/templates/teacher/bank_form.html` | **新建** — 题库创建/编辑表单 |
| `app/templates/teacher/import.html` | 修改 — 增加格式说明和模板下载 |
| `app/templates/teacher/invite.html` | **新建** — 邀请码管理页 |
| `app/templates/teacher/students.html` | **新建** — 学生管理页（班级维度） |
| `app/templates/student/guest_expired.html` | **新建** — 游客过期提示页 |
| `app/templates/browse.html` | 修改 — 增加题库维度 |
| `app/templates/base.html` | 修改 — 游客标识、导航调整 |
| `alembic/versions/` | 新迁移脚本 |
| `tests/test_question_bank.py` | **新建** — 题库功能测试 |
| `tests/test_registration.py` | **新建** — 注册体系测试 |
| `tests/test_guest.py` | **新建** — 游客模式测试 |

---

### Task 1: 数据模型 — QuestionBank + SiteConfig + User 扩展

**Files:**
- Modify: `app/models.py`
- Test: `tests/test_question_bank.py`

- [ ] **Step 1: 写失败测试 — QuestionBank 模型存在性**

```python
def test_question_bank_model_exists():
    from app.models import QuestionBank
    assert hasattr(QuestionBank, "__tablename__")
    assert QuestionBank.__tablename__ == "question_banks"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_question_bank.py::test_question_bank_model_exists -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 在 models.py 中添加 QuestionBank 模型**

在 `Notification` 类之后添加:

```python
class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subject = Column(String(20), nullable=False)
    semester = Column(String(20), default="")
    description = Column(Text, default="")
    bank_type = Column(String(20), default="custom")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_question_banks_subject", "subject"),
    )
```

在 `Question` 模型中添加 `bank_id` 字段（在 `created_by` 之前）:

```python
    bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=True, index=True)
```

- [ ] **Step 4: 添加 SiteConfig 模型**

在 `QuestionBank` 之后添加:

```python
class SiteConfig(Base):
    __tablename__ = "site_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 5: 扩展 User 模型**

在 `User` 类中 `created_at` 之后添加:

```python
    is_guest = Column(Boolean, default=False)
    guest_expires_at = Column(DateTime, nullable=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_question_bank.py::test_question_bank_model_exists -v`
Expected: PASS

- [ ] **Step 7: 运行全量测试确认无回归**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short -x`
Expected: 全部 PASS

---

### Task 2: Alembic 迁移 — 新表和新字段

**Files:**
- Create: `alembic/versions/` (新迁移脚本)

- [ ] **Step 1: 生成迁移脚本**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m alembic revision --autogenerate -m "add_question_bank_siteconfig_guest"`

- [ ] **Step 2: 检查生成的迁移脚本**

打开生成的迁移文件，确认包含:
- 创建 `question_banks` 表
- 创建 `site_configs` 表
- `questions` 表添加 `bank_id` 列
- `users` 表添加 `is_guest`, `guest_expires_at`, `class_id` 列

如果迁移脚本中使用了 `op.add_column` 而非 `batch_alter_table`，需要改为 batch 模式以兼容 SQLite:

```python
def upgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(sa.Column("bank_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_questions_bank_id", "question_banks", ["bank_id"], ["id"])

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_guest", sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column("guest_expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("class_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_users_class_id", "class_groups", ["class_id"], ["id"])
```

- [ ] **Step 3: 执行迁移**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m alembic upgrade head`
Expected: 无报错

---

### Task 3: 题库管理路由 — CRUD

**Files:**
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/banks.html`
- Create: `app/templates/teacher/bank_form.html`
- Test: `tests/test_question_bank.py`

- [ ] **Step 1: 写失败测试 — 题库列表页**

```python
def test_bank_list_page(client, db_session):
    from tests.conftest import create_test_user, login_as
    create_test_user(db_session, username="bank_teacher", role="teacher")
    login_as(client, "bank_teacher")
    resp = client.get("/teacher/banks", follow_redirects=True)
    assert resp.status_code == 200
    assert "题库" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_question_bank.py::test_bank_list_page -v`
Expected: FAIL — 404

- [ ] **Step 3: 在 teacher.py 中添加题库管理路由**

在 `field_manager` 路由之前添加:

```python
from app.models import QuestionBank


@router.get("/banks")
def bank_list(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.created_at.desc()).all()
    bank_data = []
    for b in banks:
        q_count = db.query(Question).filter(Question.bank_id == b.id).count()
        bank_data.append({"id": b.id, "name": b.name, "subject": b.subject, "semester": b.semester, "bank_type": b.bank_type, "description": b.description, "q_count": q_count, "created_at": b.created_at})
    return request.app.state.templates.TemplateResponse(
        "teacher/banks.html",
        {"request": request, "banks": bank_data, "subjects": SUBJECTS, "semesters": SEMESTERS},
    )


@router.get("/banks/create")
def create_bank_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    return request.app.state.templates.TemplateResponse(
        "teacher/bank_form.html",
        {"request": request, "bank": None, "subjects": SUBJECTS, "semesters": SEMESTERS, "csrf_token": request.session.get("csrf_token", "")},
    )


@router.post("/banks/create")
async def create_bank(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    name = sanitize_input(form.get("name", "").strip(), max_length=100)
    subject = sanitize_input(form.get("subject", "").strip(), max_length=20)
    if not name or not subject:
        return request.app.state.templates.TemplateResponse(
            "teacher/bank_form.html",
            {"request": request, "bank": None, "error": "题库名称和科目为必填项", "subjects": SUBJECTS, "semesters": SEMESTERS, "csrf_token": request.session.get("csrf_token", "")},
        )
    bank = QuestionBank(
        name=name,
        subject=subject,
        semester=form.get("semester", ""),
        description=sanitize_input(form.get("description", "").strip(), max_length=500),
        bank_type=form.get("bank_type", "custom"),
        created_by=user_id,
    )
    db.add(bank)
    db.commit()
    return RedirectResponse(url="/teacher/banks", status_code=303)


@router.post("/banks/{bank_id}/delete")
async def delete_bank(bank_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id, QuestionBank.created_by == user_id).first()
    if bank:
        db.query(Question).filter(Question.bank_id == bank_id).update({"bank_id": None})
        db.delete(bank)
        db.commit()
    return RedirectResponse(url="/teacher/banks", status_code=303)
```

- [ ] **Step 4: 创建 banks.html 模板**

创建 `app/templates/teacher/banks.html`:

```html
{% extends "base.html" %}
{% block title %}题库管理 - 付刷{% endblock %}
{% block content %}
<h1>题库管理</h1>
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
        <h2>我的题库</h2>
        <a href="/teacher/banks/create" class="btn btn-primary">+ 新建题库</a>
    </div>
    {% if banks %}
    <table class="table">
        <thead><tr><th>名称</th><th>科目</th><th>学期</th><th>类型</th><th>题目数</th><th>操作</th></tr></thead>
        <tbody>
        {% for b in banks %}
        <tr>
            <td>{{ b.name }}</td>
            <td>{{ b.subject }}</td>
            <td>{{ b.semester or '全部' }}</td>
            <td>{{ '真题' if b.bank_type == 'exam' else '模拟' if b.bank_type == 'mock' else '自定义' }}</td>
            <td>{{ b.q_count }}</td>
            <td>
                <form action="/teacher/banks/{{ b.id }}/delete" method="POST" style="display:inline;" onsubmit="return confirm('确定删除？题库中的题目不会被删除。')">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-danger btn-sm">删除</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="color:var(--text-secondary);">还没有题库，点击上方按钮创建</p>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 5: 创建 bank_form.html 模板**

创建 `app/templates/teacher/bank_form.html`:

```html
{% extends "base.html" %}
{% block title %}{{ '编辑题库' if bank else '新建题库' }} - 付刷{% endblock %}
{% block content %}
<div class="card">
    <h1>{{ '编辑题库' if bank else '新建题库' }}</h1>
    {% if error %}<div class="alert alert-error">{{ error }}</div>{% endif %}
    <form action="/teacher/banks/create" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label>题库名称 *</label>
            <input type="text" name="name" required placeholder="如：2024中考真题、期末模拟卷" value="{{ bank.name if bank else '' }}">
        </div>
        <div class="form-group">
            <label>科目 *</label>
            <select name="subject" required>
                <option value="">请选择科目</option>
                {% for s in subjects %}<option value="{{ s }}" {{ 'selected' if bank and bank.subject == s else '' }}>{{ s }}</option>{% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label>学期</label>
            <select name="semester">
                <option value="">全部学期</option>
                {% for s in semesters %}<option value="{{ s }}" {{ 'selected' if bank and bank.semester == s else '' }}>{{ s }}</option>{% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label>题库类型</label>
            <select name="bank_type">
                <option value="custom">自定义</option>
                <option value="exam">真题</option>
                <option value="mock">模拟题</option>
                <option value="daily">每日练习</option>
            </select>
        </div>
        <div class="form-group">
            <label>描述</label>
            <textarea name="description" rows="3" placeholder="题库说明（可选）">{{ bank.description if bank else '' }}</textarea>
        </div>
        <button type="submit" class="btn btn-primary">创建</button>
        <a href="/teacher/banks" class="btn btn-outline">取消</a>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 6: 在 base.html 导航中添加题库入口**

在教师导航中 `字段` 链接之后添加:

```html
                        <a href="/teacher/banks" class="nav-link">题库</a>
```

- [ ] **Step 7: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_question_bank.py -v`
Expected: PASS

---

### Task 4: 出题/导入关联题库

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `app/templates/teacher/question_form.html`
- Modify: `app/templates/teacher/import.html`

- [ ] **Step 1: 修改 create_question 路由 — 支持选择题库**

在 `create_question_page` 函数中，获取题库列表并传入模板:

```python
@router.get("/questions/create")
def create_question_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    custom_fields = db.query(FieldConfig).filter(FieldConfig.visible == True).order_by(FieldConfig.sort_order).all()
    banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
    return request.app.state.templates.TemplateResponse(
        "teacher/question_form.html",
        {
            "request": request,
            "question": None,
            "error": None,
            "question_types": QUESTION_TYPES,
            "semesters": SEMESTERS,
            "custom_fields": custom_fields,
            "banks": banks,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )
```

在 `create_question` POST 处理中，保存 `bank_id`:

在 `question = Question(...)` 构造中添加:
```python
        bank_id=form.get("bank_id", ""),
```

在 `bank_id` 赋值处（`created_by` 之前）:
```python
    bank_id_val = form.get("bank_id", "")
    question = Question(
        ...
        bank_id=int(bank_id_val) if bank_id_val else None,
        created_by=user_id,
    )
```

同样修改 `edit_question_page` 和 `edit_question` 路由，传入 `banks` 列表并保存 `bank_id`。

- [ ] **Step 2: 修改 question_form.html — 添加题库选择下拉框**

在 `科目` 选择框之后添加:

```html
        <div class="form-group">
            <label>所属题库</label>
            <select name="bank_id">
                <option value="">不归属题库</option>
                {% for b in banks %}
                <option value="{{ b.id }}" {{ 'selected' if question and question.bank_id == b.id else '' }}>{{ b.name }} ({{ b.subject }})</option>
                {% endfor %}
            </select>
        </div>
```

- [ ] **Step 3: 修改 import_questions — 支持选择目标题库**

在 `import_page` 函数中添加 banks 列表:

```python
    banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
```

在返回的 context 中添加 `"banks": banks`。

在 `import_questions` POST 处理中，获取 `bank_id` 并传给 `_build_question_from_dict`:

在 `import_questions` 函数中，`await validate_csrf_async(request)` 之后添加:
```python
    form_data = await request.form()
    bank_id = form_data.get("bank_id", "")
    bank_id = int(bank_id) if bank_id else None
```

修改 `_build_question_from_dict` 签名，添加 `bank_id=None` 参数:
```python
def _build_question_from_dict(item: dict, user_id: int, bank_id: int = None) -> Question:
```

在构造 Question 时添加 `bank_id=bank_id`。

修改 `_import_json` 和 `_import_csv` 签名和调用，传递 `bank_id`:
```python
def _import_json(content_bytes: bytes, user_id: int, db: Session, bank_id: int = None) -> int:
    ...
    q = _build_question_from_dict(item, user_id, bank_id)
```

```python
def _import_csv(content_bytes: bytes, user_id: int, db: Session, bank_id: int = None) -> int:
    ...
    q = _build_question_from_dict(item, user_id, bank_id)
```

- [ ] **Step 4: 运行全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short -x`
Expected: 全部 PASS

---

### Task 5: 导入模板下载与格式说明

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `app/templates/teacher/import.html`

- [ ] **Step 1: 添加模板下载路由**

在 `import_page` 路由之前添加:

```python
@router.get("/questions/import/template/{fmt}")
def download_template(fmt: str, request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    custom_fields = db.query(FieldConfig).filter(FieldConfig.visible == True).order_by(FieldConfig.sort_order).all()
    custom_keys = [cf.field_key for cf in custom_fields]

    if fmt == "json":
        example = [{
            "subject": "数学",
            "semester": "七年级上册",
            "chapter": "有理数",
            "q_type": "choice",
            "difficulty": 2,
            "content": "题目内容",
            "option_a": "选项A",
            "option_b": "选项B",
            "option_c": "选项C",
            "option_d": "选项D",
            "answer": "A",
            "explanation": "解析说明",
        }]
        for ck in custom_keys:
            example[0][ck] = f"自定义字段{ck}的值"
        return Response(
            content=json.dumps(example, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=import_template.json"},
        )
    elif fmt == "csv":
        fieldnames = ["subject", "semester", "chapter", "q_type", "difficulty", "content", "option_a", "option_b", "option_c", "option_d", "answer", "explanation"] + custom_keys
        example_row = {"subject": "数学", "semester": "七年级上册", "chapter": "有理数", "q_type": "choice", "difficulty": "2", "content": "题目内容", "option_a": "选项A", "option_b": "选项B", "option_c": "选项C", "option_d": "选项D", "answer": "A", "explanation": "解析说明"}
        for ck in custom_keys:
            example_row[ck] = f"自定义字段{ck}的值"
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(example_row)
        return Response(
            content="\ufeff" + output.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=import_template.csv"},
        )
    raise HTTPException(status_code=400, detail="不支持的格式")
```

- [ ] **Step 2: 修改 import.html — 添加格式说明和模板下载**

在 `import.html` 的文件上传表单之前添加:

```html
<div class="card" style="margin-bottom:1.5rem;">
    <h2>导入说明</h2>
    <div style="line-height:1.8;">
        <p><strong>支持格式：</strong>JSON (.json) 或 CSV (.csv)</p>
        <p><strong>必填字段：</strong>subject（科目）、content（题目内容）、answer（答案）</p>
        <p><strong>题型代码：</strong>choice=选择题, multi_choice=多选题, fill=填空题, judge=判断题</p>
        <p><strong>难度等级：</strong>1=简单, 2=中等, 3=困难</p>
        <p><strong>选择题选项：</strong>option_a, option_b, option_c, option_d</p>
        {% if custom_fields %}
        <p><strong>自定义字段：</strong>{% for cf in custom_fields %}{{ cf.field_key }}({{ cf.field_label }}){% if not loop.last %}, {% endif %}{% endfor %}</p>
        {% endif %}
        <p style="margin-top:0.5rem;">
            <strong>下载模板：</strong>
            <a href="/teacher/questions/import/template/json" class="btn btn-outline btn-sm">JSON 模板</a>
            <a href="/teacher/questions/import/template/csv" class="btn btn-outline btn-sm">CSV 模板</a>
        </p>
    </div>
</div>
```

在上传表单中添加题库选择（在文件选择之前）:

```html
        <div class="form-group">
            <label>导入到题库（可选）</label>
            <select name="bank_id">
                <option value="">不归属题库</option>
                {% for b in banks %}
                <option value="{{ b.id }}">{{ b.name }} ({{ b.subject }})</option>
                {% endfor %}
            </select>
        </div>
```

- [ ] **Step 3: 运行测试确认无回归**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short -x`
Expected: 全部 PASS

---

### Task 6: 教师邀请码注册

**Files:**
- Modify: `app/models.py` (SiteConfig 已在 Task 1 添加)
- Modify: `app/security.py`
- Modify: `app/routers/auth.py`
- Modify: `app/templates/register.html`
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/invite.html`
- Test: `tests/test_registration.py`

- [ ] **Step 1: 写失败测试 — 教师注册需要邀请码**

```python
def test_teacher_register_requires_invite_code(client, db_session):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "teacher_no_invite",
        "password": "teacher123",
        "role": "teacher",
        "display_name": "Test",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "邀请码" in resp.text or resp.status_code != 303
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_registration.py::test_teacher_register_requires_invite_code -v`
Expected: FAIL — 当前不校验邀请码

- [ ] **Step 3: 在 security.py 中添加邀请码校验函数**

```python
def verify_teacher_invite_code(code: str, db) -> bool:
    from app.models import SiteConfig
    if not code:
        return False
    config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    if not config or not config.value:
        return False
    codes = [c.strip() for c in config.value.split(",") if c.strip()]
    return code in codes
```

- [ ] **Step 4: 修改 auth.py register — 教师必须输入邀请码**

在 `register` 函数中，`existing = db.query(User)...` 之前添加:

```python
    if role == "teacher":
        invite_code = form.get("invite_code", "").strip() if hasattr(form, 'get') else ""
        if not invite_code:
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "教师注册需要邀请码", "csrf_token": request.session.get("csrf_token", ""), "role": role},
            )
        from app.security import verify_teacher_invite_code
        if not verify_teacher_invite_code(invite_code, db):
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "邀请码无效", "csrf_token": request.session.get("csrf_token", ""), "role": role},
            )
```

注意: `form = await request.form()` 需要在 `invite_code` 获取之前执行。当前代码中 `form` 还没有获取，需要调整顺序。将 `await validate_csrf_async(request)` 之后添加 `form = await request.form()`，后续的 `username`, `password` 等从 `form` 获取:

重构 `register` 函数为:
```python
@router.post("/register")
async def register(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,
):
    await validate_csrf_async(request)
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    role = form.get("role", "student")
    display_name = form.get("display_name", "")

    pw_error = validate_password_strength(password)
    if pw_error:
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": pw_error, "csrf_token": request.session.get("csrf_token", ""), "role": role},
        )
    username = sanitize_input(username, max_length=50)
    display_name = sanitize_input(display_name, max_length=100)
    if len(username) < 2:
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": "用户名至少2个字符", "csrf_token": request.session.get("csrf_token", ""), "role": role},
        )

    if role == "teacher":
        invite_code = form.get("invite_code", "").strip()
        if not invite_code:
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "教师注册需要邀请码", "csrf_token": request.session.get("csrf_token", ""), "role": role},
            )
        from app.security import verify_teacher_invite_code
        if not verify_teacher_invite_code(invite_code, db):
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "邀请码无效", "csrf_token": request.session.get("csrf_token", ""), "role": role},
            )

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": "用户名已存在", "csrf_token": request.session.get("csrf_token", ""), "role": role},
        )
    password_hash = User.hash_password(password)
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        display_name=display_name or username,
    )
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)
```

- [ ] **Step 5: 修改 register.html — 教师显示邀请码输入框**

替换整个 `register.html`:

```html
{% extends "base.html" %}
{% block title %}注册 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>注册</h1>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <form action="/register" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required placeholder="请输入用户名">
        </div>
        <div class="form-group">
            <label for="display_name">昵称</label>
            <input type="text" id="display_name" name="display_name" placeholder="显示名称（可选）">
        </div>
        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required placeholder="请输入密码（至少6位，非纯数字）">
        </div>
        <div class="form-group">
            <label>我是</label>
            <div class="role-select">
                <label class="role-option">
                    <input type="radio" name="role" value="student" checked onchange="toggleInviteField()">
                    <span class="role-label">🎓 学生</span>
                </label>
                <label class="role-option">
                    <input type="radio" name="role" value="teacher" onchange="toggleInviteField()">
                    <span class="role-label">👨‍🏫 教师</span>
                </label>
            </div>
        </div>
        <div class="form-group" id="classSelectGroup">
            <label for="class_id">选择班级 *</label>
            <select name="class_id" id="class_id">
                <option value="">请选择班级</option>
                {% for c in classes %}
                <option value="{{ c.id }}" {{ 'selected' if c.id|string == preselected_class else '' }}>{{ c.name }}</option>
                {% endfor %}
            </select>
            <small style="color:var(--text-secondary);">注册后可在个人设置中更换班级</small>
        </div>
        <div class="form-group" id="inviteCodeGroup" style="display:none;">
            <label for="invite_code">教师邀请码 *</label>
            <input type="text" id="invite_code" name="invite_code" placeholder="请输入管理员提供的邀请码">
            <small style="color:var(--text-secondary);">教师注册需要邀请码，请联系管理员获取</small>
        </div>
        <button type="submit" class="btn btn-primary btn-block">注册</button>
    </form>
    <p class="auth-switch">已有账号？<a href="/login">去登录</a></p>
</div>
<script>
function toggleInviteField() {
    var role = document.querySelector('input[name="role"]:checked').value;
    document.getElementById('inviteCodeGroup').style.display = role === 'teacher' ? 'block' : 'none';
    document.getElementById('classSelectGroup').style.display = role === 'student' ? 'block' : 'none';
    var inviteInput = document.getElementById('invite_code');
    var classSelect = document.getElementById('class_id');
    if (role === 'teacher') {
        inviteInput.required = true;
        classSelect.required = false;
    } else {
        inviteInput.required = false;
        classSelect.required = true;
    }
}
document.addEventListener('DOMContentLoaded', function() {
    toggleInviteField();
});
</script>
{% endblock %}
```

- [ ] **Step 6: 修改 register_page GET 路由 — 传入班级列表**

```python
@router.get("/register")
def register_page(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
    return request.app.state.templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None, "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": "student", "preselected_class": ""},
    )
```

需要在文件顶部添加 `from app.models import ClassGroup`。

- [ ] **Step 7: 添加教师邀请码管理路由**

在 `teacher.py` 中添加:

```python
@router.get("/invite")
def invite_manager(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    current_codes = config.value if config else ""
    return request.app.state.templates.TemplateResponse(
        "teacher/invite.html",
        {"request": request, "current_codes": current_codes, "csrf_token": request.session.get("csrf_token", "")},
    )


@router.post("/invite/update")
async def update_invite(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    codes = sanitize_input(form.get("codes", "").strip(), max_length=500)
    config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    if not config:
        config = SiteConfig(key="teacher_invite_code", value=codes)
        db.add(config)
    else:
        config.value = codes
    db.commit()
    return RedirectResponse(url="/teacher/invite", status_code=303)
```

需要在 teacher.py 顶部添加 `from app.models import QuestionBank, SiteConfig`。

- [ ] **Step 8: 创建 invite.html 模板**

创建 `app/templates/teacher/invite.html`:

```html
{% extends "base.html" %}
{% block title %}邀请码管理 - 付刷{% endblock %}
{% block content %}
<div class="card">
    <h1>教师邀请码管理</h1>
    <p style="color:var(--text-secondary);margin-bottom:1rem;">设置邀请码后，教师注册时必须输入正确的邀请码。多个邀请码用英文逗号分隔。</p>
    <form action="/teacher/invite/update" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label>当前邀请码</label>
            <input type="text" name="codes" value="{{ current_codes }}" placeholder="如：TEACH2024,FUSHUA888" style="font-family:monospace;">
            <small style="color:var(--text-secondary);">多个邀请码用英文逗号分隔，如：CODE1,CODE2</small>
        </div>
        <button type="submit" class="btn btn-primary">保存</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 9: 在 base.html 教师导航中添加邀请码入口**

在 `班级` 链接之后添加:

```html
                        <a href="/teacher/invite" class="nav-link">邀请码</a>
```

- [ ] **Step 10: 初始化默认邀请码**

在 `main.py` 的 `Base.metadata.create_all(bind=engine)` 之后添加:

```python
from app.models import SiteConfig
_init_db = SessionLocal()
if not _init_db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first():
    _init_db.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    _init_db.commit()
_init_db.close()
```

- [ ] **Step 11: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_registration.py -v`
Expected: PASS

---

### Task 7: 学生注册选班 + 游客降级

**Files:**
- Modify: `app/routers/auth.py`
- Modify: `app/auth.py`
- Modify: `app/routers/student.py`
- Create: `app/templates/student/guest_expired.html`
- Test: `tests/test_guest.py`

- [ ] **Step 1: 写失败测试 — 学生注册必须选班级**

```python
def test_student_register_requires_class(client, db_session):
    from tests.conftest import get_csrf_token, create_test_user
    teacher = create_test_user(db_session, username="class_teacher", role="teacher")
    from app.models import ClassGroup
    cls = ClassGroup(name="测试班", created_by=teacher.id)
    db_session.add(cls)
    db_session.commit()
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "student_no_class",
        "password": "student123",
        "role": "student",
        "display_name": "Test",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "班级" in resp.text or resp.status_code != 303
```

- [ ] **Step 2: 写失败测试 — 游客模式1小时过期**

```python
def test_guest_mode_expires(client, db_session):
    from tests.conftest import create_test_user
    from app.models import ClassGroup
    from datetime import datetime, timedelta
    teacher = create_test_user(db_session, username="guest_teacher", role="teacher")
    user = create_test_user(db_session, username="guest_user", role="student")
    user.is_guest = True
    user.guest_expires_at = datetime.now() - timedelta(hours=1)
    db_session.commit()
    from app.auth import is_guest_expired
    assert is_guest_expired(user) == True
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_guest.py -v`
Expected: FAIL

- [ ] **Step 4: 修改 auth.py register — 学生注册逻辑**

在 `register` 函数中，教师邀请码校验之后、`existing = ...` 之前添加:

```python
    is_guest = False
    class_id = None
    guest_expires_at = None

    if role == "student":
        class_id_str = form.get("class_id", "").strip()
        if class_id_str:
            class_id = int(class_id_str)
            from app.models import ClassGroup
            cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if not cls:
                class_id = None
                is_guest = True
                guest_expires_at = datetime.now() + timedelta(hours=1)
        else:
            is_guest = True
            guest_expires_at = datetime.now() + timedelta(hours=1)
```

需要在文件顶部添加 `from datetime import datetime, timedelta`。

修改 User 创建:
```python
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        display_name=display_name or username,
        is_guest=is_guest,
        guest_expires_at=guest_expires_at,
        class_id=class_id,
    )
```

如果学生选了班级，自动加入班级:
```python
    if class_id:
        from app.models import ClassMember
        db.add(ClassMember(class_id=class_id, user_id=user.id))
```

在 `db.commit()` 之前添加上面的代码。

- [ ] **Step 5: 在 auth.py 中添加游客过期检测函数**

```python
from datetime import datetime

def is_guest_expired(user) -> bool:
    if not user.is_guest:
        return False
    if not user.guest_expires_at:
        return True
    return datetime.now() > user.guest_expires_at


def require_non_guest(request: Request, db: Session = None):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if db:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_guest and is_guest_expired(user):
            raise HTTPException(status_code=403, detail="游客体验已过期，请联系教师加入班级")
    return user_id
```

- [ ] **Step 6: 修改 student.py — 游客过期拦截**

在 `student.py` 中，将所有 `require_login(request)` 替换为 `require_non_guest(request, db)`。

需要在文件顶部添加:
```python
from app.auth import require_non_guest
```

- [ ] **Step 7: 创建游客过期页面**

创建 `app/templates/student/guest_expired.html`:

```html
{% extends "base.html" %}
{% block title %}体验已过期 - 付刷{% endblock %}
{% block content %}
<div class="card" style="text-align:center;padding:3rem;">
    <h1>⏰ 游客体验已过期</h1>
    <p style="color:var(--text-secondary);margin:1rem 0;">您的1小时游客体验已结束。请联系教师将您加入班级，即可继续使用全部功能。</p>
    <a href="/" class="btn btn-primary">返回首页</a>
</div>
{% endblock %}
```

- [ ] **Step 8: 在 main.py 全局模板变量中添加 is_guest 标识**

在 `_global_template_vars` 函数中，`if user:` 块内添加:

```python
                is_guest = user.is_guest
```

在返回的字典中添加:
```python
        "is_guest": is_guest if logged_in else False,
```

- [ ] **Step 9: 在 base.html 中显示游客标识**

在 `{{ display_name }}` 之后添加:

```html
                    {% if is_guest %}<span class="badge badge-warning" style="font-size:0.7rem;margin-left:4px;">游客</span>{% endif %}
```

- [ ] **Step 10: 运行测试确认通过**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/test_guest.py tests/test_registration.py -v`
Expected: PASS

---

### Task 8: 教师学生管理增强

**Files:**
- Modify: `app/routers/classgroup.py`
- Modify: `app/routers/teacher.py`
- Create: `app/templates/teacher/students.html`

- [ ] **Step 1: 添加学生管理页面路由**

在 `teacher.py` 中添加:

```python
@router.get("/students")
def student_management(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).order_by(ClassGroup.name).all()
    class_data = []
    for cls in classes:
        members = (
            db.query(User)
            .join(ClassMember, ClassMember.user_id == User.id)
            .filter(ClassMember.class_id == cls.id)
            .all()
        )
        member_data = []
        for m in members:
            total = db.query(Record).filter(Record.user_id == m.id).count()
            correct = db.query(Record).filter(Record.user_id == m.id, Record.is_correct == True).count()
            member_data.append({
                "id": m.id,
                "username": m.username,
                "display_name": m.display_name,
                "is_guest": m.is_guest,
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
            })
        class_data.append({"id": cls.id, "name": cls.name, "members": member_data})

    guests = db.query(User).filter(User.role == "student", User.is_guest == True).all()
    guest_data = []
    for g in guests:
        guest_data.append({
            "id": g.id,
            "username": g.username,
            "display_name": g.display_name,
            "guest_expires_at": g.guest_expires_at,
        })

    return request.app.state.templates.TemplateResponse(
        "teacher/students.html",
        {"request": request, "class_data": class_data, "guest_data": guest_data},
    )


@router.post("/students/{student_id}/approve")
async def approve_student(student_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    class_id = form.get("class_id", "").strip()
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if student and class_id:
        cls = db.query(ClassGroup).filter(ClassGroup.id == int(class_id), ClassGroup.created_by == user_id).first()
        if cls:
            existing = db.query(ClassMember).filter(ClassMember.class_id == cls.id, ClassMember.user_id == student.id).first()
            if not existing:
                db.add(ClassMember(class_id=cls.id, user_id=student.id))
            student.is_guest = False
            student.guest_expires_at = None
            student.class_id = cls.id
            db.commit()
    return RedirectResponse(url="/teacher/students", status_code=303)
```

需要在 teacher.py 顶部添加 `from app.models import QuestionBank, SiteConfig, ClassGroup, ClassMember`。

- [ ] **Step 2: 创建 students.html 模板**

创建 `app/templates/teacher/students.html`:

```html
{% extends "base.html" %}
{% block title %}学生管理 - 付刷{% endblock %}
{% block content %}
<h1>学生管理</h1>

{% if guest_data %}
<div class="card" style="margin-bottom:1.5rem;border-left:4px solid #f59e0b;">
    <h2>待审核游客 ({{ guest_data|length }})</h2>
    <p style="color:var(--text-secondary);">以下学生以游客身份注册，审核通过后可使用全部功能。</p>
    <table class="table">
        <thead><tr><th>用户名</th><th>昵称</th><th>过期时间</th><th>操作</th></tr></thead>
        <tbody>
        {% for g in guest_data %}
        <tr>
            <td>{{ g.username }}</td>
            <td>{{ g.display_name }}</td>
            <td>{{ g.guest_expires_at.strftime('%m-%d %H:%M') if g.guest_expires_at else '未设置' }}</td>
            <td>
                <form action="/teacher/students/{{ g.id }}/approve" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <select name="class_id" required>
                        <option value="">选择班级</option>
                        {% for c in class_data %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}
                    </select>
                    <button type="submit" class="btn btn-primary btn-sm">通过</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% for c in class_data %}
<div class="card" style="margin-bottom:1rem;">
    <h2>{{ c.name }} ({{ c.members|length }}人)</h2>
    {% if c.members %}
    <table class="table">
        <thead><tr><th>用户名</th><th>昵称</th><th>做题数</th><th>正确率</th><th>状态</th></tr></thead>
        <tbody>
        {% for m in c.members %}
        <tr>
            <td>{{ m.username }}</td>
            <td>{{ m.display_name }}</td>
            <td>{{ m.total }}</td>
            <td>{{ m.accuracy }}%</td>
            <td>{% if m.is_guest %}<span class="badge badge-warning">游客</span>{% else %}<span class="badge badge-success">正式</span>{% endif %}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="color:var(--text-secondary);">暂无学生</p>
    {% endif %}
</div>
{% endfor %}

<div class="card">
    <h2>添加学生到班级</h2>
    <p style="color:var(--text-secondary);">在班级详情页可以通过用户名添加学生，学生注册时选择班级也会自动加入。</p>
    <a href="/teacher/classes" class="btn btn-outline">管理班级</a>
</div>
{% endblock %}
```

- [ ] **Step 3: 在 base.html 教师导航中添加学生管理入口**

在 `班级` 链接之后添加:

```html
                        <a href="/teacher/students" class="nav-link">学生</a>
```

- [ ] **Step 4: 运行全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short -x`
Expected: 全部 PASS

---

### Task 9: 浏览页支持题库维度

**Files:**
- Modify: `app/routers/pages.py`
- Modify: `app/templates/browse.html`

- [ ] **Step 1: 修改 browse 路由 — 添加题库维度**

在 `browse` 函数中，`if subject:` 块内，添加题库查询:

```python
    bank_counts = {}
    banks = []
    if subject:
        bank_rows = (
            db.query(QuestionBank.name, sa_func.count(Question.id))
            .outerjoin(Question, Question.bank_id == QuestionBank.id)
            .filter(QuestionBank.subject == subject)
            .group_by(QuestionBank.name)
            .all()
        )
        for bname, cnt in bank_rows:
            bank_counts[bname] = cnt

        bank_list = db.query(QuestionBank).filter(QuestionBank.subject == subject).order_by(QuestionBank.name).all()
        banks = [{"id": b.id, "name": b.name, "bank_type": b.bank_type, "q_count": bank_counts.get(b.name, 0)} for b in bank_list]
```

在返回的 context 中添加 `"banks": banks, "bank_counts": bank_counts`。

同时修改题目查询，支持 `bank_id` 参数:

在 `browse` 函数签名中添加 `bank_id: int = 0` 参数。

在题目查询条件中添加:
```python
    if bank_id:
        questions = questions.filter(Question.bank_id == bank_id)
```

- [ ] **Step 2: 修改 browse.html — 添加题库选择**

在学期选择区域之后添加:

```html
    {% if banks %}
    <div class="card" style="margin-bottom:1rem;">
        <h3>题库</h3>
        <div class="semester-grid">
            {% for b in banks %}
            <a href="/browse?subject={{ subject }}&semester={{ semester }}&bank_id={{ b.id }}" class="chapter-item {% if bank_id == b.id %}active{% endif %}">
                {{ b.name }}
                <span class="badge">{{ b.q_count }}</span>
            </a>
            {% endfor %}
        </div>
    </div>
    {% endif %}
```

- [ ] **Step 3: 运行全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short -x`
Expected: 全部 PASS

---

### Task 10: 全量测试验证与修复

**Files:**
- All test files

- [ ] **Step 1: 运行全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 2: 修复 conftest.py 中受影响的测试辅助函数**

由于 `register` 路由签名变更（不再使用 `Form()` 参数），`register_and_login` 和 `create_test_user` 辅助函数可能需要调整。检查并修复:

- `register_and_login` — 确保传入 `class_id` 或接受游客模式
- `login_as` — 不受影响
- `create_test_user` — 直接创建 User 对象，不受影响

- [ ] **Step 3: 修复所有因注册变更而失败的测试**

关键变更:
1. 学生注册需要 `class_id`，否则自动成为游客
2. 教师注册需要 `invite_code`

在 `conftest.py` 中修改 `register_and_login`:

```python
def register_and_login(client, username="testuser", role="student", password="abc123", class_id=None):
    from app.models import ClassGroup
    csrf = get_csrf_token(client)
    data = {
        "username": username,
        "password": password,
        "role": role,
        "display_name": username,
        "_csrf_token": csrf,
    }
    if role == "student" and class_id:
        data["class_id"] = str(class_id)
    if role == "teacher":
        data["invite_code"] = "FUSHUA2024"
    client.post("/register", data=data, follow_redirects=True)
```

- [ ] **Step 4: 最终全量测试**

Run: `cd "c:\Users\Windows 10\Desktop\trae\付刷" && py -m pytest tests/ -v --tb=short`
Expected: 全部 PASS
