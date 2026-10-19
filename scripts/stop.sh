#!/bin/sh
# =============================================================================
# GOL651 - Stop the environment. NO DATA IS DELETED.
# =============================================================================
# Usage:  sh scripts/stop.sh
# Stops and removes the containers of all services (including the optional
# profiles). The MySQL database (Docker volume) and your files are kept.
# Equivalent manual command:  docker compose --profile marimo --profile web down
# =============================================================================
set -eu
cd "$(dirname "$0")/.."

echo "+ docker compose --profile marimo --profile web down"
docker compose --profile marimo --profile web down
echo ""
echo "Stopped. MySQL data, notebooks and data/ files are kept."
echo "Start again with:  sh scripts/start.sh"
