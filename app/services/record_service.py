from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Record, Question
from app.schemas.record import RecordCreate
from typing import List, Optional
from datetime import datetime, timedelta


class RecordService:
    def get_records(
        self,
        db: Session,
        user_id: int,
        subject: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Record]:
        """获取刷题记录"""
        query = db.query(Record).filter(Record.user_id == user_id)

        if subject:
            query = query.join(Question).filter(Question.subject == subject)

        return query.order_by(Record.created_at.desc()).offset(offset).limit(limit).all()

    def create_record(self, db: Session, record_data: RecordCreate, user_id: int) -> Record:
        """创建刷题记录"""
        new_record = Record(
            **record_data.model_dump(),
            user_id=user_id
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record

    def get_mistakes(
        self,
        db: Session,
        user_id: int,
        subject: Optional[str] = None,
        limit: int = 50
    ) -> List[Record]:
        """获取错题本"""
        query = db.query(Record).filter(
            Record.user_id == user_id,
            Record.is_correct == False
        )

        if subject:
            query = query.join(Question).filter(Question.subject == subject)

        return query.order_by(Record.created_at.desc()).limit(limit).all()

    def get_stats(self, db: Session, user_id: int, subject: Optional[str] = None) -> dict:
        """获取统计数据"""
        query = db.query(Record).filter(Record.user_id == user_id)

        if subject:
            query = query.join(Question).filter(Question.subject == subject)

        total_count = query.count()
        correct_count = query.filter(Record.is_correct == True).count()
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = query.filter(Record.created_at >= today_start).count()

        return {
            "total_count": total_count,
            "correct_count": correct_count,
            "accuracy": round(accuracy, 2),
            "today_count": today_count
        }


record_service = RecordService()
