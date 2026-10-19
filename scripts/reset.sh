#!/bin/sh
# =============================================================================
# GOL651 - FULL MySQL RESET (DELETES THE MYSQL DATABASE)
# =============================================================================
# Usage:  sh scripts/reset.sh
# Deletes the Docker volume that stores MySQL, then starts again: MySQL is
# re-initialized from mysql/init/ (fresh gol651 and gol651_exercises).
# NOT deleted: notebooks, code, and files in data/sqlite and data/duckdb.
# To repair only gol651_exercises, prefer: sh scripts/restore-exercises.sh
# Equivalent manual commands:
#   docker compose --profile marimo --profile web down -v
#   docker compose up -d --wait
# =============================================================================
set -eu
cd "$(dirname "$0")/.."

echo "WARNING: This deletes the Docker-managed MySQL database volume and its stored data."
echo "         Everything in gol651 and gol651_exercises will be lost."
echo "         Notebooks, code and data/sqlite, data/duckdb files are NOT affected."
printf "Type yes to continue: "
read -r answer || answer=""
if [ "$answer" != "yes" ]; then
    echo "Cancelled. Nothing was deleted."
    exit 1
fi

echo "+ docker compose --profile marimo --profile web down -v"
docker compose --profile marimo --profile web down -v
echo "+ docker compose up -d --wait"
docker compose up -d --wait
echo ""
echo "MySQL was re-initialized. Default services are running."
