"""
lab/model_network.py
====================
Backend (logique métier) — Modèle 5 : Flot en réseau (Network flow)

Problem
-------
Route flow through a directed network from sources to sinks at minimum
total arc cost, respecting arc capacities and flow conservation.

Mathematical formulation
------------------------
Let  f_a = flow on arc a = (i, j)
     c_a = cost per unit of flow on arc a
     u_a = capacity of arc a
     b_i = net supply at node i  (> 0 source, < 0 sink, 0 transit)

  Minimize   sum_a c_a f_a
  subject to sum_{a: head=i} f_a - sum_{a: tail=i} f_a = b_i   for all i
             0 <= f_a <= u_a    for all arcs a

NOTE: The read tier is complete. The student completes build_and_solve() (Modèle 5).
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
import pyomo.environ as pyo

from lab.common_db import engine, save_result


# ---------------------------------------------------------------------------
# Read tier  — COMPLETE (provided to students)
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (nodes_df, arcs_df) from gol651."""
    eng = engine("gol651")
    with eng.connect() as conn:
        nodes = pd.read_sql(text("SELECT * FROM network_nodes ORDER BY node_id"), conn)
        arcs  = pd.read_sql(text("SELECT * FROM network_arcs  ORDER BY arc_id"),  conn)
    return nodes, arcs


# ---------------------------------------------------------------------------
# Backend: build and solve  — TO BE COMPLETED BY STUDENT
# ---------------------------------------------------------------------------

def build_and_solve(
    nodes:      pd.DataFrame,
    arcs:       pd.DataFrame,
    time_limit: int = 60,
) -> dict:
    """Build the minimum-cost network-flow LP and solve.

    The function skeleton is provided.  Fill in the TODO sections.

    Parameters
    ----------
    nodes : DataFrame with columns node_id, name, type, supply
    arcs  : DataFrame with columns arc_id, from_node, to_node, cost, capacity

    Returns
    -------
    dict with keys: status, objective_value, variables, solver_params
    """
    model = pyo.ConcreteModel("Flot_en_reseau")

    ARCS = list(arcs["arc_id"])
    cost_a     = {r["arc_id"]: r["cost"]     for _, r in arcs.iterrows()}
    capacity_a = {r["arc_id"]: r["capacity"] for _, r in arcs.iterrows()}

    # ------------------------------------------------------------------
    # TODO 1 — Créer les variables de décision f_a >= 0, bornées par u_a
    #
    # Indice : utiliser pyo.Var avec domain=pyo.NonNegativeReals
    #          et bounds={(arc_id): (0, capacity_a[arc_id]) ...}
    #
    # Exemple de structure :
    #   def f_bounds(model, a):
    #       return (0, capacity_a[a])
    #   model.f = pyo.Var(ARCS, domain=pyo.NonNegativeReals, bounds=f_bounds)
    # ------------------------------------------------------------------
    # TODO 1 : votre code ici
    raise NotImplementedError("TODO 1 : créer les variables de flot")

    # ------------------------------------------------------------------
    # TODO 2 — Définir la fonction objectif : minimiser sum_a c_a f_a
    #
    # Exemple :
    #   model.obj = pyo.Objective(
    #       expr=sum(cost_a[a] * model.f[a] for a in ARCS),
    #       sense=pyo.minimize,
    #   )
    # ------------------------------------------------------------------
    # TODO 2 : votre code ici

    # ------------------------------------------------------------------
    # TODO 3 — Ajouter la contrainte de conservation du flot pour chaque nœud
    #
    # Pour chaque nœud i :
    #   flot sortant − flot entrant = b_i  (supply du nœud)
    #
    #   flot entrant  = sum f_a pour tout arc a dont to_node   = node_id
    #   flot sortant  = sum f_a pour tout arc a dont from_node = node_id
    #
    # Exemple :
    #   model.conservation = pyo.ConstraintList()
    #   for _, node in nodes.iterrows():
    #       inflow  = [model.f[r["arc_id"]] for _, r in arcs.iterrows()
    #                  if r["to_node"]   == node["node_id"]]
    #       outflow = [model.f[r["arc_id"]] for _, r in arcs.iterrows()
    #                  if r["from_node"] == node["node_id"]]
    #       model.conservation.add(
    #           sum(outflow) - sum(inflow) == node["supply"]
    #       )
    # ------------------------------------------------------------------
    # TODO 3 : votre code ici

    # Solve (ne pas modifier)
    solver = pyo.SolverFactory("cbc")
    solver.options["seconds"] = time_limit
    result = solver.solve(model, tee=False)

    term = result.solver.termination_condition
    if term == pyo.TerminationCondition.optimal:
        status = "Optimal"
        obj    = round(pyo.value(model.obj), 4)
    elif term == pyo.TerminationCondition.infeasible:
        status = "Infeasible"
        obj    = None
    else:
        status = str(term)
        obj    = None

    node_names = nodes.set_index("node_id")["name"].to_dict()
    variables = {
        f"{node_names[r['from_node']]} → {node_names[r['to_node']]}":
            round(pyo.value(model.f[r["arc_id"]]) or 0, 2)
        for _, r in arcs.iterrows()
    }

    return {
        "status":          status,
        "objective_value": obj,
        "variables":       variables,
        "solver_params":   {"solver": "CBC", "time_limit": time_limit},
    }


# ---------------------------------------------------------------------------
# Write tier — COMPLETE (provided to students)
# ---------------------------------------------------------------------------

def persist_result(student_id: str, result: dict) -> int:
    return save_result(
        student_id      = student_id,
        model_name      = "lab_05_reseau",
        status          = result["status"],
        objective_value = result["objective_value"],
        variables       = result["variables"],
        solver_params   = result["solver_params"],
    )
