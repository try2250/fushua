# 付刷（Fushua）长期开发路线图

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将付刷从一个基础刷题平台升级为功能完善的中学生学习系统，覆盖学习体验、题目内容、数据分析、系统优化四大方向。

**Architecture:** 基于 FastAPI + Jinja2 + SQLAlchemy + SQLite 的服务端渲染架构，逐步引入前端增强（HTMX 实现局部刷新、KaTeX 渲染数学公式）。数据层通过 FieldConfig + extra_data JSON 实现灵活扩展。

**Tech Stack:** Python 3.x, FastAPI, SQLAlchemy, Jinja2, SQLite, bcrypt, pytest, HTMX (新增), KaTeX (新增)

---

## 阶段一：题目内容增强（优先级最高）

> 题目是刷题平台的核心，增强题目表达能力直接影响学习效果。

### Task 1: 题目图片支持

**Files:**
- Create: `app/routers/upload.py`
- Modify: `app/models.py` (Question 添加 image_url 字段)
- Modify: `app/routers/teacher.py` (出题/编辑支持图片上传)
- Modify: `app/templates/teacher/question_form.html` (添加图片上传区域)
- Modify: `app/templates/student/practice.html` (显示题目图片)
- Modify: `app/templates/teacher/questions.html` (图片缩略图)
- Test: `tests/test_image_upload.py`

- [ ] **Step 1: 写失败测试 — Question 有 image_url 字段**

```python
# tests/test_image_upload.py
from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import Question

class TestQuestionImage:
    def test_question_has_image_url_field(self, client, db_session):
        teacher = create_test_user(db_session, "imgteacher", "teacher")
        q = Question(
            subject="数学", content="看图答题", answer="A",
            image_url="/uploads/test.png", created_by=teacher.id,
        )
        db_session.add(q)
        db_session.commit()
        assert q.image_url == "/uploads/test.png"

    def test_create_question_with_image(self, client, db_session):
        register_and_login(client, "imgteacher2", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/create", data={
            "subject": "数学", "q_type": "choice", "difficulty": "2",
            "content": "看图选答案", "option_a": "A", "option_b": "B",
            "option_c": "C", "option_d": "D", "answer": "A",
            "image_url": "/uploads/geometry.png",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        q = db_session.query(Question).first()
        assert q.image_url == "/uploads/geometry.png"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `py -m pytest tests/test_image_upload.py -v`
Expected: FAIL — Question 没有 image_url 列

- [ ] **Step 3: 在 Question 模型添加 image_url 字段**

```python
# app/models.py — Question 类中添加
image_url = Column(String(500), default="")
```

- [ ] **Step 4: 在出题表单添加图片URL输入框**

```html
<!-- app/templates/teacher/question_form.html — explanation 之后添加 -->
<div class="form-group">
    <label for="image_url">题目图片URL</label>
    <input type="text" id="image_url" name="image_url" placeholder="输入图片地址（可选）" value="{{ question.image_url if question else '' }}">
    <small class="hint">支持输入图片链接地址，将显示在题目内容上方</small>
</div>
```

- [ ] **Step 5: 在 student practice.html 显示图片**

```html
<!-- 在题目内容前添加 -->
{% if q.image_url %}
<div class="question-image">
    <img src="{{ q.image_url }}" alt="题目图片" loading="lazy">
</div>
{% endif %}
```

- [ ] **Step 6: 在 teacher create/edit 路由处理 image_url**

```python
# app/routers/teacher.py — create_question 和 edit_question 中
question.image_url = form.get("image_url", "")
```

- [ ] **Step 7: 运行测试验证通过**

Run: `py -m pytest tests/test_image_upload.py -v`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add -A && git commit -m "feat: add image support for questions"
```

---

### Task 2: LaTeX 数学公式渲染

**Files:**
- Modify: `app/templates/base.html` (引入 KaTeX CDN)
- Modify: `app/templates/student/practice.html` (公式渲染)
- Modify: `app/templates/student/result.html` (公式渲染)
- Modify: `app/static/style.css` (公式样式)
- Test: `tests/test_latex.py`

- [ ] **Step 1: 写失败测试 — 题目内容中的 LaTeX 标记被正确渲染**

```python
# tests/test_latex.py
from tests.conftest import create_test_user, register_and_login

class TestLatexRendering:
    def test_practice_page_includes_katex(self, client, db_session):
        teacher = create_test_user(db_session, "latexteacher", "teacher")
        from tests.conftest import create_test_question
        create_test_question(db_session, content="解方程 $x^2=4$", created_by=teacher.id)
        register_and_login(client, "latexstudent", "student")
        response = client.get("/student/practice", follow_redirects=True)
        assert response.status_code == 200
        assert "katex" in response.text.lower()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `py -m pytest tests/test_latex.py -v`
Expected: FAIL — 页面不包含 katex

- [ ] **Step 3: 在 base.html 引入 KaTeX CDN**

```html
<!-- app/templates/base.html — </head> 前添加 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {delimiters: [{left: '$$', right: '$$', display: true},{left: '$', right: '$', display: false}]});"></script>
```

- [ ] **Step 4: 添加公式相关 CSS**

```css
/* app/static/style.css */
.question-content .katex { font-size: 1.1em; }
.question-content .katex-display { margin: 0.8rem 0; overflow-x: auto; }
```

- [ ] **Step 5: 运行测试验证通过**

Run: `py -m pytest tests/test_latex.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add KaTeX math formula rendering"
```

---

### Task 3: 题目难度自适应（简单/中等/困难自动推荐）

**Files:**
- Modify: `app/routers/student.py` (_smart_select 增加难度自适应逻辑)
- Modify: `app/templates/student/practice.html` (显示推荐难度)
- Test: `tests/test_adaptive.py`

- [ ] **Step 1: 写失败测试 — 自适应难度推荐**

```python
# tests/test_adaptive.py
from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import Record

class TestAdaptiveDifficulty:
    def test_recommends_easier_after_wrong_answers(self, client, db_session):
        teacher = create_test_user(db_session, "adaptteacher", "teacher")
        for d in [1, 2, 3]:
            create_test_question(db_session, content=f"难度{d}题", difficulty=d, created_by=teacher.id)
        register_and_login(client, "adaptstudent", "student")
        q = db_session.query(Question).filter(Question.difficulty == 3).first()
        for _ in range(3):
            db_session.add(Record(user_id=2, question_id=q.id, user_answer="X", is_correct=False))
            db_session.commit()
        response = client.get("/student/practice?mode=adaptive", follow_redirects=True)
        assert response.status_code == 200
        assert "难度1题" in response.text or "难度2题" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 在 _smart_select 添加 adaptive 模式**

```python
# app/routers/student.py — _smart_select 函数中
if mode == "adaptive":
    recent = db.query(Record).filter(Record.user_id == user_id).order_by(Record.created_at.desc()).limit(10).all()
    if recent:
        accuracy = sum(1 for r in recent if r.is_correct) / len(recent)
        if accuracy < 0.4:
            max_diff = 1
        elif accuracy < 0.7:
            max_diff = 2
        else:
            max_diff = 3
        query = query.filter(Question.difficulty <= max_diff)
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: add adaptive difficulty recommendation"
```

---

## 阶段二：学习体验增强

> 提升学生使用粘性和学习效率。

### Task 4: 题目收藏功能

**Files:**
- Create: `app/models.py` (Favorite 模型)
- Modify: `app/routers/student.py` (收藏/取消收藏/收藏列表)
- Create: `app/templates/student/favorites.html`
- Modify: `app/templates/student/practice.html` (收藏按钮)
- Modify: `app/templates/base.html` (导航添加收藏入口)
- Test: `tests/test_favorites.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_favorites.py
from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Favorite

class TestFavorites:
    def test_add_favorite(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "favstudent", "student")
        csrf = get_csrf_token(client)
        response = client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        assert response.status_code == 303
        fav = db_session.query(Favorite).first()
        assert fav is not None

    def test_favorites_page_lists_favorites(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher2", "teacher")
        q = create_test_question(db_session, content="收藏题", created_by=teacher.id)
        register_and_login(client, "favstudent2", "student")
        csrf = get_csrf_token(client)
        client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        response = client.get("/student/favorites", follow_redirects=True)
        assert response.status_code == 200
        assert "收藏题" in response.text

    def test_remove_favorite(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher3", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "favstudent3", "student")
        csrf = get_csrf_token(client)
        client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        client.post(f"/student/favorites/{q.id}/remove", data={"_csrf_token": csrf})
        count = db_session.query(Favorite).count()
        assert count == 0
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加 Favorite 模型**

```python
# app/models.py
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 在 student.py 添加收藏路由**

```python
@router.post("/favorites/{question_id}/add")
def add_favorite(question_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_login(request)
    existing = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.question_id == question_id).first()
    if not existing:
        db.add(Favorite(user_id=user_id, question_id=question_id))
        db.commit()
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)

@router.post("/favorites/{question_id}/remove")
def remove_favorite(question_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_login(request)
    fav = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.question_id == question_id).first()
    if fav:
        db.delete(fav)
        db.commit()
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)

@router.get("/favorites")
def favorites_page(request: Request, db: Session = Depends(get_db)):
    user_id = require_login(request)
    favs = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    questions = [db.query(Question).get(f.question_id) for f in favs]
    return request.app.state.templates.TemplateResponse("student/favorites.html", {"request": request, "questions": questions})
```

- [ ] **Step 5: 创建收藏页模板和导航入口**

- [ ] **Step 6: 运行测试验证通过**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: add question favorites feature"
```

---

### Task 5: 教师布置作业

**Files:**
- Create: `app/models.py` (Assignment, AssignmentRecord 模型)
- Create: `app/routers/assignment.py`
- Create: `app/templates/teacher/assignments.html`
- Create: `app/templates/teacher/assignment_form.html`
- Create: `app/templates/student/assignments.html`
- Modify: `app/main.py` (注册新路由)
- Modify: `app/templates/base.html` (导航入口)
- Test: `tests/test_assignment.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_assignment.py
from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Assignment

class TestAssignment:
    def test_teacher_create_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "assteacher", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "assteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/assignments/create", data={
            "title": "第一次作业", "description": "完成以下题目",
            "question_ids": str(q.id), "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        a = db_session.query(Assignment).first()
        assert a is not None
        assert a.title == "第一次作业"

    def test_student_see_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "assteacher2", "teacher")
        create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "assteacher2", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "作业1", "question_ids": "1", "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        register_and_login(client, "assstudent", "student")
        response = client.get("/student/assignments", follow_redirects=True)
        assert response.status_code == 200
        assert "作业1" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加 Assignment 和 AssignmentRecord 模型**

```python
# app/models.py
class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    question_ids = Column(Text, nullable=False)  # JSON array of question IDs
    created_by = Column(Integer, ForeignKey("users.id"))
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class AssignmentRecord(Base):
    __tablename__ = "assignment_records"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
```

- [ ] **Step 4: 创建 assignment.py 路由**

- [ ] **Step 5: 创建作业模板页面**

- [ ] **Step 6: 注册路由和导航入口**

- [ ] **Step 7: 运行测试验证通过**

- [ ] **Step 8: 提交**

```bash
git add -A && git commit -m "feat: add teacher assignment system"
```

---

### Task 6: 学习计划与定时提醒

**Files:**
- Create: `app/models.py` (StudyPlan 模型)
- Modify: `app/routers/student.py` (创建/查看计划)
- Create: `app/templates/student/plans.html`
- Create: `app/templates/student/plan_form.html`
- Modify: `app/templates/base.html` (导航入口)
- Test: `tests/test_study_plan.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_study_plan.py
from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import StudyPlan

class TestStudyPlan:
    def test_create_study_plan(self, client, db_session):
        register_and_login(client, "planuser", "student")
        csrf = get_csrf_token(client)
        response = client.post("/student/plans/create", data={
            "subject": "数学", "daily_goal": "20", "semester": "八年级上册",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        plan = db_session.query(StudyPlan).first()
        assert plan is not None
        assert plan.daily_goal == 20

    def test_plans_page_shows_plans(self, client, db_session):
        register_and_login(client, "planuser2", "student")
        csrf = get_csrf_token(client)
        client.post("/student/plans/create", data={
            "subject": "英语", "daily_goal": "15", "_csrf_token": csrf,
        })
        response = client.get("/student/plans", follow_redirects=True)
        assert response.status_code == 200
        assert "英语" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加 StudyPlan 模型**

```python
# app/models.py
class StudyPlan(Base):
    __tablename__ = "study_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(20), nullable=False)
    semester = Column(String(20), default="")
    daily_goal = Column(Integer, default=10)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 在 student.py 添加计划路由**

- [ ] **Step 5: 创建计划模板页面**

- [ ] **Step 6: 运行测试验证通过**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: add study plan feature"
```

---

### Task 7: 学习排行榜

**Files:**
- Modify: `app/routers/pages.py` (添加排行榜路由)
- Create: `app/templates/leaderboard.html`
- Modify: `app/templates/base.html` (导航入口)
- Test: `tests/test_leaderboard.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_leaderboard.py
from tests.conftest import create_test_user, register_and_login

class TestLeaderboard:
    def test_leaderboard_page_accessible(self, client, db_session):
        register_and_login(client, "leaduser", "student")
        response = client.get("/leaderboard", follow_redirects=True)
        assert response.status_code == 200
        assert "排行榜" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 在 pages.py 添加排行榜路由**

- [ ] **Step 4: 创建排行榜模板**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add leaderboard page"
```

---

## 阶段三：数据分析深化

> 让教师和学生都能从数据中获得洞察。

### Task 8: 知识点掌握雷达图

**Files:**
- Modify: `app/templates/student/analysis.html` (雷达图替代简单柱状图)
- Modify: `app/routers/student.py` (提供雷达图数据)
- Modify: `app/static/style.css` (雷达图样式)
- Test: `tests/test_radar_chart.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_radar_chart.py
from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Record

class TestRadarChart:
    def test_analysis_page_has_radar_data(self, client, db_session):
        teacher = create_test_user(db_session, "radarteacher", "teacher")
        create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        create_test_question(db_session, subject="数学", chapter="几何", created_by=teacher.id)
        register_and_login(client, "radarstudent", "student")
        response = client.get("/student/analysis", follow_redirects=True)
        assert response.status_code == 200
        assert "radar" in response.text.lower() or "雷达" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 在 analysis.html 添加 Canvas 雷达图**

- [ ] **Step 4: 在 student.py analysis 路由提供按知识点统计数据**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add radar chart for knowledge point analysis"
```

---

### Task 9: 数据看板与PDF报告导出

**Files:**
- Modify: `app/routers/teacher.py` (数据看板API)
- Modify: `app/templates/teacher/stats.html` (看板UI)
- Create: `app/utils/report.py` (PDF生成工具)
- Modify: `app/routers/teacher.py` (PDF导出路由)
- Test: `tests/test_report.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_report.py
from tests.conftest import create_test_user, register_and_login

class TestReport:
    def test_export_pdf_endpoint(self, client, db_session):
        register_and_login(client, "reportteacher", "teacher")
        response = client.get("/teacher/stats/export/pdf")
        assert response.status_code == 200
        assert "pdf" in response.headers.get("content-type", "").lower() or "application/pdf" in response.headers.get("content-type", "")
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 安装 reportlab 并创建 PDF 生成工具**

- [ ] **Step 4: 添加 PDF 导出路由**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add PDF report export"
```

---

### Task 10: 班级对比分析

**Files:**
- Modify: `app/models.py` (ClassGroup 模型)
- Create: `app/routers/classgroup.py`
- Create: `app/templates/teacher/classes.html`
- Create: `app/templates/teacher/class_detail.html`
- Modify: `app/main.py` (注册路由)
- Test: `tests/test_classgroup.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_classgroup.py
from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import ClassGroup

class TestClassGroup:
    def test_create_class(self, client, db_session):
        register_and_login(client, "classteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/classes/create", data={
            "name": "三年二班", "_csrf_token": csrf,
        })
        assert response.status_code == 303
        c = db_session.query(ClassGroup).first()
        assert c.name == "三年二班"
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加 ClassGroup 模型和路由**

- [ ] **Step 4: 创建班级模板页面**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add class group management"
```

---

## 阶段四：系统与体验优化

> 提升整体使用体验和系统质量。

### Task 11: 深色模式

**Files:**
- Modify: `app/static/style.css` (添加 dark mode 变量和样式)
- Modify: `app/templates/base.html` (主题切换按钮 + JS)
- Test: `tests/test_dark_mode.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dark_mode.py
from tests.conftest import register_and_login

class TestDarkMode:
    def test_base_template_has_theme_toggle(self, client, db_session):
        register_and_login(client, "themeuser", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "theme-toggle" in response.text or "深色" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加 CSS 变量和深色模式样式**

- [ ] **Step 4: 添加主题切换按钮和 JS**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add dark mode support"
```

---

### Task 12: HTMX 局部刷新（提升交互体验）

**Files:**
- Modify: `app/templates/base.html` (引入 HTMX)
- Modify: `app/templates/student/practice.html` (HTMX 提交答题)
- Modify: `app/routers/student.py` (返回 HTML 片段)
- Test: `tests/test_htmx.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_htmx.py
from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token

class TestHtmx:
    def test_base_template_includes_htmx(self, client, db_session):
        register_and_login(client, "htmxuser", "student")
        response = client.get("/", follow_redirects=True)
        assert "htmx" in response.text.lower()
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 在 base.html 引入 HTMX CDN**

- [ ] **Step 4: 逐步改造关键交互为 HTMX**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add HTMX for partial page updates"
```

---

### Task 13: PWA 离线支持

**Files:**
- Create: `app/static/manifest.json`
- Create: `app/static/sw.js`
- Modify: `app/templates/base.html` (注册 Service Worker)
- Test: `tests/test_pwa.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_pwa.py
class TestPWA:
    def test_manifest_json_accessible(self, client, db_session):
        response = client.get("/static/manifest.json")
        assert response.status_code == 200

    def test_base_template_has_manifest_link(self, client, db_session):
        from tests.conftest import register_and_login
        register_and_login(client, "pwauser", "student")
        response = client.get("/", follow_redirects=True)
        assert "manifest" in response.text.lower()
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 创建 manifest.json 和 sw.js**

- [ ] **Step 4: 在 base.html 注册 Service Worker**

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: add PWA offline support"
```

---

### Task 14: 消息通知系统

**Files:**
- Create: `app/models.py` (Notification 模型)
- Create: `app/routers/notification.py`
- Create: `app/templates/components/notifications.html`
- Modify: `app/templates/base.html` (通知铃铛图标)
- Test: `tests/test_notification.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_notification.py
from tests.conftest import create_test_user, register_and_login
from app.models import Notification

class TestNotification:
    def test_notification_model_exists(self, client, db_session):
        user = create_test_user(db_session, "notifuser", "student")
        n = Notification(user_id=user.id, title="测试通知", content="这是一条通知")
        db_session.add(n)
        db_session.commit()
        assert n.id is not None

    def test_notification_bell_in_nav(self, client, db_session):
        register_and_login(client, "belluser", "student")
        response = client.get("/", follow_redirects=True)
        assert "notification" in response.text.lower() or "通知" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加 Notification 模型**

- [ ] **Step 4: 创建通知路由和模板**

- [ ] **Step 5: 在导航栏添加通知铃铛**

- [ ] **Step 6: 运行测试验证通过**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: add notification system"
```

---

### Task 15: 界面美化与动画

**Files:**
- Modify: `app/static/style.css` (动画、过渡、微交互)
- Modify: `app/templates/base.html` (页面过渡动画)
- Test: `tests/test_ui_polish.py`

- [ ] **Step 1: 写失败测试 — CSS 包含动画定义**

```python
# tests/test_ui_polish.py
class TestUIPolish:
    def test_css_has_animations(self, client, db_session):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "@keyframes" in response.text or "transition" in response.text
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 添加动画和微交互样式**

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "feat: add UI animations and micro-interactions"
```

---

## 实施优先级总结

| 优先级 | Task | 功能 | 预计复杂度 |
|--------|------|------|-----------|
| P0 | Task 1 | 题目图片支持 | 中 |
| P0 | Task 2 | LaTeX 公式渲染 | 低 |
| P0 | Task 3 | 难度自适应 | 中 |
| P1 | Task 4 | 题目收藏 | 低 |
| P1 | Task 5 | 教师布置作业 | 高 |
| P1 | Task 6 | 学习计划 | 中 |
| P1 | Task 7 | 排行榜 | 低 |
| P2 | Task 8 | 雷达图 | 中 |
| P2 | Task 9 | PDF 报告 | 高 |
| P2 | Task 10 | 班级管理 | 高 |
| P3 | Task 11 | 深色模式 | 中 |
| P3 | Task 12 | HTMX 局部刷新 | 高 |
| P3 | Task 13 | PWA 离线 | 中 |
| P3 | Task 14 | 通知系统 | 中 |
| P3 | Task 15 | 界面动画 | 低 |

**建议实施顺序：** Task 1 → 2 → 3 → 4 → 7 → 6 → 5 → 8 → 11 → 15 → 12 → 14 → 9 → 10 → 13
