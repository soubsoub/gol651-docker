#!/bin/sh
# =============================================================================
# GOL651 - Restore ONLY the practice database gol651_exercises
# =============================================================================
# Usage:  sh scripts/restore-exercises.sh
# Rebuilds the tables, data and views of gol651_exercises from
# mysql/init/teaching/. The reference database gol651 and everything else
# are NOT touched. MySQL must be running.
# =============================================================================
set -eu
cd "$(dirname "$0")/.."

echo "This replaces all tables and data of gol651_exercises with the original version."
printf "Type yes to continue: "
read -r answer || answer=""
if [ "$answer" != "yes" ]; then
    echo "Cancelled. Nothing was changed."
    exit 1
fi

# 1. root drops the views (they may be owned by root on volumes created before
#    stage 2.3); 2. the course user reloads everything, so the practice objects
#    belong to the course user.
docker compose exec -T mysql sh -c '
    echo "DROP VIEW IF EXISTS v_customer_sales, v_low_stock, v_order_totals" |
        MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot gol651_exercises || exit 1
    for f in /docker-entrypoint-initdb.d/teaching/0*.sql; do
        echo "loading $(basename "$f")"
        MYSQL_PWD="$MYSQL_PASSWORD" mysql -u"$MYSQL_USER" --default-character-set=utf8mb4 \
            gol651_exercises < "$f" || exit 1
    done'
echo "gol651_exercises restored."
