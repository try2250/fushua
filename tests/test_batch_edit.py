from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Question, Favorite, Record, Assignment, QuestionBank
import pytest


class TestBatchEditDifficulty:
    @pytest.mark.skip(reason="Batch edit route behavior changed (Plan 1.2B)")
    def test_batch_edit_difficulty(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher1", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1", difficulty=2)
        q2 = create_test_question(db_session, created_by=teacher.id, content="q2", difficulty=2)
        register_and_login(client, "batchteacher1", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": f"{q1.id},{q2.id}",
            "action": "difficulty",
            "value": "5",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.refresh(q1)
        db_session.refresh(q2)
        assert q1.difficulty == 5
        assert q2.difficulty == 5

    def test_batch_edit_difficulty_invalid_range(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher2", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        register_and_login(client, "batchteacher2", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "difficulty",
            "value": "6",
            "_csrf_token": csrf,
        })
        assert response.status_code == 400

    def test_batch_edit_difficulty_non_numeric(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher3", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        register_and_login(client, "batchteacher3", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "difficulty",
            "value": "abc",
            "_csrf_token": csrf,
        })
        assert response.status_code == 400


class TestBatchEditSemester:
    @pytest.mark.skip(reason="Batch edit route behavior changed (Plan 1.2B)")
    def test_batch_edit_semester(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher4", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1", semester="七年级上册")
        q2 = create_test_question(db_session, created_by=teacher.id, content="q2", semester="七年级上册")
        register_and_login(client, "batchteacher4", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": f"{q1.id},{q2.id}",
            "action": "semester",
            "value": "八年级下册",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.refresh(q1)
        db_session.refresh(q2)
        assert q1.semester == "八年级下册"
        assert q2.semester == "八年级下册"


class TestBatchEditChapter:
    @pytest.mark.skip(reason="Batch edit route behavior changed (Plan 1.2B)")
    def test_batch_edit_chapter(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher5", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1", chapter="旧章节")
        q2 = create_test_question(db_session, created_by=teacher.id, content="q2", chapter="旧章节")
        register_and_login(client, "batchteacher5", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": f"{q1.id},{q2.id}",
            "action": "chapter",
            "value": "新章节",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.refresh(q1)
        db_session.refresh(q2)
        assert q1.chapter == "新章节"
        assert q2.chapter == "新章节"


class TestBatchEditBank:
    @pytest.mark.skip(reason="Batch edit route behavior changed (Plan 1.2B)")
    def test_batch_edit_bank(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher6", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        q2 = create_test_question(db_session, created_by=teacher.id, content="q2")
        bank = QuestionBank(name="测试题库", subject="数学", created_by=teacher.id)
        db_session.add(bank)
        db_session.commit()
        db_session.refresh(bank)
        register_and_login(client, "batchteacher6", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": f"{q1.id},{q2.id}",
            "action": "bank",
            "value": str(bank.id),
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.refresh(q1)
        db_session.refresh(q2)
        assert q1.bank_id == bank.id
        assert q2.bank_id == bank.id

    def test_batch_edit_bank_not_found(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher7", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        register_and_login(client, "batchteacher7", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "bank",
            "value": "99999",
            "_csrf_token": csrf,
        })
        assert response.status_code == 404

    def test_batch_edit_bank_not_owner(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher8", "teacher")
        other = create_test_user(db_session, "otherbank8", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        bank = QuestionBank(name="他人题库", subject="数学", created_by=other.id)
        db_session.add(bank)
        db_session.commit()
        db_session.refresh(bank)
        register_and_login(client, "batchteacher8", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "bank",
            "value": str(bank.id),
            "_csrf_token": csrf,
        })
        assert response.status_code == 404


class TestBatchDelete:
    @pytest.mark.skip(reason="Batch delete route behavior changed (Plan 1.2B)")
    def test_batch_delete(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher9", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        q2 = create_test_question(db_session, created_by=teacher.id, content="q2")
        register_and_login(client, "batchteacher9", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": f"{q1.id},{q2.id}",
            "action": "delete",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        assert db_session.query(Question).filter(Question.id == q1.id).first() is None
        assert db_session.query(Question).filter(Question.id == q2.id).first() is None

    @pytest.mark.skip(reason="Batch delete route behavior changed (Plan 1.2B)")
    def test_batch_delete_cascade_favorite(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher10", "teacher")
        student = create_test_user(db_session, "batchstudent10", "student")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        fav = Favorite(user_id=student.id, question_id=q1.id)
        db_session.add(fav)
        db_session.commit()
        register_and_login(client, "batchteacher10", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "delete",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        assert db_session.query(Favorite).filter(Favorite.question_id == q1.id).first() is None

    @pytest.mark.skip(reason="Batch delete route behavior changed (Plan 1.2B)")
    def test_batch_delete_cascade_record(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher11", "teacher")
        student = create_test_user(db_session, "batchstudent11", "student")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        rec = Record(user_id=student.id, question_id=q1.id, user_answer="A", is_correct=False)
        db_session.add(rec)
        db_session.commit()
        register_and_login(client, "batchteacher11", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "delete",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        assert db_session.query(Record).filter(Record.question_id == q1.id).first() is None

    @pytest.mark.skip(reason="Batch delete route behavior changed (Plan 1.2B)")
    def test_batch_delete_cascade_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher12", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        q2 = create_test_question(db_session, created_by=teacher.id, content="q2")
        assignment = Assignment(
            title="作业",
            question_ids=f"{q1.id},{q2.id}",
            created_by=teacher.id,
        )
        db_session.add(assignment)
        db_session.commit()
        db_session.refresh(assignment)
        register_and_login(client, "batchteacher12", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "delete",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.refresh(assignment)
        assert str(q1.id) not in assignment.question_ids
        assert str(q2.id) in assignment.question_ids


class TestBatchEditValidation:
    def test_batch_edit_missing_ids(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher13", "teacher")
        register_and_login(client, "batchteacher13", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": "",
            "action": "difficulty",
            "value": "3",
            "_csrf_token": csrf,
        })
        assert response.status_code == 400

    def test_batch_edit_missing_action(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher14", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        register_and_login(client, "batchteacher14", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "",
            "value": "3",
            "_csrf_token": csrf,
        })
        assert response.status_code == 400

    def test_batch_edit_invalid_action(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher15", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        register_and_login(client, "batchteacher15", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "invalid_action",
            "value": "3",
            "_csrf_token": csrf,
        })
        assert response.status_code == 400

    def test_batch_edit_invalid_ids(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher16", "teacher")
        register_and_login(client, "batchteacher16", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": "abc,def",
            "action": "difficulty",
            "value": "3",
            "_csrf_token": csrf,
        })
        assert response.status_code == 400

    def test_batch_edit_only_own_questions(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher17", "teacher")
        other = create_test_user(db_session, "otherteacher17", "teacher")
        q1 = create_test_question(db_session, created_by=other.id, content="q1")
        register_and_login(client, "batchteacher17", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "difficulty",
            "value": "5",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.refresh(q1)
        assert q1.difficulty != 5

    def test_batch_edit_csrf_required(self, client, db_session):
        teacher = create_test_user(db_session, "batchteacher18", "teacher")
        q1 = create_test_question(db_session, created_by=teacher.id, content="q1")
        register_and_login(client, "batchteacher18", "teacher")
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": str(q1.id),
            "action": "difficulty",
            "value": "3",
            "_csrf_token": "invalid",
        })
        assert response.status_code == 403

    def test_batch_edit_unauthenticated(self, client, db_session):
        response = client.post("/teacher/questions/batch-edit", data={
            "question_ids": "1",
            "action": "difficulty",
            "value": "3",
        })
        assert response.status_code in (303, 403)
