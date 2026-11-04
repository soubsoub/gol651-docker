"""
Modèle 6 — Planification multi-période  (défi page blanche)
============================================================
Couche PRÉSENTATION (tier 1 sur 3).

Statut des tiers
----------------
  Tier 3 — Mémoire   : COMPLET (lab/common_db.py + save_result)
  Tier 2 — Backend   : TOUS les TODO dans lab/model_planning.py
  Tier 1 — Présentation : à écrire ici

Ce laboratoire est le défi final.  Vous partez d'une page blanche et
implémentez les trois tiers du début à la fin, comme vous le ferez dans
votre projet de session.

Rappel de la progression
------------------------
  Modèle 1 — Réappro       : code fourni, lire et comprendre
  Modèle 2 — Production LP : code fourni, lire et comprendre
  Modèle 3 — Transport     : 3 TODO dans la présentation
  Modèle 4 — Affectation   : présentation entière à écrire
  Modèle 5 — Flot          : build_model + présentation à écrire
  Modèle 6 — Planification : les trois tiers à écrire  ← vous êtes ici

Étapes suggérées
----------------
1. Lire la formulation mathématique dans lab/model_planning.py.
2. Implémenter load_data() dans lab/model_planning.py.
3. Vérifier les données avec un script Python simple avant Streamlit.
4. Implémenter build_and_solve() ; tester avec des valeurs connues.
5. Implémenter persist_result().
6. Écrire cette page Streamlit.
7. Vérifier vos résultats dans la base :
       SELECT * FROM gol651_exercises.lab_results
       WHERE model_name = 'lab_06_planification'
       ORDER BY solved_at DESC;

Tables disponibles dans gol651
-------------------------------
  planning_products  — product_id, name, prod_cost, holding_cost, initial_stock
  planning_periods   — period_id, label, capacity
  planning_demand    — product_id, period_id, demand

Résultats attendus (à titre indicatif)
---------------------------------------
Avec les données fournies, la solution optimale doit être faisable.
Le coût total (production + stock) doit être strictement positif.
Vérifier que les bilans de stock sont respectés pour chaque produit
et chaque période.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lab import model_planning
from lab.common_db import fetch_my_results

st.set_page_config(page_title="Lab 06 — Planification", page_icon="📅")
st.title("📅 Modèle 6 — Planification multi-période")
st.caption("Planifier la production sur 6 périodes pour 3 familles de produits")

# ===========================================================================
# TODO : implémenter les trois tiers, puis écrire cette page.
# ===========================================================================
st.info(
    "Ce laboratoire est le défi final. Lisez le docstring de ce fichier "
    "et de `lab/model_planning.py` pour connaître les étapes à suivre.",
    icon="🎯",
)
