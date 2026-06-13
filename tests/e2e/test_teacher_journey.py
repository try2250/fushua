"""E2E：教师从邮箱注册 → 建班 → 加学生 → 建题 → 创建作业 → 看作业记录。"""
from app.models import User, ClassMember


def test_full_teacher_journey(client, db, register_teacher):
    email, token = register_teacher("alice")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/v1/classes", headers=headers, json={"name": "E2E 数学 1 班"})
    assert r.status_code == 200, r.text
    cls = r.json()["data"]
    cls_id = cls["id"]
    assert cls["name"] == "E2E 数学 1 班"

    stu = User(username="e2e_stu_alice_1", password_hash=User.hash_password("x"), role="student", display_name="A 班学生 1")
    db.add(stu); db.commit(); db.refresh(stu)
    db.add(ClassMember(class_id=cls_id, user_id=stu.id)); db.commit()

    qids = []
    for i in range(3):
        r = client.post("/api/v1/questions", headers=headers, json={
            "subject": "数学", "semester": "七年级上册", "chapter": "代数",
            "q_type": "choice", "content": f"E2E 题 {i+1}：1+{i}=?",
            "option_a": str(i), "option_b": str(i+1), "option_c": str(i+2), "option_d": str(i+3),
            "answer": "B", "difficulty": 1,
        })
        assert r.status_code == 200, r.text
        qids.append(r.json()["data"]["id"])

    r = client.post("/api/v1/assignments", headers=headers, json={
        "title": "E2E 第一次作业", "description": "", "class_id": cls_id,
        "question_ids": str(qids),
    })
    assert r.status_code == 200, r.text
    aid = r.json()["data"]["id"]

    r = client.get(f"/api/v1/assignments/{aid}/records", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"] == []

    r = client.get("/api/v1/questions", headers=headers)
    assert r.status_code == 200
    contents = [q["content"] for q in r.json()["data"]]
    assert all("E2E 题" in c for c in contents)
    assert len(contents) == 3
