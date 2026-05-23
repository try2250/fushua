import pytest
from datetime import datetime, timedelta
from app.models import Announcement, User
from sqlalchemy.orm import Session


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
