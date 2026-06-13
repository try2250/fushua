#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/fushua_${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

if [ -n "${DATABASE_URL:-}" ] && echo "${DATABASE_URL}" | grep -q "postgresql"; then
    echo "[备份] 检测到 PostgreSQL 数据库"
    mapfile -t DB_PARTS < <(python3 - <<'PY'
import os
from urllib.parse import unquote, urlparse

url = urlparse(os.environ["DATABASE_URL"])
print(url.hostname or "localhost")
print(url.port or 5432)
print(unquote(url.username or ""))
print(unquote(url.password or ""))
print((url.path or "/").lstrip("/"))
PY
)
    PGHOST="${DB_PARTS[0]}"
    PGPORT="${DB_PARTS[1]}"
    PGUSER="${DB_PARTS[2]}"
    PGPASSWORD="${DB_PARTS[3]}"
    PGDB="${DB_PARTS[4]}"

    BACKUP_FILE="${BACKUP_FILE}.sql.gz"
    echo "[备份] 导出 PostgreSQL → ${BACKUP_FILE}"
    PGPASSWORD="${PGPASSWORD}" pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" "${PGDB}" | gzip > "${BACKUP_FILE}"
    echo "[备份] 完成！文件大小: $(du -h "${BACKUP_FILE}" | cut -f1)"
    echo "BACKUP_FILE_PATH=${BACKUP_FILE}"
else
    DB_FILE="${DB_FILE:-./fushua.db}"
    if [ ! -f "${DB_FILE}" ]; then
        echo "[错误] SQLite 数据库文件不存在: ${DB_FILE}"
        exit 1
    fi
    BACKUP_FILE="${BACKUP_FILE}.db"
    echo "[备份] 复制 SQLite → ${BACKUP_FILE}"
    sqlite3 "${DB_FILE}" ".backup '${BACKUP_FILE}'"
    echo "[备份] 完成！文件大小: $(du -h "${BACKUP_FILE}" | cut -f1)"
    echo "BACKUP_FILE_PATH=${BACKUP_FILE}"
fi

KEEP_DAYS="${KEEP_DAYS:-30}"
echo "[清理] 删除 ${KEEP_DAYS} 天前的备份..."
find "${BACKUP_DIR}" -name "fushua_*" -mtime +${KEEP_DAYS} -delete 2>/dev/null || true
echo "[清理] 完成"
