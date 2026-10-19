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
    local db file user password
    for db in gol651 gol651_exercises; do
        # gol651 (reference) is created by root: students cannot drop its views.
        # gol651_exercises (practice) is created by the course user, so its
        # views belong to that user and students can drop or replace them
        # (MySQL refuses to let a normal user drop a view owned by root:
        # ERROR 1227, SYSTEM_USER privilege).
        if [ "$db" = "gol651" ]; then
            user="root";        password="$MYSQL_ROOT_PASSWORD"
        else
            user="$MYSQL_USER"; password="$MYSQL_PASSWORD"
        fi
        for file in "$dir"/01_schema.sql "$dir"/02_data.sql "$dir"/03_views.sql; do
            echo "[gol651] loading $(basename "$file") into $db as $user"
            MYSQL_PWD="$password" mysql --protocol=socket -u"$user" -hlocalhost \
                --socket="$socket" --default-character-set=utf8mb4 \
                --database="$db" < "$file" || return 1
        done
    done
    echo "[gol651] teaching schema loaded into gol651 and gol651_exercises"
}

gol651_load_teaching_schema
