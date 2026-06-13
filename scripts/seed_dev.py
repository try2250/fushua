"""验证阶段：清空并重建 dev 数据库。
用法：
    python scripts/seed_dev.py [--reset] [--scale N] [--with-records]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import User, ClassGroup, ClassMember, Question, PlatformAdmin, Record


def reset_schema(keep_db: bool):
    if not keep_db:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed(scale: int = 1, with_records: bool = False):
    db = SessionLocal()
    try:
        # 1 平台管理员（不论 scale 都只有 1 个）
        if not db.query(PlatformAdmin).first():
            db.add(PlatformAdmin(
                username="root",
                password_hash=PlatformAdmin.hash_password("rootpass"),
                email="root@fushua.local",
            ))

        # 2 老师（数量 = 2 * scale）
        teachers = []
        for i in range(2 * scale):
            slug = f"t{i+1}"
            email = f"{slug}@school.cn"
            t = db.query(User).filter(User.username == email).first()
            if not t:
                t = User(
                    username=email,
                    password_hash=User.hash_password("teacher123"),
                    role="teacher",
                    display_name=f"老师 {i+1}",
                )
                db.add(t); db.flush()
            teachers.append(t)

        db.commit()
        for t in teachers:
            db.refresh(t)

        # 3 每老师 1 班 + 3 学生 + 10 题
        for idx, t in enumerate(teachers):
            cls_name = f"{t.display_name} 的 demo 班"
            cls = db.query(ClassGroup).filter(
                ClassGroup.name == cls_name, ClassGroup.created_by == t.id,
            ).first()
            if not cls:
                cls = ClassGroup(name=cls_name, created_by=t.id)
                db.add(cls); db.flush()

            students = []
            for s in range(3):
                student_email = f"stu_{t.id}_{s}@school.cn"
                stu = db.query(User).filter(User.username == student_email).first()
                if not stu:
                    stu = User(
                        username=student_email,
                        password_hash=User.hash_password("student123"),
                        role="student",
                        display_name=f"{t.display_name}-学生{s+1}",
                    )
                    db.add(stu); db.flush()
                students.append(stu)
                if not db.query(ClassMember).filter(
                    ClassMember.class_id == cls.id, ClassMember.user_id == stu.id,
                ).first():
                    db.add(ClassMember(class_id=cls.id, user_id=stu.id))

            existing_qs = db.query(Question).filter(Question.created_by == t.id).count()
            if existing_qs == 0:
                for i in range(10):
                    db.add(Question(
                        subject="数学" if i % 2 == 0 else "物理",
                        semester="七年级上册",
                        chapter=f"第{(i // 3) + 1}章",
                        q_type="choice",
                        difficulty=(i % 3) + 1,
                        content=f"{t.display_name}的题 {i+1}：1+{i}=?",
                        option_a=str(i),
                        option_b=str(i+1),
                        option_c=str(i+2),
                        option_d=str(i+3),
                        answer="B",
                        explanation=f"答案是 1+{i}={i+1}",
                        created_by=t.id,
                    ))
            db.commit()

            if with_records:
                teacher_questions = db.query(Question).filter(
                    Question.created_by == t.id
                ).limit(5).all()
                for stu in students:
                    for i, q in enumerate(teacher_questions):
                        existing = db.query(Record).filter(
                            Record.user_id == stu.id,
                            Record.question_id == q.id,
                        ).first()
                        if existing:
                            continue
                        db.add(Record(
                            user_id=stu.id,
                            question_id=q.id,
                            user_answer="B" if i < 3 else "A",
                            is_correct=(i < 3),
                        ))
                db.commit()

        print(f"seed 完成 (scale={scale}, records={with_records})")
        print(f"  - PlatformAdmin: root / rootpass")
        for t in teachers:
            print(f"  - teacher: {t.username} / teacher123")
        print(f"  - 每老师 3 个学生 (stu_<teacher_id>_0..2@school.cn / student123)")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="fushua dev DB 重建 + 种子数据")
    parser.add_argument("--reset", action="store_true",
                        help="先 drop 所有表再重建（默认 keep）")
    parser.add_argument("--scale", type=int, default=1,
                        help="数据规模倍数（教师/班级/题目/学生数都乘以该值）")
    parser.add_argument("--with-records", action="store_true",
                        help="为每个学生生成示例答题记录")
    parser.add_argument("--keep-db", action="store_true",
                        help="不删除现有数据库（向后兼容）")
    args = parser.parse_args()
    reset_schema(keep_db=not args.reset and args.keep_db)
    seed(scale=args.scale, with_records=args.with_records)


if __name__ == "__main__":
    main()
