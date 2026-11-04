"""
lab/model_production.py
=======================
Backend (logique métier) — Modèle 2 : Production LP

Three-tier role
---------------
This module is the **backend tier**.  It reads data from MySQL, builds the
linear programme with Pyomo, solves it, and returns structured results.
No Streamlit code belongs here.

Problem
-------
Maximize weekly contribution margin for 4 product lines subject to:
  - machine-hour capacity
  - labour-hour capacity
  - raw-material capacity
  - optional maximum demand per product

Mathematical formulation
------------------------
Let  x_j = units produced of product j  (j = 1 … n)
     c_j = contribution margin of product j
     a_ij = consumption of resource i per unit of product j
     b_i  = available capacity of resource i

  Maximize   sum_j c_j x_j
  subject to sum_j a_ij x_j <= b_i   for all i
             x_j <= d_j              if max_demand is set for product j
             x_j >= 0
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
import pyomo.environ as pyo

from lab.common_db import engine, save_result


# ---------------------------------------------------------------------------
# Read tier (called by backend)
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (resources_df, products_df) from gol651."""
    eng = engine("gol651")
    with eng.connect() as conn:
        resources = pd.read_sql(
            text("SELECT * FROM production_resources ORDER BY resource_id"),
            conn,
        )
        products = pd.read_sql(
            text("SELECT * FROM production_products ORDER BY product_id"),
            conn,
        )
    return resources, products


# ---------------------------------------------------------------------------
# Backend: build and solve
# ---------------------------------------------------------------------------

def build_and_solve(
    resources:  pd.DataFrame,
    products:   pd.DataFrame,
    time_limit: int = 60,
) -> dict:
    """Build the production LP, solve with CBC, return a result dict.

    Parameters
    ----------
    resources  : DataFrame from load_data()
    products   : DataFrame from load_data()
    time_limit : solver time limit in seconds

    Returns
    -------
    dict with keys:
        status          str
        objective_value float | None
        variables       dict  { product_name : value }
        solver_params   dict  { solver, time_limit }
    """
    model = pyo.ConcreteModel("Production_LP")

    # Sets
    J = list(products["product_id"])
    I = list(resources["resource_id"])

    # Parameters
    c  = {row["product_id"]: row["margin"]   for _, row in products.iterrows()}
    b  = {row["resource_id"]: row["capacity"] for _, row in resources.iterrows()}

    consumption_cols = ["r1_consumption", "r2_consumption", "r3_consumption"]
    a = {
        (row["resource_id"], pid): products.loc[products["product_id"] == pid, consumption_cols[row["resource_id"] - 1]].values[0]
        for _, row in resources.iterrows()
        for pid in J
    }

    # Decision variables: x_j >= 0
    def x_bounds(model, j):
        row = products.loc[products["product_id"] == j].iloc[0]
        ub = row["max_demand"] if pd.notna(row["max_demand"]) else None
        return (0, ub)

    model.x = pyo.Var(J, domain=pyo.NonNegativeReals, bounds=x_bounds)

    # Objective: maximize sum c_j x_j
    model.obj = pyo.Objective(
        expr=sum(c[j] * model.x[j] for j in J),
        sense=pyo.maximize,
    )

    # Constraints: sum a_ij x_j <= b_i
    model.capacity = pyo.ConstraintList()
    for i in I:
        model.capacity.add(
            sum(a[(i, j)] * model.x[j] for j in J) <= b[i]
        )

    # Solve
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

    variables = {
        row["name"]: round(pyo.value(model.x[row["product_id"]]) or 0, 4)
        for _, row in products.iterrows()
    }

    return {
        "status":          status,
        "objective_value": obj,
        "variables":       variables,
        "solver_params":   {"solver": "CBC", "time_limit": time_limit},
    }


# ---------------------------------------------------------------------------
# Write tier (called by Streamlit page)
# ---------------------------------------------------------------------------

def persist_result(student_id: str, result: dict) -> int:
    """Save the solve result to gol651_exercises.lab_results."""
    return save_result(
        student_id      = student_id,
        model_name      = "lab_02_production",
        status          = result["status"],
        objective_value = result["objective_value"],
        variables       = result["variables"],
        solver_params   = result["solver_params"],
    )
