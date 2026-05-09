from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import User, ClassGroup, Notification
from app.auth import require_login, require_non_guest, get_current_user
from app.security import validate_csrf_async, validate_password_strength, check_login_rate_limit, record_login_attempt, sanitize_input

router = APIRouter()


@router.get("/register")
def register_page(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
    return request.app.state.templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None, "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": "student", "preselected_class": ""},
    )


@router.post("/register")
async def register(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,
):
    await validate_csrf_async(request)
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    role = form.get("role", "student")
    display_name = form.get("display_name", "")

    pw_error = validate_password_strength(password)
    if pw_error:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": pw_error, "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
        )
    username = sanitize_input(username, max_length=50)
    display_name = sanitize_input(display_name, max_length=100)
    if len(username) < 2:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": "用户名至少2个字符", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
        )

    if role == "teacher":
        invite_code = form.get("invite_code", "").strip()
        if not invite_code:
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "教师注册需要邀请码", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
            )
        from app.security import verify_teacher_invite_code
        if not verify_teacher_invite_code(invite_code, db):
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return request.app.state.templates.TemplateResponse(
                "register.html", {"request": request, "error": "邀请码无效", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
            )

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return request.app.state.templates.TemplateResponse(
            "register.html", {"request": request, "error": "用户名已存在", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
        )

    from datetime import datetime, timedelta
    is_guest = False
    class_id = None
    guest_expires_at = None

    if role == "student":
        class_id_str = form.get("class_id", "").strip()
        if class_id_str:
            class_id = int(class_id_str)
            cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if not cls:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return request.app.state.templates.TemplateResponse(
                    "register.html", {"request": request, "error": "所选班级不存在，请重新选择", "csrf_token": request.session.get("csrf_token", ""), "classes": classes, "role": role, "preselected_class": ""},
                )
        else:
            is_guest = True
            guest_expires_at = datetime.now() + timedelta(hours=1)

    password_hash = User.hash_password(password)
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        display_name=display_name or username,
        is_guest=is_guest,
        guest_expires_at=guest_expires_at,
        class_id=class_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if class_id:
        from app.models import ClassMember
        existing_member = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.user_id == user.id).first()
        if not existing_member:
            db.add(ClassMember(class_id=class_id, user_id=user.id))
            db.commit()

    request.session["user_id"] = user.id
    if user.is_guest and user.guest_expires_at:
        from datetime import datetime
        if datetime.now() > user.guest_expires_at:
            return RedirectResponse(url="/student/guest-expired", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "login.html", {"request": request, "error": None, "csrf_token": request.session.get("csrf_token", "")}
    )


@router.post("/login")
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)] = None,
):
    await validate_csrf_async(request)
    check_login_rate_limit(username, db)
    user = db.query(User).filter(User.username == username).first()
    if not user or not User.verify_password(user.password_hash, password):
        record_login_attempt(username, db)
        return request.app.state.templates.TemplateResponse(
            "login.html", {"request": request, "error": "用户名或密码错误", "csrf_token": request.session.get("csrf_token", "")}
        )
    if user.is_disabled:
        return request.app.state.templates.TemplateResponse(
            "login.html", {"request": request, "error": "账号已被禁用，请联系管理员", "csrf_token": request.session.get("csrf_token", "")}
        )
    request.session["user_id"] = user.id
    if user.is_guest and user.guest_expires_at:
        from datetime import datetime
        if datetime.now() > user.guest_expires_at:
            return RedirectResponse(url="/student/guest-expired", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/settings")
def settings_page(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    user_id = require_login(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return request.app.state.templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user,
            "pw_error": None,
            "pw_success": None,
            "profile_error": None,
            "profile_success": None,
        },
    )


@router.post("/settings/password")
async def change_password(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    user_id = require_login(request)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    form = await request.form()
    old_password = form.get("old_password", "")
    new_password = form.get("new_password", "")
    confirm_password = form.get("confirm_password", "")
    if not User.verify_password(user.password_hash, old_password):
        return request.app.state.templates.TemplateResponse(
            "settings.html",
            {"request": request, "user": user, "pw_error": "当前密码不正确", "pw_success": None, "profile_error": None, "profile_success": None},
        )
    pw_error = validate_password_strength(new_password)
    if pw_error:
        return request.app.state.templates.TemplateResponse(
            "settings.html",
            {"request": request, "user": user, "pw_error": pw_error, "pw_success": None, "profile_error": None, "profile_success": None},
        )
    if new_password != confirm_password:
        return request.app.state.templates.TemplateResponse(
            "settings.html",
            {"request": request, "user": user, "pw_error": "两次输入的新密码不一致", "pw_success": None, "profile_error": None, "profile_success": None},
        )
    user.password_hash = User.hash_password(new_password)
    db.commit()
    return request.app.state.templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "pw_error": None, "pw_success": "密码修改成功", "profile_error": None, "profile_success": None},
    )


@router.post("/settings/profile")
async def update_profile(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    user_id = require_login(request)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    form = await request.form()
    display_name = sanitize_input(form.get("display_name", ""), max_length=100)
    if not display_name:
        return request.app.state.templates.TemplateResponse(
            "settings.html",
            {"request": request, "user": user, "pw_error": None, "pw_success": None, "profile_error": "昵称不能为空", "profile_success": None},
        )
    user.display_name = display_name
    db.commit()
    db.refresh(user)
    return request.app.state.templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "pw_error": None, "pw_success": None, "profile_error": None, "profile_success": "资料修改成功"},
    )
