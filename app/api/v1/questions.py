from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse
)
from app.schemas.common import ResponseModel
from app.services.question_service import question_service
from app.models import User
from typing import List, Optional


router = APIRouter(prefix="/questions", tags=["题目管理"])


@router.get("", response_model=ResponseModel[List[QuestionResponse]])
def get_questions(
    subject: Optional[str] = None,
    semester: Optional[str] = None,
    chapter: Optional[str] = None,
    q_type: Optional[str] = None,
    difficulty: Optional[int] = None,
    bank_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    questions = question_service.get_questions_for_tenant(
        db, tenant.tenant_id, subject, semester, chapter, q_type,
        difficulty, bank_id, limit, offset,
    )
    return ResponseModel(data=[QuestionResponse.model_validate(q) for q in questions])


@router.post("", response_model=ResponseModel[QuestionResponse])
def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    if tenant.source != "teacher":
        raise HTTPException(status_code=403, detail="只有教师可以创建题目")
    new_question = question_service.create_question(db, question_data, tenant.tenant_id)
    return ResponseModel(data=QuestionResponse.model_validate(new_question))


@router.get("/random", response_model=ResponseModel[List[QuestionResponse]])
def get_random_questions(
    subject: Optional[str] = None,
    semester: Optional[str] = None,
    chapter: Optional[str] = None,
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    questions = question_service.get_random_questions_for_tenant(
        db, tenant.tenant_id, subject, semester, chapter, count,
    )
    return ResponseModel(data=[QuestionResponse.model_validate(q) for q in questions])


@router.get("/{question_id}", response_model=ResponseModel[QuestionResponse])
def get_question_detail(
    question_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    question = question_service.get_question_by_id_for_tenant(db, tenant.tenant_id, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return ResponseModel(data=QuestionResponse.model_validate(question))


@router.put("/{question_id}", response_model=ResponseModel[QuestionResponse])
def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    question = question_service.get_question_by_id_for_tenant(db, tenant.tenant_id, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    updated = question_service.update_question(db, question_id, question_data)
    return ResponseModel(data=QuestionResponse.model_validate(updated))


@router.delete("/{question_id}", response_model=ResponseModel[dict])
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    question = question_service.get_question_by_id_for_tenant(db, tenant.tenant_id, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    question_service.delete_question(db, question_id)
    return ResponseModel(data={"message": "题目已删除"})
