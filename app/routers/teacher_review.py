"""教师批改页"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Assignment, AssignmentRecord, Question, User, QuestionComment, ClassGroup
from app.auth import require_teacher

router = APIRouter()

@router.get("/teacher/assignments/{assignment_id}/review")
def review_page(assignment_id: int, request: Request, db: Session = Depends(get_db),
                teacher_id: int = Depends(require_teacher)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment or assignment.created_by != teacher_id:
        return request.app.state.templates.TemplateResponse("teacher/review.html",
            {"request": request, "error": "作业不存在"}, status_code=404)
    cls = db.query(ClassGroup).filter(ClassGroup.id == assignment.class_id).first()
    question_ids = eval(assignment.question_ids) if assignment.question_ids else []
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
    records = db.query(AssignmentRecord).filter(AssignmentRecord.assignment_id == assignment_id).all()
    return request.app.state.templates.TemplateResponse("teacher/review.html", {
        "request": request, "assignment": assignment, "cls": cls,
        "questions": questions, "records": records,
    })
