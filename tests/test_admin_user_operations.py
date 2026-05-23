import pytest
from fastapi.testclient import TestClient
from app.models import User, ClassGroup, Question, Record, Assignment, Favorite, StudyPlan, MasteryRecord, ClassMember, Notification, QuestionBank
from sqlalchemy.orm import Session
from tests.conftest import login_as


def test_admin_can_view_user_detail(client: TestClient, db: Session):
    """测试管理员可以查看用户详情"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin User"
    )
    db.add(admin)
    db.commit()

    # 创建测试学生
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test Student"
    )
    db.add(student)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 访问用户详情页
    response = client.get(f"/admin/users/{student.id}")

    assert response.status_code == 200
    assert "Test Student" in response.text
    assert "student1" in response.text


def test_non_admin_cannot_view_user_detail(client: TestClient, db: Session):
    """测试非管理员不能查看用户详情"""
    # 创建教师
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Teacher"
    )
    db.add(teacher)
    db.commit()

    # 创建学生
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Student"
    )
    db.add(student)
    db.commit()

    # 教师登录
    login_as(client, "teacher1", "Test123!@#")

    # 尝试访问用户详情
    response = client.get(f"/admin/users/{student.id}")

    assert response.status_code == 403


def test_admin_can_delete_student(client: TestClient, db: Session):
    """测试管理员可以删除学生"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 创建学生和答题记录
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Student"
    )
    db.add(student)
    db.commit()

    question = Question(
        content="测试题目",
        subject="数学",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        answer="A",
        difficulty=1,
        created_by=admin.id
    )
    db.add(question)
    db.commit()

    record = Record(
        user_id=student.id,
        question_id=question.id,
        user_answer="A",
        is_correct=True
    )
    db.add(record)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 删除学生
    response = client.post(f"/admin/users/{student.id}/delete")

    assert response.status_code == 302  # 重定向

    # 验证学生已删除
    deleted_user = db.query(User).filter(User.id == student.id).first()
    assert deleted_user is None

    # 验证答题记录已删除
    deleted_records = db.query(Record).filter(Record.user_id == student.id).all()
    assert len(deleted_records) == 0


def test_cannot_delete_teacher_with_resources(client: TestClient, db: Session):
    """测试不能删除有资源的教师"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 创建教师和班级
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Teacher"
    )
    db.add(teacher)
    db.commit()

    class_group = ClassGroup(
        name="Test Class",
        created_by=teacher.id
    )
    db.add(class_group)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 尝试删除教师
    response = client.post(f"/admin/users/{teacher.id}/delete")

    # 应该失败并显示错误
    assert response.status_code == 400 or "无法删除" in response.text

    # 验证教师未被删除
    teacher_still_exists = db.query(User).filter(User.id == teacher.id).first()
    assert teacher_still_exists is not None
