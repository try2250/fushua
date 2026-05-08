class TestPWA:
    def test_manifest_json_accessible(self, client, db_session):
        response = client.get("/static/manifest.json")
        assert response.status_code == 200

    def test_manifest_has_required_fields(self, client, db_session):
        response = client.get("/static/manifest.json")
        import json
        data = json.loads(response.text)
        assert "name" in data
        assert "short_name" in data

    def test_base_template_has_manifest_link(self, client, db_session):
        from tests.conftest import register_and_login
        register_and_login(client, "pwauser", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "manifest" in response.text.lower()
