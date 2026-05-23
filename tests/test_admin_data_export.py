import pytest
from app.models import User, ClassGroup, Question, Record, Favorite, ClassMember
from sqlalchemy.orm import Session
from tests.conftest import login_as


def test_admin_can_view_export_page(client, db: Session):
    """测试管理员可以访问数据导出页面"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 访问导出页面
    response = client.get("/admin/data-export")

    assert response.status_code == 200
    assert "数据导出" in response.text


def test_admin_can_export_users(client, db: Session):
    """测试管理员可以导出用户数据"""
    # 创建管理员和测试用户
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test Student"
    )
    db.add_all([admin, student])
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 导出用户数据
    response = client.get("/admin/export/users")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "用户名" in content
    assert "student1" in content


def test_admin_can_export_classes(client, db: Session):
    """测试管理员可以导出班级数据"""
    # 创建管理员和教师
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Test Teacher"
    )
    db.add_all([admin, teacher])
    db.commit()

    # 创建班级
    cls = ClassGroup(
        name="测试班级",
        created_by=teacher.id
    )
    db.add(cls)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 导出班级数据
    response = client.get("/admin/export/classes")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "班级名称" in content
    assert "测试班级" in content


def test_admin_can_export_questions(client, db: Session):
    """测试管理员可以导出题目数据"""
    # 创建管理员和教师
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Test Teacher"
    )
    db.add_all([admin, teacher])
    db.commit()

    # 创建题目
    question = Question(
        subject="数学",
        content="测试题目",
        option_a="选项A",
        option_b="选项B",
        option_c="选项C",
        option_d="选项D",
        answer="A",
        difficulty=1,
        created_by=teacher.id
    )
    db.add(question)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 导出题目数据
    response = client.get("/admin/export/questions")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "题目内容" in content
    assert "测试题目" in content


def test_admin_can_export_statistics(client, db: Session):
    """测试管理员可以导出统计数据"""
    # 创建管理员、教师和学生
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Test Teacher"
    )
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test Student"
    )
    db.add_all([admin, teacher, student])
    db.commit()

    # 创建题目和答题记录
    question = Question(
        subject="数学",
        content="测试题目",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        answer="A",
        difficulty=1,
        created_by=teacher.id
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

    # 导出统计数据
    response = client.get("/admin/export/statistics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "学生ID" in content
    assert "student1" in content


def test_non_admin_cannot_export(client, db: Session):
    """测试非管理员无法导出数据"""
    # 创建学生
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test Student"
    )
    db.add(student)
    db.commit()

    # 学生登录
    login_as(client, "student1", "Test123!@#")

    # 尝试访问导出页面
    response = client.get("/admin/data-export")
    assert response.status_code == 403

    # 尝试导出用户数据
    response = client.get("/admin/export/users")
    assert response.status_code == 403
