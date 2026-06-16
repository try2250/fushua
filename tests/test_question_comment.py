"""Plan 3.1 — QuestionComment 模型 + comment_service + API 测试"""
import pytest
from app.models import QuestionComment, User, Question


def test_question_comment_creation(db, teacher_a):
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="1+1=?", option_a="1", option_b="2", option_c="3", option_d="4",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    c = QuestionComment(teacher_id=teacher_a.id, student_id=999, question_id=q.id,
                       comment_text="注意符号")
    db.add(c); db.commit(); db.refresh(c)
    assert c.id is not None
    assert c.comment_text == "注意符号"
    assert c.teacher_id == teacher_a.id


def test_question_comment_with_assignment(db, teacher_a):
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="2+2=?", option_a="3", option_b="4", option_c="5", option_d="6",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    c = QuestionComment(teacher_id=teacher_a.id, student_id=888, question_id=q.id,
                       assignment_id=1, comment_text="再看看")
    db.add(c); db.commit()
    assert c.assignment_id == 1
