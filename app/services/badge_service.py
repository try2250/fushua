"""徽章服务 — 检查触发条件并授予徽章。"""
from sqlalchemy.orm import Session
from app.models import Badge, UserBadge


TRIGGER_MAP = {
    "answer_submit": {
        1: "opening",     # first answer
        100: "hundred",   # 100th answer
        1000: "thousand", # 1000th answer
    },
    "streak_change": {
        3: "streak_3",
        7: "streak_7",
        30: "streak_30",
    },
}


class BadgeService:
    def check_and_grant(self, db: Session, user_id: int, trigger_type: str, context: dict) -> None:
        triggers = TRIGGER_MAP.get(trigger_type, {})
        for threshold, code in triggers.items():
            value = context.get("total_answers") if trigger_type == "answer_submit" else context.get("streak")
            if value is None:
                continue
            if value >= threshold:
                self._grant(db, user_id, code)
        # perfect_set: trigger when context says a set was perfect
        if trigger_type == "practice_set_complete" and context.get("perfect_set"):
            self._grant(db, user_id, "perfect_set")

    def _grant(self, db: Session, user_id: int, code: str) -> None:
        badge = db.query(Badge).filter(Badge.code == code).first()
        if not badge:
            return
        existing = db.query(UserBadge).filter(
            UserBadge.user_id == user_id, UserBadge.badge_id == badge.id
        ).first()
        if existing:
            return
        db.add(UserBadge(user_id=user_id, badge_id=badge.id))
        db.commit()


badge_service = BadgeService()
