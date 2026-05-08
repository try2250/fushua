from tests.conftest import register_and_login


class TestUIPolish:
    def test_css_has_animations(self, client, db_session):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "@keyframes" in response.text or "transition" in response.text

    def test_css_has_hover_effects(self, client, db_session):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert ":hover" in response.text
