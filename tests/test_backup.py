from datetime import datetime

from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import BackupLog


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
