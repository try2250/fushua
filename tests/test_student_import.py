from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import ClassGroup, ClassMember, User


class TestStudentImport:
    def test_import_page_loads(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher1", "teacher")
        cls = ClassGroup(name="导入班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher1", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/import-students")
        assert response.status_code == 200
        assert "批量导入学生" in response.text

    def test_import_creates_new_students(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher2", "teacher")
        cls = ClassGroup(name="新建班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher2", "teacher")
        csrf = get_csrf_token(client)
        csv_data = "username,display_name\nstu1,学生一\nstu2,学生二"
        response = client.post(
            f"/teacher/classes/{cls.id}/import-students",
            data={"csv_text": csv_data, "_csrf_token": csrf},
        )
        assert response.status_code == 200
        assert "新建 2 人" in response.text
        assert "跳过" in response.text
        members = db_session.query(ClassMember).filter(ClassMember.class_id == cls.id).all()
        assert len(members) == 2
        u1 = db_session.query(User).filter(User.username == "stu1").first()
        assert u1 is not None
        assert u1.display_name == "学生一"
        assert u1.class_id == cls.id
        assert u1.role == "student"
        assert User.verify_password(u1.password_hash, "abc123")

    def test_import_skips_existing_users(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher3", "teacher")
        existing = create_test_user(db_session, "existstu", "student")
        cls = ClassGroup(name="跳过班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher3", "teacher")
        csrf = get_csrf_token(client)
        csv_data = "username,display_name\nexiststu,已存在学生\nnewstu,新学生"
        response = client.post(
            f"/teacher/classes/{cls.id}/import-students",
            data={"csv_text": csv_data, "_csrf_token": csrf},
        )
        assert response.status_code == 200
        assert "新建 1 人" in response.text
        assert "跳过（已存在） 1 人" in response.text
        members = db_session.query(ClassMember).filter(ClassMember.class_id == cls.id).all()
        assert len(members) == 2
        refreshed = db_session.query(User).filter(User.username == "existstu").first()
        assert refreshed.class_id == cls.id

    def test_import_empty_csv(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher4", "teacher")
        cls = ClassGroup(name="空班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher4", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(
            f"/teacher/classes/{cls.id}/import-students",
            data={"csv_text": "", "_csrf_token": csrf},
        )
        assert response.status_code == 200
        assert "请输入CSV数据" in response.text

    def test_import_existing_guest_joins_class(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher5", "teacher")
        guest = User(
            username="gueststu",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="游客学生",
            is_guest=True,
        )
        db_session.add(guest)
        cls = ClassGroup(name="游客班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher5", "teacher")
        csrf = get_csrf_token(client)
        csv_data = "username,display_name\ngueststu,游客学生"
        response = client.post(
            f"/teacher/classes/{cls.id}/import-students",
            data={"csv_text": csv_data, "_csrf_token": csrf},
        )
        assert response.status_code == 200
        refreshed = db_session.query(User).filter(User.username == "gueststu").first()
        assert refreshed.class_id == cls.id
        assert refreshed.is_guest == False

    def test_import_requires_teacher(self, client, db_session):
        create_test_user(db_session, "importstudent", "student")
        cls = ClassGroup(name="权限班", created_by=999)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importstudent", "student")
        response = client.get(f"/teacher/classes/{cls.id}/import-students")
        assert response.status_code == 403

    def test_import_page_has_link_in_class_detail(self, client, db_session):
        teacher = create_test_user(db_session, "importteacher6", "teacher")
        cls = ClassGroup(name="链接班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "importteacher6", "teacher")
        response = client.get(f"/classes/{cls.id}")
        assert response.status_code == 200
        assert "批量导入学生" in response.text
        assert f"/teacher/classes/{cls.id}/import-students" in response.text
