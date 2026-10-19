"""Tutorial 2 - Layout: sidebar, columns, tabs, expander, container."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from common import bilingual, show_source

st.title("2. Mise en page / Layout")
bilingual(
    "Les éléments s'affichent dans l'ordre du code. Les conteneurs (`sidebar`, "
    "`columns`, `tabs`, `expander`) contrôlent **où** ils apparaissent.",
    "Elements appear in code order. Containers control WHERE they appear.",
)

# --- Sidebar: controls that apply to the whole page --------------------------
with st.sidebar:
    st.header("Paramètres / Settings")
    weeks = st.slider("Semaines / Weeks", 4, 52, 12)
    seed = st.number_input("Germe aléatoire / Random seed", value=651, step=1)

rng = np.random.default_rng(int(seed))
demand = pd.DataFrame({
    "week": np.arange(1, weeks + 1),
    "Laval": rng.normal(120, 15, weeks).round(),
    "Longueuil": rng.normal(95, 20, weeks).round(),
})

# --- Columns -----------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Laval", f"{demand['Laval'].mean():.0f} / sem.")
c2.metric("Longueuil", f"{demand['Longueuil'].mean():.0f} / sem.")
c3.metric("Total", f"{demand[['Laval', 'Longueuil']].sum().sum():,.0f}")

# --- Tabs ----------------------------------------------------------------------
tab_chart, tab_table = st.tabs(["Graphique / Chart", "Tableau / Table"])
with tab_chart:
    long = demand.melt(id_vars="week", var_name="warehouse", value_name="units")
    st.plotly_chart(px.line(long, x="week", y="units", color="warehouse",
                            labels={"week": "Semaine / Week", "units": "Unités / Units"}),
                    width="stretch")
with tab_table:
    st.dataframe(demand, hide_index=True, width="stretch")

# --- Expander: optional details ---------------------------------------------------
with st.expander("Comment les données sont générées / How the data is generated"):
    st.markdown("Loi normale : $\\mathcal{N}(120, 15^2)$ pour Laval et "
                "$\\mathcal{N}(95, 20^2)$ pour Longueuil, arrondie à l'unité.")

# --- Container: reserve a place now, fill it later ----------------------------
summary = st.container(border=True)
summary.write(f"Semaine la plus chargée à Laval / busiest Laval week: "
              f"**{int(demand.loc[demand['Laval'].idxmax(), 'week'])}**")

show_source(__file__)
