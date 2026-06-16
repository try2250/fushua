"""章节地图 API 测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import ClassGroup, ClassMember, User
from app.core.security import create_access_token

def test_chapter_map_returns_grid(client, db, teacher_a):
    cls = ClassGroup(name="地图班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    u = User(username="chap_user", password_hash=User.hash_password("x"), role="student", display_name="CU")
    db.add(u); db.commit(); db.refresh(u)
    db.add(ClassMember(class_id=cls.id, user_id=u.id)); db.commit()
    token = create_access_token({"user_id": u.id})
    r = client.get(f"/api/v1/practice/chapter-map?subject=数学", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)  # list of chapter entries
