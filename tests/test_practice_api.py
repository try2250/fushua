"""Practice API 测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import ClassGroup, ClassMember, WeeklyScore, User
from app.core.security import create_access_token, get_week_start
from datetime import date


def test_practice_start_returns_questions(client, db, teacher_a):
    from app.models import Question
    cls = ClassGroup(name="练习班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    for i in range(10):
        db.add(Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                        content=f"题{i}", option_a="A", option_b="B", option_c="C", option_d="D",
                        answer="A", created_by=teacher_a.id))
    db.commit()
    student = User(username="ps", password_hash=User.hash_password("x"), role="student", display_name="PS")
    db.add(student); db.commit(); db.refresh(student)
    db.add(ClassMember(class_id=cls.id, user_id=student.id)); db.commit()
    token = create_access_token({"user_id": student.id})
    r = client.get(f"/api/v1/practice/start?class_id={cls.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["questions"]) == 10
    assert "session_id" in data


def test_leaderboard_returns_top_students(client, db, teacher_a):
    cls = ClassGroup(name="排行班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    monday = get_week_start()
    for uid in range(5):
        u = User(username=f"lb_{uid}", password_hash=User.hash_password("x"), role="student", display_name=f"L{uid}")
        db.add(u); db.commit(); db.refresh(u)
        db.add(ClassMember(class_id=cls.id, user_id=u.id))
        db.add(WeeklyScore(user_id=u.id, class_id=cls.id, week_start=monday, score=uid + 1))
    db.commit()
    token = create_access_token({"user_id": 1})
    r = client.get(f"/api/v1/practice/leaderboard?class_id={cls.id}&week_start={monday.isoformat()}",
                   headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    board = r.json()["data"]
    assert len(board) == 5
    assert board[0]["score"] >= board[-1]["score"]
