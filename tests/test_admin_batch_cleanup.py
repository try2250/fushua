import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.models import User, ClassGroup, ClassMember
from sqlalchemy.orm import Session
from tests.conftest import login_as, get_csrf_token


def test_admin_can_preview_test_accounts(client: TestClient, db: Session):
    """测试管理员可以预览测试账号"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 创建测试账号
    test_user1 = User(
        username="test_user1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test User 1"
    )
    test_user2 = User(
        username="test123",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test 123"
    )
    normal_user = User(
        username="student1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Normal Student"
    )
    db.add_all([test_user1, test_user2, normal_user])
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 预览测试账号
    response = client.get("/admin/batch-cleanup?type=test_accounts")

    assert response.status_code == 200
    assert "test_user1" in response.text
    assert "test123" in response.text
    assert "student1" not in response.text  # 正常用户不应出现


def test_admin_can_cleanup_test_accounts(client: TestClient, db: Session):
    """测试管理员可以清理测试账号"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 创建测试账号
    test_user = User(
        username="test_user1",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test User"
    )
    db.add(test_user)
    db.commit()

    # 保存ID以便后续查询
    test_user_id = test_user.id

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 获取CSRF token
    csrf_token = get_csrf_token(client)

    # 执行清理
    response = client.post("/admin/batch-cleanup", data={
        "cleanup_type": "test_accounts",
        "confirm": "yes",
        "_csrf_token": csrf_token
    })

    assert response.status_code == 302  # 重定向

    # 验证测试账号已删除
    deleted_user = db.query(User).filter(User.id == test_user_id).first()
    assert deleted_user is None


def test_admin_can_preview_expired_guests(client: TestClient, db: Session):
    """测试管理员可以预览过期访客"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 创建过期访客（30天前创建）
    old_date = datetime.now() - timedelta(days=31)
    expired_guest = User(
        username="guest_old",
        password_hash=User.hash_password("Test123!@#"),
        role="guest",
        display_name="Old Guest",
        created_at=old_date
    )

    # 创建新访客
    new_guest = User(
        username="guest_new",
        password_hash=User.hash_password("Test123!@#"),
        role="guest",
        display_name="New Guest"
    )

    db.add_all([expired_guest, new_guest])
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 预览过期访客
    response = client.get("/admin/batch-cleanup?type=expired_guests")

    assert response.status_code == 200
    assert "guest_old" in response.text
    assert "guest_new" not in response.text  # 新访客不应出现


def test_admin_can_preview_invalid_data(client: TestClient, db: Session):
    """测试管理员可以预览无效数据"""
    # 创建管理员
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin"
    )
    db.add(admin)
    db.commit()

    # 创建学生但不在任何班级
    orphan_student = User(
        username="orphan",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Orphan Student",
        class_id=None
    )
    db.add(orphan_student)
    db.commit()

    # 管理员登录
    login_as(client, "admin", "Admin123!@#")

    # 预览无效数据
    response = client.get("/admin/batch-cleanup?type=invalid_data")

    assert response.status_code == 200
    assert "orphan" in response.text
