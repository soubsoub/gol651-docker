"""
Modèle 3 — Transport  (page Streamlit — 3 TODOs)
=================================================
Couche PRÉSENTATION (tier 1 sur 3).

Le backend (lab/model_transport.py) et la couche mémoire (lab/common_db.py)
sont complets.  Vous devez compléter trois sections marquées TODO dans cette
page de présentation.

TODO 1 : Afficher les données dans deux tableaux côte à côte (nœuds et routes).
TODO 2 : Ajouter un widget permettant à l'étudiant de modifier la limite de
         temps du solveur.
TODO 3 : Afficher la matrice des flux optimaux sous forme de tableau.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lab import model_transport
from lab.common_db import fetch_my_results

st.set_page_config(page_title="Lab 03 — Transport", page_icon="🚚")
st.title("🚚 Modèle 3 — Transport")
st.caption("Minimiser le coût total de transport entre dépôts et centres de distribution")

# ---------------------------------------------------------------------------
# Zone 0 — Identification
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Identification")
    student_id = st.text_input("Votre nom ou numéro d'étudiant", placeholder="ex. : A1234567")

if not student_id.strip():
    st.warning("⚠️  Entrez votre identifiant dans la barre latérale pour commencer.")
    st.stop()

# ---------------------------------------------------------------------------
# Chargement des données (TIER 3 : lecture MySQL — NE PAS MODIFIER)
# ---------------------------------------------------------------------------
nodes, routes = model_transport.load_data()

# ---------------------------------------------------------------------------
# Zone 1 — Données du problème
# ---------------------------------------------------------------------------
st.subheader("① Données du problème")
st.info("Données chargées depuis `gol651` (tables `transport_nodes` et `transport_routes`).", icon="🗄️")

# ------------------------------------------------------------------
# TODO 1 — Afficher les données en deux colonnes
#
# Afficher dans la colonne gauche :
#   - Un sous-titre "Nœuds (offre / demande)"
#   - Un st.dataframe avec les colonnes : name, type, capacity
#     (renommer en "Nœud", "Type", "Offre / Demande")
#
# Afficher dans la colonne droite :
#   - Un sous-titre "Coûts de transport ($/unité)"
#   - Un st.dataframe avec les colonnes : from_node, to_node, cost_per_unit
#     (renommer en "De", "Vers", "Coût/unité")
#     Conseil : remplacer les IDs par les noms de nœuds avec un merge ou
#               un dictionnaire.
#
# Rappel Streamlit :
#   col1, col2 = st.columns(2)
#   with col1:
#       st.markdown("**...**")
#       st.dataframe(...)
# ------------------------------------------------------------------

# TODO 1 : votre code ici


# ---------------------------------------------------------------------------
# Zone 2 — Paramètres
# ---------------------------------------------------------------------------
st.subheader("② Paramètres")

with st.form("params_transport"):

    # ------------------------------------------------------------------
    # TODO 2 — Ajouter un slider pour la limite de temps du solveur
    #
    # Créer une variable `time_limit` à partir d'un st.slider :
    #   - Libellé : "Limite de temps du solveur (s)"
    #   - Minimum : 10, Maximum : 300, Valeur par défaut : 60
    # ------------------------------------------------------------------

    # TODO 2 : votre code ici
    time_limit = 60   # Remplacer cette ligne par votre st.slider

    submitted = st.form_submit_button("🔍 Résoudre", use_container_width=True, type="primary")

# ---------------------------------------------------------------------------
# Zone 3 — Résolution (TIER 2 : logique métier — NE PAS MODIFIER)
# ---------------------------------------------------------------------------
if submitted:
    with st.spinner("Résolution en cours…"):
        result = model_transport.build_and_solve(nodes, routes, time_limit)

    st.subheader("③ Résultats")

    if result["status"] == "Optimal":
        st.success(f"✅ Solution optimale — Coût total : **{result['objective_value']:,.2f} $**")

        # ----------------------------------------------------------------
        # TODO 3 — Afficher la matrice des flux optimaux
        #
        # `result["variables"]` est un dictionnaire de la forme :
        #   { "Dépôt Montréal → Centre Laval": 120.0, ... }
        #
        # Construire un pd.DataFrame avec deux colonnes :
        #   "Route" et "Flux (unités)"
        # N'afficher que les routes avec un flux > 0.
        # Utiliser st.dataframe(..., hide_index=True).
        # ----------------------------------------------------------------

        # TODO 3 : votre code ici

    else:
        st.error(f"❌ Statut : {result['status']}")

    # Écriture dans la base (NE PAS MODIFIER)
    rid = model_transport.persist_result(student_id.strip(), result)
    st.caption(f"Résultat sauvegardé dans `gol651_exercises.lab_results` (id = {rid}).")

# ---------------------------------------------------------------------------
# Zone 4 — Historique (NE PAS MODIFIER)
# ---------------------------------------------------------------------------
st.divider()
with st.expander("📋 Mes résultats précédents"):
    hist = fetch_my_results(student_id.strip(), "lab_03_transport")
    if hist.empty:
        st.info("Aucun résultat enregistré pour cet identifiant.")
    else:
        st.dataframe(
            hist[["solved_at", "status", "objective_value"]],
            use_container_width=True, hide_index=True,
        )
