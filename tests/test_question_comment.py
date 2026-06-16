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


from app.services.comment_service import comment_service

def test_comment_service_create(db, teacher_a):
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="3+3=?", option_a="5", option_b="6", option_c="7", option_d="8",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    c = comment_service.create_comment(db, teacher_id=teacher_a.id, student_id=777,
                                       question_id=q.id, comment_text="注意进位", assignment_id=None)
    assert c.id is not None
    assert c.comment_text == "注意进位"

def test_comment_service_get_for_student(db, teacher_a):
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="4+4=?", option_a="7", option_b="8", option_c="9", option_d="10",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    comment_service.create_comment(db, teacher_id=teacher_a.id, student_id=666,
                                   question_id=q.id, comment_text="试试另一种解法", assignment_id=None)
    comments = comment_service.get_comments_for_student_question(db, student_id=666, question_id=q.id)
    assert len(comments) >= 1
    assert comments[0].comment_text == "试试另一种解法"


from fastapi.testclient import TestClient
from app.main import app as main_app
from app.core.security import create_access_token

def test_comments_api_create(client, db, teacher_a):
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="5+5=?", option_a="9", option_b="10", option_c="11", option_d="12",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.post("/api/v1/comments", json={
        "student_id": 555, "question_id": q.id, "comment_text": "API 批注"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

def test_comments_api_get_for_question(client, db, teacher_a):
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="6+6=?", option_a="11", option_b="12", option_c="13", option_d="14",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    token = create_access_token({"user_id": teacher_a.id})
    client.post("/api/v1/comments", json={
        "student_id": 444, "question_id": q.id, "comment_text": "test"
    }, headers={"Authorization": f"Bearer {token}"})
    r = client.get(f"/api/v1/comments?student_id=444&question_id={q.id}",
                   headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1
