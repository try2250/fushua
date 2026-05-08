from tests.conftest import create_test_user, create_test_question, register_and_login


class TestLatexRendering:
    def test_practice_page_includes_katex(self, client, db_session):
        teacher = create_test_user(db_session, "latexteacher", "teacher")
        create_test_question(db_session, content="解方程 $x^2=4$", created_by=teacher.id)
        register_and_login(client, "latexstudent", "student")
        response = client.get("/student/practice", follow_redirects=True)
        assert response.status_code == 200
        assert "katex" in response.text.lower()

    def test_result_page_includes_katex(self, client, db_session):
        teacher = create_test_user(db_session, "latexteacher2", "teacher")
        create_test_question(db_session, content="求 $\\frac{1}{2}$", created_by=teacher.id)
        register_and_login(client, "latexstudent2", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "katex" in response.text.lower()
