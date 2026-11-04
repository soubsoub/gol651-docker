"""
Modèle 2 — Production LP  (page Streamlit — COMPLÈTE)
======================================================
Couche PRÉSENTATION (tier 1 sur 3).

Cette page est entièrement fournie à titre de modèle de référence.
Elle montre comment les trois tiers communiquent :

  Présentation  ←→  Logique métier (lab/model_production.py)
                              ↕
                       Mémoire (MySQL via lab/common_db.py)
"""

import streamlit as st
import pandas as pd
import sys
import os

# Allow importing from the lab/ package when running from streamlit/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lab import model_production
from lab.common_db import fetch_my_results

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Lab 02 — Production LP", page_icon="🏭")
st.title("🏭 Modèle 2 — Production LP")
st.caption("Maximiser la marge de contribution hebdomadaire")

# ---------------------------------------------------------------------------
# Zone 0 — Identification de l'étudiant
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Identification")
    student_id = st.text_input(
        "Votre nom ou numéro d'étudiant",
        placeholder="ex. : A1234567",
        help="Utilisé pour enregistrer vos résultats dans la base de données.",
    )

if not student_id.strip():
    st.warning("⚠️  Entrez votre identifiant dans la barre latérale pour commencer.")
    st.stop()

# ---------------------------------------------------------------------------
# Zone 1 — Données du problème (TIER 3 : lecture MySQL)
# ---------------------------------------------------------------------------
st.subheader("① Données du problème")
st.info(
    "Les données sont chargées depuis la base de données `gol651` "
    "(tables `production_resources` et `production_products`).",
    icon="🗄️",
)

resources, products = model_production.load_data()

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Ressources disponibles**")
    st.dataframe(
        resources[["name", "unit", "capacity"]].rename(
            columns={"name": "Ressource", "unit": "Unité", "capacity": "Capacité / sem."}
        ),
        use_container_width=True, hide_index=True,
    )
with col2:
    st.markdown("**Produits et marges**")
    st.dataframe(
        products[["name", "margin", "max_demand"]].rename(
            columns={"name": "Produit", "margin": "Marge ($/unité)", "max_demand": "Demande max"}
        ),
        use_container_width=True, hide_index=True,
    )

# ---------------------------------------------------------------------------
# Zone 2 — Paramètres ajustables (TIER 1 : widgets Streamlit)
# ---------------------------------------------------------------------------
st.subheader("② Paramètres")
st.markdown(
    "Modifiez les capacités des ressources pour observer l'impact sur la solution optimale."
)

with st.form("params_production"):
    cols = st.columns(len(resources))
    new_capacities = {}
    for i, (_, res) in enumerate(resources.iterrows()):
        with cols[i]:
            new_capacities[res["resource_id"]] = st.number_input(
                f"{res['name']} ({res['unit']})",
                min_value=0.0,
                value=float(res["capacity"]),
                step=10.0,
            )
    time_limit = st.slider("Limite de temps du solveur (s)", 10, 300, 60)
    submitted = st.form_submit_button("🔍 Résoudre", use_container_width=True, type="primary")

# ---------------------------------------------------------------------------
# Zone 3 — Résolution (TIER 2 : logique métier)
# ---------------------------------------------------------------------------
if submitted:
    # Apply modified capacities
    resources_mod = resources.copy()
    for rid, cap in new_capacities.items():
        resources_mod.loc[resources_mod["resource_id"] == rid, "capacity"] = cap

    with st.spinner("Résolution en cours…"):
        result = model_production.build_and_solve(resources_mod, products, time_limit)

    # --- Affichage du résultat ---
    st.subheader("③ Résultats")
    if result["status"] == "Optimal":
        st.success(f"✅ Solution optimale — Marge totale : **{result['objective_value']:,.2f} $**")
        var_df = pd.DataFrame(
            [{"Produit": k, "Production (unités)": v} for k, v in result["variables"].items()]
        )
        st.dataframe(var_df, use_container_width=True, hide_index=True)
    else:
        st.error(f"❌ Statut : {result['status']}")

    # --- Écriture dans la base (TIER 3 : écriture MySQL) ---
    rid = model_production.persist_result(student_id.strip(), result)
    st.caption(f"Résultat sauvegardé dans `gol651_exercises.lab_results` (id = {rid}).")

# ---------------------------------------------------------------------------
# Zone 4 — Historique personnel (TIER 3 : lecture MySQL)
# ---------------------------------------------------------------------------
st.divider()
with st.expander("📋 Mes résultats précédents"):
    hist = fetch_my_results(student_id.strip(), "lab_02_production")
    if hist.empty:
        st.info("Aucun résultat enregistré pour cet identifiant.")
    else:
        st.dataframe(
            hist[["solved_at", "status", "objective_value", "solver_params"]],
            use_container_width=True, hide_index=True,
        )
