"""E2E：两个老师各自工作，互相所有资源 404/不可见。"""
def test_two_teachers_full_isolation(client, db, register_teacher):
    email_a, token_a = register_teacher("iso_a")
    hdr_a = {"Authorization": f"Bearer {token_a}"}
    r = client.post("/api/v1/classes", headers=hdr_a, json={"name": "A 班"})
    assert r.status_code == 200
    cls_a = r.json()["data"]
    r = client.post("/api/v1/questions", headers=hdr_a, json={
        "subject": "数学", "semester": "七年级上册", "chapter": "代数",
        "q_type": "choice", "content": "A 的题", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4",
        "answer": "A", "difficulty": 1,
    })
    assert r.status_code == 200
    q_a = r.json()["data"]
    r = client.post("/api/v1/assignments", headers=hdr_a, json={
        "title": "A 的作业", "class_id": cls_a["id"], "question_ids": f"[{q_a['id']}]", "description": "",
    })
    assert r.status_code == 200
    a_assignment = r.json()["data"]

    email_b, token_b = register_teacher("iso_b")
    hdr_b = {"Authorization": f"Bearer {token_b}"}

    r = client.get("/api/v1/classes", headers=hdr_b)
    assert all(c["name"] != "A 班" for c in r.json()["data"])
    r = client.get(f"/api/v1/classes/{cls_a['id']}", headers=hdr_b)
    assert r.status_code == 404
    r = client.get("/api/v1/questions", headers=hdr_b)
    assert all(q["content"] != "A 的题" for q in r.json()["data"])
    r = client.get(f"/api/v1/questions/{q_a['id']}", headers=hdr_b)
    assert r.status_code == 404
    r = client.get("/api/v1/assignments", headers=hdr_b)
    assert all(a["title"] != "A 的作业" for a in r.json()["data"])
    r = client.get(f"/api/v1/assignments/{a_assignment['id']}", headers=hdr_b)
    assert r.status_code == 404
    r = client.put(f"/api/v1/classes/{cls_a['id']}", headers=hdr_b, json={"name": "改"})
    assert r.status_code == 404
    r = client.put(f"/api/v1/questions/{q_a['id']}", headers=hdr_b, json={"content": "改"})
    assert r.status_code == 404
    r = client.delete(f"/api/v1/assignments/{a_assignment['id']}", headers=hdr_b)
    assert r.status_code == 404
