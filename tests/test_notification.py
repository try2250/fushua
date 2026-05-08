from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import Notification


class TestNotification:
    def test_notification_model_exists(self, client, db_session):
        user = create_test_user(db_session, "notifuser", "student")
        n = Notification(user_id=user.id, title="测试通知", content="这是一条通知")
        db_session.add(n)
        db_session.commit()
        assert n.id is not None

    def test_notification_bell_in_nav(self, client, db_session):
        register_and_login(client, "belluser", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "通知" in response.text or "notification" in response.text.lower()

    def test_notifications_page(self, client, db_session):
        user = create_test_user(db_session, "notifuser2", "student")
        n = Notification(user_id=user.id, title="系统通知", content="欢迎使用付刷")
        db_session.add(n)
        db_session.commit()
        register_and_login(client, "notifuser2", "student")
        response = client.get("/student/notifications", follow_redirects=True)
        assert response.status_code == 200
        assert "系统通知" in response.text

    def test_mark_notification_read(self, client, db_session):
        user = create_test_user(db_session, "notifuser3", "student")
        n = Notification(user_id=user.id, title="未读通知", content="test")
        db_session.add(n)
        db_session.commit()
        register_and_login(client, "notifuser3", "student")
        csrf = get_csrf_token(client)
        response = client.post(f"/student/notifications/{n.id}/read", data={"_csrf_token": csrf})
        assert response.status_code == 303
        db_session.refresh(n)
        assert n.is_read == True
