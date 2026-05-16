from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import QuestionBank
import io


class TestQuestionBankOwnership:
    """Test that teachers cannot use other teachers' question banks"""

    def test_teacher_cannot_create_question_in_other_bank(self, client, db_session):
        """Teacher A cannot create a question in Teacher B's bank"""
        teacher_a = create_test_user(db_session, "teacherA", "teacher")
        teacher_b = create_test_user(db_session, "teacherB", "teacher")

        bank_b = QuestionBank(name="Teacher B's Bank", subject="数学", created_by=teacher_b.id)
        db_session.add(bank_b)
        db_session.commit()
        db_session.refresh(bank_b)

        register_and_login(client, "teacherA", "teacher")
        csrf = get_csrf_token(client)

        response = client.post("/teacher/questions/create", data={
            "content": "Test question",
            "answer": "Test answer",
            "subject": "数学",
            "difficulty": "3",
            "bank_id": str(bank_b.id),
            "_csrf_token": csrf,
        })

        assert response.status_code == 404

        from app.models import Question
        questions = db_session.query(Question).filter_by(
            content="Test question"
        ).all()
        assert len(questions) == 0

    def test_teacher_cannot_edit_question_to_other_bank(self, client, db_session):
        """Teacher A cannot move their question to Teacher B's bank"""
        teacher_a = create_test_user(db_session, "teacherA2", "teacher")
        teacher_b = create_test_user(db_session, "teacherB2", "teacher")

        question_a = create_test_question(db_session, created_by=teacher_a.id, content="Question A")
        original_bank_id = question_a.bank_id

        bank_b = QuestionBank(name="Teacher B's Bank 2", subject="数学", created_by=teacher_b.id)
        db_session.add(bank_b)
        db_session.commit()
        db_session.refresh(bank_b)

        register_and_login(client, "teacherA2", "teacher")
        csrf = get_csrf_token(client)

        response = client.post(f"/teacher/questions/{question_a.id}/edit", data={
            "content": "Question A",
            "answer": question_a.answer,
            "subject": question_a.subject,
            "difficulty": str(question_a.difficulty),
            "bank_id": str(bank_b.id),
            "_csrf_token": csrf,
        })

        assert response.status_code == 404

        db_session.refresh(question_a)
        assert question_a.bank_id == original_bank_id

    def test_teacher_cannot_import_to_other_bank(self, client, db_session):
        """Teacher A cannot import questions to Teacher B's bank"""
        teacher_a = create_test_user(db_session, "teacherA3", "teacher")
        teacher_b = create_test_user(db_session, "teacherB3", "teacher")

        bank_b = QuestionBank(name="Teacher B's Bank 3", subject="数学", created_by=teacher_b.id)
        db_session.add(bank_b)
        db_session.commit()
        db_session.refresh(bank_b)

        register_and_login(client, "teacherA3", "teacher")
        csrf = get_csrf_token(client)

        csv_content = "题目内容,答案,科目,难度\n测试题目,测试答案,数学,3\n"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))

        response = client.post("/teacher/questions/import", data={
            "bank_id": str(bank_b.id),
            "_csrf_token": csrf,
        }, files={
            "file": ("test.csv", csv_file, "text/csv")
        })

        assert response.status_code == 404

        from app.models import Question
        imported_questions = db_session.query(Question).filter_by(
            content="测试题目",
            created_by=teacher_a.id
        ).all()
        assert len(imported_questions) == 0

    def test_admin_can_use_any_bank(self, client, db_session):
        """Admin can create questions in any teacher's bank"""
        admin = create_test_user(db_session, "admin1", "teacher")
        admin.is_admin = True
        db_session.commit()

        teacher = create_test_user(db_session, "teacher1", "teacher")

        bank = QuestionBank(name="Teacher's Bank", subject="数学", created_by=teacher.id)
        db_session.add(bank)
        db_session.commit()
        db_session.refresh(bank)

        register_and_login(client, "admin1", "teacher")
        csrf = get_csrf_token(client)

        response = client.post("/teacher/questions/create", data={
            "content": "Admin question",
            "answer": "Admin answer",
            "subject": "数学",
            "difficulty": "3",
            "bank_id": str(bank.id),
            "_csrf_token": csrf,
        })

        assert response.status_code in [200, 303]

        from app.models import Question
        admin_question = db_session.query(Question).filter_by(
            content="Admin question",
            created_by=admin.id
        ).first()
        assert admin_question is not None
        assert admin_question.bank_id == bank.id
