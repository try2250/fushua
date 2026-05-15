from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, Integer
from typing import Annotated

from app.database import get_db
from app.models import ClassGroup, ClassMember, User, Record, Question, QUESTION_TYPES, AuditLog
from app.auth import require_teacher
from app.security import validate_csrf_async, sanitize_input

router = APIRouter()


@router.get("/teacher/classes")
def teacher_classes(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).order_by(ClassGroup.created_at.desc()).all()
    class_data = []
    for c in classes:
        members = db.query(ClassMember).filter(ClassMember.class_id == c.id).count()
        class_data.append({"id": c.id, "name": c.name, "members": members, "created_at": c.created_at})
    return request.app.state.templates.TemplateResponse(
        "teacher/classes.html",
        {"request": request, "classes": class_data},
    )


@router.post("/classes/create")
async def create_class(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    name = form.get("name", "").strip()
    name = sanitize_input(name, max_length=100)
    if not name:
        return RedirectResponse(url="/teacher/classes", status_code=303)
    cls = ClassGroup(name=name, created_by=user_id)
    db.add(cls)
    db.commit()
    return RedirectResponse(url="/teacher/classes", status_code=303)


@router.get("/classes/{class_id}")
def class_detail(class_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    member_data = (
        db.query(
            User.id,
            User.username,
            User.display_name,
            sa_func.count(Record.id).label("total"),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
        )
        .join(ClassMember, ClassMember.user_id == User.id)
        .outerjoin(Record, Record.user_id == User.id)
        .filter(ClassMember.class_id == class_id)
        .group_by(User.id)
        .all()
    )
    members = [
        {
            "id": m.id,
            "username": m.username,
            "display_name": m.display_name,
            "total": m.total,
            "correct": int(m.correct or 0),
            "accuracy": round((m.correct or 0) / m.total * 100, 1) if m.total > 0 else 0,
        }
        for m in member_data
    ]
    members.sort(key=lambda x: x["accuracy"])
    return request.app.state.templates.TemplateResponse(
        "teacher/class_detail.html",
        {"request": request, "class_info": cls, "members": members},
    )


@router.post("/classes/{class_id}/members/add")
async def add_member(class_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    form = await request.form()
    username = form.get("username", "").strip()
    user = db.query(User).filter(User.username == username, User.role == "student").first()
    if user:
        if user.class_id and user.class_id != class_id:
            return request.app.state.templates.TemplateResponse(
                "teacher/class_detail.html",
                {"request": request, "class_info": cls, "error": f"学生 {username} 已在其他班级，请先移出原班级"},
            )
        existing = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.user_id == user.id).first()
        if not existing:
            db.add(ClassMember(class_id=class_id, user_id=user.id))
        if not user.class_id:
            user.class_id = class_id
        if user.is_guest:
            user.is_guest = False
            user.guest_expires_at = None
            user.join_mode = "formal"
        db.commit()
    return RedirectResponse(url=f"/classes/{class_id}", status_code=303)


@router.post("/classes/{class_id}/members/{member_id}/remove")
async def remove_member(class_id: int, member_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.created_by == user_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    member = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.user_id == member_id).first()
    if member:
        removed_user_id = member.user_id
        removed_user = db.query(User).filter(User.id == removed_user_id).first()
        db.add(AuditLog(
            actor_id=user_id,
            action="remove_member",
            target_type="class_member",
            target_id=member_id,
            detail=f"从班级「{cls.name}」移出学生「{removed_user.username if removed_user else member_id}」"
        ))
        db.delete(member)
        user = db.query(User).filter(User.id == removed_user_id).first()
        if user and user.class_id == class_id:
            user.class_id = None
        db.commit()
    return RedirectResponse(url=f"/classes/{class_id}", status_code=303)


@router.post("/classes/{class_id}/delete")
async def delete_class(class_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    cls = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.created_by == user_id).first()
    if cls:
        db.add(AuditLog(
            actor_id=user_id,
            action="delete_class",
            target_type="class",
            target_id=class_id,
            detail=f"删除班级「{cls.name}」"
        ))
        db.query(ClassMember).filter(ClassMember.class_id == class_id).delete()
        db.query(User).filter(User.class_id == class_id).update({"class_id": None})
        db.delete(cls)
        db.commit()
    return RedirectResponse(url="/teacher/classes", status_code=303)
