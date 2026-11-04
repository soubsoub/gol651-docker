"""
Modèle 4 — Affectation  (page Streamlit — couche présentation à écrire)
========================================================================
Couche PRÉSENTATION (tier 1 sur 3).

Le backend (lab/model_assignment.py) et la couche mémoire (lab/common_db.py)
sont complets.  Vous devez écrire ENTIÈREMENT cette page de présentation.

Objectif
--------
Construire une interface Streamlit qui :

  1. Demande l'identifiant de l'étudiant (barre latérale).
  2. Charge et affiche les données depuis la base de données.
  3. Offre au minimum un paramètre ajustable (ex. : limite de temps).
  4. Lance la résolution et affiche le résultat (affectation optimale + coût).
  5. Sauvegarde le résultat dans la base de données.
  6. Affiche l'historique des tentatives.

Fonctions disponibles du backend
---------------------------------
    from lab import model_assignment
    agents, tasks, costs = model_assignment.load_data()
    result = model_assignment.build_and_solve(agents, tasks, costs, time_limit)
    rid    = model_assignment.persist_result(student_id, result)

    result est un dict avec les clés :
        status          : str  ('Optimal', 'Infeasible', …)
        objective_value : float | None
        variables       : dict  { "Agent → Tâche" : 1 }  (uniquement les paires retenues)
        solver_params   : dict

Rappels Streamlit utiles
------------------------
    st.columns(n)        — mise en page côte à côte
    st.dataframe(df)     — afficher un DataFrame
    st.form / st.form_submit_button — regrouper les widgets avant résolution
    st.success / st.error — messages de statut colorés
    st.expander          — section repliable pour l'historique

Structure suggérée
------------------
    Zone 0 — Identification (sidebar)
    Zone 1 — Données du problème (matrice des coûts)
    Zone 2 — Paramètres (time_limit au minimum)
    Zone 3 — Résolution et affichage des résultats
    Zone 4 — Historique personnel (fetch_my_results)
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lab import model_assignment
from lab.common_db import fetch_my_results

st.set_page_config(page_title="Lab 04 — Affectation", page_icon="👥")
st.title("👥 Modèle 4 — Affectation")
st.caption("Affecter des agents à des tâches au coût minimum")

# ===========================================================================
# TODO : écrire la page de présentation complète ici.
# ===========================================================================
st.info(
    "Cette page est à compléter. Utilisez les fonctions de `lab.model_assignment` "
    "et les rappels Streamlit dans le docstring ci-dessus comme point de départ.",
    icon="📝",
)
