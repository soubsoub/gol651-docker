"""
lab/model_assignment.py
=======================
Backend (logique métier) — Modèle 4 : Affectation (Assignment)

Problem
-------
Assign n agents to n tasks one-to-one at minimum total cost.

Mathematical formulation
------------------------
Let  x_ij in {0, 1} = 1 if agent i is assigned to task j
     c_ij = cost of assigning agent i to task j

  Minimize   sum_i sum_j c_ij x_ij
  subject to sum_j x_ij = 1   for all agents i   (each agent does exactly one task)
             sum_i x_ij = 1   for all tasks j    (each task is done by exactly one agent)
             x_ij in {0, 1}
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
import pyomo.environ as pyo

from lab.common_db import engine, save_result


# ---------------------------------------------------------------------------
# Read tier
# ---------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (agents_df, tasks_df, costs_df) from gol651."""
    eng = engine("gol651")
    with eng.connect() as conn:
        agents = pd.read_sql(text("SELECT * FROM assignment_agents ORDER BY agent_id"), conn)
        tasks  = pd.read_sql(text("SELECT * FROM assignment_tasks  ORDER BY task_id"),  conn)
        costs  = pd.read_sql(text("SELECT * FROM assignment_costs"),                    conn)
    return agents, tasks, costs


# ---------------------------------------------------------------------------
# Backend: build and solve
# ---------------------------------------------------------------------------

def build_and_solve(
    agents:     pd.DataFrame,
    tasks:      pd.DataFrame,
    costs:      pd.DataFrame,
    time_limit: int = 60,
) -> dict:
    """Build the assignment MIP and solve with CBC."""
    model = pyo.ConcreteModel("Affectation")

    PAIRS = [(c["agent_id"], c["task_id"]) for _, c in costs.iterrows()]
    cost  = {(c["agent_id"], c["task_id"]): c["cost"] for _, c in costs.iterrows()}

    # Decision variables x_ij in {0, 1}
    model.x = pyo.Var(PAIRS, domain=pyo.Binary)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(cost[k] * model.x[k] for k in PAIRS),
        sense=pyo.minimize,
    )

    # Each agent does exactly one task
    model.agent_ctr = pyo.ConstraintList()
    for _, a in agents.iterrows():
        pairs_a = [(ai, tj) for (ai, tj) in PAIRS if ai == a["agent_id"]]
        model.agent_ctr.add(sum(model.x[k] for k in pairs_a) == 1)

    # Each task is done by exactly one agent
    model.task_ctr = pyo.ConstraintList()
    for _, t in tasks.iterrows():
        pairs_t = [(ai, tj) for (ai, tj) in PAIRS if tj == t["task_id"]]
        model.task_ctr.add(sum(model.x[k] for k in pairs_t) == 1)

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

    agent_names = agents.set_index("agent_id")["name"].to_dict()
    task_names  = tasks.set_index("task_id")["name"].to_dict()

    variables = {
        f"{agent_names[ai]} → {task_names[tj]}": int(round(pyo.value(model.x[(ai, tj)]) or 0))
        for (ai, tj) in PAIRS
        if round(pyo.value(model.x[(ai, tj)]) or 0) == 1
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
        model_name      = "lab_04_affectation",
        status          = result["status"],
        objective_value = result["objective_value"],
        variables       = result["variables"],
        solver_params   = result["solver_params"],
    )
