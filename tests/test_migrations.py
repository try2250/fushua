import os

from alembic import command
from alembic.config import Config


def test_alembic_upgrade_head_works_with_sqlite(tmp_path, monkeypatch):
    db_path = tmp_path / "migration_check.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    assert db_path.exists()
