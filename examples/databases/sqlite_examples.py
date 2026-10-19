"""GOL651 - SQLite: a database in a single file (no server).

Run inside Docker:
    docker compose exec jupyter python examples/databases/sqlite_examples.py

Creates (or recreates) data/sqlite/gol651_demo.sqlite, a file you can also
open on your computer (e.g. with "DB Browser for SQLite"). Shows: sqlite3,
foreign keys, transactions (COMMIT / ROLLBACK), SQLAlchemy and Pandas.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, event, text

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sqlite" / "gol651_demo.sqlite"

SCHEMA = """
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS warehouses;
CREATE TABLE warehouses (
    warehouse_id INTEGER PRIMARY KEY,
    city         TEXT NOT NULL UNIQUE,
    capacity     INTEGER NOT NULL CHECK (capacity > 0)
);
CREATE TABLE stock (
    warehouse_id INTEGER NOT NULL REFERENCES warehouses (warehouse_id),
    sku          TEXT    NOT NULL,
    quantity     INTEGER NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (warehouse_id, sku)
);
"""


def sqlite3_examples() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        # SQLite does NOT enforce foreign keys unless asked, per connection.
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA)

        # executemany + parameter placeholders (?), inside a transaction:
        # "with con:" commits at the end, or rolls back if an error occurs.
        with con:
            con.executemany("INSERT INTO warehouses VALUES (?, ?, ?)",
                            [(1, "Laval", 5000), (2, "Longueuil", 3500), (3, "Québec", 4000)])
            con.executemany("INSERT INTO stock VALUES (?, ?, ?)",
                            [(1, "PAL-001", 340), (1, "GAN-080", 500),
                             (2, "PAL-001", 120), (3, "CAS-081", 90)])

        # ROLLBACK: the second insert violates the foreign key, so the first
        # insert of the same transaction is cancelled too.
        try:
            with con:
                con.execute("INSERT INTO stock VALUES (2, 'GAN-080', 50)")
                con.execute("INSERT INTO stock VALUES (99, 'GAN-080', 50)")  # no warehouse 99
        except sqlite3.IntegrityError as err:
            print(f"Rolled back: {err}")

        rows = con.execute(
            "SELECT w.city, SUM(s.quantity) FROM stock AS s "
            "JOIN warehouses AS w USING (warehouse_id) GROUP BY w.city ORDER BY w.city"
        ).fetchall()
        print("Units per warehouse:", rows)
    finally:
        con.close()


def sqlalchemy_pandas_examples() -> None:
    engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}")

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_con, _record):  # same PRAGMA for every connection
        dbapi_con.execute("PRAGMA foreign_keys = ON")

    try:
        with engine.begin() as conn:  # transaction committed at the end
            conn.execute(text("UPDATE stock SET quantity = quantity + :q "
                              "WHERE warehouse_id = :w AND sku = :sku"),
                         {"q": 10, "w": 3, "sku": "CAS-081"})

        df = pd.read_sql("SELECT * FROM stock ORDER BY warehouse_id, sku", engine)
        print("\nstock table as a DataFrame:")
        print(df.to_string(index=False))

        # DataFrame -> new SQLite table
        summary = df.groupby("sku", as_index=False)["quantity"].sum()
        summary.to_sql("stock_by_sku", engine, if_exists="replace", index=False)
        print("\nstock_by_sku:", pd.read_sql("SELECT * FROM stock_by_sku", engine)
              .to_dict("records"))
    finally:
        engine.dispose()
    print(f"\nDatabase file: {DB_PATH}")


if __name__ == "__main__":
    sqlite3_examples()
    sqlalchemy_pandas_examples()
