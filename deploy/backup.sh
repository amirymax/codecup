#!/usr/bin/env bash
# Бэкап базы CodeCup. Ставится в cron на сервере:
#   0 3 * * * /opt/codecup/deploy/backup.sh >> /var/log/codecup-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/codecup}"
KEEP_DAYS="${KEEP_DAYS:-14}"
DB_NAME="${POSTGRES_DB:-codecup}"
DB_USER="${POSTGRES_USER:-codecup}"

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y-%m-%d_%H-%M)
FILE="$BACKUP_DIR/codecup_$STAMP.sql.gz"

pg_dump --username="$DB_USER" --format=plain --no-owner "$DB_NAME" | gzip > "$FILE"

# Пустой архив означает провалившийся дамп — такой лучше удалить сразу,
# чем обнаружить его при восстановлении.
if [ ! -s "$FILE" ]; then
    echo "ОШИБКА: дамп пустой, удаляю $FILE"
    rm -f "$FILE"
    exit 1
fi

echo "$(date '+%F %T') бэкап готов: $FILE ($(du -h "$FILE" | cut -f1))"

find "$BACKUP_DIR" -name 'codecup_*.sql.gz' -mtime +"$KEEP_DAYS" -delete
