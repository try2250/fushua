from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Record, Question, User
from app.schemas.record import RecordCreate
from typing import List, Optional
from datetime import datetime, timedelta, date
import logging

from app.core.security import get_week_start
from app.services.checkin_service import checkin_service
from app.services.leaderboard_service import leaderboard_service
from app.services.badge_service import badge_service


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

        # Trigger gamification (non-fatal)
        try:
            is_correct = record_data.is_correct
            question_id = record_data.question_id
            today = date.today()
            today_count = db.query(Record).filter(
                Record.user_id == user_id,
                func.date(Record.created_at) == today
            ).count()
            checkin_service.increment_daily_count(db, user_id, today, today_count - 1, today_count)

            user = db.query(User).filter(User.id == user_id).first()
            if user and user.class_id:
                week_start = get_week_start(today)
                leaderboard_service.update_weekly_score(db, user_id, user.class_id, week_start, is_correct)
        except Exception as e:
            logging.getLogger("fushua").warning(f"Gamification trigger failed (non-fatal): {e}")

        # Event logging
        try:
            from app.services.event_log_service import log_event
            log_event(db, user_id, "answer_submit", {"question_id": question_id, "is_correct": is_correct})
        except Exception as e:
            logging.getLogger("fushua").warning(f"Event logging failed (non-fatal): {e}")

        # Trigger badges
        try:
            total = db.query(Record).filter(Record.user_id == user_id).count()
            badge_service.check_and_grant(db, user_id, "answer_submit", {"total_answers": total})
        except Exception as e:
            logging.getLogger("fushua").warning(f"Badge trigger failed (non-fatal): {e}")

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
