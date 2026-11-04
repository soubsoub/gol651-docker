"""
Modèle 5 — Flot en réseau  (page Streamlit — build_model + présentation à écrire)
==================================================================================
Couche PRÉSENTATION (tier 1 sur 3).

Statut des tiers
----------------
  Tier 3 — Mémoire   : COMPLET (lab/common_db.py)
  Tier 2 — Backend   : load_data() et persist_result() complets.
                       build_and_solve() contient 3 TODO à compléter
                       dans lab/model_network.py.
  Tier 1 — Présentation : à écrire ici.

Votre travail dans ce laboratoire est donc en deux parties :

PARTIE A — Compléter lab/model_network.py
  Ouvrir le fichier et remplir les TODO 1, 2 et 3 dans build_and_solve().
  Tester la fonction directement en Python avant de passer à Streamlit.

PARTIE B — Écrire cette page Streamlit
  Même structure que les pages précédentes :
    Zone 0 — Identification (sidebar)
    Zone 1 — Données : nœuds et arcs du réseau
    Zone 2 — Paramètres (time_limit)
    Zone 3 — Résolution et affichage
    Zone 4 — Historique

Fonctions disponibles
---------------------
    from lab import model_network
    nodes, arcs = model_network.load_data()
    result = model_network.build_and_solve(nodes, arcs, time_limit)
    rid    = model_network.persist_result(student_id, result)

    result["variables"] est un dict { "Nœud A → Nœud B" : flux }

Conseil d'affichage
-------------------
Pour les résultats, n'afficher que les arcs avec un flux > 0.
Un st.dataframe trié par flux décroissant est plus lisible.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lab import model_network
from lab.common_db import fetch_my_results

st.set_page_config(page_title="Lab 05 — Flot en réseau", page_icon="🔀")
st.title("🔀 Modèle 5 — Flot en réseau")
st.caption("Router le flot d'un réseau de distribution au coût minimum")

# ===========================================================================
# PARTIE A — Compléter lab/model_network.py avant d'écrire cette page.
# PARTIE B — TODO : écrire la page de présentation ici.
# ===========================================================================
st.info(
    "**Étape 1** : Ouvrir `lab/model_network.py` et compléter les TODO 1, 2 et 3 "
    "dans `build_and_solve()`.\n\n"
    "**Étape 2** : Écrire la page de présentation Streamlit dans ce fichier.",
    icon="📝",
)
