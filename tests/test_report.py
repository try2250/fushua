from tests.conftest import create_test_user, register_and_login


class TestReport:
    def test_export_pdf_endpoint_exists(self, client, db_session):
        register_and_login(client, "reportteacher", "teacher")
        response = client.get("/teacher/stats/export/pdf")
        assert response.status_code == 200

    def test_export_pdf_returns_pdf(self, client, db_session):
        register_and_login(client, "reportteacher2", "teacher")
        response = client.get("/teacher/stats/export/pdf")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type or "octet-stream" in content_type

    def test_export_student_pdf(self, client, db_session):
        teacher = create_test_user(db_session, "reportteacher3", "teacher")
        student = create_test_user(db_session, "reportstudent", "student")
        register_and_login(client, "reportteacher3", "teacher")
        response = client.get(f"/teacher/students/{student.id}/export/pdf")
        assert response.status_code == 200
