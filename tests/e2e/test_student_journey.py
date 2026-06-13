"""E2E：学生加班 → 看题库 → 答题 → 查错题本。"""
from app.models import Question, User


def test_full_student_journey(client, db, register_teacher, student_in_class):
    email, t_token = register_teacher("bob")
    t_headers = {"Authorization": f"Bearer {t_token}"}
    teacher = db.query(User).filter(User.username == email).first()
    student, cls, s_token = student_in_class(teacher.id, "E2E 学生路径班")
    s_headers = {"Authorization": f"Bearer {s_token}"}

    qids = []
    for i in range(5):
        r = client.post("/api/v1/questions", headers=t_headers, json={
            "subject": "数学", "semester": "七年级上册", "chapter": "代数",
            "q_type": "choice", "content": f"学生路径题 {i+1}",
            "option_a": "0", "option_b": "1", "option_c": "2", "option_d": "3",
            "answer": "B", "difficulty": 1,
        })
        assert r.status_code == 200
        qids.append(r.json()["data"]["id"])

    r = client.get(f"/api/v1/questions?class_id={cls.id}", headers=s_headers)
    assert r.status_code == 200
    student_seen = [q["content"] for q in r.json()["data"]]
    assert len(student_seen) == 5

    for i, qid in enumerate(qids):
        r = client.post("/api/v1/records", headers=s_headers, json={
            "question_id": qid, "user_answer": "B" if i < 3 else "A", "is_correct": (i < 3),
        })
        assert r.status_code == 200

    r = client.get("/api/v1/records/mistakes", headers=s_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) == 2

    r = client.get("/api/v1/records/stats", headers=s_headers)
    assert r.status_code == 200
    stats = r.json()["data"]
    assert stats["total_count"] == 5
