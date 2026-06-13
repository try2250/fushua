"""平台数据导出。"""
import csv
import io
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ClassGroup, Question, PlatformAdmin
from app.routers.platform_users import _require_platform


router = APIRouter(prefix="/platform")


@router.get("/data-export")
def export_page(request: Request, pa: PlatformAdmin = Depends(_require_platform)):
    return request.app.state.templates.TemplateResponse(
        "platform/data_export.html", {"request": request, "pa": pa},
    )


def _csv_response(headers: list, rows: list, filename: str) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow(r)
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"content-disposition": f'attachment; filename="{filename}"'})


@router.get("/export/users")
def export_users(db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    rows = [(u.id, u.username, u.role, u.display_name, u.created_at)
            for u in db.query(User).order_by(User.id).all()]
    return _csv_response(["id", "username", "role", "display_name", "created_at"], rows, "users.csv")


@router.get("/export/classes")
def export_classes(db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    rows = [(c.id, c.name, c.created_by, c.created_at)
            for c in db.query(ClassGroup).order_by(ClassGroup.id).all()]
    return _csv_response(["id", "name", "created_by", "created_at"], rows, "classes.csv")


@router.get("/export/questions")
def export_questions(db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    rows = [(q.id, q.subject, q.semester, q.chapter, q.q_type, q.created_by, q.created_at)
            for q in db.query(Question).order_by(Question.id).all()]
    return _csv_response(["id", "subject", "semester", "chapter", "q_type", "created_by", "created_at"], rows, "questions.csv")


@router.get("/export/statistics")
def export_stats(db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    rows = [
        ("total_users", db.query(User).count()),
        ("total_teachers", db.query(User).filter(User.role == "teacher").count()),
        ("total_students", db.query(User).filter(User.role == "student").count()),
        ("total_classes", db.query(ClassGroup).count()),
        ("total_questions", db.query(Question).count()),
    ]
    return _csv_response(["metric", "value"], rows, "statistics.csv")
