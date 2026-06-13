from datetime import datetime
import gzip

from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import BackupLog
from app.services.backup_service import BackupService


class TestBackupAdminPage:
    def test_backup_page_requires_admin(self, client):
        response = client.get("/admin/backup", follow_redirects=False)

        assert response.status_code == 303

    def test_backup_page_renders_for_admin(self, client, db_session):
        create_test_user(db_session, username="backup_admin", role="admin")
        db_session.add(BackupLog(status="success", file_path="fushua_test.sql.gz", file_size=2048))
        db_session.commit()
        register_and_login(client, username="backup_admin", role="admin")

        response = client.get("/admin/backup", follow_redirects=False)

        assert response.status_code == 200
        assert "downloadBackup" in response.text


class TestBackupTrigger:
    def test_backup_trigger_rejects_invalid_secret(self, client, monkeypatch):
        monkeypatch.setattr("app.routers.backup.BACKUP_SECRET", "valid-secret")

        response = client.post(
            "/admin/backup/trigger",
            headers={"X-Backup-Secret": "wrong-secret"},
        )

        assert response.status_code == 401

    def test_backup_trigger_accepts_valid_secret(self, client, monkeypatch):
        monkeypatch.setattr("app.routers.backup.BACKUP_SECRET", "valid-secret")

        def fake_trigger_backup(self, triggered_by="cron"):
            return {
                "status": "success",
                "backup_id": 123,
                "file_path": "fushua_test.sql.gz",
                "file_size": 2048,
                "duration_seconds": 1,
            }

        monkeypatch.setattr("app.routers.backup.BackupService.trigger_backup", fake_trigger_backup)

        response = client.post(
            "/admin/backup/trigger",
            headers={"X-Backup-Secret": "valid-secret"},
        )

        assert response.status_code == 200
        assert response.json()["backup_id"] == 123


class TestBackupJsonActions:
    def test_backup_delete_accepts_json_csrf_payload_from_admin_page(self, client, db_session):
        create_test_user(db_session, username="backup_delete_admin", role="admin")
        backup = BackupLog(
            status="success",
            file_path=None,
            file_size=2048,
            created_at=datetime.utcnow(),
        )
        db_session.add(backup)
        db_session.commit()
        db_session.refresh(backup)
        register_and_login(client, username="backup_delete_admin", role="admin")
        csrf = get_csrf_token(client)

        response = client.post(
            f"/admin/backup/delete/{backup.id}",
            json={"_csrf_token": csrf},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"


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
