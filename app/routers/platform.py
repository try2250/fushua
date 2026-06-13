"""平台管理员 Web 后台 — 独立认证体系（Plan 1.2B）"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import PlatformAdmin, User


router = APIRouter(prefix="/platform")


def _platform_session(request: Request, db: Session) -> PlatformAdmin | None:
    pa_id = request.session.get("platform_admin_id")
    if not pa_id:
        return None
    return db.query(PlatformAdmin).filter(
        PlatformAdmin.id == pa_id,
        PlatformAdmin.is_active == True,
    ).first()


def require_platform(request: Request, db: Annotated[Session, Depends(get_db)]):
    pa = _platform_session(request, db)
    if not pa:
        raise HTTPException(status_code=303, headers={"location": "/platform/login"})
    return pa


@router.get("/login")
def login_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "platform/login.html", {"request": request}
    )


@router.post("/login")
async def login(request: Request, db: Annotated[Session, Depends(get_db)]):
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "")
    pa = db.query(PlatformAdmin).filter(PlatformAdmin.username == username).first()
    if not pa or not PlatformAdmin.verify_password(pa.password_hash, password):
        return request.app.state.templates.TemplateResponse(
            "platform/login.html",
            {"request": request, "error": "用户名或密码错误"},
            status_code=400,
        )
    request.session["platform_admin_id"] = pa.id
    return RedirectResponse(url="/platform/dashboard", status_code=303)


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    pa: PlatformAdmin = Depends(require_platform),
):
    teacher_count = db.query(User).filter(User.role == "teacher").count()
    student_count = db.query(User).filter(User.role == "student").count()
    return request.app.state.templates.TemplateResponse(
        "platform/dashboard.html",
        {
            "request": request,
            "pa": pa,
            "teacher_count": teacher_count,
            "student_count": student_count,
        },
    )


@router.post("/logout")
def logout(request: Request):
    request.session.pop("platform_admin_id", None)
    return RedirectResponse(url="/platform/login", status_code=303)
