"""GOL651 - MySQL with SQLAlchemy 2.x and Pandas.

Run inside Docker:
    docker compose exec jupyter python examples/databases/mysql_sqlalchemy.py

Shows: engine and connection pool settings, text() queries with bound
parameters, transactions (engine.begin(), explicit rollback, automatic
rollback on error), and pandas.read_sql. Writes use gol651_exercises and
restore the original values.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, exc, text

from db_config import EXERCISES_DB, REFERENCE_DB, sqlalchemy_url


def make_engine(database: str):
    return create_engine(
        sqlalchemy_url(database),
        pool_size=5,          # connections kept open
        max_overflow=5,       # extra connections allowed under load
        pool_pre_ping=True,   # test a connection before using it
        pool_recycle=1800,    # renew connections older than 30 min
    )


def queries(engine) -> None:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar_one()
        print(f"Connected to MySQL {version} as "
              f"{engine.url.render_as_string(hide_password=True)}")

        rows = conn.execute(
            text("SELECT sku, name, quantity_on_hand, reorder_level "
                 "FROM v_low_stock WHERE lead_time_days >= :min_days"),
            {"min_days": 10},
        ).mappings().all()
        print("Low stock with long lead time:", [r["sku"] for r in rows])

    # Pandas: SQL result -> DataFrame (parameters still passed separately).
    df = pd.read_sql(
        text("SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, "
             "       SUM(order_total) AS sales "
             "FROM v_order_totals WHERE status <> :excluded "
             "GROUP BY month ORDER BY month"),
        engine,
        params={"excluded": "cancelled"},
    )
    print("\nMonthly sales (pandas.read_sql):")
    print(df.to_string(index=False))
    print("Pool status:", engine.pool.status())


def transactions(engine) -> None:
    get_qty = text("SELECT quantity_on_hand FROM inventory WHERE product_id = :pid")
    move = text("UPDATE inventory SET quantity_on_hand = quantity_on_hand + :delta "
                "WHERE product_id = :pid")
    pid = 13

    with engine.connect() as conn:
        start = conn.execute(get_qty, {"pid": pid}).scalar_one()

    # 1. engine.begin(): COMMIT automatically at the end of the block.
    with engine.begin() as conn:
        conn.execute(move, {"delta": -10, "pid": pid})
    with engine.begin() as conn:                       # put the stock back
        conn.execute(move, {"delta": +10, "pid": pid})

    # 2. Explicit ROLLBACK.
    with engine.connect() as conn:
        conn.execute(move, {"delta": -10, "pid": pid})  # autobegins a transaction
        conn.rollback()

    # 3. Automatic ROLLBACK on error: the second statement violates the CHECK
    #    constraint ck_inventory_quantity, so the first one is undone as well.
    try:
        with engine.begin() as conn:
            conn.execute(move, {"delta": -10, "pid": pid})
            conn.execute(move, {"delta": -1_000_000, "pid": pid})
    except exc.DBAPIError as err:
        print(f"\nTransaction rolled back: {err.orig}")

    with engine.connect() as conn:
        end = conn.execute(get_qty, {"pid": pid}).scalar_one()
    assert start == end, (start, end)
    print(f"Stock of product {pid}: {start} before, {end} after (unchanged)")


if __name__ == "__main__":
    reference = make_engine(REFERENCE_DB)
    exercises = make_engine(EXERCISES_DB)
    try:
        queries(reference)
        transactions(exercises)
    finally:
        reference.dispose()
        exercises.dispose()
