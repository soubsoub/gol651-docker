r"""GOL651 - Mixed-integer programming: warehouse location (Pyomo).

Run inside Docker:
    docker compose exec jupyter python examples/optimization/facility_location_milp.py
    docker compose exec jupyter python examples/optimization/facility_location_milp.py --compare

A distributor serves six zones of Greater Montréal. Which candidate
warehouses should it open, and how should demand be assigned, to minimize
the yearly fixed + transport cost?

Model (capacitated facility location)
-------------------------------------
Sets        I = candidate warehouses, J = customer zones
Parameters  f_i   yearly fixed cost of opening warehouse i ($)
            u_i   capacity of warehouse i (pallets/year)
            d_j   demand of zone j (pallets/year)
            c_ij  transport cost from i to j ($/pallet)
Variables   y_i in {0, 1}   1 if warehouse i is opened       (integer!)
            x_ij >= 0       pallets shipped from i to j

    min   sum_i f_i y_i + sum_i sum_j c_ij x_ij
    s.t.  sum_i x_ij = d_j               for every zone j     (serve demand)
          sum_j x_ij <= u_i y_i          for every warehouse i (capacity only if open)
          x_ij <= d_j y_i                for every i, j        (tighter formulation)

The binary variables y_i make this a MILP: a pure LP could "half-open" a
warehouse. With --compare, the same model is solved by HiGHS, CBC and GLPK.
"""

from __future__ import annotations

import argparse

import pyomo.environ as pyo

WAREHOUSES = {  # name: (fixed cost $/year, capacity pallets/year)
    "Laval":        (180_000, 9_000),
    "Longueuil":    (165_000, 8_000),
    "Boucherville": (140_000, 6_500),
    "Mirabel":      (120_000, 7_000),
}
ZONES = {  # name: demand pallets/year
    "Montréal-Centre": 4_200,
    "Montréal-Est":    2_600,
    "Rive-Sud":        3_100,
    "Laval":           2_400,
    "Rive-Nord":       1_900,
    "Vaudreuil":       1_300,
}
COST = {  # transport cost $/pallet, COST[warehouse][zone]
    "Laval":        {"Montréal-Centre": 7.0, "Montréal-Est": 9.0, "Rive-Sud": 13.0,
                     "Laval": 3.0, "Rive-Nord": 6.0, "Vaudreuil": 11.0},
    "Longueuil":    {"Montréal-Centre": 6.5, "Montréal-Est": 8.0, "Rive-Sud": 3.5,
                     "Laval": 11.0, "Rive-Nord": 13.0, "Vaudreuil": 12.0},
    "Boucherville": {"Montréal-Centre": 8.5, "Montréal-Est": 5.0, "Rive-Sud": 5.5,
                     "Laval": 12.0, "Rive-Nord": 12.5, "Vaudreuil": 15.0},
    "Mirabel":      {"Montréal-Centre": 12.0, "Montréal-Est": 14.0, "Rive-Sud": 17.0,
                     "Laval": 6.0, "Rive-Nord": 4.0, "Vaudreuil": 10.0},
}


def build_model() -> pyo.ConcreteModel:
    m = pyo.ConcreteModel(name="facility_location")
    m.I = pyo.Set(initialize=list(WAREHOUSES))
    m.J = pyo.Set(initialize=list(ZONES))

    m.fixed = pyo.Param(m.I, initialize={i: v[0] for i, v in WAREHOUSES.items()})
    m.cap = pyo.Param(m.I, initialize={i: v[1] for i, v in WAREHOUSES.items()})
    m.demand = pyo.Param(m.J, initialize=ZONES)
    m.cost = pyo.Param(m.I, m.J, initialize={(i, j): COST[i][j] for i in WAREHOUSES
                                             for j in ZONES})

    m.y = pyo.Var(m.I, domain=pyo.Binary)
    m.x = pyo.Var(m.I, m.J, domain=pyo.NonNegativeReals)

    m.total_cost = pyo.Objective(
        expr=sum(m.fixed[i] * m.y[i] for i in m.I)
        + sum(m.cost[i, j] * m.x[i, j] for i in m.I for j in m.J),
        sense=pyo.minimize,
    )

    @m.Constraint(m.J)
    def serve_demand(m, j):
        return sum(m.x[i, j] for i in m.I) == m.demand[j]

    @m.Constraint(m.I)
    def capacity(m, i):
        return sum(m.x[i, j] for j in m.J) <= m.cap[i] * m.y[i]

    @m.Constraint(m.I, m.J)
    def link(m, i, j):
        return m.x[i, j] <= m.demand[j] * m.y[i]

    return m


def solve(solver_name: str = "highs") -> pyo.ConcreteModel:
    m = build_model()
    results = pyo.SolverFactory(solver_name).solve(m)
    if not pyo.check_optimal_termination(results):
        raise RuntimeError(f"No optimal solution: {results.solver.termination_condition}")
    return m


def report(m: pyo.ConcreteModel, solver_name: str) -> None:
    opened = [i for i in m.I if pyo.value(m.y[i]) > 0.5]
    fixed = sum(m.fixed[i] for i in opened)
    print(f"Solver: {solver_name}")
    print(f"  Warehouses opened : {', '.join(opened)}")
    print(f"  Fixed cost        : {fixed:>12,.0f} $")
    print(f"  Transport cost    : {pyo.value(m.total_cost) - fixed:>12,.0f} $")
    print(f"  Total yearly cost : {pyo.value(m.total_cost):>12,.0f} $")
    print("  Assignment (pallets/year):")
    for i in opened:
        flows = {j: pyo.value(m.x[i, j]) for j in m.J if pyo.value(m.x[i, j]) > 1e-6}
        load = sum(flows.values())
        print(f"    {i:<13} {load:7,.0f} / {m.cap[i]:,}  -> "
              + ", ".join(f"{j} {q:,.0f}" for j, q in flows.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solver", default="highs", choices=["highs", "cbc", "glpk"])
    parser.add_argument("--compare", action="store_true",
                        help="solve with HiGHS, CBC and GLPK and compare")
    args = parser.parse_args()

    if not args.compare:
        report(solve(args.solver), args.solver)
    else:
        values = {}
        for name in ("highs", "cbc", "glpk"):
            model = solve(name)
            values[name] = pyo.value(model.total_cost)
            report(model, name)
            print()
        spread = max(values.values()) - min(values.values())
        print("Same optimum with every solver:", spread < 1e-6 * max(values.values()))
