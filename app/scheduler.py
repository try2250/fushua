"""APScheduler 集成。dev 模式每天 19:00 跑推送 dryrun。"""
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

scheduler = BackgroundScheduler(daemon=True)


def start_scheduler():
    from app.services.notification_service import daily_push_dryrun
    scheduler.add_job(daily_push_dryrun, 'cron', hour=19, minute=0, id='daily_push')
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
