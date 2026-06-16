"""打卡服务：记录每日做题数，触发 streak 更新。"""
from datetime import date
from sqlalchemy.orm import Session
from app.models import DailyCheckin, UserStreak

CHECK_THRESHOLD = 5


class CheckinService:
    def increment_daily_count(self, db: Session, user_id: int, today: date,
                              count_before: int, count_after: int) -> None:
        """答题后调用。创建/更新 DailyCheckin；达到 5 题触发 check。"""
        ci = db.query(DailyCheckin).filter(
            DailyCheckin.user_id == user_id, DailyCheckin.date == today
        ).first()
        if not ci:
            ci = DailyCheckin(user_id=user_id, date=today, question_count=0)
            db.add(ci)
        ci.question_count = count_after
        if count_after >= CHECK_THRESHOLD and count_before < CHECK_THRESHOLD:
            ci.is_checked = True
            self._trigger_streak(db, user_id, today)
        db.commit()

    def _trigger_streak(self, db: Session, user_id: int, today: date) -> None:
        s = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
        if not s:
            s = UserStreak(user_id=user_id, current_streak=0, max_streak=0)
            db.add(s)
        from datetime import timedelta
        yesterday = today - timedelta(days=1)
        if s.last_checkin_date == yesterday:
            s.current_streak += 1
        else:
            s.current_streak = 1  # reset or first checkin
        if s.current_streak > s.max_streak:
            s.max_streak = s.current_streak
        s.last_checkin_date = today
        db.commit()


checkin_service = CheckinService()
