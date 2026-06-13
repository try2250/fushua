import pytest
from datetime import datetime, timedelta
from app.models import Announcement, User
from sqlalchemy.orm import Session
from tests.conftest import login_as, get_csrf_token


def _platform_login(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={
        "username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


def test_create_announcement(db: Session):
    """测试创建公告"""
    admin = User(
        username="admin",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin User"
    )
    db.add(admin)
    db.commit()

    announcement = Announcement(
        title="系统维护通知",
        content="系统将于今晚进行维护",
        type="warning",
        target_role="all",
        created_by=admin.id,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db.add(announcement)
    db.commit()

    assert announcement.id is not None
    assert announcement.title == "系统维护通知"
    assert announcement.is_active is True
    assert announcement.priority == 0


def test_announcement_relationships(db: Session):
    """测试公告与创建者的关系"""
    admin = User(
        username="admin2",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin User 2"
    )
    db.add(admin)
    db.commit()

    announcement = Announcement(
        title="测试公告",
        content="测试内容",
        created_by=admin.id
    )
    db.add(announcement)
    db.commit()

    # 验证关系
    assert announcement.creator.username == "admin2"


def test_announcement_default_values(db: Session):
    """测试公告默认值"""
    admin = User(
        username="admin3",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin User 3"
    )
    db.add(admin)
    db.commit()

    # 创建公告，只提供必填字段
    announcement = Announcement(
        title="默认值测试",
        content="测试默认值",
        created_by=admin.id
    )
    db.add(announcement)
    db.commit()

    # 验证默认值
    assert announcement.type == "info"
    assert announcement.target_role == "all"
    assert announcement.is_active is True
    assert announcement.priority == 0
    assert announcement.expires_at is None


def test_announcement_nullable_expires_at(db: Session):
    """测试过期时间可为空"""
    admin = User(
        username="admin4",
        password_hash=User.hash_password("Admin123!@#"),
        role="admin",
        display_name="Admin User 4"
    )
    db.add(admin)
    db.commit()

    # 创建永久有效的公告
    announcement = Announcement(
        title="永久公告",
        content="永久有效",
        created_by=admin.id,
        expires_at=None
    )
    db.add(announcement)
    db.commit()

    assert announcement.expires_at is None


def test_admin_can_view_announcements(client, db: Session, platform_admin):
    """测试管理员可以查看公告列表"""
    # 创建公告
    announcement = Announcement(
        title="测试公告",
        content="这是测试内容",
        type="info",
    )
    db.add(announcement)
    db.commit()

    _platform_login(client, platform_admin)

    # 访问公告列表
    response = client.get("/platform/announcements")

    assert response.status_code == 200
    assert "测试公告" in response.text


def test_admin_can_create_announcement(client, db: Session, platform_admin):
    """测试管理员可以创建公告"""
    _platform_login(client, platform_admin)

    csrf = get_csrf_token(client)

    # 创建公告
    response = client.post("/platform/announcements/create", data={
        "title": "新公告",
        "content": "公告内容",
        "_csrf_token": csrf
    })

    assert response.status_code == 303  # 重定向

    # 验证公告已创建
    announcement = db.query(Announcement).filter(
        Announcement.title == "新公告"
    ).first()
    assert announcement is not None


def test_admin_can_toggle_announcement(client, db: Session, platform_admin):
    """测试管理员可以启用/禁用公告"""
    # 创建公告
    announcement = Announcement(
        title="测试公告",
        content="内容",
        is_active=True
    )
    db.add(announcement)
    db.commit()

    _platform_login(client, platform_admin)

    csrf = get_csrf_token(client)

    # 禁用公告
    response = client.post(f"/platform/announcements/{announcement.id}/toggle", data={
        "_csrf_token": csrf
    })

    assert response.status_code == 303

    # 验证公告已禁用
    db.refresh(announcement)
    assert announcement.is_active is False


def test_student_can_see_active_announcements(client, db: Session):
    """测试学生可以看到启用的公告"""
    # 创建管理员和学生
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
        display_name="Student"
    )
    db.add_all([admin, student])
    db.commit()

    # 创建公告
    announcement1 = Announcement(
        title="学生公告",
        content="这是给学生的公告",
        target_role="student",
        is_active=True,
        created_by=admin.id
    )
    announcement2 = Announcement(
        title="全体公告",
        content="这是给所有人的公告",
        target_role="all",
        is_active=True,
        created_by=admin.id
    )
    announcement3 = Announcement(
        title="教师公告",
        content="这是给教师的公告",
        target_role="teacher",
        is_active=True,
        created_by=admin.id
    )
    announcement4 = Announcement(
        title="禁用公告",
        content="这条公告已禁用",
        target_role="student",
        is_active=False,
        created_by=admin.id
    )
    db.add_all([announcement1, announcement2, announcement3, announcement4])
    db.commit()

    # 学生登录
    login_as(client, "student1", "Test123!@#")

    # 访问学生首页
    response = client.get("/student/dashboard")

    assert response.status_code == 200
    assert "学生公告" in response.text
    assert "全体公告" in response.text
    assert "教师公告" not in response.text  # 不应看到教师公告
    assert "禁用公告" not in response.text  # 不应看到禁用公告
