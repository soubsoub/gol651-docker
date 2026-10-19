#!/bin/bash
# =============================================================================
# GOL651 - Load the teaching schema into gol651 AND gol651_exercises
# =============================================================================
# Run automatically by the official MySQL image on FIRST start only (empty
# volume), after 01_init.sql. The same SQL files (mysql/init/teaching/) are
# applied to both databases, so there is a single source of truth.
#
# Works whether the image SOURCES this file or EXECUTES it (files mounted from
# Windows often appear executable): it uses only the mysql client and the
# container environment, never entrypoint helper functions. It never calls
# "exit", so it is also safe when sourced.
#
# Keep LF line endings (enforced by .gitattributes).
# =============================================================================

gol651_load_teaching_schema() {
    local socket="${SOCKET:-/var/run/mysqld/mysqld.sock}"
    local dir="/docker-entrypoint-initdb.d/teaching"
    local db file
    for db in gol651 gol651_exercises; do
        for file in "$dir"/01_schema.sql "$dir"/02_data.sql "$dir"/03_views.sql; do
            echo "[gol651] loading $(basename "$file") into $db"
            MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --protocol=socket -uroot -hlocalhost \
                --socket="$socket" --default-character-set=utf8mb4 \
                --database="$db" < "$file" || return 1
        done
    done
    echo "[gol651] teaching schema loaded into gol651 and gol651_exercises"
}

gol651_load_teaching_schema
