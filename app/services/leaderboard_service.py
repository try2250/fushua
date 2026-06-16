"""班级排行榜服务。"""
from datetime import date
from sqlalchemy.orm import Session
from app.models import WeeklyScore, User


class LeaderboardService:
    def update_weekly_score(self, db: Session, user_id: int, class_id: int,
                            week_start: date, is_correct: bool) -> None:
        if not is_correct:
            return
        ws = db.query(WeeklyScore).filter(
            WeeklyScore.user_id == user_id,
            WeeklyScore.class_id == class_id,
            WeeklyScore.week_start == week_start,
        ).first()
        if not ws:
            ws = WeeklyScore(user_id=user_id, class_id=class_id, week_start=week_start, score=1)
            db.add(ws)
        else:
            ws.score += 1
        db.commit()

    def get_class_leaderboard(self, db: Session, class_id: int,
                              week_start: date, limit: int = 10) -> list:
        rows = db.query(WeeklyScore).filter(
            WeeklyScore.class_id == class_id,
            WeeklyScore.week_start == week_start,
        ).order_by(WeeklyScore.score.desc()).limit(limit).all()
        result = []
        for row in rows:
            user = db.query(User).filter(User.id == row.user_id).first()
            result.append({
                "user_id": row.user_id,
                "display_name": user.display_name if user else "?",
                "score": row.score,
            })
        return result


leaderboard_service = LeaderboardService()
