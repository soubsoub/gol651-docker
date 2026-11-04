"""
lab/model_planning.py
=====================
Backend (logique métier) — Modèle 6 : Planification multi-période

Problem
-------
Plan production over T periods for P product families to minimize total
production cost plus inventory holding cost, subject to capacity and
inventory balance constraints.

Mathematical formulation
------------------------
Let  x_pt = units produced of product p in period t
     I_pt = inventory of product p at end of period t
     c_p  = production cost per unit of product p
     h_p  = holding cost per unit per period for product p
     D_pt = demand for product p in period t
     C_t  = total production capacity in period t
     I0_p = initial stock of product p

  Minimize   sum_p sum_t ( c_p x_pt + h_p I_pt )

  subject to I_pt = I_p,t-1 + x_pt - D_pt   for all p, t   (inventory balance)
             sum_p x_pt <= C_t               for all t       (capacity)
             x_pt >= 0,  I_pt >= 0           for all p, t

NOTE: This is Modèle 6 — the blank-page challenge.
      The schema and data are loaded; ALL three tiers must be implemented
      by the student.  Only the function signatures and docstrings are
      provided here.
"""

from __future__ import annotations

import pandas as pd
import pyomo.environ as pyo
from sqlalchemy import text

from lab.common_db import engine, save_result


# ---------------------------------------------------------------------------
# Read tier  — TO BE IMPLEMENTED BY STUDENT
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lire les données du modèle depuis la base gol651.

    Tables à interroger :
        planning_products (product_id, name, prod_cost, holding_cost, initial_stock)
        planning_periods  (period_id, label, capacity)
        planning_demand   (product_id, period_id, demand)

    Retourner
    ---------
    (products_df, periods_df, demand_df)

    TODO : implémenter cette fonction.
    Indice : utiliser engine("gol651") et pd.read_sql() comme dans les modèles précédents.
    """
    # TODO : créer le moteur, ouvrir une connexion et lire les trois tables.
    raise NotImplementedError("TODO : implémenter load_data()")


# ---------------------------------------------------------------------------
# Backend: build and solve  — TO BE IMPLEMENTED BY STUDENT
# ---------------------------------------------------------------------------

def build_and_solve(
    products:   pd.DataFrame,
    periods:    pd.DataFrame,
    demand:     pd.DataFrame,
    time_limit: int = 60,
) -> dict:
    """Construire et résoudre le modèle de planification multi-période.

    Paramètres
    ----------
    products : DataFrame — colonnes : product_id, name, prod_cost,
                           holding_cost, initial_stock
    periods  : DataFrame — colonnes : period_id, label, capacity
    demand   : DataFrame — colonnes : product_id, period_id, demand

    Retourner
    ---------
    dict avec les clés : status, objective_value, variables, solver_params

    TODO : implémenter cette fonction selon la formulation mathématique
           décrite dans le docstring du module.

    Conseils
    --------
    1. Créer un ConcreteModel Pyomo.
    2. Définir deux familles de variables :
           model.x = pyo.Var(P, T, domain=pyo.NonNegativeReals)   (production)
           model.I = pyo.Var(P, T, domain=pyo.NonNegativeReals)   (stock)
       où P = liste des product_id, T = liste des period_id.
    3. L'équilibre des stocks lie les deux familles.
       Pour t = premier période, utiliser initial_stock comme I_p0.
    4. La contrainte de capacité porte sur la somme de toutes les productions
       d'une même période : sum_p x_pt <= C_t.
    5. Résoudre avec pyo.SolverFactory("cbc").
    6. Retourner un dict avec les clés status, objective_value, variables,
       solver_params (voir modèles précédents pour le format attendu).
    """
    # TODO : implémenter le modèle Pyomo.
    raise NotImplementedError("TODO : implémenter build_and_solve()")


# ---------------------------------------------------------------------------
# Write tier  — TO BE IMPLEMENTED BY STUDENT
# ---------------------------------------------------------------------------

def persist_result(student_id: str, result: dict) -> int:
    """Sauvegarder le résultat dans gol651_exercises.lab_results.

    Utiliser save_result() de lab.common_db avec model_name='lab_06_planification'.

    TODO : appeler save_result() avec les bons arguments.
    Indice : voir persist_result() dans model_transport.py pour la structure.
    """
    # TODO : implémenter persist_result().
    raise NotImplementedError("TODO : implémenter persist_result()")
