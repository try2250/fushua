import pytest
from app.models import User, ClassGroup, Question, Record, Favorite, ClassMember
from sqlalchemy.orm import Session
from tests.conftest import login_as


def _platform_login(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={
        "username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


def test_admin_can_view_export_page(client, db: Session, platform_admin):
    """测试管理员可以访问数据导出页面"""
    _platform_login(client, platform_admin)
    response = client.get("/platform/data-export")
    assert response.status_code == 200


def test_admin_can_export_users(client, db: Session, platform_admin):
    """测试管理员可以导出用户数据"""
    student = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test Student"
    )
    db.add(student)
    db.commit()

    _platform_login(client, platform_admin)

    # 导出用户数据
    response = client.get("/platform/export/users")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "username" in content
    assert "student1" in content


def test_admin_can_export_classes(client, db: Session, platform_admin):
    """测试管理员可以导出班级数据"""
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Test Teacher"
    )
    db.add(teacher)
    db.commit()

    # 创建班级
    cls = ClassGroup(
        name="测试班级",
        created_by=teacher.id
    )
    db.add(cls)
    db.commit()

    _platform_login(client, platform_admin)

    # 导出班级数据
    response = client.get("/platform/export/classes")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "name" in content
    assert "测试班级" in content


def test_admin_can_export_questions(client, db: Session, platform_admin):
    """测试管理员可以导出题目数据"""
    teacher = User(
        username="teacher1",
        password_hash=User.hash_password("Test123!@#"),
        role="teacher",
        display_name="Test Teacher"
    )
    db.add(teacher)
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

    _platform_login(client, platform_admin)

    # 导出题目数据
    response = client.get("/platform/export/questions")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "subject" in content
    assert "数学" in content


def test_admin_can_export_statistics(client, db: Session, platform_admin):
    """测试管理员可以导出统计数据"""
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
    db.add_all([teacher, student])
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

    _platform_login(client, platform_admin)

    # 导出统计数据
    response = client.get("/platform/export/statistics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # 验证CSV内容
    content = response.content.decode('utf-8-sig')
    assert "total_users" in content
    assert "total_students" in content


def test_non_admin_cannot_export(client, db: Session):
    """测试非管理员无法导出数据"""
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

    # 尝试访问导出页面 - platform routes redirect non-admin to login
    response = client.get("/platform/data-export", follow_redirects=False)
    assert response.status_code == 303

    # 尝试导出用户数据
    response = client.get("/platform/export/users", follow_redirects=False)
    assert response.status_code == 303
