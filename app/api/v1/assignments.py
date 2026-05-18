from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentSubmitRequest, AssignmentRecordResponse
)
from app.schemas.common import ResponseModel
from app.services.assignment_service import assignment_service
from app.models import User
from typing import List, Optional


router = APIRouter(prefix="/assignments", tags=["作业管理"])


@router.get("", response_model=ResponseModel[List[AssignmentResponse]])
def get_assignments(
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignments = assignment_service.get_assignments(db, current_user.id, current_user.role, class_id)
    return ResponseModel(data=[AssignmentResponse.model_validate(a) for a in assignments])


@router.post("", response_model=ResponseModel[AssignmentResponse])
def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师和管理员可以创建作业")

    new_assignment = assignment_service.create_assignment(db, assignment_data, current_user.id)
    return ResponseModel(data=AssignmentResponse.model_validate(new_assignment))


@router.get("/{assignment_id}", response_model=ResponseModel[AssignmentResponse])
def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = assignment_service.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")
    return ResponseModel(data=AssignmentResponse.model_validate(assignment))


@router.put("/{assignment_id}", response_model=ResponseModel[AssignmentResponse])
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = assignment_service.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    if current_user.role not in ["teacher", "admin"] and assignment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建者、教师或管理员可以修改作业")

    updated_assignment = assignment_service.update_assignment(db, assignment_id, assignment_data)
    return ResponseModel(data=AssignmentResponse.model_validate(updated_assignment))


@router.delete("/{assignment_id}", response_model=ResponseModel[dict])
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = assignment_service.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    if current_user.role not in ["teacher", "admin"] and assignment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建者、教师或管理员可以删除作业")

    assignment_service.delete_assignment(db, assignment_id)
    return ResponseModel(data={"message": "作业已删除"})


@router.post("/{assignment_id}/submit", response_model=ResponseModel[AssignmentRecordResponse])
def submit_assignment(
    assignment_id: int,
    submit_data: AssignmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = assignment_service.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    record = assignment_service.submit_assignment(db, assignment_id, current_user.id)
    return ResponseModel(data=AssignmentRecordResponse.model_validate(record))


@router.get("/{assignment_id}/records", response_model=ResponseModel[List[AssignmentRecordResponse]])
def get_assignment_records(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = assignment_service.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    if current_user.role not in ["teacher", "admin"] and assignment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建者、教师或管理员可以查看提交记录")

    records = assignment_service.get_assignment_records(db, assignment_id)
    return ResponseModel(data=[AssignmentRecordResponse.model_validate(r) for r in records])
