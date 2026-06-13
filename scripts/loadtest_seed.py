"""为 locust 压测预先准备数据。
执行：python scripts/loadtest_seed.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, ClassGroup, ClassMember, Question


def main():
    db = SessionLocal()
    try:
        t = db.query(User).filter(User.username == "stress@school.cn").first()
        if not t:
            t = User(username="stress@school.cn", password_hash=User.hash_password("stresspass"), role="teacher", display_name="压测老师")
            db.add(t); db.commit(); db.refresh(t)

        cls = db.query(ClassGroup).filter(ClassGroup.name == "压测班", ClassGroup.created_by == t.id).first()
        if not cls:
            cls = ClassGroup(name="压测班", created_by=t.id)
            db.add(cls); db.commit(); db.refresh(cls)

        for i in range(100):
            uname = f"s_{i}"
            stu = db.query(User).filter(User.username == uname).first()
            if not stu:
                stu = User(username=uname, password_hash=User.hash_password("stresspass"), role="student", display_name=f"压测学生 {i}")
                db.add(stu); db.commit(); db.refresh(stu)
            if not db.query(ClassMember).filter(ClassMember.class_id == cls.id, ClassMember.user_id == stu.id).first():
                db.add(ClassMember(class_id=cls.id, user_id=stu.id))

        if db.query(Question).filter(Question.created_by == t.id).count() == 0:
            for i in range(50):
                db.add(Question(subject="数学", semester="七年级上册", chapter=f"第{i // 10 + 1}章", q_type="choice", difficulty=(i % 3) + 1, content=f"压测题 {i}", option_a="A", option_b="B", option_c="C", option_d="D", answer="A", created_by=t.id))
        db.commit()
        print(f"loadtest seed done: 1 teacher + 1 class + 100 students + 50 questions")
        print(f"   class_id = {cls.id}")
        print(f"   students: s_0..s_99 / stresspass")
    finally:
        db.close()


if __name__ == "__main__":
    main()
