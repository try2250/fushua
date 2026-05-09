import pytest
from app.models import ClassGroup, ClassMember, QuestionBank, Question
from app.routers.permissions import (
    teacher_owns_student,
    teacher_owns_bank,
    teacher_owns_class,
    teacher_owns_question,
)
from tests.conftest import create_test_user


def test_teacher_owns_student_same_class(db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    student = create_test_user(db_session, "student1", role="student")

    class_group = ClassGroup(name="Test Class", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    member = ClassMember(class_id=class_group.id, user_id=student.id)
    db_session.add(member)
    db_session.commit()

    assert teacher_owns_student(db_session, teacher.id, student.id) is True


def test_teacher_owns_student_different_class(db_session):
    teacher1 = create_test_user(db_session, "teacher1", role="teacher")
    teacher2 = create_test_user(db_session, "teacher2", role="teacher")
    student = create_test_user(db_session, "student1", role="student")

    class_group = ClassGroup(name="Teacher2's Class", created_by=teacher2.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    member = ClassMember(class_id=class_group.id, user_id=student.id)
    db_session.add(member)
    db_session.commit()

    assert teacher_owns_student(db_session, teacher1.id, student.id) is False


def test_teacher_owns_bank_own(db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    bank = QuestionBank(name="My Bank", subject="数学", created_by=teacher.id)
    db_session.add(bank)
    db_session.commit()

    assert teacher_owns_bank(db_session, teacher.id, bank.id) is True


def test_teacher_owns_bank_other(db_session):
    teacher1 = create_test_user(db_session, "teacher1", role="teacher")
    teacher2 = create_test_user(db_session, "teacher2", role="teacher")
    bank = QuestionBank(name="Teacher2's Bank", subject="数学", created_by=teacher2.id)
    db_session.add(bank)
    db_session.commit()

    assert teacher_owns_bank(db_session, teacher1.id, bank.id) is False


def test_teacher_owns_class_own(db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    class_group = ClassGroup(name="My Class", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    assert teacher_owns_class(db_session, teacher.id, class_group.id) is True


def test_teacher_owns_class_other(db_session):
    teacher1 = create_test_user(db_session, "teacher1", role="teacher")
    teacher2 = create_test_user(db_session, "teacher2", role="teacher")
    class_group = ClassGroup(name="Teacher2's Class", created_by=teacher2.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    assert teacher_owns_class(db_session, teacher1.id, class_group.id) is False


def test_teacher_owns_question_own(db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    question = Question(
        subject="数学",
        q_type="choice",
        content="1+1=?",
        answer="B",
        created_by=teacher.id,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)

    assert teacher_owns_question(db_session, teacher.id, question.id) is True


def test_teacher_owns_question_other(db_session):
    teacher1 = create_test_user(db_session, "teacher1", role="teacher")
    teacher2 = create_test_user(db_session, "teacher2", role="teacher")
    question = Question(
        subject="数学",
        q_type="choice",
        content="2+2=?",
        answer="C",
        created_by=teacher2.id,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)

    assert teacher_owns_question(db_session, teacher1.id, question.id) is False
