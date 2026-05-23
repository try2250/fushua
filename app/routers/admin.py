from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sa_func, or_
from typing import Annotated

from app.database import get_db
from app.models import User, ClassGroup, Question, ClassMember, AuditLog, AccountRecoveryRequest, SiteConfig, Favorite, QuestionBank, Record, StudyPlan, MasteryRecord, Notification
from app.auth import get_current_user, require_admin_role
from app.security import validate_csrf_async, sanitize_input
from app.utils.validation import parse_int
from app.utils.error_monitor import error_monitor

router = APIRouter()


def require_admin(request: Request, db: Session):
    user_id = require_admin_role(request, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def is_admin(request: Request, db: Session):
    """检查并返回管理员用户ID"""
    user_id = require_admin_role(request, db)
    return user_id


@router.get("/admin")
def admin_index(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    user_count = db.query(User).count()
    class_count = db.query(ClassGroup).count()
    question_count = db.query(Question).count()
    teacher_count = db.query(User).filter(User.role == "teacher").count()
    guest_count = db.query(User).filter(User.is_guest == True).count()
    admin_count = db.query(User).filter(User.role == "admin").count()

    # 获取最近的错误
    recent_errors = error_monitor.get_recent_errors(limit=10)
    error_count = error_monitor.get_error_count()

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
            "recent_errors": recent_errors,
            "error_count": error_count,
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


@router.get("/admin/users/{user_id}", response_class=HTMLResponse)
def admin_user_detail(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """管理员查看用户详情"""
    admin_id = is_admin(request, db)

    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取用户统计数据
    stats = {}

    if user.role == "student":
        # 学生统计
        stats["total_records"] = db.query(Record).filter(Record.user_id == user_id).count()
        stats["correct_records"] = db.query(Record).filter(
            Record.user_id == user_id,
            Record.is_correct == True
        ).count()
        stats["accuracy"] = (
            round(stats["correct_records"] / stats["total_records"] * 100, 1)
            if stats["total_records"] > 0 else 0
        )
        stats["total_favorites"] = db.query(Favorite).filter(Favorite.user_id == user_id).count()

        # 获取班级信息
        if user.class_id:
            stats["class"] = db.query(ClassGroup).filter(ClassGroup.id == user.class_id).first()
        else:
            stats["class"] = None

    elif user.role == "teacher":
        # 教师统计
        stats["total_classes"] = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).count()
        stats["total_students"] = db.query(ClassMember).join(ClassGroup).filter(
            ClassGroup.created_by == user_id
        ).count()
        stats["total_questions"] = db.query(Question).filter(Question.created_by == user_id).count()
        stats["total_banks"] = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).count()

    # 获取最近活动
    recent_records = db.query(Record).filter(
        Record.user_id == user_id
    ).order_by(Record.created_at.desc()).limit(10).all()

    return request.app.state.templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "recent_records": recent_records
        }
    )


@router.post("/admin/users/{user_id}/delete")
def admin_delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """管理员删除用户"""
    # from app.utils.audit import log_audit

    admin_id = is_admin(request, db)

    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能删除自己
    if user_id == admin_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    # 检查教师是否有创建的资源
    if user.role == "teacher":
        has_classes = db.query(ClassGroup).filter(ClassGroup.created_by == user_id).count() > 0
        has_questions = db.query(Question).filter(Question.created_by == user_id).count() > 0
        has_banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).count() > 0

        if has_classes or has_questions or has_banks:
            raise HTTPException(
                status_code=400,
                detail="该教师创建了班级、题目或题库，无法删除。请先转移或删除这些资源。"
            )

    # 删除学生的相关数据
    if user.role == "student":
        # 删除答题记录
        db.query(Record).filter(Record.user_id == user_id).delete()

        # 删除收藏
        db.query(Favorite).filter(Favorite.user_id == user_id).delete()

        # 删除学习计划
        db.query(StudyPlan).filter(StudyPlan.user_id == user_id).delete()

        # 删除掌握记录
        db.query(MasteryRecord).filter(MasteryRecord.user_id == user_id).delete()

        # 从班级中移除
        db.query(ClassMember).filter(ClassMember.user_id == user_id).delete()

        # 删除通知
        db.query(Notification).filter(Notification.user_id == user_id).delete()

    # 记录审计日志
    db.add(AuditLog(
        actor_id=admin_id,
        action="delete_user",
        target_type="user",
        target_id=user_id,
        detail=f"删除用户 {user.username} ({user.role})"
    ))

    # 删除用户
    db.delete(user)
    db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/admin/batch-cleanup", response_class=HTMLResponse)
def admin_batch_cleanup_page(
    request: Request,
    type: str = None,
    db: Session = Depends(get_db)
):
    """批量清理页面"""
    admin_id = is_admin(request, db)

    preview_data = []
    cleanup_type = type

    if cleanup_type == "test_accounts":
        # 查找测试账号（用户名包含test、demo等）
        test_users = db.query(User).filter(
            or_(
                User.username.like("%test%"),
                User.username.like("%demo%"),
                User.display_name.like("%测试%"),
                User.display_name.like("%test%")
            )
        ).all()
        preview_data = test_users

    elif cleanup_type == "expired_guests":
        # 查找30天前创建的访客
        cutoff_date = datetime.now() - timedelta(days=30)
        expired_guests = db.query(User).filter(
            User.role == "guest",
            User.created_at < cutoff_date
        ).all()
        preview_data = expired_guests

    elif cleanup_type == "invalid_data":
        # 查找无效数据
        # 1. 学生但没有班级
        orphan_students = db.query(User).filter(
            User.role == "student",
            User.class_id == None
        ).all()

        # 2. class_members 中的用户不存在
        invalid_members = db.query(ClassMember).outerjoin(User).filter(
            User.id == None
        ).all()

        preview_data = {
            "orphan_students": orphan_students,
            "invalid_members": invalid_members
        }

    return request.app.state.templates.TemplateResponse(
        "admin/batch_cleanup.html",
        {
            "request": request,
            "cleanup_type": cleanup_type,
            "preview_data": preview_data
        }
    )


@router.post("/admin/batch-cleanup")
async def admin_batch_cleanup_execute(
    request: Request,
    cleanup_type: str = Form(...),
    confirm: str = Form(...),
    db: Session = Depends(get_db)
):
    """执行批量清理"""
    await validate_csrf_async(request)
    admin_id = is_admin(request, db)

    if confirm != "yes":
        raise HTTPException(status_code=400, detail="未确认操作")

    deleted_count = 0

    if cleanup_type == "test_accounts":
        # 删除测试账号
        test_users = db.query(User).filter(
            or_(
                User.username.like("%test%"),
                User.username.like("%demo%"),
                User.display_name.like("%测试%"),
                User.display_name.like("%test%")
            )
        ).all()

        for user in test_users:
            # 删除相关数据
            if user.role == "student":
                db.query(Record).filter(Record.user_id == user.id).delete()
                db.query(Favorite).filter(Favorite.user_id == user.id).delete()
                db.query(StudyPlan).filter(StudyPlan.user_id == user.id).delete()
                db.query(ClassMember).filter(ClassMember.user_id == user.id).delete()

            db.delete(user)
            deleted_count += 1

    elif cleanup_type == "expired_guests":
        # 删除过期访客
        cutoff_date = datetime.now() - timedelta(days=30)
        expired_guests = db.query(User).filter(
            User.role == "guest",
            User.created_at < cutoff_date
        ).all()

        for guest in expired_guests:
            db.query(Record).filter(Record.user_id == guest.id).delete()
            db.query(Favorite).filter(Favorite.user_id == guest.id).delete()
            db.delete(guest)
            deleted_count += 1

    elif cleanup_type == "invalid_data":
        # 清理无效数据
        # 1. 删除孤立学生
        orphan_students = db.query(User).filter(
            User.role == "student",
            User.class_id == None
        ).all()

        for student in orphan_students:
            db.query(Record).filter(Record.user_id == student.id).delete()
            db.query(Favorite).filter(Favorite.user_id == student.id).delete()
            db.query(StudyPlan).filter(StudyPlan.user_id == student.id).delete()
            db.delete(student)
            deleted_count += 1

        # 2. 删除无效的班级成员记录
        invalid_members = db.query(ClassMember).outerjoin(User).filter(
            User.id == None
        ).all()

        for member in invalid_members:
            db.delete(member)
            deleted_count += 1

    # 记录审计日志
    db.add(AuditLog(
        actor_id=admin_id,
        action="batch_cleanup",
        target_type="users",
        target_id=None,
        detail=f"批量清理：{cleanup_type}，删除数量：{deleted_count}"
    ))

    db.commit()

    return RedirectResponse(
        url=f"/admin/batch-cleanup?type={cleanup_type}&success={deleted_count}",
        status_code=302
    )


