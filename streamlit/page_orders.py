"""Application - Order management (create, update, cancel) on gol651_exercises.

Every write is ONE transaction implemented in common.py (place_order,
set_order_status, cancel_order). The reference database gol651 is never
modified. To start again from the original data:
    scripts/restore-exercises.sh   (Windows: .\\scripts\\restore-exercises.ps1)
"""

import streamlit as st
from common import (EXERCISES_DB, OrderError, bilingual, cancel_order, database_warning,
                    load_catalog, load_customers, load_recent_orders, place_order,
                    set_order_status, show_source)

st.title("Gestion des commandes / Order management")
bilingual(
    f"Cette page **modifie** la base d'exercice `{EXERCISES_DB}` : création de commandes, "
    "changement de statut, annulation. Chaque opération est une **transaction** : tout "
    "est enregistré, ou rien.",
    f"This page MODIFIES the practice database {EXERCISES_DB}. Each operation is a "
    "transaction: everything is saved, or nothing.",
)

try:
    catalog = load_catalog()
    customers = load_customers()
except Exception as exc:  # noqa: BLE001
    database_warning(exc)
    st.stop()

# Messages survive the rerun that follows each action.
if "order_message" in st.session_state:
    kind, message = st.session_state.pop("order_message")
    (st.success if kind == "ok" else st.error)(message)

create_tab, manage_tab, stock_tab = st.tabs(
    ["Nouvelle commande / New order", "Suivi / Tracking", "Stock"])

# --- Create -----------------------------------------------------------------------
with create_tab:
    with st.form("new_order", clear_on_submit=True):
        customer_id = st.selectbox(
            "Client / Customer", customers["customer_id"],
            format_func=lambda cid: "{name} ({city})".format(
                **customers.set_index("customer_id").loc[cid]))
        product_id = st.selectbox(
            "Produit / Product", catalog["product_id"],
            format_func=lambda pid: "{sku} - {name} - {unit_price:.2f} $ "
                                    "(stock {quantity_on_hand})".format(
                **catalog.set_index("product_id").loc[pid]))
        quantity = st.number_input("Quantité / Quantity", min_value=1, value=1, step=1)
        if st.form_submit_button("Créer la commande / Create order", type="primary"):
            try:
                order_id = place_order(int(customer_id), int(product_id), int(quantity))
                st.session_state.order_message = (
                    "ok", f"Commande {order_id} créée, stock mis à jour. "
                          f"/ Order {order_id} created, stock updated.")
            except OrderError as err:
                st.session_state.order_message = ("error", str(err))
            except Exception as err:  # noqa: BLE001 - database error: show it
                st.session_state.order_message = ("error", f"Erreur MySQL / error: {err}")
            st.rerun()
    st.caption("Règle : 5 % de remise pour un client « business » si la ligne atteint "
               "500 $. / Rule: 5 % off for business customers on lines of 500 $ or more.")

# --- Update / cancel -------------------------------------------------------------------
with manage_tab:
    recent = load_recent_orders()
    st.dataframe(recent, hide_index=True, width="stretch")
    pending_or_shipped = recent[recent["status"].isin(["pending", "shipped"])]
    if pending_or_shipped.empty:
        st.info("Aucune commande à faire avancer. / No order to update.")
    else:
        order_id = st.selectbox("Commande / Order", pending_or_shipped["order_id"],
                                format_func=lambda oid: f"#{oid} - " + str(
                                    recent.set_index("order_id").loc[oid, "status"]))
        status = recent.set_index("order_id").loc[order_id, "status"]
        c1, c2 = st.columns(2)
        next_status = "shipped" if status == "pending" else "delivered"
        if c1.button(f"Passer à « {next_status} » / Mark as {next_status}"):
            try:
                set_order_status(int(order_id), next_status)
                st.session_state.order_message = ("ok", f"#{order_id} -> {next_status}")
            except OrderError as err:
                st.session_state.order_message = ("error", str(err))
            st.rerun()
        if status == "pending" and c2.button("Annuler et remettre en stock / Cancel"):
            try:
                cancel_order(int(order_id))
                st.session_state.order_message = (
                    "ok", f"#{order_id} annulée, stock rétabli. / cancelled, stock restored.")
            except OrderError as err:
                st.session_state.order_message = ("error", str(err))
            st.rerun()

# --- Stock ---------------------------------------------------------------------
with stock_tab:
    low = catalog["quantity_on_hand"] <= catalog["reorder_level"]
    st.metric("Produits sous le seuil / Products at or below reorder level", int(low.sum()))
    st.dataframe(catalog.style.apply(
        lambda row: ["background-color: rgba(255, 165, 0, 0.25)" if low[row.name] else ""
                     for _ in row], axis=1),
        hide_index=True, width="stretch")

st.caption("Repartir des données d'origine / Reset the data: `restore-exercises` script.")
show_source(__file__)
