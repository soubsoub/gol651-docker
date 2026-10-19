"""GOL651 Streamlit - shared helpers used by every page.

Contents
  bilingual(), show_source()      presentation helpers (French first, English in italics)
  engine()                        one SQLAlchemy engine (connection pool) per database
  load_* functions                cached read queries
  place_order(), set_order_status(), cancel_order()
                                  write operations on gol651_exercises, each in ONE transaction

Business logic lives here, not in the pages, so it can be tested without a browser
(see scripts/verify_examples.py).
"""

import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import URL, Engine, create_engine, text

REFERENCE_DB = "gol651"            # read-only use in these pages
EXERCISES_DB = "gol651_exercises"  # the order-management page writes here
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "datasets"


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------
def bilingual(fr: str, en: str) -> None:
    """French paragraph, then the English version in italics."""
    st.markdown(f"{fr}\n\n*{en}*")


def show_source(file: str) -> None:
    """Expander at the bottom of a page showing the page's own source code."""
    with st.expander("Code de cette page / Page source"):
        st.code(Path(file).read_text(encoding="utf-8"), language="python")


def database_warning(exc: Exception) -> None:
    st.warning(
        "MySQL n'est pas accessible. Vérifiez `docker compose ps` et "
        "`scripts/verify_databases.py`.\n\n"
        f"*MySQL is not reachable.* ({type(exc).__name__}: {exc})"
    )


# --------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------
@st.cache_resource
def engine(database: str = REFERENCE_DB) -> Engine:
    """One engine (connection pool) per database, shared by all sessions.

    st.cache_resource keeps the SAME object for every user and rerun: right
    for connections. Inside Docker the MySQL host is the service name "mysql".
    """
    url = URL.create(
        "mysql+pymysql",
        username=os.environ.get("MYSQL_USER", "gol651"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        host=os.environ.get("DB_HOST", "mysql"),
        port=int(os.environ.get("DB_PORT", "3306")),
        database=database,
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


SALES_LINES_SQL = """
    SELECT o.order_id, o.order_date, o.status,
           c.customer_id, CONCAT(c.first_name, ' ', c.last_name) AS customer, c.city,
           p.sku, p.name AS product, p.category,
           oi.quantity, oi.unit_price, oi.discount_pct,
           ROUND(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100), 2) AS amount
    FROM orders AS o
    JOIN customers   AS c  ON c.customer_id = o.customer_id
    JOIN order_items AS oi ON oi.order_id   = o.order_id
    JOIN products    AS p  ON p.product_id  = oi.product_id
    WHERE o.order_date BETWEEN :start AND :end
"""


@st.cache_data(ttl=60)
def load_sales_lines(start: date, end: date) -> pd.DataFrame:
    """One row per order line in the date range (bound parameters, never f-strings).

    st.cache_data stores the RESULT for 60 s per (start, end) combination.
    """
    df = pd.read_sql(text(SALES_LINES_SQL), engine(REFERENCE_DB),
                     params={"start": start, "end": end})
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


@st.cache_data(ttl=60)
def load_order_date_range() -> tuple[date, date]:
    with engine(REFERENCE_DB).connect() as conn:
        first, last = conn.execute(
            text("SELECT MIN(order_date), MAX(order_date) FROM orders")).one()
    return first, last


def load_catalog(database: str = EXERCISES_DB) -> pd.DataFrame:
    """Active products with their current stock (not cached: stock changes)."""
    return pd.read_sql(text("""
        SELECT p.product_id, p.sku, p.name, p.category, p.unit_price,
               i.quantity_on_hand, i.reorder_level
        FROM products AS p JOIN inventory AS i ON i.product_id = p.product_id
        WHERE p.is_active = TRUE
        ORDER BY p.category, p.name
    """), engine(database))


def load_customers(database: str = EXERCISES_DB) -> pd.DataFrame:
    return pd.read_sql(text("""
        SELECT customer_id, CONCAT(first_name, ' ', last_name) AS name, city, customer_type
        FROM customers ORDER BY last_name, first_name
    """), engine(database))


def load_recent_orders(limit: int = 15, database: str = EXERCISES_DB) -> pd.DataFrame:
    return pd.read_sql(text("""
        SELECT o.order_id, o.order_date, o.status, o.shipped_date,
               CONCAT(c.first_name, ' ', c.last_name) AS customer,
               t.line_count, t.order_total
        FROM orders AS o
        JOIN customers AS c ON c.customer_id = o.customer_id
        JOIN v_order_totals AS t ON t.order_id = o.order_id
        ORDER BY o.order_id DESC
        LIMIT :limit
    """), engine(database), params={"limit": limit})


# --------------------------------------------------------------------------
# Write operations (gol651_exercises only), each one ATOMIC
# --------------------------------------------------------------------------
class OrderError(Exception):
    """Business-rule violation with a bilingual message for the user."""


def place_order(customer_id: int, product_id: int, quantity: int,
                database: str = EXERCISES_DB) -> int:
    """Create an order with one line and decrease the stock, in ONE transaction.

    engine.begin() commits at the end of the block, or rolls back EVERYTHING if
    any statement fails. SELECT ... FOR UPDATE locks the stock row so two users
    cannot sell the same last units at the same time.
    """
    if quantity <= 0:
        raise OrderError("La quantité doit être positive. / Quantity must be positive.")
    with engine(database).begin() as conn:
        row = conn.execute(text("""
            SELECT p.unit_price, i.quantity_on_hand, c.customer_type
            FROM products AS p
            JOIN inventory AS i ON i.product_id = p.product_id
            JOIN customers AS c ON c.customer_id = :cid
            WHERE p.product_id = :pid AND p.is_active = TRUE
            FOR UPDATE
        """), {"pid": product_id, "cid": customer_id}).one_or_none()
        if row is None:
            raise OrderError("Produit ou client introuvable. / Unknown product or customer.")
        unit_price, stock, customer_type = row
        if quantity > stock:
            raise OrderError(f"Stock insuffisant : {stock} disponible(s). "
                             f"/ Not enough stock: {stock} available.")
        discount = 5 if customer_type == "business" and unit_price * quantity >= 500 else 0
        order_id = conn.execute(
            text("INSERT INTO orders (customer_id, order_date, status) "
                 "VALUES (:cid, CURRENT_DATE, 'pending')"),
            {"cid": customer_id}).lastrowid
        conn.execute(
            text("INSERT INTO order_items (order_id, product_id, quantity, unit_price, "
                 "discount_pct) VALUES (:oid, :pid, :qty, :price, :disc)"),
            {"oid": order_id, "pid": product_id, "qty": quantity,
             "price": unit_price, "disc": discount})
        conn.execute(
            text("UPDATE inventory SET quantity_on_hand = quantity_on_hand - :qty "
                 "WHERE product_id = :pid"),
            {"qty": quantity, "pid": product_id})
    return int(order_id)


ALLOWED_TRANSITIONS = {"pending": {"shipped"}, "shipped": {"delivered"}}


def set_order_status(order_id: int, new_status: str, database: str = EXERCISES_DB) -> None:
    """pending -> shipped (sets shipped_date) -> delivered."""
    with engine(database).begin() as conn:
        current = conn.execute(
            text("SELECT status FROM orders WHERE order_id = :oid FOR UPDATE"),
            {"oid": order_id}).scalar_one_or_none()
        if current is None:
            raise OrderError(f"Commande {order_id} introuvable. / Order {order_id} not found.")
        if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
            raise OrderError(f"Transition impossible : {current} -> {new_status}. "
                             f"/ Invalid transition: {current} -> {new_status}.")
        conn.execute(
            text("UPDATE orders SET status = :st, shipped_date = "
                 "CASE WHEN :st = 'shipped' THEN CURRENT_DATE ELSE shipped_date END "
                 "WHERE order_id = :oid"),
            {"st": new_status, "oid": order_id})


def cancel_order(order_id: int, database: str = EXERCISES_DB) -> None:
    """Cancel a PENDING order and put its quantities back in stock (one transaction)."""
    with engine(database).begin() as conn:
        current = conn.execute(
            text("SELECT status FROM orders WHERE order_id = :oid FOR UPDATE"),
            {"oid": order_id}).scalar_one_or_none()
        if current != "pending":
            raise OrderError("Seule une commande « pending » peut être annulée. "
                             "/ Only a pending order can be cancelled.")
        conn.execute(text("""
            UPDATE inventory AS i
            JOIN order_items AS oi ON oi.product_id = i.product_id
            SET i.quantity_on_hand = i.quantity_on_hand + oi.quantity
            WHERE oi.order_id = :oid
        """), {"oid": order_id})
        conn.execute(text("UPDATE orders SET status = 'cancelled' WHERE order_id = :oid"),
                     {"oid": order_id})
