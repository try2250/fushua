"""
测试 N+1 查询修复的性能测试
"""
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.models import User, Question, Record, ClassGroup, ClassMember, ClassJoinRequest
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


def test_student_mistakes_n_plus_one_fix(client, db_session):
    """测试学生错题本的 N+1 查询修复"""
    # 创建测试数据
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

    # 为每个题目创建错误记录
    for q in questions:
        record = Record(
            user_id=student.id,
            question_id=q.id,
            user_answer="Wrong answer",
            is_correct=False
        )
        db_session.add(record)
    db_session.commit()

    # 登录学生
    login_as(client, "student1", password)

    # 测试查询数量
    with QueryCounter() as counter:
        response = client.get("/student/mistakes")
        assert response.status_code == 200

    # 修复前：1 (查询 records) + 10 (每个 record 访问 question) + 其他查询 ≈ 15+
    # 修复后：应该显著减少，预期 < 10 次查询
    print(f"\n学生错题本查询数量: {counter.count}")
    print(f"查询详情: {len(counter.queries)} 条")

    # 修复后应该少于 10 次查询（包括 session、user、records 等基础查询）
    assert counter.count < 10, f"查询次数过多: {counter.count}，可能存在 N+1 问题"


def test_teacher_stats_n_plus_one_fix(client, db_session):
    """测试教师统计页面的 N+1 查询修复"""
    # 创建教师
    password = "abc12345"
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password(password),
        role="teacher",
        display_name="Teacher 1"
    )
    db_session.add(teacher)
    db_session.flush()

    # 创建学生
    student = User(
        username="student1",
        password_hash=User.hash_password(password),
        role="student",
        display_name="Student 1"
    )
    db_session.add(student)
    db_session.flush()

    # 创建班级
    class_group = ClassGroup(name="Class 1", created_by=teacher.id)
    db_session.add(class_group)
    db_session.flush()

    # 添加学生到班级
    member = ClassMember(class_id=class_group.id, user_id=student.id)
    db_session.add(member)
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

    # 为每个题目创建多个记录
    for q in questions:
        for _ in range(3):
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
        response = client.get("/teacher/stats")
        assert response.status_code == 200

    # 修复前：基础查询 + N 次访问 question.records ≈ 20+
    # 修复后：应该显著减少，预期 < 15 次查询
    print(f"\n教师统计页面查询数量: {counter.count}")
    print(f"查询详情: {len(counter.queries)} 条")

    # 修复后应该少于 15 次查询
    assert counter.count < 15, f"查询次数过多: {counter.count}，可能存在 N+1 问题"


def test_admin_classes_n_plus_one_fix(client, db_session):
    """测试管理员班级列表的 N+1 查询修复"""
    # 创建管理员
    password = "abc12345"
    admin = User(
        username="admin1",
        password_hash=User.hash_password(password),
        role="admin",
        display_name="Admin 1"
    )
    db_session.add(admin)
    db_session.flush()

    # 创建 10 个班级，每个班级有不同数量的学生
    for i in range(10):
        teacher = User(
            username=f"teacher{i}",
            password_hash=User.hash_password(password),
            role="teacher",
            display_name=f"Teacher {i}"
        )
        db_session.add(teacher)
        db_session.flush()

        class_group = ClassGroup(name=f"Class {i}", created_by=teacher.id)
        db_session.add(class_group)
        db_session.flush()

        # 添加 3 个学生到每个班级
        for j in range(3):
            student = User(
                username=f"student{i}_{j}",
                password_hash=User.hash_password(password),
                role="student",
                display_name=f"Student {i}_{j}"
            )
            db_session.add(student)
            db_session.flush()

            member = ClassMember(class_id=class_group.id, user_id=student.id)
            db_session.add(member)

    db_session.commit()

    # 登录管理员
    login_as(client, "admin1", password)

    # 测试查询数量
    with QueryCounter() as counter:
        response = client.get("/admin/classes")
        assert response.status_code == 200

    # 修复前：1 (classes) + 10×2 (member_count + creator) = 21 次查询
    # 修复后：应该 < 10 次查询
    print(f"\n管理员班级列表查询数量: {counter.count}")
    assert counter.count < 10, f"查询次数过多: {counter.count}，可能存在 N+1 问题"


def test_teacher_join_requests_n_plus_one_fix(client, db_session):
    """测试教师学生管理页面加入请求的 N+1 查询修复"""
    # 创建教师和班级
    password = "abc12345"
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password(password),
        role="teacher",
        display_name="Teacher 1"
    )
    db_session.add(teacher)
    db_session.flush()

    class_group = ClassGroup(name="Class 1", created_by=teacher.id)
    db_session.add(class_group)
    db_session.flush()

    # 创建 10 个加入请求
    for i in range(10):
        student = User(
            username=f"student{i}",
            password_hash=User.hash_password(password),
            role="student",
            display_name=f"Student {i}"
        )
        db_session.add(student)
        db_session.flush()

        join_request = ClassJoinRequest(
            user_id=student.id,
            class_id=class_group.id,
            status="pending"
        )
        db_session.add(join_request)

    db_session.commit()

    # 登录教师
    login_as(client, "teacher1", password)

    # 测试查询数量
    with QueryCounter() as counter:
        response = client.get("/teacher/students")
        assert response.status_code == 200

    # 修复前：基础查询 + 10×2 (user + class) ≈ 25+ 次查询
    # 修复后：应该 < 15 次查询
    print(f"\n教师学生管理页面查询数量: {counter.count}")
    assert counter.count < 15, f"查询次数过多: {counter.count}，可能存在 N+1 问题"
