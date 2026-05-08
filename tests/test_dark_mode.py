from tests.conftest import register_and_login


class TestDarkMode:
    def test_base_template_has_theme_toggle(self, client, db_session):
        register_and_login(client, "themeuser", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "theme-toggle" in response.text or "深色" in response.text

    def test_css_has_dark_mode_vars(self, client, db_session):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "dark" in response.text.lower() or "[data-theme" in response.text
