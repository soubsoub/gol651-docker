#!/bin/sh
# =============================================================================
# GOL651 - Start the environment (thin wrapper around "docker compose")
# =============================================================================
# Usage (from the project folder):
#   sh scripts/start.sh              default services: mysql, phpmyadmin, jupyter
#   sh scripts/start.sh marimo       + Marimo
#   sh scripts/start.sh web          + Streamlit, FastAPI, Flask
#   sh scripts/start.sh marimo web   + both
#   sh scripts/start.sh all          everything
# Equivalent manual command:  docker compose [--profile ...] up -d --wait
# The image is built automatically on the first start. After updating the
# repository, rebuild it once with:  docker compose build
# =============================================================================
set -eu
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "ERROR: .env not found. Run:  cp .env.example .env   then edit the passwords."
    exit 1
fi

profiles=""
for arg in "$@"; do
    case "$arg" in
        marimo) profiles="$profiles --profile marimo" ;;
        web)    profiles="$profiles --profile web" ;;
        all)    profiles=" --profile marimo --profile web" ;;
        *)      echo "Unknown option: $arg  (use: marimo, web, all)"; exit 2 ;;
    esac
done

echo "+ docker compose$profiles up -d --wait"
# shellcheck disable=SC2086  # $profiles must split into separate arguments
docker compose $profiles up -d --wait

port() {  # port VARIABLE DEFAULT -> value from .env, or the default
    value=$(grep -E "^$1=" .env | tail -n 1 | cut -d= -f2 | tr -d '\r')
    echo "${value:-$2}"
}

echo ""
echo "GOL651 is ready:"
echo "  Jupyter Notebook  http://localhost:$(port JUPYTER_PORT 8888)"
echo "  JupyterLab        http://localhost:$(port JUPYTER_PORT 8888)/lab"
echo "  phpMyAdmin        http://localhost:$(port PHPMYADMIN_PORT 8080)"
echo "  MySQL (Workbench) 127.0.0.1:$(port MYSQL_PORT 3306)"
case "$profiles" in *marimo*)
echo "  Marimo            http://localhost:$(port MARIMO_PORT 2718)" ;; esac
case "$profiles" in *web*)
echo "  Streamlit         http://localhost:$(port STREAMLIT_PORT 8501)"
echo "  FastAPI           http://localhost:$(port FASTAPI_PORT 8000)/docs"
echo "  Flask             http://localhost:$(port FLASK_PORT 5000)" ;; esac
