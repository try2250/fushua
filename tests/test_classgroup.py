from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import ClassGroup, ClassMember


class TestClassGroup:
    def test_create_class(self, client, db_session):
        register_and_login(client, "classteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/classes/create", data={
            "name": "三年二班", "_csrf_token": csrf,
        })
        assert response.status_code == 303
        c = db_session.query(ClassGroup).first()
        assert c is not None
        assert c.name == "三年二班"

    def test_teacher_see_classes(self, client, db_session):
        register_and_login(client, "classteacher2", "teacher")
        csrf = get_csrf_token(client)
        client.post("/classes/create", data={"name": "一班", "_csrf_token": csrf})
        response = client.get("/teacher/classes", follow_redirects=True)
        assert response.status_code == 200
        assert "一班" in response.text

    def test_add_student_to_class(self, client, db_session):
        teacher = create_test_user(db_session, "classteacher3", "teacher")
        student = create_test_user(db_session, "classstudent", "student")
        cls = ClassGroup(name="二班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "classteacher3", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(f"/classes/{cls.id}/members/add", data={
            "username": "classstudent", "_csrf_token": csrf,
        })
        assert response.status_code == 303
        member = db_session.query(ClassMember).first()
        assert member is not None
