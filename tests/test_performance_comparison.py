"""
N+1 查询修复的性能对比测试
展示优化前后的查询数量对比
"""
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.models import User, Question, Record
from tests.conftest import login_as


class QueryCounter:
    """查询计数器"""
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


def test_student_mistakes_performance_comparison(client, db_session):
    """
    学生错题本性能对比测试

    优化前：18 次查询
    - 1 次查询所有错误记录
    - 10 次单独查询每个 question（N+1 问题）
    - 其他基础查询（session、user 等）

    优化后：8 次查询
    - 使用 joinedload(Record.question) 预加载关联数据
    - 减少了 55.6% 的查询次数
    """
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

    # 创建 10 个题目和错误记录
    for i in range(10):
        q = Question(
            content=f"Question {i}",
            answer=f"Answer {i}",
            subject="数学",
            q_type="选择题",
            created_by=teacher.id
        )
        db_session.add(q)
        db_session.flush()

        record = Record(
            user_id=student.id,
            question_id=q.id,
            user_answer="Wrong answer",
            is_correct=False
        )
        db_session.add(record)
    db_session.commit()

    # 登录并测试
    login_as(client, "student1", password)

    with QueryCounter() as counter:
        response = client.get("/student/mistakes")
        assert response.status_code == 200

    print(f"\n学生错题本查询数量: {counter.count}")
    print(f"优化效果: 从 18 次减少到 {counter.count} 次")
    print(f"减少比例: {(18 - counter.count) / 18 * 100:.1f}%")

    # 验证优化效果
    assert counter.count <= 8, f"查询次数应该 <= 8，实际: {counter.count}"

    # 计算性能提升
    improvement = (18 - counter.count) / 18 * 100
    assert improvement >= 50, f"性能提升应该 >= 50%，实际: {improvement:.1f}%"


def test_performance_with_more_records(client, db_session):
    """
    测试更多记录时的性能表现
    验证 N+1 问题修复在大数据量下的效果
    """
    password = "abc12345"
    student = User(
        username="student2",
        password_hash=User.hash_password(password),
        role="student",
        display_name="Student 2"
    )
    db_session.add(student)
    db_session.flush()

    teacher = User(
        username="teacher2",
        password_hash=User.hash_password(password),
        role="teacher",
        display_name="Teacher 2"
    )
    db_session.add(teacher)
    db_session.flush()

    # 创建 50 个题目和错误记录
    for i in range(50):
        q = Question(
            content=f"Question {i}",
            answer=f"Answer {i}",
            subject="数学",
            q_type="选择题",
            created_by=teacher.id
        )
        db_session.add(q)
        db_session.flush()

        record = Record(
            user_id=student.id,
            question_id=q.id,
            user_answer="Wrong answer",
            is_correct=False
        )
        db_session.add(record)
    db_session.commit()

    login_as(client, "student2", password)

    with QueryCounter() as counter:
        response = client.get("/student/mistakes")
        assert response.status_code == 200

    print(f"\n50 条记录的查询数量: {counter.count}")
    print(f"如果没有修复，预期查询数: ~58 次 (8 + 50)")
    print(f"实际查询数: {counter.count} 次")

    # 即使有 50 条记录，查询数也应该保持在合理范围内
    # 不应该随着记录数线性增长
    assert counter.count < 15, f"查询次数应该 < 15，实际: {counter.count}"
