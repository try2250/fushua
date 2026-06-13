"""验证阶段：清空并重建 dev 数据库。
用法：
    python scripts/seed_dev.py [--keep-db]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import User, ClassGroup, ClassMember, Question, PlatformAdmin


def reset_schema(keep_db: bool):
    if not keep_db:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # 1 平台管理员
        if not db.query(PlatformAdmin).first():
            db.add(PlatformAdmin(
                username="root",
                password_hash=PlatformAdmin.hash_password("rootpass"),
                email="root@fushua.local",
            ))

        # 2 老师
        teachers = []
        for slug, name in [("li", "李老师"), ("wang", "王老师")]:
            email = f"{slug}@school.cn"
            t = db.query(User).filter(User.username == email).first()
            if not t:
                t = User(
                    username=email,
                    password_hash=User.hash_password("teacher123"),
                    role="teacher",
                    display_name=name,
                )
                db.add(t); db.flush()
            teachers.append(t)

        db.commit()
        for t in teachers:
            db.refresh(t)

        # 每老师 1 班 + 1 学生 + 5 题
        for idx, t in enumerate(teachers):
            cls_name = f"{t.display_name} 的 demo 班"
            cls = db.query(ClassGroup).filter(
                ClassGroup.name == cls_name, ClassGroup.created_by == t.id,
            ).first()
            if not cls:
                cls = ClassGroup(name=cls_name, created_by=t.id)
                db.add(cls); db.flush()

            student_email = f"stu{idx}_{t.id}@school.cn"
            stu = db.query(User).filter(User.username == student_email).first()
            if not stu:
                stu = User(
                    username=student_email,
                    password_hash=User.hash_password("student123"),
                    role="student",
                    display_name=f"{t.display_name}班-学生{idx}",
                )
                db.add(stu); db.flush()
            if not db.query(ClassMember).filter(
                ClassMember.class_id == cls.id, ClassMember.user_id == stu.id,
            ).first():
                db.add(ClassMember(class_id=cls.id, user_id=stu.id))

            if not db.query(Question).filter(Question.created_by == t.id).first():
                for i in range(5):
                    db.add(Question(
                        subject="数学", semester="七年级上册", chapter="代数",
                        q_type="choice",
                        content=f"{t.display_name}的题 {i+1}：1+{i}=?",
                        option_a=str(i), option_b=str(i+1),
                        option_c=str(i+2), option_d=str(i+3),
                        answer="B", created_by=t.id,
                    ))

        db.commit()
        print("seed 完成")
        print("  - platform admin: root / rootpass")
        for t in teachers:
            print(f"  - teacher: {t.username} / teacher123")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-db", action="store_true")
    args = parser.parse_args()
    reset_schema(args.keep_db)
    seed()


if __name__ == "__main__":
    main()
