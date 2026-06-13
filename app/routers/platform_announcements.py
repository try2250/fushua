"""平台公告管理。"""
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Announcement, PlatformAdmin
from app.routers.platform_users import _require_platform


router = APIRouter(prefix="/platform")


@router.get("/announcements")
def list_announcements(request: Request, db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    rows = db.query(Announcement).order_by(Announcement.id.desc()).all()
    return request.app.state.templates.TemplateResponse("platform/announcements.html", {"request": request, "pa": pa, "rows": rows})


@router.get("/announcements/create")
def create_form(request: Request, pa: PlatformAdmin = Depends(_require_platform)):
    return request.app.state.templates.TemplateResponse("platform/announcement_form.html", {"request": request, "pa": pa, "ann": None, "action": "create"})


@router.post("/announcements/create")
async def create_post(request: Request, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    form = await request.form()
    is_active = form.get("is_active") == "on"
    a = Announcement(title=title, content=content, is_active=is_active)
    db.add(a); db.commit()
    return RedirectResponse(url="/platform/announcements", status_code=303)


@router.get("/announcements/{ann_id}/edit")
def edit_form(ann_id: int, request: Request, db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    a = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not a: raise HTTPException(status_code=404, detail="公告不存在")
    return request.app.state.templates.TemplateResponse("platform/announcement_form.html", {"request": request, "pa": pa, "ann": a, "action": "edit"})


@router.post("/announcements/{ann_id}/edit")
async def edit_post(ann_id: int, request: Request, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    a = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not a: raise HTTPException(status_code=404, detail="公告不存在")
    form = await request.form()
    a.title = title; a.content = content; a.is_active = form.get("is_active") == "on"
    db.commit()
    return RedirectResponse(url="/platform/announcements", status_code=303)


@router.post("/announcements/{ann_id}/toggle")
def toggle(ann_id: int, db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    a = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not a: raise HTTPException(status_code=404, detail="公告不存在")
    a.is_active = not a.is_active; db.commit()
    return RedirectResponse(url="/platform/announcements", status_code=303)


@router.post("/announcements/{ann_id}/delete")
def delete(ann_id: int, db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    a = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not a: raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(a); db.commit()
    return RedirectResponse(url="/platform/announcements", status_code=303)
