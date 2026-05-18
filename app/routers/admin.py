from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sa_func
from typing import Annotated

from app.database import get_db
from app.models import User, ClassGroup, Question, ClassMember, AuditLog, AccountRecoveryRequest, SiteConfig
from app.auth import get_current_user, require_admin_role
from app.security import validate_csrf_async, sanitize_input
from app.utils.validation import parse_int

router = APIRouter()


def require_admin(request: Request, db: Session):
    user_id = require_admin_role(request, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


@router.get("/admin")
def admin_index(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    user_count = db.query(User).count()
    class_count = db.query(ClassGroup).count()
    question_count = db.query(Question).count()
    teacher_count = db.query(User).filter(User.role == "teacher").count()
    guest_count = db.query(User).filter(User.is_guest == True).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    return request.app.state.templates.TemplateResponse(
        "admin/index.html",
        {
            "request": request,
            "user_count": user_count,
            "class_count": class_count,
            "question_count": question_count,
            "teacher_count": teacher_count,
            "guest_count": guest_count,
            "admin_count": admin_count,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.get("/admin/users")
def admin_users(request: Request, db: Annotated[Session, Depends(get_db)], q: str = "", role: str = ""):
    require_admin(request, db)
    query = db.query(User)
    if q:
        safe_q = q.replace('%', '\\%').replace('_', '\\_')
        query = query.filter(
            (User.username.contains(safe_q)) | (User.display_name.contains(safe_q))
        )
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "users": users, "q": q, "role": role, "csrf_token": request.session.get("csrf_token", "")},
    )


@router.post("/admin/users/{user_id}/reset-password")
async def reset_password(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = User.hash_password("abc12345")
    user.force_password_change = True
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="reset_password",
        target_type="user",
        target_id=user_id,
        detail=f"管理员重置用户 {user.username} 的密码"
    ))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/toggle-disable")
async def toggle_disable(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="不能禁用管理员账号")
    user.is_disabled = not user.is_disabled
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="toggle_disable",
        target_type="user",
        target_id=user_id,
        detail=f"{'禁用' if user.is_disabled else '启用'}用户 {user.username}"
    ))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/cleanup-guests")
async def cleanup_guests(request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    now = datetime.now()
    expired_guests = db.query(User).filter(
        User.is_guest == True,
        User.guest_expires_at != None,
        User.guest_expires_at < now,
    ).all()
    count = len(expired_guests)
    for guest in expired_guests:
        db.query(ClassMember).filter(ClassMember.user_id == guest.id).delete()
        db.delete(guest)
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="cleanup_guests",
        target_type="system",
        detail=f"清理了 {count} 个过期游客"
    ))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/admin/recovery-requests")
def recovery_requests_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    pending = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.status == "pending"
    ).order_by(AccountRecoveryRequest.created_at.desc()).all()
    processed = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.status != "pending"
    ).order_by(AccountRecoveryRequest.reviewed_at.desc()).limit(50).all()
    return request.app.state.templates.TemplateResponse(
        "admin/recovery_requests.html",
        {
            "request": request,
            "pending": pending,
            "processed": processed,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.post("/admin/recovery-requests/{request_id}/approve")
async def approve_recovery(request_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    recovery = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.id == request_id, AccountRecoveryRequest.status == "pending"
    ).first()
    if not recovery:
        return RedirectResponse(url="/admin/recovery-requests", status_code=303)
    user = db.query(User).filter(User.username == recovery.username).first()
    if not user:
        recovery.status = "rejected"
        recovery.reviewed_by = admin_user.id
        recovery.reviewed_at = datetime.now()
        db.commit()
        return RedirectResponse(url="/admin/recovery-requests", status_code=303)
    user.password_hash = User.hash_password("abc12345")
    user.force_password_change = True
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="approve_recovery",
        target_type="user",
        target_id=user.id,
        detail=f"管理员批准找回申请，重置用户 {user.username} 的密码"
    ))
    recovery.status = "approved"
    recovery.reviewed_by = admin_user.id
    recovery.reviewed_at = datetime.now()
    db.commit()
    return RedirectResponse(url="/admin/recovery-requests", status_code=303)


@router.get("/admin/invite")
def admin_invite_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    teacher_config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    admin_config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
    teacher_codes = teacher_config.value if teacher_config else ""
    admin_codes = admin_config.value if admin_config else ""
    return request.app.state.templates.TemplateResponse(
        "admin/invite.html",
        {"request": request, "teacher_codes": teacher_codes, "admin_codes": admin_codes, "csrf_token": request.session.get("csrf_token", "")},
    )


@router.post("/admin/invite/update")
async def admin_invite_update(request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    teacher_codes = sanitize_input(form.get("teacher_codes", "").strip(), max_length=500)
    admin_codes = sanitize_input(form.get("admin_codes", "").strip(), max_length=500)
    teacher_config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    if not teacher_config:
        teacher_config = SiteConfig(key="teacher_invite_code", value=teacher_codes)
        db.add(teacher_config)
    else:
        teacher_config.value = teacher_codes
    admin_config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
    if not admin_config:
        admin_config = SiteConfig(key="admin_invite_code", value=admin_codes)
        db.add(admin_config)
    else:
        admin_config.value = admin_codes
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="update_invite_codes",
        target_type="system",
        detail="管理员更新邀请码配置"
    ))
    db.commit()
    return RedirectResponse(url="/admin/invite", status_code=303)


@router.post("/admin/users/{user_id}/toggle-admin")
async def toggle_admin(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="不能修改管理员角色的 is_admin 标记")
    user.is_admin = not user.is_admin
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="toggle_admin",
        target_type="user",
        target_id=user_id,
        detail=f"{'授予' if user.is_admin else '撤销'}用户 {user.username} 的教师管理权限"
    ))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/recovery-requests/{request_id}/reject")
async def reject_recovery(request_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    recovery = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.id == request_id, AccountRecoveryRequest.status == "pending"
    ).first()
    if not recovery:
        return RedirectResponse(url="/admin/recovery-requests", status_code=303)
    recovery.status = "rejected"
    recovery.reviewed_by = admin_user.id
    recovery.reviewed_at = datetime.now()
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="reject_recovery",
        target_type="recovery_request",
        target_id=request_id,
        detail=f"管理员拒绝找回申请：{recovery.username}"
    ))
    db.commit()
    return RedirectResponse(url="/admin/recovery-requests", status_code=303)


@router.get("/admin/classes")
def admin_classes(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)

    # 使用 joinedload 预加载创建者信息
    classes = (
        db.query(ClassGroup)
        .options(joinedload(ClassGroup.creator))
        .order_by(ClassGroup.created_at.desc())
        .all()
    )

    # 一次性查询所有班级的成员计数
    class_ids = [c.id for c in classes]
    member_counts = {}
    if class_ids:
        count_results = (
            db.query(
                ClassMember.class_id,
                sa_func.count(ClassMember.user_id).label("count")
            )
            .filter(ClassMember.class_id.in_(class_ids))
            .group_by(ClassMember.class_id)
            .all()
        )
        member_counts = {row.class_id: row.count for row in count_results}

    # 构建结果
    class_data = []
    for c in classes:
        class_data.append({
            "id": c.id,
            "name": c.name,
            "created_by": c.creator.display_name if c.creator else "未知",
            "member_count": member_counts.get(c.id, 0),
            "created_at": c.created_at,
        })

    return request.app.state.templates.TemplateResponse(
        "admin/classes.html",
        {"request": request, "class_data": class_data},
    )


@router.get("/admin/audit-log")
def audit_log_page(request: Request, db: Annotated[Session, Depends(get_db)], action: str = "", page: str = "1"):
    require_admin(request, db)
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    page_num = parse_int(page, default=1, min_value=1) or 1
    per_page = 50
    offset = (page_num - 1) * per_page
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    actor_ids = list({log.actor_id for log in logs if log.actor_id})
    actors = {}
    if actor_ids:
        for u in db.query(User).filter(User.id.in_(actor_ids)).all():
            actors[u.id] = u.display_name or u.username

    actions = [row[0] for row in db.query(AuditLog.action).distinct().order_by(AuditLog.action).all()]

    return request.app.state.templates.TemplateResponse(
        "admin/audit_log.html",
        {
            "request": request,
            "logs": logs,
            "actors": actors,
            "actions": actions,
            "current_action": action,
            "page": page_num,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.get("/admin/audit-log/export")
def audit_log_export(request: Request, db: Annotated[Session, Depends(get_db)], action: str = ""):
    require_admin(request, db)
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.created_at.desc()).limit(5000).all()

    actor_ids = list({log.actor_id for log in logs if log.actor_id})
    actors = {}
    if actor_ids:
        for u in db.query(User).filter(User.id.in_(actor_ids)).all():
            actors[u.id] = u.display_name or u.username

    import csv
    import io
    import urllib.parse
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["时间", "操作者", "操作", "目标类型", "目标ID", "详情"])
    for log in logs:
        writer.writerow([
            log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            actors.get(log.actor_id, str(log.actor_id or "")),
            log.action,
            log.target_type,
            log.target_id or "",
            log.detail,
        ])
    buf.seek(0)
    output = buf.getvalue().encode("utf-8-sig")
    from fastapi.responses import StreamingResponse
    filename = urllib.parse.quote("审计日志.csv")
    return StreamingResponse(
        io.BytesIO(output),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
