"""
lab/model_transport.py
======================
Backend (logique métier) — Modèle 3 : Transport

Problem
-------
Minimize total shipping cost from m depots (sources) to n distribution
centres (sinks), respecting supply and demand constraints.

Mathematical formulation
------------------------
Let  x_ij = units shipped from source i to sink j
     c_ij = cost per unit on route (i, j)
     s_i  = supply at source i
     d_j  = demand at sink j

  Minimize   sum_i sum_j c_ij x_ij
  subject to sum_j x_ij <= s_i   for all sources i  (supply)
             sum_i x_ij  = d_j   for all sinks j    (demand satisfied)
             x_ij >= 0
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
import pyomo.environ as pyo

from lab.common_db import engine, save_result


# ---------------------------------------------------------------------------
# Read tier
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (nodes_df, routes_df) from gol651."""
    eng = engine("gol651")
    with eng.connect() as conn:
        nodes  = pd.read_sql(text("SELECT * FROM transport_nodes ORDER BY node_id"), conn)
        routes = pd.read_sql(text("SELECT * FROM transport_routes"),                 conn)
    return nodes, routes


# ---------------------------------------------------------------------------
# Backend: build and solve
# ---------------------------------------------------------------------------

def build_and_solve(
    nodes:      pd.DataFrame,
    routes:     pd.DataFrame,
    time_limit: int = 60,
) -> dict:
    """Build the transport LP and solve with CBC."""
    sources = nodes[nodes["type"] == "source"]
    sinks   = nodes[nodes["type"] == "sink"]

    model = pyo.ConcreteModel("Transport")

    # Set of routes as (from, to) pairs
    ROUTES = [(r["from_node"], r["to_node"]) for _, r in routes.iterrows()]
    cost   = {(r["from_node"], r["to_node"]): r["cost_per_unit"] for _, r in routes.iterrows()}

    model.x = pyo.Var(ROUTES, domain=pyo.NonNegativeReals)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(cost[k] * model.x[k] for k in ROUTES),
        sense=pyo.minimize,
    )

    # Supply constraints (<=)
    model.supply = pyo.ConstraintList()
    for _, s in sources.iterrows():
        outflow = [model.x[(s["node_id"], t)] for t in sinks["node_id"]
                   if (s["node_id"], t) in ROUTES]
        if outflow:
            model.supply.add(sum(outflow) <= s["capacity"])

    # Demand constraints (=)
    model.demand = pyo.ConstraintList()
    for _, d in sinks.iterrows():
        inflow = [model.x[(s, d["node_id"])] for s in sources["node_id"]
                  if (s, d["node_id"]) in ROUTES]
        if inflow:
            model.demand.add(sum(inflow) == d["capacity"])

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
        f"{node_names[fr]} → {node_names[to]}": round(pyo.value(model.x[(fr, to)]) or 0, 2)
        for (fr, to) in ROUTES
    }

    return {
        "status":          status,
        "objective_value": obj,
        "variables":       variables,
        "solver_params":   {"solver": "CBC", "time_limit": time_limit},
    }


# ---------------------------------------------------------------------------
# Write tier
# ---------------------------------------------------------------------------

def persist_result(student_id: str, result: dict) -> int:
    return save_result(
        student_id      = student_id,
        model_name      = "lab_03_transport",
        status          = result["status"],
        objective_value = result["objective_value"],
        variables       = result["variables"],
        solver_params   = result["solver_params"],
    )
