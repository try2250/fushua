"""公告相关API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.database import get_db
from app.models import Announcement, User
from app.core.deps import get_current_user

router = APIRouter()


@router.get("/announcements")
def get_announcements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户可见的公告列表"""

    # 构建查询条件
    conditions = [
        Announcement.is_active == True,
    ]

    # 根据用户角色过滤
    if current_user.role == "student":
        conditions.append(
            Announcement.target_role.in_(["all", "student"])
        )
    elif current_user.role == "teacher":
        conditions.append(
            Announcement.target_role.in_(["all", "teacher"])
        )
    else:
        # 管理员可以看到所有公告
        conditions.append(
            Announcement.target_role.in_(["all", "student", "teacher", "admin"])
        )

    # 查询公告
    announcements = db.query(Announcement).filter(
        and_(*conditions)
    ).order_by(
        Announcement.priority.desc(),
        Announcement.created_at.desc()
    ).all()

    # 过滤过期公告
    now = datetime.now()
    active_announcements = [
        ann for ann in announcements
        if ann.expires_at is None or ann.expires_at > now
    ]

    # 返回公告列表
    return {
        "announcements": [
            {
                "id": ann.id,
                "title": ann.title,
                "content": ann.content,
                "type": ann.type,
                "priority": ann.priority,
                "created_at": ann.created_at.isoformat() if ann.created_at else None,
                "expires_at": ann.expires_at.isoformat() if ann.expires_at else None
            }
            for ann in active_announcements
        ]
    }
