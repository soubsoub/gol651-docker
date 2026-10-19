"""Application - Interactive production planning with Pyomo (HiGHS, CBC, GLPK).

Same model as examples/optimization/production_plan_lp.py, but every parameter
is a widget: change a capacity or a profit and the model is solved again.
"""

import pandas as pd
import plotly.express as px
import pyomo.environ as pyo
import streamlit as st
from common import bilingual, show_source

PRODUCTS = ["standard_pallet", "reinforced_pallet", "shipping_crate"]
RESOURCES = ["wood_m3", "assembly_h", "finishing_h"]
USAGE = {  # usage[resource][product], per unit
    "wood_m3":     {"standard_pallet": 0.06, "reinforced_pallet": 0.09, "shipping_crate": 0.15},
    "assembly_h":  {"standard_pallet": 0.15, "reinforced_pallet": 0.25, "shipping_crate": 0.40},
    "finishing_h": {"standard_pallet": 0.05, "reinforced_pallet": 0.10, "shipping_crate": 0.25},
}


def solve(profit: dict, demand: dict, capacity: dict, solver: str, integer: bool):
    """Build and solve the model; return (model, results)."""
    m = pyo.ConcreteModel()
    m.P = pyo.Set(initialize=PRODUCTS)
    m.R = pyo.Set(initialize=RESOURCES)
    domain = pyo.NonNegativeIntegers if integer else pyo.NonNegativeReals
    m.x = pyo.Var(m.P, domain=domain, bounds=lambda m, p: (0, demand[p]))
    m.profit = pyo.Objective(expr=sum(profit[p] * m.x[p] for p in m.P), sense=pyo.maximize)
    m.resource = pyo.Constraint(
        m.R, rule=lambda m, r: sum(USAGE[r][p] * m.x[p] for p in m.P) <= capacity[r])
    if not integer:
        m.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)   # shadow prices (LP only)
    return m, pyo.SolverFactory(solver).solve(m)


st.title("Optimisation de la production / Production optimization")
bilingual(
    "Un atelier de Laval fabrique trois produits. Modifiez les paramètres : le modèle "
    "est résolu de nouveau à chaque changement.",
    "A Laval workshop builds three products. Change the parameters: the model is "
    "solved again on every change.",
)
st.latex(r"\max \sum_{j} p_j x_j \quad \text{s.c.} \quad "
         r"\sum_{j} a_{ij} x_j \le b_i \;\; \forall i, \qquad 0 \le x_j \le d_j")

with st.sidebar:
    st.header("Solveur / Solver")
    solver = st.selectbox("Solveur / Solver", ["highs", "cbc", "glpk"])
    integer = st.checkbox("Unités entières (PLNE) / Integer units (MILP)", value=False)
    st.header("Capacités / Capacities")
    capacity = {
        "wood_m3": st.slider("Bois (m³) / Wood", 20.0, 120.0, 60.0, 5.0),
        "assembly_h": st.slider("Assemblage (h) / Assembly", 50.0, 300.0, 150.0, 10.0),
        "finishing_h": st.slider("Finition (h) / Finishing", 20.0, 150.0, 70.0, 5.0),
    }

st.subheader("Produits / Products")
inputs = st.data_editor(
    pd.DataFrame({"product": PRODUCTS, "profit_$": [12.0, 19.0, 30.0],
                  "demand_max": [400, 250, 120]}),
    hide_index=True, disabled=["product"], width="stretch",
    column_config={"profit_$": st.column_config.NumberColumn(min_value=0.0, step=0.5),
                   "demand_max": st.column_config.NumberColumn(min_value=0, step=10)})
profit = dict(zip(inputs["product"], inputs["profit_$"].astype(float)))
demand = dict(zip(inputs["product"], inputs["demand_max"].astype(int)))

model, results = solve(profit, demand, capacity, solver, integer)
if not pyo.check_optimal_termination(results):
    st.error(f"Pas de solution optimale / No optimal solution: "
             f"{results.solver.termination_condition}")
    st.stop()

# --- Results ---------------------------------------------------------------------
st.subheader("Plan optimal / Optimal plan")
c1, c2 = st.columns([1, 2])
c1.metric("Profit", f"{pyo.value(model.profit):,.2f} $")
c1.caption(f"Solveur / solver: {solver}" + (" · PLNE / MILP" if integer else " · PL / LP"))
plan = pd.DataFrame({
    "product": PRODUCTS,
    "units": [round(pyo.value(model.x[p]), 2) for p in PRODUCTS],
    "demand_max": [demand[p] for p in PRODUCTS],
})
c2.dataframe(plan, hide_index=True, width="stretch")

usage = pd.DataFrame({
    "resource": RESOURCES,
    "used": [pyo.value(sum(USAGE[r][p] * model.x[p] for p in PRODUCTS)) for r in RESOURCES],
    "available": [capacity[r] for r in RESOURCES],
})
usage["utilization_%"] = (100 * usage["used"] / usage["available"]).round(1)
if not integer:
    usage["shadow_price_$"] = [round(model.dual[model.resource[r]], 2) for r in RESOURCES]

left, right = st.columns(2)
left.plotly_chart(px.bar(usage, x="resource", y=["used", "available"], barmode="group",
                         title="Ressources / Resources", labels={"value": "", "variable": ""}),
                  width="stretch")
right.dataframe(usage, hide_index=True, width="stretch")
if integer:
    right.caption("Pas de prix duaux pour un PLNE. / No dual prices for a MILP.")
else:
    right.caption("Prix dual : profit supplémentaire par unité de ressource en plus "
                  "(0 = ressource non saturée). / Dual price: extra profit per extra unit "
                  "of resource (0 = not binding).")

# --- Sensitivity ------------------------------------------------------------------
with st.expander("Analyse de sensibilité : heures d'assemblage / Sensitivity: assembly hours"):
    hours = list(range(50, 301, 25))
    profits = []
    for h in hours:
        m, r = solve(profit, demand, {**capacity, "assembly_h": float(h)}, solver, integer)
        profits.append(pyo.value(m.profit) if pyo.check_optimal_termination(r) else None)
    st.plotly_chart(px.line(pd.DataFrame({"assembly_h": hours, "profit": profits}),
                            x="assembly_h", y="profit", markers=True,
                            labels={"assembly_h": "Heures d'assemblage / Assembly hours",
                                    "profit": "Profit ($)"}), width="stretch")

show_source(__file__)
