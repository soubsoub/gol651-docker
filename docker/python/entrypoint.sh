#!/bin/sh
# =============================================================================
# GOL651 - Entrypoint of the shared Python image
# =============================================================================
# 1. Makes sure the persistent data sub-folders exist in the bind mount.
# 2. Warns clearly when the mounted data/ folder is not writable
#    (typical Linux UID/GID mismatch), instead of failing later.
# 3. Hands over to the service command (jupyter, marimo, streamlit, ...).
# This file must keep LF line endings (enforced by .gitattributes).
# =============================================================================
set -eu

DATA_DIR=/workspace/data

if [ -d "$DATA_DIR" ]; then
    for sub in sqlite duckdb datasets; do
        if [ ! -d "$DATA_DIR/$sub" ]; then
            mkdir -p "$DATA_DIR/$sub" 2>/dev/null || true
        fi
    done
    if [ ! -w "$DATA_DIR" ]; then
        echo "[gol651] WARNING: $DATA_DIR is not writable by user $(id -un) ($(id -u):$(id -g))." >&2
        echo "[gol651] On Linux: set LOCAL_UID and LOCAL_GID in .env to the output of" >&2
        echo "[gol651] 'id -u' and 'id -g', uncomment the COMPOSE_FILE line in .env," >&2
        echo "[gol651] then run: docker compose build && docker compose up -d" >&2
    fi
fi

exec "$@"
