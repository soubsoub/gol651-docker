"""GOL651 - MySQL with mysql-connector-python (Oracle's official driver).

Run inside Docker:
    docker compose exec jupyter python examples/databases/mysql_connector.py

Shows: dictionary cursor, parameterized query, a CONNECTION POOL, and how a
constraint violation is caught and rolled back.
"""

from __future__ import annotations

import mysql.connector
from mysql.connector import errorcode
from mysql.connector.pooling import MySQLConnectionPool

from db_config import EXERCISES_DB, REFERENCE_DB, mysql_settings


def simple_query() -> None:
    con = mysql.connector.connect(**mysql_settings(REFERENCE_DB))
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(
            "SELECT o.order_id, o.order_date, o.status, t.order_total "
            "FROM orders AS o JOIN v_order_totals AS t ON t.order_id = o.order_id "
            "WHERE o.customer_id = %s ORDER BY o.order_date",
            (4,),
        )
        print("Orders of customer 4:")
        for row in cur.fetchall():
            print(f"  #{row['order_id']:<3} {row['order_date']}  {row['status']:<10}"
                  f" {row['order_total']:>10} $")
        cur.close()
    finally:
        con.close()


def pooled_queries() -> None:
    # A pool keeps a few connections open and lends them out: much cheaper than
    # opening a new connection for every request (web apps, APIs).
    pool = MySQLConnectionPool(pool_name="gol651_pool", pool_size=3,
                               **mysql_settings(REFERENCE_DB))
    for city in ("Montréal", "Laval", "Gatineau"):
        con = pool.get_connection()          # borrow
        try:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM customers WHERE city = %s", (city,))
            print(f"  pool -> customers in {city}: {cur.fetchone()[0]}")
            cur.close()
        finally:
            con.close()                      # returns the connection to the pool


def constraint_violation() -> None:
    con = mysql.connector.connect(**mysql_settings(EXERCISES_DB))
    try:
        cur = con.cursor()
        try:
            # This e-mail already exists: UNIQUE constraint uq_customers_email.
            cur.execute("INSERT INTO customers (first_name, last_name, email, city) "
                        "VALUES (%s, %s, %s, %s)",
                        ("Copie", "Tremblay", "sophie.tremblay@example.com", "Montréal"))
            con.commit()
        except mysql.connector.IntegrityError as exc:
            con.rollback()
            assert exc.errno == errorcode.ER_DUP_ENTRY
            print(f"\nRejected as expected (errno {exc.errno}): {exc.msg}")
        cur.close()
    finally:
        con.close()


if __name__ == "__main__":
    simple_query()
    print("\nConnection pool:")
    pooled_queries()
    constraint_violation()
