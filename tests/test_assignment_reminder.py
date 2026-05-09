from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Assignment, AssignmentRecord, ClassGroup, ClassMember, Notification


class TestAssignmentReminder:
    def test_teacher_can_view_assignment_detail(self, client, db_session):
        teacher = create_test_user(db_session, "detailteacher", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "detailteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "详情测试作业", "description": "查看详情",
            "question_ids": str(q.id), "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()
        response = client.get(f"/teacher/assignments/{assignment.id}", follow_redirects=True)
        assert response.status_code == 200
        assert "详情测试作业" in response.text

    def test_teacher_remind_incomplete_students(self, client, db_session):
        teacher = create_test_user(db_session, "remindteacher", "teacher")
        student1 = create_test_user(db_session, "remindstu1", "student")
        student2 = create_test_user(db_session, "remindstu2", "student")
        q = create_test_question(db_session, created_by=teacher.id)

        cls = ClassGroup(name="提醒测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student1.id))
        db_session.add(ClassMember(class_id=cls.id, user_id=student2.id))
        db_session.commit()

        register_and_login(client, "remindteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "提醒测试作业", "description": "测试提醒",
            "question_ids": str(q.id), "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()

        db_session.add(AssignmentRecord(
            assignment_id=assignment.id, user_id=student1.id, completed=True,
        ))
        db_session.commit()

        csrf = get_csrf_token(client)
        response = client.post(f"/teacher/assignments/{assignment.id}/remind", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 200
        assert "1" in response.text

        notifications = db_session.query(Notification).filter(
            Notification.user_id == student2.id,
            Notification.title == "作业提醒",
        ).all()
        assert len(notifications) == 1
        assert "提醒测试作业" in notifications[0].content

    def test_remind_no_duplicate_for_completed(self, client, db_session):
        teacher = create_test_user(db_session, "nodupteacher", "teacher")
        student = create_test_user(db_session, "nodupstu", "student")
        q = create_test_question(db_session, created_by=teacher.id)

        cls = ClassGroup(name="无重复班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        register_and_login(client, "nodupteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "完成作业", "question_ids": str(q.id),
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()

        db_session.add(AssignmentRecord(
            assignment_id=assignment.id, user_id=student.id, completed=True,
        ))
        db_session.commit()

        csrf = get_csrf_token(client)
        response = client.post(f"/teacher/assignments/{assignment.id}/remind", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 200

        notifications = db_session.query(Notification).filter(
            Notification.user_id == student.id,
        ).all()
        assert len(notifications) == 0

    def test_remind_requires_teacher(self, client, db_session):
        teacher = create_test_user(db_session, "remindt2", "teacher")
        student = create_test_user(db_session, "remindstu3", "student")
        q = create_test_question(db_session, created_by=teacher.id)

        register_and_login(client, "remindt2", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "权限测试", "question_ids": str(q.id),
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()

        register_and_login(client, "remindstu3", "student")
        response = client.get(f"/teacher/assignments/{assignment.id}", follow_redirects=False)
        assert response.status_code == 403

    def test_remind_other_teacher_assignment(self, client, db_session):
        teacher1 = create_test_user(db_session, "ownt1", "teacher")
        teacher2 = create_test_user(db_session, "ownt2", "teacher")
        q = create_test_question(db_session, created_by=teacher1.id)

        register_and_login(client, "ownt1", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "他人作业", "question_ids": str(q.id),
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()

        register_and_login(client, "ownt2", "teacher")
        response = client.get(f"/teacher/assignments/{assignment.id}", follow_redirects=False)
        assert response.status_code == 404

    def test_remind_shows_count(self, client, db_session):
        teacher = create_test_user(db_session, "countteacher", "teacher")
        s1 = create_test_user(db_session, "countstu1", "student")
        s2 = create_test_user(db_session, "countstu2", "student")
        s3 = create_test_user(db_session, "countstu3", "student")
        q = create_test_question(db_session, created_by=teacher.id)

        cls = ClassGroup(name="计数班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=s1.id))
        db_session.add(ClassMember(class_id=cls.id, user_id=s2.id))
        db_session.add(ClassMember(class_id=cls.id, user_id=s3.id))
        db_session.commit()

        register_and_login(client, "countteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "计数作业", "question_ids": str(q.id),
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()

        db_session.add(AssignmentRecord(assignment_id=assignment.id, user_id=s1.id, completed=True))
        db_session.commit()

        csrf = get_csrf_token(client)
        response = client.post(f"/teacher/assignments/{assignment.id}/remind", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 200
        assert "2" in response.text

    def test_student_receives_notification_content(self, client, db_session):
        teacher = create_test_user(db_session, "notifteacher", "teacher")
        student = create_test_user(db_session, "notifstu", "student")
        q = create_test_question(db_session, created_by=teacher.id)

        cls = ClassGroup(name="通知班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        register_and_login(client, "notifteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "通知作业", "question_ids": str(q.id),
            "_csrf_token": csrf,
        })
        assignment = db_session.query(Assignment).first()

        csrf = get_csrf_token(client)
        client.post(f"/teacher/assignments/{assignment.id}/remind", data={
            "_csrf_token": csrf,
        })

        register_and_login(client, "notifstu", "student")
        response = client.get("/student/notifications", follow_redirects=True)
        assert response.status_code == 200
        assert "作业提醒" in response.text
        assert "通知作业" in response.text
