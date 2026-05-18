from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.schemas.record import RecordCreate, RecordResponse, RecordStatsResponse
from app.schemas.common import ResponseModel
from app.services.record_service import record_service
from app.models import User
from typing import List, Optional


router = APIRouter(prefix="/records", tags=["刷题记录"])


@router.get("", response_model=ResponseModel[List[RecordResponse]])
def get_records(
    subject: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = record_service.get_records(db, current_user.id, subject, limit, offset)
    return ResponseModel(data=[RecordResponse.model_validate(r) for r in records])


@router.post("", response_model=ResponseModel[RecordResponse])
def create_record(
    record_data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_record = record_service.create_record(db, record_data, current_user.id)
    return ResponseModel(data=RecordResponse.model_validate(new_record))


@router.get("/mistakes", response_model=ResponseModel[List[RecordResponse]])
def get_mistakes(
    subject: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistakes = record_service.get_mistakes(db, current_user.id, subject, limit)
    return ResponseModel(data=[RecordResponse.model_validate(r) for r in mistakes])


@router.get("/stats", response_model=ResponseModel[RecordStatsResponse])
def get_stats(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = record_service.get_stats(db, current_user.id, subject)
    return ResponseModel(data=RecordStatsResponse(**stats))
