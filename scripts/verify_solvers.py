#!/usr/bin/env python3
"""GOL651 - Pyomo solver verification (HiGHS, CBC, GLPK).

Run INSIDE the Docker Python container:

    docker compose exec jupyter python scripts/verify_solvers.py

Each solver must do more than report itself "available": it must solve a
small LP and a small MILP, return an optimal termination condition, and
reproduce the known optimal objective and decision variables.

Test models
-----------
LP   : max 3x + 2y
       s.t. x + y <= 4,  x + 3y <= 6,  x <= 3,  x, y >= 0
       optimum: x = 3, y = 1, objective = 11

MILP : max x + y
       s.t. -x + y <= 1,  3x + 2y <= 12,  2x + 3y <= 12,  x, y integer >= 0
       LP relaxation optimum = 4.8 at (2.4, 2.4); integer optimum = 4.
       A solver that ignored integrality would return 4.8 and FAIL.

Exit code: 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Callable

TOL = 1e-6

# (Pyomo solver name, executable expected on PATH or None for a Python API)
SOLVERS: list[tuple[str, str, str | None]] = [
    ("HiGHS", "highs", None),      # provided by the highspy Python package
    ("CBC", "cbc", "cbc"),         # Debian package coinor-cbc
    ("GLPK", "glpk", "glpsol"),    # Debian package glpk-utils
]


# --------------------------------------------------------------------------
# Minimal check runner (identical structure in every verify_*.py script)
# --------------------------------------------------------------------------
def _run(name: str, func: Callable[[], str], hint: str) -> tuple[str, bool, str, str]:
    try:
        detail = func()
        return (name, True, detail or "", "")
    except Exception as exc:  # noqa: BLE001 - report every failure clearly
        return (name, False, f"{type(exc).__name__}: {exc}", hint)


def _print(results: list[tuple[str, bool, str, str]]) -> None:
    for name, ok, detail, hint in results:
        status = "[PASS]" if ok else "[FAIL]"
        line = f"{status} {name}"
        if ok and detail:
            line += f" ({detail})"
        print(line)
        if not ok:
            print(f"       Reason: {detail}")
            print(f"       Hint:   {hint}")


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
def _build_lp():
    import pyomo.environ as pyo

    m = pyo.ConcreteModel(name="gol651_lp")
    m.x = pyo.Var(domain=pyo.NonNegativeReals)
    m.y = pyo.Var(domain=pyo.NonNegativeReals)
    m.obj = pyo.Objective(expr=3 * m.x + 2 * m.y, sense=pyo.maximize)
    m.c1 = pyo.Constraint(expr=m.x + m.y <= 4)
    m.c2 = pyo.Constraint(expr=m.x + 3 * m.y <= 6)
    m.c3 = pyo.Constraint(expr=m.x <= 3)
    return m, {"x": 3.0, "y": 1.0}, 11.0


def _build_milp():
    import pyomo.environ as pyo

    m = pyo.ConcreteModel(name="gol651_milp")
    m.x = pyo.Var(domain=pyo.NonNegativeIntegers)
    m.y = pyo.Var(domain=pyo.NonNegativeIntegers)
    m.obj = pyo.Objective(expr=m.x + m.y, sense=pyo.maximize)
    m.c1 = pyo.Constraint(expr=-m.x + m.y <= 1)
    m.c2 = pyo.Constraint(expr=3 * m.x + 2 * m.y <= 12)
    m.c3 = pyo.Constraint(expr=2 * m.x + 3 * m.y <= 12)
    # Several integer optima exist (objective 4); only the objective and
    # integrality are checked, not a specific (x, y) pair.
    return m, None, 4.0


def _solve_and_check(solver_name: str, builder) -> str:
    import pyomo.environ as pyo

    model, expected_vars, expected_obj = builder()
    solver = pyo.SolverFactory(solver_name)
    if not solver.available(exception_flag=False):
        raise RuntimeError(f"Pyomo reports solver '{solver_name}' as unavailable")
    results = solver.solve(model)
    if not pyo.check_optimal_termination(results):
        tc = results.solver.termination_condition
        raise RuntimeError(f"non-optimal termination: {tc}")
    obj = pyo.value(model.obj)
    if abs(obj - expected_obj) > TOL:
        raise RuntimeError(f"objective {obj} != expected {expected_obj}")
    if expected_vars is None:
        for var in (model.x, model.y):
            v = pyo.value(var)
            if abs(v - round(v)) > TOL:
                raise RuntimeError(f"{var.name}={v} is not integer")
    else:
        for name, target in expected_vars.items():
            v = pyo.value(getattr(model, name))
            if abs(v - target) > TOL:
                raise RuntimeError(f"{name}={v} != expected {target}")
    return f"objective={obj:g}"


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------
def _check_pyomo() -> str:
    import pyomo
    import pyomo.environ  # noqa: F401

    return f"Pyomo {pyomo.__version__}"


def _check_executable(exe: str) -> Callable[[], str]:
    def check() -> str:
        path = shutil.which(exe)
        if path is None:
            raise FileNotFoundError(f"'{exe}' not found on PATH")
        # Both CBC and glpsol print their version banner on these flags.
        flag = ["-quit"] if exe == "cbc" else ["--version"]
        out = subprocess.run([exe, *flag], capture_output=True, text=True, timeout=30)
        first = (out.stdout or out.stderr).strip().splitlines()
        banner = next((ln.strip() for ln in first if "Version" in ln or "GLPSOL" in ln), "")
        return f"{path} {banner}".strip()

    return check


def _check_highspy() -> str:
    from importlib.metadata import version

    import highspy

    h = highspy.Highs()
    return f"highspy {version('highspy')} / HiGHS {h.version()}"


def run_checks() -> list[tuple[str, bool, str, str]]:
    results = [
        _run("Pyomo", _check_pyomo,
             "Pyomo is missing from the image; download it again: docker compose pull"),
        _run("HiGHS library (highspy)", _check_highspy,
             "highspy is missing; check requirements-lock.txt and rebuild the image"),
    ]
    for label, name, exe in SOLVERS:
        if exe is not None:
            results.append(_run(
                f"{label} executable", _check_executable(exe),
                f"'{exe}' must be installed by the Dockerfile (apt); rebuild the image"))
        results.append(_run(
            f"{label} LP solve", lambda n=name: _solve_and_check(n, _build_lp),
            f"Pyomo could not solve the LP with '{name}'; run inside the container"))
        results.append(_run(
            f"{label} MILP solve", lambda n=name: _solve_and_check(n, _build_milp),
            f"Pyomo could not solve the MILP with '{name}'; run inside the container"))
    return results


def main() -> int:
    print("GOL651 Solver Verification")
    print("=" * 40)
    results = run_checks()
    _print(results)
    failed = sum(1 for r in results if not r[1])
    print("=" * 40)
    print(f"Summary: {len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
