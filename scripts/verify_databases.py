#!/usr/bin/env python3
"""GOL651 - Database verification (SQLite, DuckDB, MySQL, SQLAlchemy).

Run INSIDE the Docker Python container:

    docker compose exec jupyter python scripts/verify_databases.py

Every check performs a real operation (create, insert, query, transaction),
not just an import. Temporary files created under data/sqlite/ and
data/duckdb/ are deleted afterwards; existing student files are never touched.

MySQL connection parameters are read from the container environment:
    DB_HOST (default: mysql)   DB_PORT (default: 3306)
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE   (from .env)

Inside Docker the MySQL host is the service name "mysql".
From the host computer (MySQL Workbench) it is localhost / 127.0.0.1.

Exit code: 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
SQLITE_DIR = ROOT / "data" / "sqlite"
DUCKDB_DIR = ROOT / "data" / "duckdb"
VERIFY_STEM = "_gol651_verify"  # prefix of temporary verification files

# Release written by mysql/init/01_init.sql into gol651.environment_info.
# Init scripts run only on an EMPTY volume, so an older value means the MySQL
# volume was created by an older release of this repository.
EXPECTED_STAGE = "stage-2"

IN_CONTAINER_HINT = (
    "Run this script inside the container: "
    "docker compose exec jupyter python scripts/verify_databases.py"
)


# --------------------------------------------------------------------------
# Minimal check runner (identical structure in every verify_*.py script)
# --------------------------------------------------------------------------
def _run(name: str, func: Callable[[], str], hint: str) -> tuple[str, bool, str, str]:
    try:
        detail = func()
        return (name, True, detail or "", "")
    except Exception as exc:  # noqa: BLE001 - report every failure clearly
        return (name, False, f"{type(exc).__name__}: {exc}", hint)


def _print(results: list[tuple[str, bool, str, str]]) -> None:
    for name, ok, detail, hint in results:
        status = "[PASS]" if ok else "[FAIL]"
        line = f"{status} {name}"
        if ok and detail:
            line += f" ({detail})"
        print(line)
        if not ok:
            print(f"       Reason: {detail}")
            print(f"       Hint:   {hint}")


def _remove(path: Path) -> None:
    for p in (path, path.with_name(path.name + ".wal")):
        if p.exists():
            p.unlink()


# --------------------------------------------------------------------------
# MySQL connection settings
# --------------------------------------------------------------------------
def _mysql_settings() -> dict[str, object]:
    password = os.environ.get("MYSQL_PASSWORD")
    if not password:
        raise RuntimeError("MYSQL_PASSWORD is not set in this environment")
    return {
        "host": os.environ.get("DB_HOST", "mysql"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "gol651"),
        "password": password,
        "database": os.environ.get("MYSQL_DATABASE", "gol651"),
    }


def _mysql_engine():
    from sqlalchemy import URL, create_engine

    s = _mysql_settings()
    url = URL.create(
        "mysql+pymysql",
        username=s["user"], password=s["password"],
        host=s["host"], port=s["port"], database=s["database"],
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})


# --------------------------------------------------------------------------
# SQLite
# --------------------------------------------------------------------------
def _check_sqlite_file() -> str:
    """Create a file DB in data/sqlite, test commit + rollback, then delete it."""
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SQLITE_DIR / f"{VERIFY_STEM}.sqlite"
    _remove(path)
    try:
        con = sqlite3.connect(path)
        try:
            con.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            with con:  # committed transaction
                con.execute("INSERT INTO item (name) VALUES (?)", ("committed",))
            try:
                with con:  # rolled-back transaction
                    con.execute("INSERT INTO item (name) VALUES (?)", ("rolled back",))
                    raise RuntimeError("force rollback")
            except RuntimeError:
                pass
            rows = con.execute("SELECT name FROM item").fetchall()
        finally:
            con.close()
        if rows != [("committed",)]:
            raise AssertionError(f"unexpected rows after commit/rollback: {rows}")
        return f"SQLite {sqlite3.sqlite_version}, file in data/sqlite, commit+rollback OK"
    finally:
        _remove(path)


def _check_sqlite_cli() -> str:
    out = subprocess.run(["sqlite3", ":memory:", "SELECT 6*7;"],
                         capture_output=True, text=True, timeout=30, check=True)
    if out.stdout.strip() != "42":
        raise AssertionError(f"unexpected CLI output: {out.stdout!r}")
    return "sqlite3 CLI"


def _check_sqlite_sqlalchemy_pandas() -> str:
    import pandas as pd
    from sqlalchemy import create_engine, text

    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SQLITE_DIR / f"{VERIFY_STEM}_sa.sqlite"
    _remove(path)
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        df = pd.DataFrame({"product": ["A", "B", "C"], "qty": [3, 5, 7]})
        df.to_sql("stock", engine, index=False)
        with engine.connect() as conn:
            total = conn.execute(text("SELECT SUM(qty) FROM stock")).scalar_one()
        back = pd.read_sql("SELECT * FROM stock ORDER BY product", engine)
        if total != 15 or len(back) != 3:
            raise AssertionError(f"sum={total}, rows={len(back)}")
        return "sqlite:/// engine, to_sql + read_sql OK"
    finally:
        engine.dispose()
        _remove(path)


# --------------------------------------------------------------------------
# DuckDB
# --------------------------------------------------------------------------
def _check_duckdb_memory() -> str:
    import duckdb
    import pandas as pd

    con = duckdb.connect()  # in-memory
    try:
        total = con.execute("SELECT SUM(i) FROM range(1, 101) t(i)").fetchone()[0]
        sales = pd.DataFrame({"region": ["E", "W", "E"], "amount": [10, 20, 30]})
        con.register("sales", sales)
        east = con.execute(
            "SELECT SUM(amount) FROM sales WHERE region = 'E'").fetchone()[0]
    finally:
        con.close()
    if total != 5050 or east != 40:
        raise AssertionError(f"range sum={total}, DataFrame query={east}")
    return f"DuckDB {duckdb.__version__}, in-memory + Pandas DataFrame query OK"


def _check_duckdb_file() -> str:
    import duckdb

    DUCKDB_DIR.mkdir(parents=True, exist_ok=True)
    path = DUCKDB_DIR / f"{VERIFY_STEM}.duckdb"
    _remove(path)
    try:
        con = duckdb.connect(str(path))
        con.execute("CREATE TABLE t AS SELECT 42 AS answer")
        con.close()
        con = duckdb.connect(str(path))  # reopen: proves persistence on disk
        answer = con.execute("SELECT answer FROM t").fetchone()[0]
        con.close()
        if answer != 42:
            raise AssertionError(f"read back {answer}")
        return "file in data/duckdb written, reopened and read"
    finally:
        _remove(path)


def _check_duckdb_sqlalchemy() -> str:
    from sqlalchemy import create_engine, text

    engine = create_engine("duckdb:///:memory:")
    try:
        with engine.connect() as conn:
            value = conn.execute(text("SELECT 21 * 2")).scalar_one()
    finally:
        engine.dispose()
    if value != 42:
        raise AssertionError(f"got {value}")
    return "duckdb:/// engine via duckdb-engine"


# --------------------------------------------------------------------------
# MySQL
# --------------------------------------------------------------------------
def _check_mysql_pymysql() -> str:
    import pymysql

    s = _mysql_settings()
    con = pymysql.connect(**s, connect_timeout=5, charset="utf8mb4")
    try:
        with con.cursor() as cur:
            cur.execute("SELECT 1, VERSION(), DATABASE()")
            one, ver, db = cur.fetchone()
    finally:
        con.close()
    if one != 1:
        raise AssertionError(f"SELECT 1 returned {one}")
    return f"MySQL {ver}, database={db}, host={s['host']}"


def _check_mysql_init() -> str:
    """Confirm mysql/init/*.sql ran: marker row + gol651_exercises schema."""
    import pymysql

    s = _mysql_settings()
    con = pymysql.connect(**s, connect_timeout=5, charset="utf8mb4")
    try:
        with con.cursor() as cur:
            cur.execute("SELECT stage FROM gol651.environment_info WHERE id = 1")
            row = cur.fetchone()
            cur.execute("SHOW DATABASES LIKE 'gol651_exercises'")
            exercises = cur.fetchone()
            cur.execute("SELECT @@character_set_server")
            charset = cur.fetchone()[0]
    finally:
        con.close()
    if row is None:
        raise AssertionError("marker row gol651.environment_info(id=1) not found")
    if row[0] != EXPECTED_STAGE:
        raise AssertionError(
            f"the MySQL volume was initialized by release '{row[0]}', but this "
            f"repository is '{EXPECTED_STAGE}': its new init scripts never ran")
    if exercises is None:
        raise AssertionError("schema gol651_exercises does not exist")
    if charset != "utf8mb4":
        raise AssertionError(f"character_set_server={charset}")
    return f"init scripts ran (stage={row[0]}), gol651_exercises present, utf8mb4"


# Rows loaded by mysql/init/teaching/02_data.sql. Checked exactly in the
# REFERENCE database only: students may modify gol651_exercises freely.
TEACHING_ROWS = {
    "customers": 12, "suppliers": 6, "products": 20, "product_suppliers": 24,
    "inventory": 20, "orders": 25, "order_items": 59,
}
TEACHING_VIEWS = ("v_order_totals", "v_customer_sales", "v_low_stock")


def _check_teaching_schema() -> str:
    """Teaching tables and views exist in both databases; reference counts exact."""
    import pymysql

    s = _mysql_settings()
    con = pymysql.connect(**s, connect_timeout=5, charset="utf8mb4")
    try:
        with con.cursor() as cur:
            for db in ("gol651", "gol651_exercises"):
                cur.execute(
                    "SELECT table_name AS name FROM information_schema.tables "
                    "WHERE table_schema = %s", (db,))
                present = {r[0] for r in cur.fetchall()}
                missing = (set(TEACHING_ROWS) | set(TEACHING_VIEWS)) - present
                if missing:
                    raise AssertionError(f"{db}: missing {sorted(missing)}")
            counts = {}
            for table in TEACHING_ROWS:
                cur.execute(f"SELECT COUNT(*) FROM gol651.`{table}`")
                counts[table] = cur.fetchone()[0]
            for view in TEACHING_VIEWS:
                cur.execute(f"SELECT COUNT(*) FROM gol651.`{view}`")
                cur.fetchone()
    finally:
        con.close()
    wrong = {t: (counts[t], n) for t, n in TEACHING_ROWS.items() if counts[t] != n}
    if wrong:
        raise AssertionError(f"gol651 row counts differ (found, expected): {wrong}")
    return f"7 tables + 3 views in gol651 and gol651_exercises; {sum(counts.values())} reference rows"


def _check_constraints_enforced() -> str:
    """FK, CHECK and UNIQUE reject bad data (in gol651_exercises, rolled back)."""
    import pymysql

    s = _mysql_settings()
    s["database"] = "gol651_exercises"
    con = pymysql.connect(**s, connect_timeout=5, charset="utf8mb4")
    with con.cursor() as cur:  # prerequisite: report the root cause, not error 1146
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = "
                    "'gol651_exercises' AND table_name IN ('orders', 'inventory', 'customers')")
        if cur.fetchone()[0] < 3:
            con.close()
            raise RuntimeError("not tested: teaching tables are missing in gol651_exercises "
                               "(see 'MySQL teaching schema' above)")
    # kind: (statement, MySQL error code expected when the constraint works)
    attempts = {
        "foreign key": ("INSERT INTO orders (customer_id, order_date) "
                        "VALUES (999999, '2026-01-01')", 1452),
        "check": ("UPDATE inventory SET quantity_on_hand = -1 WHERE product_id = 1", 3819),
        "unique": ("INSERT INTO customers (first_name, last_name, email, city) "
                   "SELECT 'Copy', 'Copy', email, city FROM customers "
                   "ORDER BY customer_id LIMIT 1", 1062),
    }
    problems = []
    try:
        for kind, (sql, expected_code) in attempts.items():
            try:
                with con.cursor() as cur:
                    cur.execute(sql)
                problems.append(f"{kind}: accepted")
            except pymysql.MySQLError as err:
                if err.args[0] != expected_code:
                    problems.append(f"{kind}: error {err.args[0]} instead of {expected_code}")
            finally:
                con.rollback()
    finally:
        con.close()
    if problems:
        raise AssertionError("; ".join(problems))
    return "foreign key, CHECK and UNIQUE violations rejected"


def _check_mysql_connector() -> str:
    import mysql.connector

    s = _mysql_settings()
    con = mysql.connector.connect(**s, connection_timeout=5)
    try:
        cur = con.cursor()
        cur.execute("SELECT %s + %s", (40, 2))  # parameterized query
        value = cur.fetchone()[0]
        cur.close()
    finally:
        con.close()
    if int(value) != 42:
        raise AssertionError(f"got {value}")
    return f"mysql-connector-python {mysql.connector.__version__}"


def _check_mysql_sqlalchemy_pandas() -> str:
    import pandas as pd
    from sqlalchemy import text

    engine = _mysql_engine()
    try:
        # Transaction test on a TEMPORARY table: nothing persists afterwards.
        with engine.connect() as conn:
            conn.execute(text("CREATE TEMPORARY TABLE _verify_tx (id INT PRIMARY KEY)"))
            conn.commit()  # end SQLAlchemy 2.x "autobegin" before an explicit begin()
            trans = conn.begin()
            conn.execute(text("INSERT INTO _verify_tx VALUES (:v)"), {"v": 1})
            trans.rollback()
            remaining = conn.execute(text("SELECT COUNT(*) FROM _verify_tx")).scalar_one()
            conn.execute(text("DROP TEMPORARY TABLE _verify_tx"))
        if remaining != 0:
            raise AssertionError(f"rollback failed, {remaining} row(s) remain")
        df = pd.read_sql(text("SELECT 1 AS ok, DATABASE() AS db"), engine)
        if int(df.loc[0, "ok"]) != 1:
            raise AssertionError(f"read_sql returned {df.to_dict()}")
    finally:
        engine.dispose()
    return "mysql+pymysql engine, rollback + read_sql OK"


def run_checks() -> list[tuple[str, bool, str, str]]:
    mysql_hint = (
        "Check that MySQL is running (docker compose ps) and that you run this inside "
        "the container. 'Access denied' usually means MYSQL_PASSWORD in .env was changed "
        "after the first start: MySQL keeps the password of its first start, so put the "
        "previous one back. " + IN_CONTAINER_HINT
    )
    write_hint = (
        "The data/ folder must be writable by the container user. On Linux, set "
        "LOCAL_UID/LOCAL_GID in .env to the output of 'id -u' / 'id -g', enable the "
        "COMPOSE_FILE line of .env (local build) and run: docker compose build."
    )
    return [
        _run("SQLite (file, transactions)", _check_sqlite_file, write_hint),
        _run("SQLite CLI", _check_sqlite_cli,
             "sqlite3 must be installed by the Dockerfile; " + IN_CONTAINER_HINT),
        _run("SQLite via SQLAlchemy + Pandas", _check_sqlite_sqlalchemy_pandas, write_hint),
        _run("DuckDB (in-memory, Pandas)", _check_duckdb_memory,
             "duckdb is missing; download the image again: docker compose pull"),
        _run("DuckDB (persistent file)", _check_duckdb_file, write_hint),
        _run("DuckDB via SQLAlchemy (duckdb-engine)", _check_duckdb_sqlalchemy,
             "duckdb-engine is missing; download the image again: docker compose pull"),
        _run("MySQL (PyMySQL)", _check_mysql_pymysql, mysql_hint),
        _run("MySQL initialization", _check_mysql_init,
             "Init scripts in mysql/init/ run only on an EMPTY volume. After updating "
             "the repository, a one-time full reset is needed: scripts/reset.sh or "
             "scripts/reset.ps1 (DELETES MySQL data; back it up first if you need it)."),
        _run("MySQL teaching schema", _check_teaching_schema,
             "The teaching tables are created only when the MySQL volume is EMPTY. "
             "A volume created by an older version needs a deliberate reset "
             "(scripts/reset.sh or reset.ps1 - DELETES MySQL data). "
             "If only gol651_exercises is damaged, use scripts/restore-exercises."),
        _run("MySQL constraints enforced", _check_constraints_enforced,
             "Fix the failures above first. If only gol651_exercises is damaged, run "
             "scripts/restore-exercises (sh or ps1), then retry."),
        _run("MySQL (mysql-connector-python)", _check_mysql_connector, mysql_hint),
        _run("MySQL via SQLAlchemy + Pandas", _check_mysql_sqlalchemy_pandas, mysql_hint),
    ]


def main() -> int:
    print("GOL651 Database Verification")
    print("=" * 40)
    results = run_checks()
    _print(results)
    failed = sum(1 for r in results if not r[1])
    print("=" * 40)
    print(f"Summary: {len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
