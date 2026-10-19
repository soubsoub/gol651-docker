# syntax=docker/dockerfile:1
# =============================================================================
# GOL651 - Shared Python image
# =============================================================================
# One image for jupyter, marimo, streamlit, fastapi and flask; each Compose
# service only changes the command. Built natively for linux/amd64 and
# linux/arm64 (no platform override): every dependency below has native
# packages or wheels on both architectures.
#
# Students DOWNLOAD this image ready-made (ghcr.io, built and tested by the
# course CI). It is built locally only with docker-compose.build.yml.
# Build context: repository root. Only the files allowed by .dockerignore
# are sent to the builder.
# =============================================================================

# Python 3.12 is the semester baseline. Debian 13 "trixie" is pinned explicitly
# so that the OS packages (CBC, GLPK, sqlite3) do not change underneath us.
FROM python:3.12-slim-trixie

# Links the published package to its source repository on GitHub.
LABEL org.opencontainers.image.source="https://github.com/soubsoub/gol651-docker" \
      org.opencontainers.image.description="GOL651 course environment: Python 3.12, Jupyter, Pyomo, Streamlit, FastAPI, Flask"

# Same uv version that generated requirements-lock.txt.
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

# UID/GID of the non-root user. The published image uses 1000:1000. A Linux
# user whose "id -u" is not 1000 builds locally with LOCAL_UID/LOCAL_GID
# (see docker-compose.build.yml). Docker Desktop (Windows/macOS) needs nothing.
ARG LOCAL_UID=1000
ARG LOCAL_GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# -----------------------------------------------------------------------------
# System packages
#   coinor-cbc  -> "cbc" executable    (Pyomo solver "cbc")
#   glpk-utils  -> "glpsol" executable (Pyomo solver "glpk")
#   sqlite3     -> SQLite command-line client
#   build-essential (gcc, g++, make) -> lets students pip-install packages
#   that must be compiled; the locked dependencies themselves use wheels.
# -----------------------------------------------------------------------------
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        git \
        unzip \
        nano \
        build-essential \
        sqlite3 \
        glpk-utils \
        coinor-cbc \
 && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Python dependencies: installed EXACTLY from the uv lock file.
# Copied before anything else so this layer stays cached until the lock changes.
# -----------------------------------------------------------------------------
COPY requirements/requirements-lock.txt /tmp/requirements-lock.txt
RUN uv pip install --system --no-cache -r /tmp/requirements-lock.txt \
 && rm /tmp/requirements-lock.txt

# -----------------------------------------------------------------------------
# Non-root user "student". If the requested GID already exists in the image
# (e.g. GID 20 used by macOS users), that existing group is reused.
# -----------------------------------------------------------------------------
RUN if ! getent group "${LOCAL_GID}" > /dev/null; then \
        groupadd --gid "${LOCAL_GID}" student; \
    fi \
 && useradd --uid "${LOCAL_UID}" --gid "${LOCAL_GID}" \
        --create-home --shell /bin/bash student \
 && mkdir -p /workspace \
 && chown "${LOCAL_UID}:${LOCAL_GID}" /workspace

COPY --chmod=0755 docker/python/entrypoint.sh /usr/local/bin/gol651-entrypoint

USER ${LOCAL_UID}:${LOCAL_GID}
WORKDIR /workspace

ENTRYPOINT ["gol651-entrypoint"]
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser"]
