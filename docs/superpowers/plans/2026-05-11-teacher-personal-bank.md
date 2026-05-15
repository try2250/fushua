# 教师个人题库功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有系统题库基础上，增加教师个人题库功能，支持公开/私有/准入码三种可见性模式，让学生可以浏览和练习教师题库的题目。

**Architecture:** 在现有 `QuestionBank` 模型上扩展 `visibility`（public/private/code）和 `access_code` 字段；浏览页增加"教师题库"分区；学生练习时根据可见性规则过滤题库；教师端增加题库可见性和准入码管理。

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, Alembic, Jinja2

---

## 需求拆解

### 学生视角
1. 浏览页可以看到"系统题库"和"教师题库"两个分区
2. 教师题库分为：公开（所有人可见）、私有（仅本班学生可见）、准入码（输入码后可见）
3. 选择教师题库后可以像系统题库一样刷题

### 教师视角
1. 创建/编辑题库时可以设置可见性（公开/私有/准入码）
2. 设置准入码后，学生需要输入正确的码才能看到该题库
3. 可以查看自己题库的访问统计

### 访问控制规则
- `visibility=public`：所有登录学生可见
- `visibility=private`：仅该教师班级内的学生可见
- `visibility=code`：输入正确准入码的学生可见（准入码正确后存入 session 记忆）

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 修改 | `app/models.py` | QuestionBank 增加 visibility + access_code 字段 |
| 创建 | `alembic/versions/20260511_bank_visibility.py` | 数据库迁移 |
| 修改 | `app/routers/teacher.py` | 创建题库时保存 visibility + access_code |
| 修改 | `app/routers/pages.py` | 浏览页显示教师题库 + 准入码验证 |
| 修改 | `app/templates/browse.html` | 浏览页 UI 改造 |
| 修改 | `app/templates/teacher/bank_form.html` | 创建/编辑题库表单增加可见性选项 |
| 修改 | `app/templates/teacher/banks.html` | 题库列表显示可见性标签 |
| 修改 | `app/routers/student.py` | 练习时支持 bank_id 参数 |
| 创建 | `tests/test_teacher_bank_visibility.py` | 测试 |

---

### Task 1: 数据模型扩展 — QuestionBank 增加 visibility + access_code

**Files:**
- Modify: `app/models.py`
- Create: `alembic/versions/20260511_bank_visibility.py`

- [ ] **Step 1: 修改 models.py — QuestionBank 模型增加字段**

在 `app/models.py` 的 `QuestionBank` 类中，在 `bank_type` 行之后添加：

```python
    visibility = Column(String(20), default="public")
    access_code = Column(String(50), default="")
```

完整的 QuestionBank 模型应为：

```python
class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subject = Column(String(20), nullable=False)
    semester = Column(String(20), default="")
    description = Column(Text, default="")
    bank_type = Column(String(20), default="custom")
    visibility = Column(String(20), default="public")
    access_code = Column(String(50), default="")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_question_banks_subject", "subject"),
    )
```

- [ ] **Step 2: 创建 Alembic 迁移**

创建 `alembic/versions/20260511_bank_visibility.py`：

```python
"""add bank visibility and access_code

Revision ID: 20260511bank
Revises: 20260510_force_pwd
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa

revision = "20260511bank"
down_revision = "20260510_force_pwd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("question_banks", sa.Column("visibility", sa.String(20), server_default="public", nullable=True))
    op.add_column("question_banks", sa.Column("access_code", sa.String(50), server_default="", nullable=True))


def downgrade() -> None:
    op.drop_column("question_banks", "access_code")
    op.drop_column("question_banks", "visibility")
```

- [ ] **Step 3: 更新 alembic/env.py 导入**

确认 `alembic/env.py` 已导入 `QuestionBank`（Task 3 of 部署计划已添加），无需额外修改。

- [ ] **Step 4: 运行迁移验证**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m alembic upgrade head`
Expected: 无错误

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m alembic heads`
Expected: 单个 head = `20260511bank`

- [ ] **Step 5: 写模型测试**

在 `tests/test_teacher_bank_visibility.py` 中添加：

```python
import pytest
from tests.conftest import get_csrf_token, login_as


def test_question_bank_has_visibility_field(db):
    from app.models import QuestionBank
    bank = QuestionBank(name="测试题库", subject="数学", visibility="private", access_code="ABC123", created_by=1)
    db.add(bank)
    db.commit()
    db.refresh(bank)
    assert bank.visibility == "private"
    assert bank.access_code == "ABC123"


def test_question_bank_default_visibility(db):
    from app.models import QuestionBank
    bank = QuestionBank(name="默认题库", subject="英语", created_by=1)
    db.add(bank)
    db.commit()
    db.refresh(bank)
    assert bank.visibility == "public"
    assert bank.access_code == ""
```

- [ ] **Step 6: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/test_teacher_bank_visibility.py -v --tb=short`
Expected: PASS

---

### Task 2: 教师端 — 题库创建/编辑支持可见性设置

**Files:**
- Modify: `app/routers/teacher.py`
- Modify: `app/templates/teacher/bank_form.html`
- Modify: `app/templates/teacher/banks.html`

- [ ] **Step 1: 修改 teacher.py create_bank — 保存 visibility + access_code**

在 `app/routers/teacher.py` 的 `create_bank` 函数中，找到 `bank = QuestionBank(...)` 创建代码块，在 `bank_type=` 行之后添加：

```python
        visibility=form.get("visibility", "public"),
        access_code=sanitize_input(form.get("access_code", "").strip(), max_length=50) if form.get("visibility") == "code" else "",
```

完整的 bank 创建代码应为：

```python
    bank = QuestionBank(
        name=name,
        subject=subject,
        semester=form.get("semester", ""),
        description=sanitize_input(form.get("description", "").strip(), max_length=500),
        bank_type=form.get("bank_type", "custom"),
        visibility=form.get("visibility", "public"),
        access_code=sanitize_input(form.get("access_code", "").strip(), max_length=50) if form.get("visibility") == "code" else "",
        created_by=user_id,
    )
```

- [ ] **Step 2: 修改 bank_form.html — 增加可见性选项**

替换 `app/templates/teacher/bank_form.html` 全部内容为：

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
            <label>可见性</label>
            <div style="display:flex;flex-direction:column;gap:0.6rem;margin-top:0.4rem;">
                <label style="cursor:pointer;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);" class="visibility-option" data-vis="public">
                    <input type="radio" name="visibility" value="public" {{ 'checked' if not bank or bank.visibility == 'public' else '' }} style="margin-right:0.4rem;">
                    <strong>🌍 公开</strong>
                    <div style="color:var(--ink-muted);font-size:0.82rem;margin-top:0.2rem;">所有学生均可看到此题库</div>
                </label>
                <label style="cursor:pointer;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);" class="visibility-option" data-vis="private">
                    <input type="radio" name="visibility" value="private" {{ 'checked' if bank and bank.visibility == 'private' else '' }} style="margin-right:0.4rem;">
                    <strong>🔒 仅本班学生</strong>
                    <div style="color:var(--ink-muted);font-size:0.82rem;margin-top:0.2rem;">只有您班级内的学生可以看到</div>
                </label>
                <label style="cursor:pointer;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);" class="visibility-option" data-vis="code">
                    <input type="radio" name="visibility" value="code" {{ 'checked' if bank and bank.visibility == 'code' else '' }} style="margin-right:0.4rem;">
                    <strong>🔑 准入码</strong>
                    <div style="color:var(--ink-muted);font-size:0.82rem;margin-top:0.2rem;">学生需要输入准入码才能看到此题库</div>
                </label>
            </div>
        </div>
        <div class="form-group" id="accessCodeGroup" style="display:none;">
            <label for="access_code">准入码 *</label>
            <input type="text" id="access_code" name="access_code" placeholder="设置一个准入码，如 CLASS2024" value="{{ bank.access_code if bank else '' }}">
            <small style="color:var(--ink-muted);font-size:0.82rem;">将此码告知学生，学生输入后即可访问题库</small>
        </div>
        <div class="form-group">
            <label>描述</label>
            <textarea name="description" rows="3" placeholder="题库说明（可选）">{{ bank.description if bank else '' }}</textarea>
        </div>
        <button type="submit" class="btn btn-primary">创建</button>
        <a href="/teacher/banks" class="btn btn-outline">取消</a>
    </form>
</div>
<script>
document.querySelectorAll('input[name="visibility"]').forEach(function(radio) {
    radio.addEventListener('change', function() {
        var codeGroup = document.getElementById('accessCodeGroup');
        codeGroup.style.display = this.value === 'code' ? 'block' : 'none';
        document.querySelectorAll('.visibility-option').forEach(function(opt) {
            opt.style.borderColor = 'var(--ivory-dark)';
            opt.style.background = '';
        });
        if (this.closest('.visibility-option')) {
            this.closest('.visibility-option').style.borderColor = 'var(--gold)';
            this.closest('.visibility-option').style.background = 'var(--gold-bg)';
        }
    });
});
document.addEventListener('DOMContentLoaded', function() {
    var checked = document.querySelector('input[name="visibility"]:checked');
    if (checked) {
        checked.dispatchEvent(new Event('change'));
    }
});
</script>
{% endblock %}
```

- [ ] **Step 3: 修改 banks.html — 显示可见性标签**

替换 `app/templates/teacher/banks.html` 全部内容为：

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
    <table class="data-table">
        <thead><tr><th>名称</th><th>科目</th><th>学期</th><th>类型</th><th>可见性</th><th>题目数</th><th>操作</th></tr></thead>
        <tbody>
        {% for b in banks %}
        <tr>
            <td><strong>{{ b.name }}</strong></td>
            <td>{{ b.subject }}</td>
            <td>{{ b.semester or '全部' }}</td>
            <td>{{ '真题' if b.bank_type == 'exam' else '模拟' if b.bank_type == 'mock' else '自定义' }}</td>
            <td>
                {% if b.visibility == 'public' %}
                    <span class="badge badge-correct">🌍 公开</span>
                {% elif b.visibility == 'private' %}
                    <span class="badge badge-subject">🔒 本班</span>
                {% elif b.visibility == 'code' %}
                    <span class="badge badge-wrong">🔑 准入码</span>
                {% endif %}
            </td>
            <td>{{ b.q_count }}</td>
            <td>
                <form action="/teacher/banks/{{ b.id }}/delete" method="POST" style="display:inline;" onsubmit="return confirm('确定删除？题库中的题目不会被删除。')">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-outline btn-sm">删除</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="color:var(--ink-muted);">还没有题库，点击上方按钮创建</p>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 4: 写测试**

在 `tests/test_teacher_bank_visibility.py` 中追加：

```python
def test_teacher_create_bank_with_visibility(client, db_session):
    from app.models import User, SiteConfig, QuestionBank
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_vis", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    login_as(client, "teacher_vis", "teacher1234a")

    csrf = get_csrf_token(client)
    resp = client.post("/teacher/banks/create", data={
        "_csrf_token": csrf,
        "name": "私有题库",
        "subject": "数学",
        "visibility": "private",
    }, follow_redirects=True)
    assert resp.status_code == 200

    bank = db_session.query(QuestionBank).filter(QuestionBank.name == "私有题库").first()
    assert bank is not None
    assert bank.visibility == "private"
    assert bank.access_code == ""


def test_teacher_create_bank_with_access_code(client, db_session):
    from app.models import User, SiteConfig, QuestionBank
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_code", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    login_as(client, "teacher_code", "teacher1234a")

    csrf = get_csrf_token(client)
    resp = client.post("/teacher/banks/create", data={
        "_csrf_token": csrf,
        "name": "准入码题库",
        "subject": "英语",
        "visibility": "code",
        "access_code": "MATH2024",
    }, follow_redirects=True)
    assert resp.status_code == 200

    bank = db_session.query(QuestionBank).filter(QuestionBank.name == "准入码题库").first()
    assert bank is not None
    assert bank.visibility == "code"
    assert bank.access_code == "MATH2024"
```

- [ ] **Step 5: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/test_teacher_bank_visibility.py -v --tb=short`
Expected: PASS

---

### Task 3: 学生端 — 浏览页教师题库分区 + 准入码验证

**Files:**
- Modify: `app/routers/pages.py`
- Modify: `app/templates/browse.html`
- Modify: `app/routers/student.py`

- [ ] **Step 1: 修改 pages.py — browse 函数增加教师题库查询和准入码验证**

在 `app/routers/pages.py` 中，添加导入：

```python
from app.models import Question, Record, User, QuestionBank, ClassGroup, ClassMember, SUBJECTS, SEMESTERS, Feedback
```

（替换原来的导入行，增加了 ClassGroup 和 ClassMember）

在 `browse` 函数的参数列表中，在 `bank_id: int = 0,` 之后添加：

```python
    access_code_input: str = "",
```

在 `browse` 函数中，在 `banks = []` 行之后，添加教师题库查询逻辑：

```python
    teacher_banks = []
    if logged_in and user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "student":
            tb_query = db.query(QuestionBank).filter(QuestionBank.created_by != None)
            all_teacher_banks = tb_query.order_by(QuestionBank.name).all()
            student_class_ids = [c.class_id for c in db.query(ClassMember).filter(ClassMember.user_id == user_id).all()]
            unlocked_bank_ids = request.session.get("unlocked_banks", [])
            for b in all_teacher_banks:
                if b.visibility == "public":
                    q_count = db.query(Question).filter(Question.bank_id == b.id).count()
                    teacher_banks.append({"id": b.id, "name": b.name, "subject": b.subject, "visibility": "public", "q_count": q_count, "creator": db.query(User).filter(User.id == b.created_by).first()})
                elif b.visibility == "private":
                    bank_creator = db.query(User).filter(User.id == b.created_by).first()
                    if bank_creator:
                        creator_class_ids = [c.id for c in db.query(ClassGroup).filter(ClassGroup.created_by == bank_creator.id).all()]
                        if set(student_class_ids) & set(creator_class_ids):
                            q_count = db.query(Question).filter(Question.bank_id == b.id).count()
                            teacher_banks.append({"id": b.id, "name": b.name, "subject": b.subject, "visibility": "private", "q_count": q_count, "creator": bank_creator})
                elif b.visibility == "code":
                    if b.id in unlocked_bank_ids:
                        q_count = db.query(Question).filter(Question.bank_id == b.id).count()
                        creator = db.query(User).filter(User.id == b.created_by).first()
                        teacher_banks.append({"id": b.id, "name": b.name, "subject": b.subject, "visibility": "code", "q_count": q_count, "creator": creator})

            if access_code_input:
                matched = db.query(QuestionBank).filter(QuestionBank.visibility == "code", QuestionBank.access_code == access_code_input).first()
                if matched and matched.id not in unlocked_bank_ids:
                    unlocked_bank_ids.append(matched.id)
                    request.session["unlocked_banks"] = unlocked_bank_ids
                    q_count = db.query(Question).filter(Question.bank_id == matched.id).count()
                    creator = db.query(User).filter(User.id == matched.created_by).first()
                    teacher_banks.append({"id": matched.id, "name": matched.name, "subject": matched.subject, "visibility": "code", "q_count": q_count, "creator": creator})
```

在 TemplateResponse 的 context dict 中添加 `"teacher_banks": teacher_banks`。

- [ ] **Step 2: 添加准入码验证路由**

在 `app/routers/pages.py` 末尾添加：

```python
@router.post("/browse/unlock-bank")
async def unlock_bank(request: Request, db: Annotated[Session, Depends(get_db)]):
    await validate_csrf_async(request)
    form = await request.form()
    access_code = sanitize_input(form.get("access_code", "").strip(), max_length=50)
    if not access_code:
        return RedirectResponse(url="/browse", status_code=303)
    return RedirectResponse(url=f"/browse?access_code_input={access_code}", status_code=303)
```

- [ ] **Step 3: 修改 browse.html — 增加教师题库分区**

在 `app/templates/browse.html` 的 `{% block content %}` 开头、`<h1>📚 题库浏览</h1>` 之后，添加教师题库分区：

```html
{% if teacher_banks %}
<div class="card" style="margin-bottom:1.5rem;">
    <h2>👨‍🏫 教师题库</h2>
    <div class="chapter-list">
        {% for b in teacher_banks %}
        <a href="/student/practice?bank_id={{ b.id }}" class="chapter-item">
            <span class="chapter-name">
                {{ b.name }}
                {% if b.visibility == 'public' %}
                    <span class="badge badge-correct" style="font-size:0.7rem;">公开</span>
                {% elif b.visibility == 'private' %}
                    <span class="badge badge-subject" style="font-size:0.7rem;">本班</span>
                {% elif b.visibility == 'code' %}
                    <span class="badge" style="font-size:0.7rem;background:var(--gold-bg);color:var(--gold);">准入码</span>
                {% endif %}
            </span>
            <span style="color:var(--ink-muted);font-size:0.85rem;">{{ b.creator.display_name or b.creator.username if b.creator else '' }}</span>
            <span class="chapter-count">{{ b.q_count }} 题</span>
            <span class="chapter-action">去刷题 →</span>
        </a>
        {% endfor %}
    </div>
</div>
{% endif %}

<div class="card" style="margin-bottom:1.5rem;">
    <h2>🔑 输入准入码</h2>
    <form action="/browse/unlock-bank" method="post" style="display:flex;gap:0.5rem;align-items:center;">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <input type="text" name="access_code" placeholder="输入教师提供的准入码" style="flex:1;">
        <button type="submit" class="btn btn-primary btn-sm">解锁</button>
    </form>
</div>
```

注意：需要在 browse 函数的 TemplateResponse context 中添加 `"csrf_token": request.session.get("csrf_token", "")`。

- [ ] **Step 4: 修改 student.py — practice 支持 bank_id 参数**

在 `app/routers/student.py` 的 `practice_page` 函数参数中，在 `mode: str = "smart",` 之后添加：

```python
    bank_id: int = 0,
```

在 `practice_page` 函数的查询逻辑中，在 `query = db.query(Question)` 之后添加 bank_id 过滤：

```python
        if bank_id:
            query = query.filter(Question.bank_id == bank_id)
```

同样在 smart/adaptive 模式的 `_smart_select` 调用前，如果 bank_id 存在，需要先过滤。在 `if mode in ("smart", "adaptive"):` 分支中：

```python
    if mode in ("smart", "adaptive"):
        smart_result = _smart_select(user_id, db, subject, semester, chapter, count, mode=mode, bank_id=bank_id)
        selected = [q for q, _ in smart_result]
```

需要修改 `_smart_select` 函数签名，添加 `bank_id: int = 0` 参数，并在查询中添加 `if bank_id: query = query.filter(Question.bank_id == bank_id)` 过滤。

- [ ] **Step 5: 写测试**

在 `tests/test_teacher_bank_visibility.py` 中追加：

```python
def test_student_sees_public_teacher_bank(client, db_session):
    from app.models import User, QuestionBank, Question, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_pub", password_hash=User.hash_password("teacher1234a"), role="teacher", display_name="张老师")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="公开题库", subject="数学", visibility="public", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    q = Question(subject="数学", content="1+1=?", answer="2", bank_id=bank.id, created_by=teacher.id)
    db_session.add(q)
    db_session.commit()

    student = User(username="student_pub", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_pub", "student1234a")

    resp = client.get("/browse", follow_redirects=True)
    assert resp.status_code == 200
    assert "公开题库" in resp.text


def test_student_cannot_see_private_bank_not_in_class(client, db_session):
    from app.models import User, QuestionBank, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_priv", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="私有题库", subject="数学", visibility="private", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()

    student = User(username="student_priv", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_priv", "student1234a")

    resp = client.get("/browse", follow_redirects=True)
    assert resp.status_code == 200
    assert "私有题库" not in resp.text


def test_student_unlock_bank_with_access_code(client, db_session):
    from app.models import User, QuestionBank, Question, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_code2", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="准入码题库", subject="英语", visibility="code", access_code="SECRET123", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    q = Question(subject="英语", content="hello?", answer="hi", bank_id=bank.id, created_by=teacher.id)
    db_session.add(q)
    db_session.commit()

    student = User(username="student_code", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_code", "student1234a")

    resp = client.get("/browse?access_code_input=SECRET123", follow_redirects=True)
    assert resp.status_code == 200
    assert "准入码题库" in resp.text
```

- [ ] **Step 6: 运行测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/test_teacher_bank_visibility.py -v --tb=short`
Expected: PASS

- [ ] **Step 7: 运行全量测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

---

### Task 4: 浏览页系统题库分区标签 + 最终集成测试

**Files:**
- Modify: `app/templates/browse.html`
- Modify: `app/routers/pages.py`

- [ ] **Step 1: 在 browse.html 中为系统题库添加"系统题库"标题**

在 browse.html 的教师题库分区之后、科目选择之前，将现有的科目选择区域包裹在：

```html
<div class="card">
    <h2>📚 系统题库</h2>
    ...existing subject grid content...
</div>
```

- [ ] **Step 2: 在 browse 函数中为系统题库添加标识**

在 `pages.py` 的 `browse` 函数中，系统题库查询（`db.query(QuestionBank).filter(QuestionBank.subject == subject)`）应排除教师私有/准入码题库，只显示公开的。修改为：

```python
        bank_list = db.query(QuestionBank).filter(
            QuestionBank.subject == subject,
            (QuestionBank.visibility == "public") | (QuestionBank.visibility == None) | (QuestionBank.visibility == "")
        ).order_by(QuestionBank.name).all()
```

这样浏览页的"题库"列表只显示公开题库，私有和准入码题库只在"教师题库"分区中显示。

- [ ] **Step 3: 写集成测试**

在 `tests/test_teacher_bank_visibility.py` 中追加：

```python
def test_browse_bank_list_excludes_private_and_code(client, db_session):
    from app.models import User, QuestionBank, Question, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_browse", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    pub_bank = QuestionBank(name="公开浏览题库", subject="数学", visibility="public", created_by=teacher.id)
    priv_bank = QuestionBank(name="私有浏览题库", subject="数学", visibility="private", created_by=teacher.id)
    code_bank = QuestionBank(name="准入码浏览题库", subject="数学", visibility="code", access_code="X", created_by=teacher.id)
    db_session.add_all([pub_bank, priv_bank, code_bank])
    db_session.commit()

    student = User(username="student_browse", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_browse", "student1234a")

    resp = client.get("/browse?subject=数学", follow_redirects=True)
    assert resp.status_code == 200
    assert "公开浏览题库" in resp.text
    assert "私有浏览题库" not in resp.text
    assert "准入码浏览题库" not in resp.text


def test_student_practice_with_bank_id(client, db_session):
    from app.models import User, QuestionBank, Question, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    teacher = User(username="teacher_prac", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="练习题库", subject="数学", visibility="public", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    q1 = Question(subject="数学", content="3+3=?", answer="6", q_type="choice", option_a="5", option_b="6", option_c="7", option_d="8", bank_id=bank.id, created_by=teacher.id)
    db_session.add(q1)
    db_session.commit()

    student = User(username="student_prac", password_hash=User.hash_password("student1234a"), role="student", is_guest=False)
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_prac", "student1234a")

    resp = client.get(f"/student/practice?bank_id={bank.id}", follow_redirects=True)
    assert resp.status_code == 200
    assert "3+3=?" in resp.text
```

- [ ] **Step 4: 运行全量测试**

Run: `& "C:\Users\Windows 10\python-sdk\python3.13.2\python.exe" -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

---

## 自查清单

### 1. 需求覆盖

| 需求 | 对应 Task |
|------|-----------|
| 教师创建题库时设置可见性 | Task 2 |
| 公开题库所有学生可见 | Task 3 |
| 私有题库仅本班学生可见 | Task 3 |
| 准入码题库输入码后可见 | Task 3 |
| 学生浏览页看到教师题库分区 | Task 3 |
| 学生选择教师题库刷题 | Task 3 |
| 浏览页系统题库/教师题库分区 | Task 4 |
| 教师题库列表显示可见性标签 | Task 2 |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- `visibility` 字段在 models.py、bank_form.html、pages.py、banks.html 中一致使用 "public"/"private"/"code" 三个值
- `access_code` 字段在 models.py、bank_form.html、pages.py 中一致使用
- `bank_id` 参数在 student.py 的 practice_page 和 _smart_select 中一致使用
- `teacher_banks` 列表中的字典键（id, name, subject, visibility, q_count, creator）在 pages.py 和 browse.html 中一致
