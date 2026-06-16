"""推送 dryrun 服务。"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import NotificationDryrun, InboxMessage


class NotificationService:
    def create_push_for_user(self, db: Session, user_id: int, template: str,
                             payload: dict, scheduled_at: datetime) -> NotificationDryrun:
        import json
        dr = NotificationDryrun(
            user_id=user_id, template=template,
            payload=json.dumps(payload, ensure_ascii=False),
            scheduled_at=scheduled_at,
        )
        db.add(dr)
        db.commit()
        return dr

    def create_inbox(self, db: Session, user_id: int, msg_type: str,
                     title: str, body: str) -> InboxMessage:
        im = InboxMessage(user_id=user_id, type=msg_type, title=title, body=body)
        db.add(im)
        db.commit()
        return im


notification_service = NotificationService()


def daily_push_dryrun():
    """每天 19:00 由 APScheduler 触发。扫描需推送的用户，写 dryrun + inbox。"""
    from app.database import SessionLocal
    from app.models import User, DailyCheckin, UserStreak
    from datetime import date, timedelta
    db = SessionLocal()
    try:
        students = db.query(User).filter(User.role == "student").limit(50).all()
        today = date.today()
        yesterday = today - timedelta(days=1)
        for stu in students:
            svc = notification_service
            # 1. daily_checkin: 提醒今日还未打卡
            ci = db.query(DailyCheckin).filter(
                DailyCheckin.user_id == stu.id, DailyCheckin.date == today
            ).first()
            if not ci or ci.question_count < 5:
                svc.create_push_for_user(db, stu.id, "daily_checkin", {"today_count": ci.question_count if ci else 0}, datetime.utcnow())
                svc.create_inbox(db, stu.id, "daily_checkin", "每日打卡提醒", f"今日已做{ci.question_count if ci else 0}题，还差{5 - (ci.question_count if ci else 0)}题完成打卡！")
            # 2. mistake_review: 有错题的学生
            svc.create_inbox(db, stu.id, "mistake_review", "错题复习", "你有未订正的错题，快去复习吧！")
        db.commit()
    finally:
        db.close()


def daily_push_real(db=None):
    """真实推送：扫描未发送的 dryrun 记录，调微信 API 发送，标记 sent_at。"""
    import logging
    logger = logging.getLogger("fushua.push")
    if db is None:
        from app.database import SessionLocal
        db = SessionLocal()
        own_db = True
    else:
        own_db = False
    try:
        from app.services.wechat_push_service import wechat_push_service
        pending = db.query(NotificationDryrun).filter(NotificationDryrun.sent_at == None).limit(50).all()
        for dr in pending:
            template_map = {
                "daily_checkin": "TEMPLATE_CHECKIN_ID",
                "assignment_due": "TEMPLATE_ASSIGNMENT_ID",
                "rank_change": "TEMPLATE_RANK_ID",
                "mistake_review": "TEMPLATE_MISTAKE_ID",
            }
            tmpl_id = template_map.get(dr.template, template_map["daily_checkin"])
            result = wechat_push_service.send_subscribe_message(
                openid=f"o_{dr.user_id}", template_id=tmpl_id,
                data={"thing1": {"value": dr.payload}}, page="pages/index/index",
            )
            if result.get("errcode") == 0:
                dr.sent_at = datetime.utcnow()
                dr.delivered = True
                # 同时写 InboxMessage
                notification_service.create_inbox(
                    db, dr.user_id, dr.template, f"推送已发送: {dr.template}", str(dr.payload),
                )
            else:
                logger.warning(f"Push failed for user {dr.user_id}: {result}")
        db.commit()
    finally:
        if own_db:
            db.close()
