from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_systemd_path_includes_system_binaries():
    deploy_script = (ROOT / "scripts" / "deploy_to_server.sh").read_text(encoding="utf-8")

    assert 'Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"' in deploy_script


def test_backup_script_parses_postgres_url_safely():
    backup_script = (ROOT / "scripts" / "backup_db.sh").read_text(encoding="utf-8")

    assert "urllib.parse" in backup_script
    assert "url.hostname" in backup_script
    assert "url.username" in backup_script
    assert "PGPASSWORD" in backup_script
    assert "sed -n 's/.*:\\/\\/\\([^:]*\\):.*/\\1/p'" not in backup_script
