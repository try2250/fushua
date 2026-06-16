"""插入 10 个 Badge seed 数据。用法: python scripts/seed_badges.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app.models import Badge

BADGES = [
    ("opening", "开门红", "首次答题"),
    ("streak_3", "三日连击", "连续打卡 3 天"),
    ("streak_7", "七日不缀", "连续打卡 7 天"),
    ("streak_30", "三十日大师", "连续打卡 30 天"),
    ("hundred", "百题成就", "累计答对 100 题"),
    ("thousand", "千题成就", "累计答对 1000 题"),
    ("perfect_set", "满分组", "一组 10 题全对"),
    ("subject_math", "数学开光", "数学正确率 >= 80% 且 >= 50 题"),
    ("subject_physics", "物理开光", "物理正确率 >= 80% 且 >= 50 题"),
    ("subject_chinese", "语文开光", "语文正确率 >= 80% 且 >= 50 题"),
]

def main():
    db = SessionLocal()
    try:
        for code, name, desc in BADGES:
            if not db.query(Badge).filter(Badge.code == code).first():
                db.add(Badge(code=code, name=name, description=desc,
                            icon_url=f"/static/badges/{code}.png"))
        db.commit()
        print(f"seed_badges: {len(BADGES)} badges seeded")
    finally:
        db.close()

if __name__ == "__main__":
    main()
