"""Tutorial 1 - Widgets and display.

Each widget RETURNS its current value. When the user changes it, Streamlit
reruns this script from the top, and the new value flows through the code.
"""

from datetime import date

import pandas as pd
import streamlit as st
from common import bilingual, show_source

st.title("1. Widgets et affichage / Widgets and display")
bilingual(
    "Un widget retourne sa valeur actuelle. Modifiez une valeur : tout le script est "
    "réexécuté et les résultats ci-dessous se mettent à jour.",
    "A widget returns its current value. Change a value: the whole script reruns and "
    "the results below update.",
)

st.subheader("Saisie / Input")
col1, col2 = st.columns(2)
with col1:
    product = st.selectbox("Produit / Product",
                           ["Palette de bois", "Casque de sécurité", "Ruban adhésif"])
    quantity = st.number_input("Quantité / Quantity", min_value=1, max_value=1000, value=20)
    unit_price = st.slider("Prix unitaire / Unit price ($)", 1.0, 100.0, 18.5, step=0.5)
with col2:
    delivery = st.date_input("Livraison / Delivery", value=date(2026, 11, 2))
    express = st.checkbox("Livraison express (+ 25 $) / Express delivery")
    note = st.text_input("Note", placeholder="ex. quai de chargement 3 / loading dock 3")

st.subheader("Affichage / Display")
subtotal = quantity * unit_price
total = subtotal + (25 if express else 0)
m1, m2, m3 = st.columns(3)
m1.metric("Sous-total / Subtotal", f"{subtotal:,.2f} $")
m2.metric("Express", "oui / yes" if express else "non / no")
m3.metric("Total", f"{total:,.2f} $")

st.write("`st.write` affiche presque tout / *displays almost anything*:",
         {"product": product, "quantity": quantity, "delivery": str(delivery),
          "note": note or None})

st.dataframe(pd.DataFrame({
    "quantité / quantity": [quantity * k for k in (1, 2, 5)],
    "total ($)": [quantity * k * unit_price for k in (1, 2, 5)],
}), hide_index=True)

if st.button("Confirmer / Confirm", type="primary"):
    st.success(f"Commande simulée : {quantity} × {product} pour le {delivery}. "
               f"/ Simulated order.")

show_source(__file__)
