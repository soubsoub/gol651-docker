#!/bin/bash
# =============================================================================
# GOL651 - Load the lab OR-models schema into gol651 AND gol651_exercises
# =============================================================================
# Runs automatically after 02_teaching_schema.sh (alphabetical order).
# - 04_lab_schema.sql   input tables (both databases)
# - 05_lab_data.sql     seed data (both databases)
# - 06_lab_results.sql  lab_results output table (gol651_exercises ONLY)
# =============================================================================

gol651_load_lab_schema() {
    local socket="${SOCKET:-/var/run/mysqld/mysqld.sock}"
    local dir="/docker-entrypoint-initdb.d/teaching"
    local db file user password

    # Input tables + seed data go into both databases
    for db in gol651 gol651_exercises; do
        if [ "$db" = "gol651" ]; then
            user="root";        password="$MYSQL_ROOT_PASSWORD"
        else
            user="$MYSQL_USER"; password="$MYSQL_PASSWORD"
        fi
        for file in "$dir"/04_lab_schema.sql "$dir"/05_lab_data.sql; do
            echo "[gol651] loading $(basename "$file") into $db as $user"
            MYSQL_PWD="$password" mysql --protocol=socket -u"$user" -hlocalhost \
                --socket="$socket" --default-character-set=utf8mb4 \
                --database="$db" < "$file" || return 1
        done
    done

    # lab_results goes into gol651_exercises only
    file="$dir/06_lab_results.sql"
    user="$MYSQL_USER"; password="$MYSQL_PASSWORD"
    echo "[gol651] loading $(basename "$file") into gol651_exercises as $user"
    MYSQL_PWD="$password" mysql --protocol=socket -u"$user" -hlocalhost \
        --socket="$socket" --default-character-set=utf8mb4 \
        --database="gol651_exercises" < "$file" || return 1

    echo "[gol651] lab OR-models schema loaded"
}

gol651_load_lab_schema
