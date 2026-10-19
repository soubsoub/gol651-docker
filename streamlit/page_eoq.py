"""Application - Economic order quantity (EOQ, Wilson model)."""

import math

import pandas as pd
import plotly.express as px
import streamlit as st
from common import bilingual, show_source

st.title("Quantité économique de commande / Economic order quantity")
bilingual(
    "La quantité $Q^*$ minimise la somme du coût de commande et du coût de stockage.",
    "Q* minimizes the sum of ordering and holding costs.",
)
st.latex(r"Q^{*} = \sqrt{\frac{2\,D\,S}{H}} \qquad "
         r"C(Q) = \frac{D}{Q}\,S + \frac{Q}{2}\,H")

col1, col2, col3 = st.columns(3)
demand = col1.number_input("Demande annuelle D (unités) / annual demand",
                           min_value=1, value=4000, step=100)
order_cost = col2.number_input("Coût par commande S ($) / cost per order",
                               min_value=0.01, value=45.0)
holding = col3.number_input("Coût de stockage H ($/unité/an) / holding cost",
                            min_value=0.01, value=2.2)

q_star = math.sqrt(2 * demand * order_cost / holding)
total = demand / q_star * order_cost + q_star / 2 * holding

m1, m2, m3 = st.columns(3)
m1.metric("Q*", f"{q_star:,.0f} unités / units")
m2.metric("Commandes par an / orders per year", f"{demand / q_star:.1f}")
m3.metric("Coût annuel minimal / minimum yearly cost", f"{total:,.2f} $")

quantities = [q_star * k / 20 for k in range(4, 61)]
curve = pd.DataFrame({
    "Q": quantities,
    "commande / ordering": [demand / q * order_cost for q in quantities],
    "stockage / holding": [q / 2 * holding for q in quantities],
})
curve["total"] = curve["commande / ordering"] + curve["stockage / holding"]
fig = px.line(curve, x="Q", y=["commande / ordering", "stockage / holding", "total"],
              labels={"value": "Coût ($/an) / Cost ($/year)", "variable": ""})
fig.add_vline(x=q_star, line_dash="dash")
st.plotly_chart(fig, width="stretch")

show_source(__file__)
