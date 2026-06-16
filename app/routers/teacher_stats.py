"""教师统计页"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Assignment, ClassGroup
from app.auth import require_teacher
from app.services.assignment_service import get_assignment_stats as _get_assignment_stats
import json

router = APIRouter()


@router.get("/teacher/assignments/{assignment_id}/stats")
def stats_page(assignment_id: int, request: Request, db: Session = Depends(get_db),
               teacher_id: int = Depends(require_teacher)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment or assignment.created_by != teacher_id:
        return request.app.state.templates.TemplateResponse("teacher/assignment_stats.html",
            {"request": request, "error": "作业不存在"}, status_code=404)
    cls = db.query(ClassGroup).filter(ClassGroup.id == assignment.class_id).first()
    stats = _get_assignment_stats(db, assignment_id, teacher_id)
    return request.app.state.templates.TemplateResponse("teacher/assignment_stats.html", {
        "request": request, "assignment": assignment, "cls": cls,
        "stats": stats, "stats_json": json.dumps(stats),
    })
