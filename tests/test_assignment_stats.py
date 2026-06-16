"""Plan 3.2 — 班级作业统计 API 测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, Question, ClassGroup, ClassMember, Assignment, AssignmentRecord, Record
from app.core.security import create_access_token


def _setup_assignment_with_records(db, teacher, student_ids, correct_patterns):
    """Helper: create class + assignment + questions + records."""
    cls = ClassGroup(name="统计班", created_by=teacher.id)
    db.add(cls); db.commit(); db.refresh(cls)
    for sid in student_ids:
        if not db.query(ClassMember).filter(ClassMember.class_id == cls.id, ClassMember.user_id == sid).first():
            db.add(ClassMember(class_id=cls.id, user_id=sid))
    db.commit()
    qids = []
    for i in range(3):
        q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                     content=f"统计题{i}", option_a="A", option_b="B", option_c="C", option_d="D",
                     answer="B", created_by=teacher.id)
        db.add(q); db.commit(); db.refresh(q)
        qids.append(q.id)
    a = Assignment(title="统计作业", class_id=cls.id, question_ids=str(qids), created_by=teacher.id)
    db.add(a); db.commit(); db.refresh(a)
    for si, sid in enumerate(student_ids):
        db.add(AssignmentRecord(assignment_id=a.id, user_id=sid, score=correct_patterns[si]))
        for qi, qid in enumerate(qids):
            db.add(Record(user_id=sid, question_id=qid, user_answer="B" if (si + qi) % 2 == 0 else "A",
                         is_correct=(si + qi) % 2 == 0))
    db.commit()
    return a, cls


def test_assignment_stats_api_returns_metrics(db, teacher_a):
    """模拟 3 学生提交作业 → 验证统计 API 返回正确指标。"""
    students = []
    for i in range(3):
        s = User(username=f"stats_s{i}", password_hash=User.hash_password("x"), role="student",
                 display_name=f"S{i}")
        db.add(s); db.commit(); db.refresh(s)
        students.append(s)

    a, cls = _setup_assignment_with_records(db, teacher_a, [s.id for s in students], [2, 3, 1])

    token = create_access_token({"user_id": teacher_a.id})
    client = TestClient(main_app)
    r = client.get(f"/api/v1/assignments/{a.id}/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_students"] == 3
    assert data["submitted_count"] == 3
    assert data["completion_rate"] == 1.0
    assert len(data["question_stats"]) == 3


def test_assignment_stats_tenant_isolation(db, teacher_a, teacher_b):
    """教师 B 访问教师 A 的作业统计 → 404。"""
    s = User(username="iso_s", password_hash=User.hash_password("x"), role="student", display_name="IS")
    db.add(s); db.commit(); db.refresh(s)
    a, cls = _setup_assignment_with_records(db, teacher_a, [s.id], [1])
    token_b = create_access_token({"user_id": teacher_b.id})
    client = TestClient(main_app)
    r = client.get(f"/api/v1/assignments/{a.id}/stats", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404
