"""
测试额外发现的 N+1 查询修复
"""
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.models import User, Question, Record, Favorite, ClassGroup, ClassMember
from tests.conftest import login_as


class QueryCounter:
    """查询计数器，用于检测 N+1 查询问题"""
    def __init__(self):
        self.count = 0
        self.queries = []

    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self._before_cursor_execute)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self._before_cursor_execute)

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.queries.append(statement)


def test_student_favorites_n_plus_one_fix(client, db_session):
    """测试学生收藏夹的 N+1 查询修复"""
    password = "abc12345"
    student = User(
        username="student1",
        password_hash=User.hash_password(password),
        role="student",
        display_name="Student 1"
    )
    db_session.add(student)
    db_session.flush()

    teacher = User(
        username="teacher1",
        password_hash=User.hash_password(password),
        role="teacher",
        display_name="Teacher 1"
    )
    db_session.add(teacher)
    db_session.flush()

    # 创建 10 个题目
    questions = []
    for i in range(10):
        q = Question(
            content=f"Question {i}",
            answer=f"Answer {i}",
            subject="数学",
            q_type="选择题",
            created_by=teacher.id
        )
        db_session.add(q)
        questions.append(q)
    db_session.flush()

    # 收藏所有题目
    for q in questions:
        fav = Favorite(user_id=student.id, question_id=q.id)
        db_session.add(fav)
    db_session.commit()

    # 登录学生
    login_as(client, "student1", password)

    # 测试查询数量
    with QueryCounter() as counter:
        response = client.get("/student/favorites")
        assert response.status_code == 200

    # 修复前：1 (查询 favorites) + 10 (每个 favorite 查询 question) ≈ 15+
    # 修复后：应该显著减少，预期 < 10 次查询
    print(f"\n学生收藏夹查询数量: {counter.count}")
    print(f"查询详情: {len(counter.queries)} 条")

    # 修复后应该少于 10 次查询
    assert counter.count < 10, f"查询次数过多: {counter.count}，可能存在 N+1 问题"


def test_teacher_report_export_n_plus_one_fix(client, db_session):
    """测试教师报告导出的 N+1 查询修复"""
    password = "abc12345"
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password(password),
        role="teacher",
        display_name="Teacher 1"
    )
    db_session.add(teacher)
    db_session.flush()

    # 创建班级
    class_group = ClassGroup(name="Class 1", created_by=teacher.id)
    db_session.add(class_group)
    db_session.flush()

    # 创建 5 个学生
    students = []
    for i in range(5):
        student = User(
            username=f"student{i}",
            password_hash=User.hash_password(password),
            role="student",
            display_name=f"Student {i}"
        )
        db_session.add(student)
        students.append(student)
    db_session.flush()

    # 添加学生到班级
    for student in students:
        member = ClassMember(class_id=class_group.id, user_id=student.id)
        db_session.add(member)
    db_session.flush()

    # 创建 5 个题目
    questions = []
    for i in range(5):
        q = Question(
            content=f"Question {i}",
            answer=f"Answer {i}",
            subject="数学",
            q_type="选择题",
            created_by=teacher.id
        )
        db_session.add(q)
        questions.append(q)
    db_session.flush()

    # 为每个学生创建记录
    for student in students:
        for q in questions:
            record = Record(
                user_id=student.id,
                question_id=q.id,
                user_answer="Correct answer",
                is_correct=True
            )
            db_session.add(record)
    db_session.commit()

    # 登录教师
    login_as(client, "teacher1", password)

    # 测试查询数量
    with QueryCounter() as counter:
        response = client.get("/teacher/stats/export/pdf")
        assert response.status_code == 200

    # 修复前：基础查询 + 5 * 2 (每个学生查询 total 和 correct) ≈ 20+
    # 修复后：应该显著减少，预期 < 20 次查询
    print(f"\n教师报告导出查询数量: {counter.count}")
    print(f"查询详情: {len(counter.queries)} 条")

    # 修复后应该少于 20 次查询
    assert counter.count < 20, f"查询次数过多: {counter.count}，可能存在 N+1 问题"
