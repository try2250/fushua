import pytest
from unittest.mock import patch
from tests.conftest import create_test_user, login_as
from app.models import ClassGroup, ClassMember, Question, Record


def test_teacher_stats_pdf_only_shows_own_class_students(client, db_session):
    teacher_a = create_test_user(db_session, "teacher_a", role="teacher")
    teacher_b = create_test_user(db_session, "teacher_b", role="teacher")

    class_a = ClassGroup(name="Class A", created_by=teacher_a.id)
    db_session.add(class_a)
    db_session.commit()
    db_session.refresh(class_a)

    student_a = create_test_user(db_session, "student_a", role="student")
    student_a.class_id = class_a.id
    db_session.add(ClassMember(class_id=class_a.id, user_id=student_a.id))

    class_b = ClassGroup(name="Class B", created_by=teacher_b.id)
    db_session.add(class_b)
    db_session.commit()
    db_session.refresh(class_b)

    student_b = create_test_user(db_session, "student_b", role="student")
    student_b.class_id = class_b.id
    db_session.add(ClassMember(class_id=class_b.id, user_id=student_b.id))
    db_session.commit()

    question_a = Question(
        subject="数学",
        q_type="choice",
        content="Teacher A question",
        answer="A",
        created_by=teacher_a.id,
    )
    db_session.add(question_a)
    db_session.commit()
    db_session.refresh(question_a)

    db_session.add(Record(user_id=student_a.id, question_id=question_a.id, user_answer="A", is_correct=True))
    db_session.add(Record(user_id=student_b.id, question_id=question_a.id, user_answer="B", is_correct=False))
    db_session.commit()

    login_as(client, "teacher_a", "abc12345")

    with patch("app.utils.report.generate_teacher_report") as mock_report:
        import io
        mock_report.return_value = io.BytesIO(b"%PDF-1.4 test")
        response = client.get("/teacher/stats/export/pdf")

    assert response.status_code == 200
    call_args = mock_report.call_args
    student_stats = call_args[0][5]
    student_usernames = [s["username"] for s in student_stats]
    assert "student_a" in student_usernames
    assert "student_b" not in student_usernames


def test_teacher_stats_pdf_empty_when_no_students(client, db_session):
    teacher = create_test_user(db_session, "teacher_solo", role="teacher")

    question = Question(
        subject="数学",
        q_type="choice",
        content="Solo question",
        answer="A",
        created_by=teacher.id,
    )
    db_session.add(question)
    db_session.commit()

    login_as(client, "teacher_solo", "abc12345")

    with patch("app.utils.report.generate_teacher_report") as mock_report:
        import io
        mock_report.return_value = io.BytesIO(b"%PDF-1.4 test")
        response = client.get("/teacher/stats/export/pdf")

    assert response.status_code == 200
    call_args = mock_report.call_args
    student_stats = call_args[0][5]
    assert len(student_stats) == 0


def test_admin_can_see_all_students_in_stats(client, db_session):
    admin = create_test_user(db_session, "admin_stats", role="admin")
    teacher = create_test_user(db_session, "teacher_stats", role="teacher")

    class_group = ClassGroup(name="Test Class", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    student = create_test_user(db_session, "student_stats", role="student")
    student.class_id = class_group.id
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    db_session.commit()

    question = Question(
        subject="数学",
        q_type="choice",
        content="Admin question",
        answer="A",
        created_by=admin.id,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)

    db_session.add(Record(user_id=student.id, question_id=question.id, user_answer="A", is_correct=True))
    db_session.commit()

    login_as(client, "admin_stats", "abc12345")

    with patch("app.utils.report.generate_teacher_report") as mock_report:
        import io
        mock_report.return_value = io.BytesIO(b"%PDF-1.4 test")
        response = client.get("/teacher/stats/export/pdf")

    assert response.status_code == 200
    call_args = mock_report.call_args
    student_stats = call_args[0][5]
    student_usernames = [s["username"] for s in student_stats]
    assert "student_stats" in student_usernames


def test_teacher_with_multiple_classes_sees_all_own_students(client, db_session):
    teacher = create_test_user(db_session, "teacher_multi", role="teacher")

    class_1 = ClassGroup(name="Class 1", created_by=teacher.id)
    class_2 = ClassGroup(name="Class 2", created_by=teacher.id)
    db_session.add_all([class_1, class_2])
    db_session.commit()
    db_session.refresh(class_1)
    db_session.refresh(class_2)

    student_1 = create_test_user(db_session, "student_m1", role="student")
    student_1.class_id = class_1.id
    db_session.add(ClassMember(class_id=class_1.id, user_id=student_1.id))

    student_2 = create_test_user(db_session, "student_m2", role="student")
    student_2.class_id = class_2.id
    db_session.add(ClassMember(class_id=class_2.id, user_id=student_2.id))
    db_session.commit()

    question = Question(
        subject="数学",
        q_type="choice",
        content="Multi-class question",
        answer="A",
        created_by=teacher.id,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)

    db_session.add(Record(user_id=student_1.id, question_id=question.id, user_answer="A", is_correct=True))
    db_session.add(Record(user_id=student_2.id, question_id=question.id, user_answer="A", is_correct=True))
    db_session.commit()

    login_as(client, "teacher_multi", "abc12345")

    with patch("app.utils.report.generate_teacher_report") as mock_report:
        import io
        mock_report.return_value = io.BytesIO(b"%PDF-1.4 test")
        response = client.get("/teacher/stats/export/pdf")

    assert response.status_code == 200
    call_args = mock_report.call_args
    student_stats = call_args[0][5]
    student_usernames = [s["username"] for s in student_stats]
    assert "student_m1" in student_usernames
    assert "student_m2" in student_usernames


def test_teacher_stats_page_only_shows_own_class_students(client, db_session):
    """Teacher A's stats page should not show Teacher B's students who answered A's questions"""
    # Setup: Two teachers with separate classes
    teacher_a = create_test_user(db_session, "teacher_a_stats", role="teacher")
    teacher_b = create_test_user(db_session, "teacher_b_stats", role="teacher")

    # Teacher A's class and student
    class_a = ClassGroup(name="Class A Stats", created_by=teacher_a.id)
    db_session.add(class_a)
    db_session.commit()
    db_session.refresh(class_a)

    student_a = create_test_user(db_session, "student_a_stats", role="student")
    student_a.class_id = class_a.id
    db_session.add(ClassMember(class_id=class_a.id, user_id=student_a.id))

    # Teacher B's class and student
    class_b = ClassGroup(name="Class B Stats", created_by=teacher_b.id)
    db_session.add(class_b)
    db_session.commit()
    db_session.refresh(class_b)

    student_b = create_test_user(db_session, "student_b_stats", role="student")
    student_b.class_id = class_b.id
    db_session.add(ClassMember(class_id=class_b.id, user_id=student_b.id))
    db_session.commit()

    # Teacher A creates a question
    question_a = Question(
        subject="数学",
        q_type="choice",
        content="Teacher A's stats question",
        answer="A",
        created_by=teacher_a.id,
    )
    db_session.add(question_a)
    db_session.commit()
    db_session.refresh(question_a)

    # Both students answer Teacher A's question
    db_session.add(Record(user_id=student_a.id, question_id=question_a.id, user_answer="A", is_correct=True))
    db_session.add(Record(user_id=student_b.id, question_id=question_a.id, user_answer="B", is_correct=False))
    db_session.commit()

    # Test: Teacher A views stats page
    login_as(client, "teacher_a_stats", "abc12345")
    response = client.get("/teacher/stats")

    # Verify: Response should be successful
    assert response.status_code == 200
    html_content = response.text

    # Verify: Should show student_a but NOT student_b
    assert "student_a_stats" in html_content or student_a.display_name in html_content
    assert "student_b_stats" not in html_content
    assert student_b.display_name not in html_content


def test_admin_sees_all_students_in_stats_page(client, db_session):
    """Admin should see all students in stats page regardless of class"""
    admin = create_test_user(db_session, "admin_stats_page", role="admin")
    teacher = create_test_user(db_session, "teacher_stats_admin", role="teacher")

    # Teacher's class and student
    class_group = ClassGroup(name="Teacher Stats Class", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    student = create_test_user(db_session, "student_stats_admin", role="student")
    student.class_id = class_group.id
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    db_session.commit()

    # Admin creates a question
    question = Question(
        subject="数学",
        q_type="choice",
        content="Admin stats question",
        answer="A",
        created_by=admin.id,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)

    # Student answers
    db_session.add(Record(user_id=student.id, question_id=question.id, user_answer="A", is_correct=True))
    db_session.commit()

    # Admin views stats
    login_as(client, "admin_stats_page", "abc12345")
    response = client.get("/teacher/stats")

    assert response.status_code == 200
    html_content = response.text
    assert "student_stats_admin" in html_content or student.display_name in html_content
