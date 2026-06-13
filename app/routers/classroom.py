"""
课堂管理路由
提供课堂伴侣工具的 Web 访问入口
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_teacher


router = APIRouter(prefix="/teacher", tags=["课堂管理"])


@router.get("/classroom", response_class=HTMLResponse)
def classroom_page(request: Request, db: Session = Depends(get_db)):
    """
    课堂伴侣工具页面
    仅教师可访问
    第一版：嵌入旧课堂工具，使用 localStorage 存储
    """
    user = require_teacher(request, db)

    # 使用 request.app.state.templates 访问模板
    return request.app.state.templates.TemplateResponse("teacher/classroom.html", {
        "request": request,
        "user": user
    })
