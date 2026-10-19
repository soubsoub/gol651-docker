"""Application - Sales dashboard on the MySQL reference database (gol651).

Pattern: ONE parameterized SQL query (date range, filtered in MySQL), then
interactive filters in Pandas, KPIs, charts and a CSV export.
"""

import plotly.express as px
import streamlit as st
from common import bilingual, database_warning, load_order_date_range, load_sales_lines, show_source

st.title("Tableau de bord des ventes / Sales dashboard")
bilingual("Données : base de référence `gol651` (lecture seule).",
          "Data: reference database gol651 (read only).")

try:
    first_day, last_day = load_order_date_range()
except Exception as exc:  # noqa: BLE001 - show a friendly message instead of a crash
    database_warning(exc)
    st.stop()

# --- Filters (sidebar) ----------------------------------------------------------
with st.sidebar:
    st.header("Filtres / Filters")
    period = st.date_input("Période / Period", value=(first_day, last_day),
                           min_value=first_day, max_value=last_day)
    include_cancelled = st.checkbox("Inclure les commandes annulées / Include cancelled",
                                    value=False)

if not isinstance(period, tuple) or len(period) != 2:
    st.info("Choisissez une date de début et une date de fin. / Pick a start and end date.")
    st.stop()

lines = load_sales_lines(period[0], period[1])          # filtered by MySQL
if not include_cancelled:
    lines = lines[lines["status"] != "cancelled"]

with st.sidebar:
    categories = st.multiselect("Catégories / Categories", sorted(lines["category"].unique()),
                                default=sorted(lines["category"].unique()))
    cities = st.multiselect("Villes / Cities", sorted(lines["city"].unique()),
                            default=sorted(lines["city"].unique()))
lines = lines[lines["category"].isin(categories) & lines["city"].isin(cities)]  # Pandas

if lines.empty:
    st.warning("Aucune vente pour ces filtres. / No sales for these filters.")
    st.stop()

# --- KPIs ----------------------------------------------------------------------
orders = lines.groupby("order_id")["amount"].sum()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Chiffre d'affaires / Revenue", f"{lines['amount'].sum():,.0f} $")
k2.metric("Commandes / Orders", f"{orders.size}")
k3.metric("Panier moyen / Average order", f"{orders.mean():,.0f} $")
k4.metric("Clients / Customers", f"{lines['customer_id'].nunique()}")

# --- Charts ----------------------------------------------------------------------
left, right = st.columns(2)
monthly = (lines.set_index("order_date")["amount"].resample("MS").sum().reset_index())
left.plotly_chart(px.bar(monthly, x="order_date", y="amount",
                         title="Ventes mensuelles / Monthly sales",
                         labels={"order_date": "", "amount": "$"}), width="stretch")
by_category = lines.groupby("category", as_index=False)["amount"].sum()
right.plotly_chart(px.pie(by_category, names="category", values="amount",
                          title="Par catégorie / By category"), width="stretch")

top_customers = (lines.groupby("customer", as_index=False)["amount"].sum()
                 .sort_values("amount", ascending=True).tail(8))
st.plotly_chart(px.bar(top_customers, x="amount", y="customer", orientation="h",
                       title="Meilleurs clients / Top customers",
                       labels={"amount": "$", "customer": ""}), width="stretch")

# --- Detail and export ------------------------------------------------------------
with st.expander(f"Détail des {len(lines)} lignes / Line detail"):
    st.dataframe(lines.drop(columns=["customer_id"]), hide_index=True, width="stretch")
st.download_button("Télécharger en CSV / Download CSV",
                   lines.to_csv(index=False).encode("utf-8"),
                   file_name="gol651_sales.csv", mime="text/csv")

show_source(__file__)
