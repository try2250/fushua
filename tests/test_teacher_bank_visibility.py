import pytest
from tests.conftest import get_csrf_token, login_as


def test_question_bank_has_visibility_field(db_session):
    from app.models import QuestionBank
    bank = QuestionBank(name="测试题库", subject="数学", visibility="private", access_code="ABC123", created_by=1)
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    assert bank.visibility == "private"
    assert bank.access_code == "ABC123"


def test_question_bank_default_visibility(db_session):
    from app.models import QuestionBank
    bank = QuestionBank(name="默认题库", subject="英语", created_by=1)
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    assert bank.visibility in ("public", None)
    assert bank.access_code in ("", None)


def test_teacher_create_bank_with_visibility(client, db_session):
    from app.models import User, QuestionBank
    teacher = User(username="teacher_vis", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    login_as(client, "teacher_vis", "teacher1234a")

    csrf = get_csrf_token(client)
    resp = client.post("/teacher/banks/create", data={
        "_csrf_token": csrf,
        "name": "私有题库",
        "subject": "数学",
        "visibility": "private",
    }, follow_redirects=True)
    assert resp.status_code == 200

    bank = db_session.query(QuestionBank).filter(QuestionBank.name == "私有题库").first()
    assert bank is not None
    assert bank.visibility == "private"
    assert bank.access_code == ""


def test_teacher_create_bank_with_access_code(client, db_session):
    from app.models import User, QuestionBank
    teacher = User(username="teacher_code", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    login_as(client, "teacher_code", "teacher1234a")

    csrf = get_csrf_token(client)
    resp = client.post("/teacher/banks/create", data={
        "_csrf_token": csrf,
        "name": "准入码题库",
        "subject": "英语",
        "visibility": "code",
        "access_code": "MATH2024",
    }, follow_redirects=True)
    assert resp.status_code == 200

    bank = db_session.query(QuestionBank).filter(QuestionBank.name == "准入码题库").first()
    assert bank is not None
    assert bank.visibility == "code"
    assert bank.access_code == "MATH2024"


def test_student_sees_public_teacher_bank(client, db_session):
    from app.models import User, QuestionBank, Question
    teacher = User(username="teacher_pub", password_hash=User.hash_password("teacher1234a"), role="teacher", display_name="张老师")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="公开题库", subject="数学", visibility="public", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    q = Question(subject="数学", content="1+1=?", answer="2", bank_id=bank.id, created_by=teacher.id)
    db_session.add(q)
    db_session.commit()
    student = User(username="student_pub", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_pub", "student1234a")
    resp = client.get("/browse", follow_redirects=True)
    assert resp.status_code == 200
    assert "公开题库" in resp.text


def test_student_cannot_see_private_bank_not_in_class(client, db_session):
    from app.models import User, QuestionBank
    teacher = User(username="teacher_priv", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="私有题库X", subject="数学", visibility="private", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    student = User(username="student_priv", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_priv", "student1234a")
    resp = client.get("/browse", follow_redirects=True)
    assert resp.status_code == 200
    assert "私有题库X" not in resp.text


def test_student_unlock_bank_with_access_code(client, db_session):
    from app.models import User, QuestionBank, Question
    teacher = User(username="teacher_code2", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="准入码题库Y", subject="英语", visibility="code", access_code="SECRET123", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    q = Question(subject="英语", content="hello?", answer="hi", bank_id=bank.id, created_by=teacher.id)
    db_session.add(q)
    db_session.commit()
    student = User(username="student_code", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_code", "student1234a")
    resp = client.get("/browse?access_code_input=SECRET123", follow_redirects=True)
    assert resp.status_code == 200
    assert "准入码题库Y" in resp.text


def test_browse_bank_list_excludes_private_and_code(client, db_session):
    from app.models import User, QuestionBank, Question
    teacher = User(username="teacher_browse", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    pub_bank = QuestionBank(name="公开浏览题库", subject="数学", visibility="public", created_by=teacher.id)
    priv_bank = QuestionBank(name="私有浏览题库", subject="数学", visibility="private", created_by=teacher.id)
    code_bank = QuestionBank(name="准入码浏览题库", subject="数学", visibility="code", access_code="X", created_by=teacher.id)
    db_session.add_all([pub_bank, priv_bank, code_bank])
    db_session.commit()
    student = User(username="student_browse", password_hash=User.hash_password("student1234a"), role="student")
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_browse", "student1234a")
    resp = client.get("/browse?subject=数学", follow_redirects=True)
    assert resp.status_code == 200
    assert "公开浏览题库" in resp.text
    assert "私有浏览题库" not in resp.text
    assert "准入码浏览题库" not in resp.text


def test_student_practice_with_bank_id(client, db_session):
    from app.models import User, QuestionBank, Question
    teacher = User(username="teacher_prac", password_hash=User.hash_password("teacher1234a"), role="teacher")
    db_session.add(teacher)
    db_session.commit()
    bank = QuestionBank(name="练习题库Z", subject="数学", visibility="public", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()
    q1 = Question(subject="数学", content="3+3=?", answer="6", q_type="choice", option_a="5", option_b="6", option_c="7", option_d="8", bank_id=bank.id, created_by=teacher.id)
    db_session.add(q1)
    db_session.commit()
    student = User(username="student_prac", password_hash=User.hash_password("student1234a"), role="student", is_guest=False)
    db_session.add(student)
    db_session.commit()
    login_as(client, "student_prac", "student1234a")
    resp = client.get(f"/student/practice?bank_id={bank.id}", follow_redirects=True)
    assert resp.status_code == 200
    assert "3+3=?" in resp.text
