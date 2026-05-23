import pytest
from fastapi.testclient import TestClient
from app.models import User, ClassGroup, Question, Record, Assignment
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
