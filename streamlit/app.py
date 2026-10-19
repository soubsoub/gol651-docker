"""GOL651 - Streamlit example application.

Started by the "web" profile:   docker compose --profile web up -d
Open:                           http://localhost:8501

Edit this file in VS Code and save: the page reloads with your changes.
Shows: user input widgets, a calculation, Pandas, Plotly charts, and an
optional MySQL query (the page still works if MySQL is unavailable).
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import URL, create_engine, text

DATA = Path(__file__).resolve().parents[1] / "data" / "datasets"

st.set_page_config(page_title="GOL651 - Streamlit", layout="wide")
st.title("GOL651 – Streamlit")
st.caption("Exemple d'application web interactive / Interactive web application example")


@st.cache_resource
def mysql_engine():
    """One engine (connection pool) shared by all page refreshes."""
    url = URL.create(
        "mysql+pymysql",
        username=os.environ.get("MYSQL_USER", "gol651"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        host=os.environ.get("DB_HOST", "mysql"),
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ.get("MYSQL_DATABASE", "gol651"),
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


@st.cache_data(ttl=60)
def customer_sales() -> pd.DataFrame:
    return pd.read_sql(text("SELECT * FROM v_customer_sales ORDER BY total_sales DESC"),
                       mysql_engine())


eoq_tab, sales_tab, shipments_tab = st.tabs(
    ["Quantité économique / EOQ", "Ventes / Sales (MySQL)", "Expéditions / Shipments (CSV)"]
)

# --- Tab 1: user input + calculation -------------------------------------------
with eoq_tab:
    st.latex(r"Q^{*} = \sqrt{\frac{2\,D\,S}{H}}")
    col1, col2, col3 = st.columns(3)
    demand = col1.number_input("Demande annuelle D (unités)", min_value=1, value=4000, step=100)
    order_cost = col2.number_input("Coût par commande S ($)", min_value=0.01, value=45.0)
    holding = col3.number_input("Coût de stockage H ($/unité/an)", min_value=0.01, value=2.2)

    q_star = math.sqrt(2 * demand * order_cost / holding)
    total = demand / q_star * order_cost + q_star / 2 * holding
    m1, m2, m3 = st.columns(3)
    m1.metric("Q*", f"{q_star:,.0f} units")
    m2.metric("Commandes / orders per year", f"{demand / q_star:.1f}")
    m3.metric("Coût annuel / yearly cost", f"{total:,.2f} $")

    quantities = [q_star * k / 20 for k in range(4, 61)]
    curve = pd.DataFrame({
        "Q": quantities,
        "ordering": [demand / q * order_cost for q in quantities],
        "holding": [q / 2 * holding for q in quantities],
    })
    curve["total"] = curve["ordering"] + curve["holding"]
    st.plotly_chart(px.line(curve, x="Q", y=["ordering", "holding", "total"],
                            labels={"value": "Cost ($/year)", "variable": ""}),
                    width="stretch")

# --- Tab 2: optional database query ------------------------------------------------
with sales_tab:
    try:
        sales = customer_sales()
    except Exception as exc:  # noqa: BLE001 - show a friendly message instead of a crash
        st.warning(f"MySQL n'est pas accessible / MySQL is not reachable: {exc}")
    else:
        cities = ["(toutes / all)"] + sorted(sales["city"].unique())
        city = st.selectbox("Ville / City", cities)
        shown = sales if city == cities[0] else sales[sales["city"] == city]
        st.dataframe(shown, hide_index=True, width="stretch")
        st.plotly_chart(px.bar(shown, x="customer_name", y="total_sales",
                               labels={"customer_name": "", "total_sales": "Sales ($)"}),
                        width="stretch")

# --- Tab 3: CSV file ------------------------------------------------------------
with shipments_tab:
    shipments = pd.read_csv(DATA / "shipments.csv", parse_dates=["ship_date"])
    carriers = st.multiselect("Transporteurs / carriers",
                              sorted(shipments["carrier"].unique()),
                              default=sorted(shipments["carrier"].unique()))
    selected = shipments[shipments["carrier"].isin(carriers)]
    st.write(f"{len(selected)} expéditions / shipments")
    st.plotly_chart(px.scatter(selected, x="weight_kg", y="cost_cad", color="carrier",
                               labels={"weight_kg": "Weight (kg)", "cost_cad": "Cost ($)"}),
                    width="stretch")
