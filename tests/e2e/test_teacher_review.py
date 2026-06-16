"""E2E: 教师批注 → 学生错题本看到"""
from app.models import Question


def test_teacher_comment_visible_to_student(client, db, register_teacher, student_in_class):
    from app.core.security import create_access_token

    email_t, token_t = register_teacher("review_t")
    hdr_t = {"Authorization": f"Bearer {token_t}"}
    teacher = db.query(__import__("app.models", fromlist=["User"]).User).filter(
        __import__("app.models", fromlist=["User"]).User.username == email_t
    ).first()
    student, cls, s_token = student_in_class(teacher.id, "批改班")
    hdr_s = {"Authorization": f"Bearer {s_token}"}

    # 老师建题
    r = client.post("/api/v1/questions", headers=hdr_t, json={
        "subject": "数学", "semester": "七年级上册", "chapter": "代数",
        "q_type": "choice", "content": "批注测试题", "option_a": "A", "option_b": "B",
        "option_c": "C", "option_d": "D", "answer": "B", "difficulty": 1,
    })
    qid = r.json()["data"]["id"]

    # 老师写批注
    r = client.post("/api/v1/comments", headers=hdr_t, json={
        "student_id": student.id, "question_id": qid,
        "comment_text": "这里要注意符号!"
    })
    assert r.status_code == 200

    # 学生答题（错）
    client.post("/api/v1/records", headers=hdr_s, json={
        "question_id": qid, "user_answer": "A", "is_correct": False,
    })

    # 学生查错题 — 应看到批注
    r = client.get("/api/v1/practice-records/mistakes", headers=hdr_s)
    assert r.status_code == 200
    mistakes = r.json()["data"]
    assert len(mistakes) >= 1
    assert any("注意符号" in (str(m.get("comments", []))) for m in mistakes)
