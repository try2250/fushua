from tests.conftest import register_and_login, create_test_user, create_test_question


class TestHtmx:
    def test_base_template_includes_htmx(self, client, db_session):
        register_and_login(client, "htmxuser", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "htmx" in response.text.lower()

    def test_favorite_button_uses_htmx(self, client, db_session):
        teacher = create_test_user(db_session, "htmxteacher", "teacher")
        create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "htmxstudent", "student")
        response = client.get("/student/practice", follow_redirects=True)
        assert response.status_code == 200
        assert "hx-post" in response.text
