import os
import json
import httpx
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import Question, User, QuestionBank, SiteConfig, QUESTION_TYPES, SEMESTERS, SUBJECTS
from app.auth import require_teacher
from app.security import validate_csrf_async, sanitize_input
from app.utils.validation import parse_int

router = APIRouter(prefix="/extractor")

FUTI_BASE_URL = os.environ.get("FUTI_BASE_URL", "http://localhost:8001")
FUTI_API_TOKEN = os.environ.get("FUTI_API_TOKEN", "")


def _get_csrf(request: Request) -> str:
    return request.session.get("csrf_token", "")


def _futi_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if FUTI_API_TOKEN:
        headers["X-API-Token"] = FUTI_API_TOKEN
    return headers


@router.get("/")
def extractor_index(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    futi_available = _check_futi()
    return request.app.state.templates.TemplateResponse(
        "extractor_proxy/index.html",
        {
            "request": request,
            "futi_url": FUTI_BASE_URL,
            "futi_available": futi_available,
            "csrf_token": _get_csrf(request),
        },
    )


@router.get("/import")
def extractor_import_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
    return request.app.state.templates.TemplateResponse(
        "extractor_proxy/import.html",
        {
            "request": request,
            "subjects": SUBJECTS,
            "semesters": SEMESTERS,
            "banks": banks,
            "futi_url": FUTI_BASE_URL,
            "csrf_token": _get_csrf(request),
        },
    )


@router.post("/import")
async def extractor_import_questions(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_teacher(request, db)
    await validate_csrf_async(request)
    form = await request.form()

    question_ids_str = form.get("question_ids", "")
    bank_id_val = form.get("bank_id", "")
    subject = sanitize_input(form.get("subject", "").strip(), max_length=20)

    if not question_ids_str:
        banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
        return request.app.state.templates.TemplateResponse(
            "extractor_proxy/import.html",
            {
                "request": request, "subjects": SUBJECTS, "semesters": SEMESTERS,
                "banks": banks, "futi_url": FUTI_BASE_URL,
                "error": "请输入题目ID", "csrf_token": _get_csrf(request),
            },
        )

    qids = [x.strip() for x in question_ids_str.split(",") if x.strip()]
    try:
        int_ids = [int(x) for x in qids]
    except ValueError:
        banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
        return request.app.state.templates.TemplateResponse(
            "extractor_proxy/import.html",
            {
                "request": request, "subjects": SUBJECTS, "semesters": SEMESTERS,
                "banks": banks, "futi_url": FUTI_BASE_URL,
                "error": "题目ID格式错误", "csrf_token": _get_csrf(request),
            },
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{FUTI_BASE_URL}/api/export",
                json={"ids": int_ids, "format": "fushua"},
                headers=_futi_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
        return request.app.state.templates.TemplateResponse(
            "extractor_proxy/import.html",
            {
                "request": request, "subjects": SUBJECTS, "semesters": SEMESTERS,
                "banks": banks, "futi_url": FUTI_BASE_URL,
                "error": f"连接付题服务失败：{str(e)}", "csrf_token": _get_csrf(request),
            },
        )

    questions_data = data.get("questions", [])
    if not questions_data:
        banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
        return request.app.state.templates.TemplateResponse(
            "extractor_proxy/import.html",
            {
                "request": request, "subjects": SUBJECTS, "semesters": SEMESTERS,
                "banks": banks, "futi_url": FUTI_BASE_URL,
                "error": "未找到指定题目", "csrf_token": _get_csrf(request),
            },
        )

    bank_id = None
    if bank_id_val:
        from app.routers.permissions import teacher_owns_bank
        bid = parse_int(bank_id_val, min_value=1)
        if bid and teacher_owns_bank(db, user_id, bid):
            bank_id = bid

    count = 0
    batch_size = 50
    for q_data in questions_data:
        if subject and not q_data.get("subject"):
            q_data["subject"] = subject

        q = Question(
            subject=q_data.get("subject", ""),
            semester=q_data.get("semester", ""),
            chapter=q_data.get("chapter", ""),
            difficulty=parse_int(q_data.get("difficulty"), default=2, min_value=1, max_value=5) or 2,
            q_type=q_data.get("q_type", "choice"),
            content=q_data.get("content", ""),
            option_a=q_data.get("option_a", ""),
            option_b=q_data.get("option_b", ""),
            option_c=q_data.get("option_c", ""),
            option_d=q_data.get("option_d", ""),
            answer=q_data.get("answer", ""),
            explanation=q_data.get("explanation", ""),
            image_url=q_data.get("image_url", ""),
            bank_id=bank_id,
            created_by=user_id,
        )
        db.add(q)
        count += 1
        if count > 0 and count % batch_size == 0:
            db.commit()
    db.commit()

    banks = db.query(QuestionBank).filter(QuestionBank.created_by == user_id).order_by(QuestionBank.name).all()
    return request.app.state.templates.TemplateResponse(
        "extractor_proxy/import.html",
        {
            "request": request, "subjects": SUBJECTS, "semesters": SEMESTERS,
            "banks": banks, "futi_url": FUTI_BASE_URL,
            "success": f"成功从付题导入 {count} 道题目！",
            "csrf_token": _get_csrf(request),
        },
    )


@router.get("/questions")
async def extractor_list_questions(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_teacher(request, db)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{FUTI_BASE_URL}/api/questions?limit=100",
                headers=_futi_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            questions = data.get("questions", [])
    except Exception:
        questions = []

    return request.app.state.templates.TemplateResponse(
        "extractor_proxy/questions.html",
        {
            "request": request,
            "questions": questions,
            "question_types": QUESTION_TYPES,
            "futi_url": FUTI_BASE_URL,
            "csrf_token": _get_csrf(request),
        },
    )


def _check_futi() -> bool:
    try:
        resp = httpx.get(f"{FUTI_BASE_URL}/api/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
