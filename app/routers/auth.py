from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import User, ClassGroup, Notification, AccountRecoveryRequest
from app.auth import require_login, require_non_guest, get_current_user
from app.security import validate_csrf_async, validate_password_strength, check_login_rate_limit, record_login_attempt, sanitize_input, check_rate_limit, record_rate_limit_attempt, REGISTER_MAX_ATTEMPTS, REGISTER_LOCKOUT_SECONDS, RECOVER_MAX_ATTEMPTS, RECOVER_LOCKOUT_SECONDS
from app.utils.validation import parse_int

router = APIRouter()


def _register_error(request, error, csrf_token, classes, role, preselected_class, client_ip, db):
    record_rate_limit_attempt(f"_register_limit:{client_ip}", db)
    db.commit()
    return request.app.state.templates.TemplateResponse(
        "register.html", {"request": request, "error": error, "csrf_token": csrf_token, "classes": classes, "role": role, "preselected_class": preselected_class},
    )


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
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"_register_limit:{client_ip}", REGISTER_MAX_ATTEMPTS, REGISTER_LOCKOUT_SECONDS, db)
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    role = form.get("role", "student")
    display_name = form.get("display_name", "")

    pw_error = validate_password_strength(password)
    if pw_error:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return _register_error(request, pw_error, request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
    username = sanitize_input(username, max_length=50)
    display_name = sanitize_input(display_name, max_length=100)
    if len(username) < 2:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return _register_error(request, "用户名至少2个字符", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)

    if role == "teacher":
        invite_code = form.get("invite_code", "").strip()
        if not invite_code:
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return _register_error(request, "教师注册需要邀请码", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
        from app.security import verify_teacher_invite_code
        if not verify_teacher_invite_code(invite_code, db):
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return _register_error(request, "邀请码无效", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)

    if role == "admin":
        invite_code = form.get("invite_code", "").strip()
        if not invite_code:
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return _register_error(request, "管理员注册需要邀请码", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
        from app.security import verify_admin_invite_code
        if not verify_admin_invite_code(invite_code, db):
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return _register_error(request, "邀请码无效", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        return _register_error(request, "用户名已存在", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)

    from datetime import datetime, timedelta
    is_guest = False
    class_id = None
    guest_expires_at = None
    join_mode = ""

    if role == "student":
        join_mode = form.get("join_mode", "").strip()
        if join_mode not in ("formal", "apply", "guest"):
            classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
            return _register_error(request, "请选择注册方式", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)

        if join_mode == "formal":
            class_id_str = form.get("class_id", "").strip()
            if not class_id_str:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return _register_error(request, "正式加入班级请选择班级", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
            class_id = parse_int(class_id_str, min_value=1)
            if class_id is None:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return _register_error(request, "所选班级不存在，请重新选择", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
            cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if not cls:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return _register_error(request, "所选班级不存在，请重新选择", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)

        elif join_mode == "apply":
            class_id_str = form.get("class_id", "").strip()
            if not class_id_str:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return _register_error(request, "申请加入班级请选择班级", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
            class_id = parse_int(class_id_str, min_value=1)
            if class_id is None:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return _register_error(request, "所选班级不存在，请重新选择", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
            cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if not cls:
                classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
                return _register_error(request, "所选班级不存在，请重新选择", request.session.get("csrf_token", ""), classes, role, "", client_ip, db)
            is_guest = True
            guest_expires_at = datetime.now() + timedelta(hours=24)
            class_id = None

        elif join_mode == "guest":
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
        join_mode=join_mode,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if join_mode == "apply":
        apply_class_id_str = form.get("class_id", "").strip()
        apply_class_id = parse_int(apply_class_id_str, min_value=1)
        if apply_class_id:
            from app.models import ClassJoinRequest
            existing_req = db.query(ClassJoinRequest).filter(
                ClassJoinRequest.user_id == user.id, ClassJoinRequest.class_id == apply_class_id
            ).first()
            if not existing_req:
                db.add(ClassJoinRequest(
                    user_id=user.id,
                    class_id=apply_class_id,
                    display_name=display_name or username,
                    status="pending",
                ))
                db.commit()

    if class_id:
        from app.models import ClassMember
        existing_member = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.user_id == user.id).first()
        if not existing_member:
            db.add(ClassMember(class_id=class_id, user_id=user.id))
            db.commit()

    request.session["user_id"] = user.id
    if user.force_password_change:
        return RedirectResponse(url="/settings?force_change=1", status_code=303)
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
    if user.force_password_change:
        return RedirectResponse(url="/settings?force_change=1", status_code=303)
    if user.is_guest and user.guest_expires_at:
        from datetime import datetime
        if datetime.now() > user.guest_expires_at:
            return RedirectResponse(url="/student/guest-expired", status_code=303)
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=303)
    if user.role == "teacher":
        return RedirectResponse(url="/teacher/questions", status_code=303)
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
    user.force_password_change = False
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


@router.get("/recover")
def recover_page(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
    return request.app.state.templates.TemplateResponse(
        "recover.html",
        {"request": request, "error": None, "csrf_token": request.session.get("csrf_token", ""), "classes": classes},
    )


@router.post("/recover")
async def recover_submit(request: Request, db: Annotated[Session, Depends(get_db)] = None):
    await validate_csrf_async(request)
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"_recover_limit:{client_ip}", RECOVER_MAX_ATTEMPTS, RECOVER_LOCKOUT_SECONDS, db)
    form = await request.form()
    username = sanitize_input(form.get("username", "").strip(), max_length=50)
    class_id_str = form.get("class_id", "").strip()
    display_name = sanitize_input(form.get("display_name", "").strip(), max_length=100)

    if not username:
        classes = db.query(ClassGroup).order_by(ClassGroup.name).all()
        record_rate_limit_attempt(f"_recover_limit:{client_ip}", db)
        db.commit()
        return request.app.state.templates.TemplateResponse(
            "recover.html",
            {"request": request, "error": "请输入用户名", "csrf_token": request.session.get("csrf_token", ""), "classes": classes},
        )

    class_id = None
    if class_id_str:
        class_id = parse_int(class_id_str, min_value=1)

    existing_pending = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.username == username,
        AccountRecoveryRequest.status == "pending"
    ).first()
    if existing_pending:
        return request.app.state.templates.TemplateResponse(
            "recover_submitted.html",
            {"request": request},
        )

    recovery = AccountRecoveryRequest(
        username=username,
        class_id=class_id,
        display_name=display_name,
        status="pending",
    )
    db.add(recovery)
    db.commit()

    return request.app.state.templates.TemplateResponse(
        "recover_submitted.html",
        {"request": request},
    )
