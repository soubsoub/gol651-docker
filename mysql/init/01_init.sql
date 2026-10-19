-- =============================================================================
-- GOL651 - MySQL initialization, step 1: databases and marker
-- =============================================================================
-- Executed automatically by the official MySQL image ONLY when the data volume
-- is empty (first start, or after a deliberate "docker compose down -v").
--
-- Before this script runs, the image has already created, from .env:
--   - database  MYSQL_DATABASE  (gol651)
--   - user      MYSQL_USER      (gol651) with ALL privileges on gol651.*
--
-- Course convention: MYSQL_DATABASE and MYSQL_USER must stay "gol651";
-- the GRANT below refers to that user name explicitly.
--
-- Files in this folder run in alphabetical order:
--   01_init.sql              this file (second database + marker table)
--   02_teaching_schema.sh    loads teaching/*.sql into gol651 AND gol651_exercises
-- =============================================================================

-- Second course schema, for exercises.
CREATE DATABASE IF NOT EXISTS gol651_exercises
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

GRANT ALL PRIVILEGES ON gol651_exercises.* TO 'gol651'@'%';

-- Marker table used by scripts/verify_databases.py to confirm that the
-- initialization scripts actually ran.
CREATE TABLE IF NOT EXISTS gol651.environment_info (
    id           TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    stage        VARCHAR(20)      NOT NULL,
    initialized  TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;

INSERT IGNORE INTO gol651.environment_info (id, stage) VALUES (1, 'stage-2');
