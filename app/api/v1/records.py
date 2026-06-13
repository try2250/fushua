from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.schemas.record import RecordCreate, RecordResponse, RecordStatsResponse
from app.schemas.common import ResponseModel
from app.services.record_service import record_service
from app.models import User, Record
from app.api.v1.compat_helpers import record_to_miniprogram_dict
from typing import List, Optional


router = APIRouter(prefix="/records", tags=["刷题记录"])
practice_router = APIRouter(prefix="/practice-records", tags=["小程序刷题记录兼容"])


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


@practice_router.get("/today-stats", response_model=ResponseModel[dict])
def get_today_stats_for_miniprogram(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = record_service.get_stats(db, current_user.id)
    return ResponseModel(data={
        "completed": stats["today_count"],
        "correct": stats["correct_count"],
        "total": stats["total_count"],
    })


@practice_router.get("/mistakes", response_model=ResponseModel[List[dict]])
def get_mistakes_for_miniprogram(
    subject: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistakes = record_service.get_mistakes(db, current_user.id, subject, limit)
    return ResponseModel(data=[record_to_miniprogram_dict(record) for record in mistakes])


@practice_router.post("", response_model=ResponseModel[dict])
def create_practice_record_for_miniprogram(
    record_data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_record = record_service.create_record(db, record_data, current_user.id)
    return ResponseModel(data=record_to_miniprogram_dict(new_record))


@practice_router.post("/{record_id}/remove-mistake", response_model=ResponseModel[dict])
def remove_mistake_for_miniprogram(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    record.is_correct = True
    db.commit()
    return ResponseModel(data={"message": "已移出错题本"})
