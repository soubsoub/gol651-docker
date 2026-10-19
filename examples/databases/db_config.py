"""GOL651 - MySQL connection settings shared by the database examples.

Where does the code run?
------------------------
* INSIDE Docker (Jupyter, Marimo, Streamlit, FastAPI containers):
  docker-compose.yml sets DB_HOST=mysql, the SERVICE NAME of the database.
* On YOUR COMPUTER (outside Docker, e.g. MySQL Workbench or a local Python):
  the database is reached through the published port on 127.0.0.1
  (= localhost), and the password is read from the project's .env file.

Never write passwords in source code: they come from environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import URL

REPO_ROOT = Path(__file__).resolve().parents[2]

# The teaching schema exists in two databases:
REFERENCE_DB = "gol651"            # keep intact
EXERCISES_DB = "gol651_exercises"  # examples that WRITE use this one


def _load_dotenv_outside_docker() -> None:
    """Outside Docker, read MYSQL_PASSWORD etc. from the project's .env file."""
    if "MYSQL_PASSWORD" in os.environ:
        return  # inside Docker: already provided by docker-compose.yml
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file)


def mysql_settings(database: str | None = None) -> dict[str, object]:
    """Connection parameters usable by PyMySQL and mysql-connector-python."""
    _load_dotenv_outside_docker()
    password = os.environ.get("MYSQL_PASSWORD")
    if not password:
        raise RuntimeError(
            "MYSQL_PASSWORD is not defined. Run this code inside Docker "
            "(docker compose exec jupyter python ...) or create the .env file."
        )
    return {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),   # "mysql" inside Docker
        "port": int(os.environ.get("DB_PORT", os.environ.get("MYSQL_PORT", "3306"))),
        "user": os.environ.get("MYSQL_USER", "gol651"),
        "password": password,
        "database": database or os.environ.get("MYSQL_DATABASE", REFERENCE_DB),
    }


def sqlalchemy_url(database: str | None = None, driver: str = "pymysql") -> URL:
    """SQLAlchemy URL, e.g. mysql+pymysql://gol651:***@mysql:3306/gol651.

    URL.create() escapes special characters in the password safely.
    """
    s = mysql_settings(database)
    return URL.create(
        f"mysql+{driver}",
        username=str(s["user"]),
        password=str(s["password"]),
        host=str(s["host"]),
        port=int(s["port"]),
        database=str(s["database"]),
        query={"charset": "utf8mb4"},
    )


if __name__ == "__main__":
    shown = {k: ("***" if k == "password" else v) for k, v in mysql_settings().items()}
    print("MySQL settings:", shown)
    print("SQLAlchemy URL:", sqlalchemy_url().render_as_string(hide_password=True))
