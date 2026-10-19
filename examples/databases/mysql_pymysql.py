"""GOL651 - MySQL with PyMySQL (raw DB-API connector).

Run inside Docker:
    docker compose exec jupyter python examples/databases/mysql_pymysql.py

Shows: connection, parameterized queries, JOIN, a view, and transactions
(COMMIT and ROLLBACK). Writes happen only in gol651_exercises and are undone,
so the script can be run any number of times.
"""

from __future__ import annotations

from datetime import date

import pymysql
from pymysql.cursors import DictCursor

from db_config import EXERCISES_DB, REFERENCE_DB, mysql_settings


def connect(database: str) -> pymysql.connections.Connection:
    # autocommit=False (default): changes are kept only after COMMIT.
    return pymysql.connect(**mysql_settings(database), charset="utf8mb4",
                           cursorclass=DictCursor)


def read_examples() -> None:
    con = connect(REFERENCE_DB)
    try:
        with con.cursor() as cur:
            # 1. Parameterized query: NEVER build SQL with f-strings and user
            #    input; pass values separately (%s placeholders) to prevent
            #    SQL injection.
            cur.execute(
                "SELECT sku, name, unit_price FROM products "
                "WHERE category = %s AND unit_price < %s ORDER BY unit_price",
                ("Sécurité", 100),
            )
            print("Safety products under 100 $:")
            for row in cur.fetchall():
                print(f"  {row['sku']:<8} {row['name']:<30} {row['unit_price']:>8} $")

            # 2. JOIN across the many-to-many table order_items.
            cur.execute(
                """
                SELECT p.category, SUM(oi.quantity) AS units
                FROM order_items AS oi
                JOIN products    AS p ON p.product_id = oi.product_id
                JOIN orders      AS o ON o.order_id   = oi.order_id
                WHERE o.status <> 'cancelled'
                GROUP BY p.category
                ORDER BY units DESC
                """
            )
            print("\nUnits sold per category:")
            for row in cur.fetchall():
                print(f"  {row['category']:<14} {row['units']:>6}")

            # 3. Query a view like a table.
            cur.execute("SELECT customer_name, total_sales FROM v_customer_sales "
                        "ORDER BY total_sales DESC LIMIT 3")
            print("\nTop 3 customers:", [(r["customer_name"], float(r["total_sales"]))
                                         for r in cur.fetchall()])
    finally:
        con.close()


def transaction_examples() -> None:
    con = connect(EXERCISES_DB)
    try:
        with con.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM orders")
            before = cur.fetchone()["n"]

            # --- ROLLBACK: an order and its lines are written, then cancelled.
            cur.execute("INSERT INTO orders (customer_id, order_date) VALUES (%s, %s)",
                        (1, date(2026, 10, 1)))
            new_id = cur.lastrowid
            cur.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
                        "VALUES (%s, %s, %s, %s)", (new_id, 13, 50, 6.50))
            con.rollback()
            cur.execute("SELECT COUNT(*) AS n FROM orders")
            print(f"\nROLLBACK: orders before={before}, after rollback={cur.fetchone()['n']}")

            # --- COMMIT: a customer is created, committed, then removed again.
            email = "demo.transaction@example.com"
            cur.execute("DELETE FROM customers WHERE email = %s", (email,))
            cur.execute(
                "INSERT INTO customers (first_name, last_name, email, city) "
                "VALUES (%s, %s, %s, %s)", ("Demo", "Transaction", email, "Montréal"))
            con.commit()
            cur.execute("SELECT customer_id FROM customers WHERE email = %s", (email,))
            print(f"COMMIT: customer created with id {cur.fetchone()['customer_id']}")
            cur.execute("DELETE FROM customers WHERE email = %s", (email,))
            con.commit()
            print("Clean-up committed: gol651_exercises is unchanged.")
    except pymysql.MySQLError:
        con.rollback()  # always undo a half-finished transaction on error
        raise
    finally:
        con.close()


if __name__ == "__main__":
    read_examples()
    transaction_examples()
