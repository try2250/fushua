from tests.conftest import create_test_user, register_and_login


class TestHelpRoute:
    def test_help_page_anonymous(self, client, db_session):
        response = client.get("/help")
        assert response.status_code == 200
        assert "帮助中心" in response.text

    def test_help_page_student(self, client, db_session):
        create_test_user(db_session, "helpstu", "student")
        register_and_login(client, "helpstu", "student")
        response = client.get("/help")
        assert response.status_code == 200
        assert "学生帮助" in response.text
        assert "注册登录" in response.text
        assert "做题流程" in response.text
        assert "查看错题和收藏" in response.text
        assert "学习计划" in response.text

    def test_help_page_teacher(self, client, db_session):
        register_and_login(client, "helptch", "teacher")
        response = client.get("/help")
        assert response.status_code == 200
        assert "教师帮助" in response.text
        assert "建班" in response.text
        assert "导入题目" in response.text
        assert "布置作业" in response.text
        assert "查看统计" in response.text
        assert "忘记密码" in response.text

    def test_help_page_common_section(self, client, db_session):
        response = client.get("/help")
        assert response.status_code == 200
        assert "通用帮助" in response.text
        assert "反馈问题" in response.text
        assert "联系管理员" in response.text

    def test_help_page_anonymous_shows_both_roles(self, client, db_session):
        response = client.get("/help")
        assert response.status_code == 200
        assert "教师帮助" in response.text
        assert "学生帮助" in response.text


class TestHelpNavLink:
    def test_help_link_in_nav_student(self, client, db_session):
        create_test_user(db_session, "navstu", "student")
        register_and_login(client, "navstu", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert 'href="/help"' in response.text

    def test_help_link_in_nav_teacher(self, client, db_session):
        register_and_login(client, "navtch", "teacher")
        response = client.get("/teacher/questions", follow_redirects=True)
        assert response.status_code == 200
        assert 'href="/help"' in response.text

    def test_help_link_in_nav_anonymous(self, client, db_session):
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert 'href="/help"' in response.text
