r"""GOL651 - Linear programming: weekly production plan (Pyomo + HiGHS).

Run inside Docker:
    docker compose exec jupyter python examples/optimization/production_plan_lp.py
    docker compose exec jupyter python examples/optimization/production_plan_lp.py --solver glpk

A workshop in Laval builds three wooden products. How many units of each
should it build this week to maximize profit?

Model
-----
Sets        P = products, R = resources (wood, assembly, finishing)
Parameters  p_j   profit per unit of product j            ($/unit)
            a_ij  use of resource i per unit of product j
            b_i   available quantity of resource i
            d_j   maximum weekly demand of product j
Variables   x_j >= 0   units of product j to build

    max   sum_j p_j x_j
    s.t.  sum_j a_ij x_j <= b_i     for every resource i
          x_j <= d_j                for every product j

LaTeX form (see notebooks/examples/03_optimization_pyomo.ipynb):
    \max \sum_{j \in P} p_j x_j \;\; \text{s.t.} \;\;
    \sum_{j \in P} a_{ij} x_j \le b_i \;\; \forall i \in R, \quad
    0 \le x_j \le d_j \;\; \forall j \in P

The dual value (shadow price) of a resource constraint is the extra profit
earned per additional unit of that resource.
"""

from __future__ import annotations

import argparse

import pyomo.environ as pyo

# --- Data (kept separate from the model) ------------------------------------
PRODUCTS = ["standard_pallet", "reinforced_pallet", "shipping_crate"]
RESOURCES = ["wood_m3", "assembly_h", "finishing_h"]

profit = {"standard_pallet": 12.0, "reinforced_pallet": 19.0, "shipping_crate": 30.0}
demand = {"standard_pallet": 400, "reinforced_pallet": 250, "shipping_crate": 120}
capacity = {"wood_m3": 60.0, "assembly_h": 150.0, "finishing_h": 70.0}
usage = {  # usage[resource][product]
    "wood_m3":     {"standard_pallet": 0.06, "reinforced_pallet": 0.09, "shipping_crate": 0.15},
    "assembly_h":  {"standard_pallet": 0.15, "reinforced_pallet": 0.25, "shipping_crate": 0.40},
    "finishing_h": {"standard_pallet": 0.05, "reinforced_pallet": 0.10, "shipping_crate": 0.25},
}


def build_model() -> pyo.ConcreteModel:
    m = pyo.ConcreteModel(name="production_plan")
    m.P = pyo.Set(initialize=PRODUCTS)
    m.R = pyo.Set(initialize=RESOURCES)

    m.profit = pyo.Param(m.P, initialize=profit)
    m.demand = pyo.Param(m.P, initialize=demand)
    m.capacity = pyo.Param(m.R, initialize=capacity)
    m.usage = pyo.Param(m.R, m.P, initialize={(r, p): usage[r][p] for r in RESOURCES
                                              for p in PRODUCTS})

    m.x = pyo.Var(m.P, domain=pyo.NonNegativeReals, bounds=lambda m, p: (0, m.demand[p]))

    m.total_profit = pyo.Objective(expr=sum(m.profit[p] * m.x[p] for p in m.P),
                                   sense=pyo.maximize)

    @m.Constraint(m.R)
    def resource_limit(m, r):
        return sum(m.usage[r, p] * m.x[p] for p in m.P) <= m.capacity[r]

    m.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)  # ask for shadow prices
    return m


def solve(solver_name: str = "highs") -> pyo.ConcreteModel:
    m = build_model()
    results = pyo.SolverFactory(solver_name).solve(m)
    if not pyo.check_optimal_termination(results):
        raise RuntimeError(f"No optimal solution: {results.solver.termination_condition}")
    return m


def report(m: pyo.ConcreteModel, solver_name: str) -> None:
    print(f"Optimal weekly plan (solver: {solver_name})")
    for p in m.P:
        print(f"  {p:<18} {pyo.value(m.x[p]):8.1f} units   (demand max {m.demand[p]})")
    print(f"  Total profit       {pyo.value(m.total_profit):8.2f} $")
    print("\nResources        used / available   shadow price")
    for r in m.R:
        used = pyo.value(sum(m.usage[r, p] * m.x[p] for p in m.P))
        dual = m.dual.get(m.resource_limit[r], 0.0)
        print(f"  {r:<14} {used:7.2f} / {m.capacity[r]:<9g} {dual:8.2f} $ per extra unit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solver", default="highs", choices=["highs", "cbc", "glpk"])
    args = parser.parse_args()
    model = solve(args.solver)
    report(model, args.solver)
