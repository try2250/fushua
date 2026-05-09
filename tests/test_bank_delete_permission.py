import pytest
from app.models import QuestionBank
from tests.conftest import create_test_user, register_and_login, get_csrf_token, create_test_question


def create_test_bank(db, name="测试题库", subject="数学", created_by=1, **kwargs):
    bank = QuestionBank(
        name=name,
        subject=subject,
        semester=kwargs.get("semester", "八年级上册"),
        description=kwargs.get("description", ""),
        bank_type=kwargs.get("bank_type", "custom"),
        created_by=created_by,
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


class TestBankDeletePermission:
    def test_teacher_cannot_delete_other_teacher_bank(self, client, db_session):
        teacher_a = create_test_user(db_session, username="teacher_a", role="teacher")
        teacher_b = create_test_user(db_session, username="teacher_b", role="teacher")
        bank_b = create_test_bank(db_session, name="教师B的题库", created_by=teacher_b.id)

        register_and_login(client, "teacher_a", role="teacher")

        csrf = get_csrf_token(client)
        response = client.post(
            f"/teacher/banks/{bank_b.id}/delete",
            data={"_csrf_token": csrf},
            follow_redirects=False,
        )
        assert response.status_code == 404

        bank_still_exists = db_session.query(QuestionBank).filter(QuestionBank.id == bank_b.id).first()
        assert bank_still_exists is not None

    def test_teacher_can_delete_own_bank(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher", role="teacher")
        bank = create_test_bank(db_session, name="我的题库", created_by=teacher.id)

        register_and_login(client, "teacher", role="teacher")

        csrf = get_csrf_token(client)
        response = client.post(
            f"/teacher/banks/{bank.id}/delete",
            data={"_csrf_token": csrf},
            follow_redirects=False,
        )
        assert response.status_code == 303

        bank_deleted = db_session.query(QuestionBank).filter(QuestionBank.id == bank.id).first()
        assert bank_deleted is None

    def test_delete_nonexistent_bank_returns_404(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher", role="teacher")

        register_and_login(client, "teacher", role="teacher")

        csrf = get_csrf_token(client)
        response = client.post(
            "/teacher/banks/99999/delete",
            data={"_csrf_token": csrf},
            follow_redirects=False,
        )
        assert response.status_code == 404
