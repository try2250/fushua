from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentSubmitRequest, AssignmentRecordResponse
)
from app.schemas.common import ResponseModel
from app.services.assignment_service import assignment_service
from app.models import User, Question
from app.api.v1.compat_helpers import assignment_to_miniprogram_dict
from typing import List, Optional


router = APIRouter(prefix="/assignments", tags=["作业管理"])


@router.get("", response_model=ResponseModel[List[AssignmentResponse]])
def get_assignments(
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    items = assignment_service.get_assignments_for_tenant(db, tenant.tenant_id, class_id)
    return ResponseModel(data=[AssignmentResponse.model_validate(a) for a in items])


@router.post("", response_model=ResponseModel[AssignmentResponse])
def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    if tenant.source != "teacher":
        raise HTTPException(status_code=403, detail="只有教师可以创建作业")
    new_assignment = assignment_service.create_assignment(db, assignment_data, tenant.tenant_id)
    return ResponseModel(data=AssignmentResponse.model_validate(new_assignment))


@router.get("/{assignment_id}", response_model=ResponseModel[dict])
def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    assignment = assignment_service.get_assignment_by_id_for_tenant(
        db, tenant.tenant_id, assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    user_id = tenant.user.id if tenant.user else None
    return ResponseModel(data=assignment_to_miniprogram_dict(db, assignment, user_id))


@router.put("/{assignment_id}", response_model=ResponseModel[AssignmentResponse])
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    assignment = assignment_service.get_assignment_by_id_for_tenant(
        db, tenant.tenant_id, assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    updated = assignment_service.update_assignment(db, assignment_id, assignment_data)
    return ResponseModel(data=AssignmentResponse.model_validate(updated))


@router.delete("/{assignment_id}", response_model=ResponseModel[dict])
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    assignment = assignment_service.get_assignment_by_id_for_tenant(
        db, tenant.tenant_id, assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    assignment_service.delete_assignment(db, assignment_id)
    return ResponseModel(data={"message": "作业已删除"})


@router.post("/{assignment_id}/submit", response_model=ResponseModel[dict])
def submit_assignment(
    assignment_id: int,
    submit_data: AssignmentSubmitRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    assignment = assignment_service.get_assignment_by_id_for_tenant(
        db, tenant.tenant_id, assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    record = assignment_service.submit_assignment(db, assignment_id, tenant.user.id)
    answers = submit_data.answers
    if isinstance(answers, list):
        answer_map = {
            int(item["question_id"]): item.get("user_answer", "")
            for item in answers
            if "question_id" in item
        }
    else:
        answer_map = {int(key): value for key, value in answers.items()}

    questions = db.query(Question).filter(Question.id.in_(answer_map.keys())).all() if answer_map else []
    correct_count = sum(1 for question in questions if answer_map.get(question.id) == question.answer)
    score = round(correct_count / len(questions) * 100) if questions else 0
    return ResponseModel(data={
        "id": record.id,
        "assignment_id": record.assignment_id,
        "user_id": record.user_id,
        "completed": record.completed,
        "completed_at": record.completed_at,
        "score": score,
        "answers": [
            {"question_id": question_id, "user_answer": user_answer}
            for question_id, user_answer in answer_map.items()
        ],
    })


@router.get("/{assignment_id}/submission", response_model=ResponseModel[dict])
def get_assignment_submission_for_miniprogram(
    assignment_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    assignment = assignment_service.get_assignment_by_id_for_tenant(
        db, tenant.tenant_id, assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    record = assignment_service.get_user_assignment_record(db, assignment_id, tenant.user.id)
    return ResponseModel(data={
        "assignment_id": assignment_id,
        "completed": bool(record and record.completed),
        "completed_at": record.completed_at if record else None,
        "answers": [],
    })


@router.get("/{assignment_id}/records", response_model=ResponseModel[List[AssignmentRecordResponse]])
def get_assignment_records(
    assignment_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    if tenant.source != "teacher":
        raise HTTPException(status_code=403, detail="只有教师可以查看提交记录")
    assignment = assignment_service.get_assignment_by_id_for_tenant(
        db, tenant.tenant_id, assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    records = assignment_service.get_assignment_records(db, assignment_id)
    return ResponseModel(data=[AssignmentRecordResponse.model_validate(r) for r in records])
