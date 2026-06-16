"""徽章 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models import Badge, UserBadge, User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/badges", tags=["徽章"])

@router.get("/me", response_model=ResponseModel[list])
def my_badges(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    all_badges = db.query(Badge).order_by(Badge.id).all()
    earned = {ub.badge_id for ub in db.query(UserBadge).filter(UserBadge.user_id == current_user.id).all()}
    result = []
    for b in all_badges:
        result.append({
            "code": b.code, "name": b.name, "description": b.description,
            "icon_url": b.icon_url, "earned": b.id in earned,
        })
    return ResponseModel(data=result)
