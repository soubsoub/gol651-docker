"""GOL651 - DuckDB: analytical SQL on files and DataFrames (no server).

Run inside Docker:
    docker compose exec jupyter python examples/databases/duckdb_examples.py

Shows: in-memory database, querying a Pandas DataFrame directly, reading a
CSV file, writing and reading Parquet, a persistent database file, and
SQLAlchemy access through duckdb-engine.

Files used / created:
    data/datasets/shipments.csv          (provided)
    data/duckdb/shipments.parquet        (created)
    data/duckdb/gol651_demo.duckdb       (created)
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from sqlalchemy import create_engine, text

DATA = Path(__file__).resolve().parents[2] / "data"
CSV_FILE = DATA / "datasets" / "shipments.csv"
PARQUET_FILE = DATA / "duckdb" / "shipments.parquet"
DB_FILE = DATA / "duckdb" / "gol651_demo.duckdb"


def in_memory_and_dataframes() -> None:
    con = duckdb.connect()  # in-memory: disappears when closed
    try:
        rates = pd.DataFrame({
            "carrier": ["Purolator", "Postes Canada", "Transport Pelletier", "Day & Ross"],
            "on_time_rate": [0.94, 0.88, 0.97, 0.91],
        })
        # A local DataFrame variable can be queried by its name.
        best = con.sql("SELECT carrier FROM rates ORDER BY on_time_rate DESC LIMIT 1").fetchone()
        print("Best on-time carrier:", best[0])

        # Query a CSV file directly, with parameters ($1, $2 ...).
        result = con.execute(
            "SELECT carrier, COUNT(*) AS shipments, ROUND(AVG(cost_cad), 2) AS avg_cost "
            "FROM read_csv_auto($1) WHERE weight_kg > $2 "
            "GROUP BY carrier ORDER BY avg_cost",
            [str(CSV_FILE), 100],
        ).df()
        print("\nShipments over 100 kg, by carrier (from CSV):")
        print(result.to_string(index=False))

        # CSV -> Parquet (columnar, compressed, typed), then query the Parquet.
        PARQUET_FILE.parent.mkdir(parents=True, exist_ok=True)
        con.execute(f"COPY (SELECT * FROM read_csv_auto('{CSV_FILE.as_posix()}')) "
                    f"TO '{PARQUET_FILE.as_posix()}' (FORMAT parquet)")
        monthly = con.execute(
            "SELECT strftime(ship_date, '%Y-%m') AS month, ROUND(SUM(cost_cad), 2) AS cost "
            "FROM read_parquet($1) GROUP BY month ORDER BY month",
            [str(PARQUET_FILE)],
        ).df()
        print("\nMonthly transport cost (from Parquet):")
        print(monthly.head(4).to_string(index=False))
    finally:
        con.close()


def persistent_database() -> None:
    con = duckdb.connect(str(DB_FILE))   # file database: survives restarts
    try:
        con.execute("CREATE OR REPLACE TABLE shipments AS "
                    "SELECT * FROM read_parquet(?)", [str(PARQUET_FILE)])
        n = con.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
        print(f"\nPersistent table 'shipments' in {DB_FILE.name}: {n} rows")
    finally:
        con.close()

    # Same file through SQLAlchemy + Pandas (duckdb-engine).
    engine = create_engine(f"duckdb:///{DB_FILE.as_posix()}")
    try:
        df = pd.read_sql(
            text("SELECT destination_city, COUNT(*) AS n FROM shipments "
                 "GROUP BY destination_city ORDER BY n DESC LIMIT 3"),
            engine,
        )
        print("Top destinations (SQLAlchemy):", df.to_dict("records"))
    finally:
        engine.dispose()


if __name__ == "__main__":
    in_memory_and_dataframes()
    persistent_database()
