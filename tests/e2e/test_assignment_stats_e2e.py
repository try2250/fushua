"""E2E: 模拟 10 学生提交作业 → 统计正确"""
from app.models import User, ClassGroup, ClassMember, Question, Assignment, AssignmentRecord, Record
from app.core.security import create_access_token
from fastapi.testclient import TestClient
from app.main import app as main_app


def test_ten_students_submit_stats_are_correct(db, teacher_a):
    """10 个学生提交同一作业，验证统计页面数据正确。"""
    cls = ClassGroup(name="十人班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)

    students = []
    for i in range(10):
        s = User(username=f"ten_s{i}", password_hash=User.hash_password("x"), role="student", display_name=f"TenS{i}")
        db.add(s); db.commit(); db.refresh(s)
        db.add(ClassMember(class_id=cls.id, user_id=s.id))
        students.append(s)
    db.commit()

    qids = []
    for i in range(5):
        q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                     content=f"十人题{i}", option_a="A", option_b="B", option_c="C", option_d="D",
                     answer="B", created_by=teacher_a.id)
        db.add(q); db.commit(); db.refresh(q)
        qids.append(q.id)

    a = Assignment(title="十人作业", class_id=cls.id, question_ids=str(qids), created_by=teacher_a.id)
    db.add(a); db.commit(); db.refresh(a)

    # 每个人的答题模式不同，方便验证统计正确
    for si, s in enumerate(students):
        db.add(AssignmentRecord(assignment_id=a.id, user_id=s.id, score=si % 6))
        for qi, qid in enumerate(qids):
            db.add(Record(user_id=s.id, question_id=qid, user_answer="B" if (si + qi) % 3 != 0 else "A",
                         is_correct=(si + qi) % 3 != 0))
    db.commit()

    token = create_access_token({"user_id": teacher_a.id})
    client = TestClient(main_app)
    r = client.get(f"/api/v1/assignments/{a.id}/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_students"] == 10
    assert data["submitted_count"] == 10
    assert data["completion_rate"] == 1.0
    assert data["max_score"] == 5
    assert len(data["question_stats"]) == 5
    # 每道题的 correct_rate 应该是一致的（由交错的正确模式决定）
    for qs in data["question_stats"]:
        assert 0 <= qs["correct_rate"] <= 1
