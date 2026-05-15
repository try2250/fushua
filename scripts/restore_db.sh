#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "用法: ./restore_db.sh <备份文件路径>"
    echo ""
    echo "示例:"
    echo "  ./restore_db.sh ./backups/fushua_20260511_120000.db        # SQLite"
    echo "  ./restore_db.sh ./backups/fushua_20260511_120000.sql.gz    # PostgreSQL"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[错误] 备份文件不存在: ${BACKUP_FILE}"
    exit 1
fi

if [[ "${BACKUP_FILE}" == *.sql.gz ]]; then
    if [ -z "${DATABASE_URL:-}" ]; then
        echo "[错误] 恢复 PostgreSQL 备份需要设置 DATABASE_URL 环境变量"
        exit 1
    fi
    echo "[恢复] 从 PostgreSQL 备份恢复: ${BACKUP_FILE}"
    echo "[警告] 这将覆盖当前数据库！"
    read -p "确认继续？(输入 YES): " confirm
    if [ "${confirm}" != "YES" ]; then
        echo "[取消] 恢复已取消"
        exit 0
    fi
    PGHOST=$(echo "${DATABASE_URL}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    PGPORT=$(echo "${DATABASE_URL}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    PGUSER=$(echo "${DATABASE_URL}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    PGDB=$(echo "${DATABASE_URL}" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    PGPASSWORD=$(echo "${DATABASE_URL}" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${PGPASSWORD}" psql -h "${PGHOST}" -p "${PGPORT:-5432}" -U "${PGUSER}" "${PGDB}"
    echo "[恢复] 完成！"

elif [[ "${BACKUP_FILE}" == *.db ]]; then
    DB_FILE="${DB_FILE:-./fushua.db}"
    echo "[恢复] 从 SQLite 备份恢复: ${BACKUP_FILE} → ${DB_FILE}"
    echo "[警告] 这将覆盖当前数据库！"
    read -p "确认继续？(输入 YES): " confirm
    if [ "${confirm}" != "YES" ]; then
        echo "[取消] 恢复已取消"
        exit 0
    fi
    cp "${BACKUP_FILE}" "${DB_FILE}"
    echo "[恢复] 完成！"
else
    echo "[错误] 不支持的备份文件格式: ${BACKUP_FILE}"
    exit 1
fi
