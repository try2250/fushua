from app.core.config import Settings


def test_settings_ignore_non_model_app_env_keys():
    settings = Settings(
        SECRET_KEY="session-secret",
        BACKUP_SECRET="backup-secret",
        BACKUP_DIR="/tmp/backups",
        DATABASE_URL="sqlite:///./test.db",
    )

    assert settings.DATABASE_URL == "sqlite:///./test.db"
