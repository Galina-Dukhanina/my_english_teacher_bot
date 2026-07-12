#!/bin/sh
# Резервная копия SQLite-базы.
# Использование: ./scripts/backup_db.sh
# Переменные: DB_PATH (путь к БД), BACKUP_DIR (каталог бэкапов)

set -e

DB_PATH="${DB_PATH:-./bot_database.db}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bot_database_${TIMESTAMP}.db"

sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
echo "Backup saved: $BACKUP_FILE"

# Оставляем последние 14 копий
ls -1t "$BACKUP_DIR"/bot_database_*.db 2>/dev/null | tail -n +15 | xargs -r rm --
