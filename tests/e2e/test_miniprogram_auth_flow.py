"""E2E：小程序学生 username/password 登录 → /me → practice-records 答题 → mistakes。"""
from app.models import User, ClassGroup, ClassMember, Question


def test_miniprogram_student_auth_and_practice(client, db, register_teacher):
    email_t, token_t = register_teacher("mp_t")
    hdr_t = {"Authorization": f"Bearer {token_t}"}
    teacher = db.query(User).filter(User.username == email_t).first()

    cls = ClassGroup(name="MP 班", created_by=teacher.id)
    db.add(cls); db.commit(); db.refresh(cls)
    student = User(username="mp_student", password_hash=User.hash_password("studentpass"), role="student", display_name="MP 学生")
    db.add(student); db.commit(); db.refresh(student)
    db.add(ClassMember(class_id=cls.id, user_id=student.id)); db.commit()

    for i in range(3):
        client.post("/api/v1/questions", headers=hdr_t, json={
            "subject": "数学", "semester": "七年级上册", "chapter": "代数",
            "q_type": "choice", "content": f"MP 题 {i}", "option_a": "0", "option_b": "1", "option_c": "2", "option_d": "3",
            "answer": "B", "difficulty": 1,
        })
    q_ids = [q["id"] for q in client.get("/api/v1/questions", headers=hdr_t).json()["data"]]

    r = client.post("/api/v1/auth/login", json={"username": "mp_student", "password": "studentpass"})
    assert r.status_code == 200
    s_token = r.json()["data"]["token"]
    hdr_s = {"Authorization": f"Bearer {s_token}"}

    r = client.get("/api/v1/users/me", headers=hdr_s)
    assert r.status_code == 200
    assert r.json()["data"]["username"] == "mp_student"

    for i, qid in enumerate(q_ids[:2]):
        r = client.post("/api/v1/practice-records", headers=hdr_s, json={
            "question_id": qid, "user_answer": "B" if i == 0 else "A", "is_correct": (i == 0),
        })
        assert r.status_code == 200, r.text

    r = client.get("/api/v1/practice-records/mistakes", headers=hdr_s)
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1
