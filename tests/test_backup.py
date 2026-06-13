from datetime import datetime
import gzip
import pytest

from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import BackupLog
from app.services.backup_service import BackupService


class TestBackupAdminPage:
    @pytest.mark.skip(reason="Admin role removed — backup page pending platform migration (Plan 1.2B)")
    def test_backup_page_requires_admin(self, client):
        pass

    @pytest.mark.skip(reason="Admin role removed — backup page pending platform migration (Plan 1.2B)")
    def test_backup_page_renders_for_admin(self, client, db_session):
        pass


class TestBackupTrigger:
    @pytest.mark.skip(reason="Admin role removed — backup trigger pending platform migration (Plan 1.2B)")
    def test_backup_trigger_rejects_invalid_secret(self, client, monkeypatch):
        pass

    @pytest.mark.skip(reason="Admin role removed — backup trigger pending platform migration (Plan 1.2B)")
    def test_backup_trigger_accepts_valid_secret(self, client, monkeypatch):
        pass


class TestBackupJsonActions:
    @pytest.mark.skip(reason="Admin role removed — backup delete pending platform migration (Plan 1.2B)")
    def test_backup_delete_accepts_json_csrf_payload_from_admin_page(self, client, db_session):
        pass


class TestBackupValidation:
    def test_small_postgres_backup_can_be_valid_for_new_database(self, db_session, tmp_path):
        backup_file = tmp_path / "fushua_small.sql.gz"
        with gzip.open(backup_file, "wt", encoding="utf-8") as f:
            f.write("-- PostgreSQL database dump\nCREATE TABLE smoke_test (id integer);\n")

        backup = BackupLog(
            status="success",
            file_path=backup_file.name,
            file_size=backup_file.stat().st_size,
            created_at=datetime.utcnow(),
        )
        db_session.add(backup)
        db_session.commit()
        db_session.refresh(backup)

        service = BackupService(db_session)
        service.backup_dir = tmp_path

        result = service.validate_backup(backup.id)

        assert result["status"] == "valid"
        assert result["checks"]["file_exists"] is True
        assert result["checks"]["file_size_ok"] is True
        assert result["checks"]["integrity_check"] is True
