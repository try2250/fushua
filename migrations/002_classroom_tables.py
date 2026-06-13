"""课堂管理表结构迁移脚本。"""


def _classroom_tables():
    from app.models import (
        ClassroomDrawRecord,
        ClassroomQuestionSnapshot,
        ClassroomSession,
    )

    return (
        ClassroomSession.__table__,
        ClassroomDrawRecord.__table__,
        ClassroomQuestionSnapshot.__table__,
    )


def upgrade(engine):
    """创建课堂管理相关表"""
    for table in _classroom_tables():
        table.create(bind=engine, checkfirst=True)


def downgrade(engine):
    """删除课堂管理相关表"""
    for table in reversed(_classroom_tables()):
        table.drop(bind=engine, checkfirst=True)


if __name__ == "__main__":
    import sys
    import os

    # 添加项目根目录到 Python 路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app.database import engine

    if len(sys.argv) < 2:
        print("Usage: python migrations/002_classroom_tables.py [upgrade|downgrade]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "upgrade":
        print("Running migration: Create classroom tables...")
        upgrade(engine)
        print("Migration completed successfully!")
    elif action == "downgrade":
        print("Running downgrade: Drop classroom tables...")
        downgrade(engine)
        print("Downgrade completed successfully!")
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
