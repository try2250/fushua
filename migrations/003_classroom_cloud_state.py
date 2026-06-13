"""Cloud-only classroom state migration."""


def _tables():
    from app.models import ClassroomGroupMember, ClassroomGroupSet, ClassroomSessionState

    return (
        ClassroomSessionState.__table__,
        ClassroomGroupSet.__table__,
        ClassroomGroupMember.__table__,
    )


def upgrade(engine):
    for table in _tables():
        table.create(bind=engine, checkfirst=True)


def downgrade(engine):
    for table in reversed(_tables()):
        table.drop(bind=engine, checkfirst=True)


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.database import engine

    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "upgrade":
        print("Running migration: Create classroom cloud state tables...")
        upgrade(engine)
        print("Migration completed successfully!")
    elif action == "downgrade":
        print("Running downgrade: Drop classroom cloud state tables...")
        downgrade(engine)
        print("Downgrade completed successfully!")
    else:
        print("Usage: python migrations/003_classroom_cloud_state.py [upgrade|downgrade]")
        sys.exit(1)
