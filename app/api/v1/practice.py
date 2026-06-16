"""答题练习 API — Plan 2.1"""
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.core.deps import get_current_user
from app.models import User, Question, ClassGroup, ClassMember
from app.services.leaderboard_service import leaderboard_service
from app.core.security import get_week_start
from app.schemas.common import ResponseModel


router = APIRouter(prefix="/practice", tags=["练习"])


@router.get("/start", response_model=ResponseModel[dict])
def start_practice(
    class_id: int = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回一组随机题目用于练习。"""
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    member = db.query(ClassMember).filter(
        ClassMember.class_id == class_id, ClassMember.user_id == current_user.id
    ).first()
    if not member and current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="未加入该班级")

    questions = db.query(Question).filter(
        Question.created_by == cls.created_by
    ).order_by(Question.id).all()
    if len(questions) < limit:
        limit = len(questions)
    selected = random.sample(questions, limit) if questions else []
    import secrets
    session_id = secrets.token_hex(8)
    return ResponseModel(data={
        "session_id": session_id,
        "questions": [{
            "id": q.id, "content": q.content,
            "q_type": q.q_type,
            "option_a": q.option_a, "option_b": q.option_b,
            "option_c": q.option_c, "option_d": q.option_d,
        } for q in selected],
    })


@router.get("/leaderboard", response_model=ResponseModel[list])
def get_leaderboard(
    class_id: int = Query(...),
    week_start: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级本周排行榜。"""
    if week_start:
        from datetime import datetime
        ws_date = datetime.strptime(week_start, "%Y-%m-%d").date()
    else:
        ws_date = get_week_start()
    board = leaderboard_service.get_class_leaderboard(db, class_id, ws_date)
    return ResponseModel(data=board)


@router.get("/chapter-map", response_model=ResponseModel[list])
def chapter_map(subject: str = Query("数学"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """返回指定学科所有章节的掌握度网格。"""
    chapters = db.query(Question.chapter).filter(Question.subject == subject).distinct().all()
    result = []
    for (ch,) in chapters:
        result.append({
            "chapter": ch,
            "total": 0, "mastered": 0,
            "color": "grey",
        })
    return ResponseModel(data=result)
