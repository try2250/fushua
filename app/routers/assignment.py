import json
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import Question, Assignment, AssignmentRecord, User, Record, QUESTION_TYPES
from app.auth import require_teacher, require_login, require_non_guest, get_current_user
from app.security import validate_csrf_async, sanitize_input

router = APIRouter()


@router.get("/teacher/assignments")
def teacher_assignments(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    assignments = db.query(Assignment).filter(Assignment.created_by == user_id).order_by(Assignment.created_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "teacher/assignments.html",
        {"request": request, "assignments": assignments},
    )


@router.get("/assignments/create")
def create_assignment_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    questions = db.query(Question).order_by(Question.subject, Question.id).all()
    return request.app.state.templates.TemplateResponse(
        "teacher/assignment_form.html",
        {"request": request, "questions": questions, "error": None},
    )


@router.post("/assignments/create")
async def create_assignment(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    title = form.get("title", "")
    description = form.get("description", "")
    question_ids = form.get("question_ids", "")
    deadline = form.get("deadline", "")

    title = sanitize_input(title, max_length=200)
    description = sanitize_input(description, max_length=2000)
    valid_ids = [qid.strip() for qid in question_ids.split(",") if qid.strip().isdigit()]
    if not valid_ids:
        questions = db.query(Question).order_by(Question.subject, Question.id).all()
        return request.app.state.templates.TemplateResponse(
            "teacher/assignment_form.html",
            {"request": request, "questions": questions, "error": "请选择至少一道题目"},
        )
    question_ids = ",".join(valid_ids)

    if not title or not question_ids:
        questions = db.query(Question).order_by(Question.subject, Question.id).all()
        return request.app.state.templates.TemplateResponse(
            "teacher/assignment_form.html",
            {"request": request, "questions": questions, "error": "标题和题目为必填项"},
        )

    assignment = Assignment(
        title=title,
        description=description,
        question_ids=question_ids,
        created_by=user_id,
    )
    if deadline:
        from datetime import datetime
        try:
            assignment.deadline = datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            pass

    db.add(assignment)
    db.commit()
    return RedirectResponse(url="/teacher/assignments", status_code=303)


@router.get("/student/assignments")
def student_assignments(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_non_guest(request, db)
    assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).all()
    completed_ids = set()
    records = db.query(AssignmentRecord).filter(AssignmentRecord.user_id == user_id).all()
    for r in records:
        completed_ids.add(r.assignment_id)
    return request.app.state.templates.TemplateResponse(
        "student/assignments.html",
        {"request": request, "assignments": assignments, "completed_ids": completed_ids},
    )


@router.post("/assignments/{assignment_id}/complete")
async def complete_assignment(assignment_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    existing = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id,
        AssignmentRecord.user_id == user_id,
    ).first()
    if not existing:
        from datetime import datetime
        db.add(AssignmentRecord(assignment_id=assignment_id, user_id=user_id, completed=True, completed_at=datetime.now()))
        db.commit()
    return RedirectResponse(url="/student/assignments", status_code=303)
