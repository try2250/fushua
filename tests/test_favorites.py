from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Favorite


class TestFavorites:
    def test_add_favorite(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "favstudent", "student")
        csrf = get_csrf_token(client)
        response = client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        assert response.status_code == 303
        fav = db_session.query(Favorite).first()
        assert fav is not None

    def test_favorites_page_lists_favorites(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher2", "teacher")
        q = create_test_question(db_session, content="收藏题", created_by=teacher.id)
        register_and_login(client, "favstudent2", "student")
        csrf = get_csrf_token(client)
        client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        response = client.get("/student/favorites", follow_redirects=True)
        assert response.status_code == 200
        assert "收藏题" in response.text

    def test_remove_favorite(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher3", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "favstudent3", "student")
        csrf = get_csrf_token(client)
        client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        client.post(f"/student/favorites/{q.id}/remove", data={"_csrf_token": csrf})
        count = db_session.query(Favorite).count()
        assert count == 0

    def test_duplicate_favorite_ignored(self, client, db_session):
        teacher = create_test_user(db_session, "favteacher4", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "favstudent4", "student")
        csrf = get_csrf_token(client)
        client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        client.post(f"/student/favorites/{q.id}/add", data={"_csrf_token": csrf})
        count = db_session.query(Favorite).count()
        assert count == 1

    def test_nav_has_favorites_link(self, client, db_session):
        register_and_login(client, "favstudent5", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "/student/favorites" in response.text or "收藏" in response.text
