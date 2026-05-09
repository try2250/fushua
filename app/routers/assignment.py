import json
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, Integer
from typing import Annotated

from app.database import get_db
from app.models import Question, Assignment, AssignmentRecord, User, Record, ClassGroup, ClassMember, Notification, QUESTION_TYPES
from app.auth import require_teacher, require_login, require_non_guest, get_current_user
from app.security import validate_csrf_async, sanitize_input
from app.utils.validation import parse_int

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
    user_id = require_teacher(request, db)
    questions = db.query(Question).order_by(Question.subject, Question.id).all()
    classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).order_by(ClassGroup.name).all()
    return request.app.state.templates.TemplateResponse(
        "teacher/assignment_form.html",
        {"request": request, "questions": questions, "classes": classes, "error": None},
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
    class_id = form.get("class_id", "")

    title = sanitize_input(title, max_length=200)
    description = sanitize_input(description, max_length=2000)
    valid_ids = [qid.strip() for qid in question_ids.split(",") if qid.strip().isdigit()]
    if not valid_ids:
        questions = db.query(Question).order_by(Question.subject, Question.id).all()
        classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).order_by(ClassGroup.name).all()
        return request.app.state.templates.TemplateResponse(
            "teacher/assignment_form.html",
            {"request": request, "questions": questions, "classes": classes, "error": "请选择至少一道题目"},
        )
    question_ids = ",".join(valid_ids)

    if not title or not question_ids:
        questions = db.query(Question).order_by(Question.subject, Question.id).all()
        classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).order_by(ClassGroup.name).all()
        return request.app.state.templates.TemplateResponse(
            "teacher/assignment_form.html",
            {"request": request, "questions": questions, "classes": classes, "error": "标题和题目为必填项"},
        )

    assignment = Assignment(
        title=title,
        description=description,
        question_ids=question_ids,
        created_by=user_id,
    )
    if class_id and class_id.isdigit():
        assignment.class_id = parse_int(class_id) if class_id else None
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
    user = db.query(User).filter(User.id == user_id).first()
    if user.class_id:
        assignments = db.query(Assignment).filter(
            Assignment.class_id == user.class_id
        ).order_by(Assignment.created_at.desc()).all()
    else:
        assignments = []
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
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    if assignment.class_id:
        member = db.query(ClassMember).filter(
            ClassMember.class_id == assignment.class_id,
            ClassMember.user_id == user_id,
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="您不属于该作业班级")
    existing = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id,
        AssignmentRecord.user_id == user_id,
    ).first()
    if not existing:
        from datetime import datetime
        db.add(AssignmentRecord(assignment_id=assignment_id, user_id=user_id, completed=True, completed_at=datetime.now()))
        db.commit()
    return RedirectResponse(url="/student/assignments", status_code=303)


@router.get("/teacher/assignments/{assignment_id}")
def assignment_detail(assignment_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.created_by == user_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    qid_list = [int(x.strip()) for x in assignment.question_ids.split(",") if x.strip().isdigit()]

    completed_records = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id,
        AssignmentRecord.completed == True,
    ).all()
    completed_user_ids = {r.user_id for r in completed_records}

    if assignment.class_id:
        members = db.query(ClassMember).filter(ClassMember.class_id == assignment.class_id).all()
        student_ids = [m.user_id for m in members]
    else:
        classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).all()
        class_ids = [c.id for c in classes]
        members = db.query(ClassMember).filter(ClassMember.class_id.in_(class_ids)).all() if class_ids else []
        student_ids = list({m.user_id for m in members})

    total_students = len(student_ids)
    completed_count = len(completed_user_ids & set(student_ids))

    students = db.query(User).filter(User.id.in_(student_ids), User.role == "student").all() if student_ids else []
    complete_students = [s for s in students if s.id in completed_user_ids]
    incomplete_students = [s for s in students if s.id not in completed_user_ids]

    question_accuracy = []
    avg_accuracy = 0.0
    top_wrong = []

    if qid_list and completed_user_ids:
        accuracy_rows = (
            db.query(
                Record.question_id,
                sa_func.count(Record.id).label("total"),
                sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
            )
            .filter(
                Record.question_id.in_(qid_list),
                Record.user_id.in_(completed_user_ids),
            )
            .group_by(Record.question_id)
            .all()
        )
        accuracy_map = {row.question_id: {"total": row.total, "correct": int(row.correct or 0)} for row in accuracy_rows}

        questions = db.query(Question).filter(Question.id.in_(qid_list)).all()
        q_map = {q.id: q for q in questions}

        for qid in qid_list:
            info = accuracy_map.get(qid, {"total": 0, "correct": 0})
            acc = round(info["correct"] / info["total"] * 100, 1) if info["total"] > 0 else 0
            q_obj = q_map.get(qid)
            question_accuracy.append({
                "id": qid,
                "content": q_obj.content[:40] if q_obj else f"题目#{qid}",
                "total": info["total"],
                "correct": info["correct"],
                "accuracy": acc,
            })

        total_acc_vals = [qa["accuracy"] for qa in question_accuracy if qa["total"] > 0]
        avg_accuracy = round(sum(total_acc_vals) / len(total_acc_vals), 1) if total_acc_vals else 0

        sorted_by_acc = sorted(question_accuracy, key=lambda x: x["accuracy"])
        top_wrong = sorted_by_acc[:5]

    return request.app.state.templates.TemplateResponse(
        "teacher/assignment_detail.html",
        {
            "request": request,
            "assignment": assignment,
            "total_students": total_students,
            "completed_count": completed_count,
            "avg_accuracy": avg_accuracy,
            "question_accuracy": question_accuracy,
            "top_wrong": top_wrong,
            "complete_students": complete_students,
            "incomplete_students": incomplete_students,
            "reminded_count": 0,
        },
    )


@router.post("/teacher/assignments/{assignment_id}/remind")
async def send_reminder(assignment_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.created_by == user_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    qid_list = [int(x.strip()) for x in assignment.question_ids.split(",") if x.strip().isdigit()]

    completed_records = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id,
        AssignmentRecord.completed == True,
    ).all()
    completed_user_ids = {r.user_id for r in completed_records}

    if assignment.class_id:
        members = db.query(ClassMember).filter(ClassMember.class_id == assignment.class_id).all()
        student_ids = [m.user_id for m in members]
    else:
        classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).all()
        class_ids = [c.id for c in classes]
        members = db.query(ClassMember).filter(ClassMember.class_id.in_(class_ids)).all() if class_ids else []
        student_ids = list({m.user_id for m in members})

    total_students = len(student_ids)
    completed_count = len(completed_user_ids & set(student_ids))

    students = db.query(User).filter(User.id.in_(student_ids), User.role == "student").all() if student_ids else []
    complete_students = [s for s in students if s.id in completed_user_ids]
    incomplete_students = [s for s in students if s.id not in completed_user_ids]

    reminded_count = 0
    for s in incomplete_students:
        db.add(Notification(
            user_id=s.id,
            title="作业提醒",
            content=f"您有一份作业尚未完成：「{assignment.title}」，请尽快完成。",
        ))
        reminded_count += 1
    db.commit()

    question_accuracy = []
    avg_accuracy = 0.0
    top_wrong = []

    if qid_list and completed_user_ids:
        accuracy_rows = (
            db.query(
                Record.question_id,
                sa_func.count(Record.id).label("total"),
                sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
            )
            .filter(
                Record.question_id.in_(qid_list),
                Record.user_id.in_(completed_user_ids),
            )
            .group_by(Record.question_id)
            .all()
        )
        accuracy_map = {row.question_id: {"total": row.total, "correct": int(row.correct or 0)} for row in accuracy_rows}

        questions = db.query(Question).filter(Question.id.in_(qid_list)).all()
        q_map = {q.id: q for q in questions}

        for qid in qid_list:
            info = accuracy_map.get(qid, {"total": 0, "correct": 0})
            acc = round(info["correct"] / info["total"] * 100, 1) if info["total"] > 0 else 0
            q_obj = q_map.get(qid)
            question_accuracy.append({
                "id": qid,
                "content": q_obj.content[:40] if q_obj else f"题目#{qid}",
                "total": info["total"],
                "correct": info["correct"],
                "accuracy": acc,
            })

        total_acc_vals = [qa["accuracy"] for qa in question_accuracy if qa["total"] > 0]
        avg_accuracy = round(sum(total_acc_vals) / len(total_acc_vals), 1) if total_acc_vals else 0

        sorted_by_acc = sorted(question_accuracy, key=lambda x: x["accuracy"])
        top_wrong = sorted_by_acc[:5]

    return request.app.state.templates.TemplateResponse(
        "teacher/assignment_detail.html",
        {
            "request": request,
            "assignment": assignment,
            "total_students": total_students,
            "completed_count": completed_count,
            "avg_accuracy": avg_accuracy,
            "question_accuracy": question_accuracy,
            "top_wrong": top_wrong,
            "complete_students": complete_students,
            "incomplete_students": incomplete_students,
            "reminded_count": reminded_count,
        },
    )
