#!/usr/bin/env python3
"""GOL651 - Execute every example: scripts, notebooks and applications.

Run INSIDE the Docker Python container (MySQL must be running):

    docker compose exec jupyter python scripts/verify_examples.py

What is executed
  examples/databases/*.py         each script runs to completion
  examples/optimization/*.py      LP and MILP (MILP compared across 3 solvers)
  notebooks/examples/*.ipynb      every cell, headless (outputs are NOT saved)
  marimo/demo_app.py              "marimo check" + run as a script
  streamlit/app.py                Streamlit AppTest: no exception raised
  fastapi/main.py                 endpoints called with FastAPI's TestClient
  flask/app.py                    pages called with Flask's test client

The database examples write only in gol651_exercises and undo their changes;
they create demo files in data/sqlite/ and data/duckdb/.
Exit code: 0 if every check passes, 1 otherwise (used by GitHub Actions CI).
"""

import importlib.util
import logging
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


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


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Scripts and notebooks
# --------------------------------------------------------------------------
def _script(path: Path, *args: str) -> Callable[[], str]:
    def check() -> str:
        out = subprocess.run([PY, path.name, *args], cwd=path.parent, capture_output=True,
                             text=True, timeout=300)
        if out.returncode != 0:
            last = (out.stderr or out.stdout).strip().splitlines()[-3:]
            raise RuntimeError(f"exit code {out.returncode}: {' | '.join(last)}")
        lines = [ln for ln in out.stdout.strip().splitlines() if ln.strip()]
        return lines[-1].strip()[:90] if lines else "ran"

    return check


def _notebook(path: Path) -> Callable[[], str]:
    def check() -> str:
        import nbformat
        from nbclient import NotebookClient

        nb = nbformat.read(path, as_version=4)
        NotebookClient(nb, timeout=300, kernel_name="python3",
                       resources={"metadata": {"path": str(path.parent)}}).execute()
        cells = sum(1 for c in nb.cells if c.cell_type == "code")
        return f"{cells} code cells executed"

    return check


# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
def _marimo() -> str:
    app = ROOT / "marimo" / "demo_app.py"
    check = subprocess.run([PY, "-m", "marimo", "check", str(app)],
                           capture_output=True, text=True, timeout=120)
    if check.returncode != 0:
        raise RuntimeError(f"marimo check: {(check.stdout + check.stderr).strip()[-300:]}")
    _script(app)()
    return "marimo check + run as a script"


def _streamlit() -> str:
    os.environ.setdefault("STREAMLIT_LOGGER_LEVEL", "error")
    from streamlit.testing.v1 import AppTest

    for name in list(logging.Logger.manager.loggerDict):
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)
    at = AppTest.from_file(str(ROOT / "streamlit" / "app.py"), default_timeout=120).run()
    if at.exception:
        raise RuntimeError(at.exception[0].message)
    if at.warning:   # the app shows a warning when MySQL is unreachable
        raise RuntimeError(f"app warning: {at.warning[0].value}")
    return f"{len(at.metric)} metrics, {len(at.dataframe)} table from MySQL"


def _fastapi() -> str:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from fastapi.testclient import TestClient
    client = TestClient(_load_module(ROOT / "fastapi" / "main.py", "gol651_fastapi_app").app)

    health = client.get("/health").json()
    if health != {"status": "ok", "database": "ok"}:
        raise AssertionError(f"/health returned {health}")
    products = client.get("/products")
    if products.status_code != 200 or len(products.json()) != 19:
        raise AssertionError(f"/products: {products.status_code}, {len(products.json())} items")
    if client.get("/products/GAN-080").json().get("sku") != "GAN-080":
        raise AssertionError("/products/GAN-080 failed")
    if client.get("/products/NOPE-000").status_code != 404:
        raise AssertionError("unknown SKU should return 404")
    bad = client.post("/quote", json={"lines": [{"sku": "GAN-080", "quantity": 0}]})
    if bad.status_code != 422:
        raise AssertionError(f"invalid quote should return 422, got {bad.status_code}")
    good = client.post("/quote", json={"lines": [{"sku": "GAN-080", "quantity": 10}]})
    if good.json().get("total") != 65.0:
        raise AssertionError(f"quote total {good.json()}")
    return "/health, /products, /products/{sku}, POST /quote (200 and 422)"


def _flask() -> str:
    client = _load_module(ROOT / "flask" / "app.py", "gol651_flask_app").app.test_client()
    for url in ("/", "/hello?name=Test", "/api/time"):
        response = client.get(url)
        if response.status_code != 200:
            raise AssertionError(f"{url} returned {response.status_code}")
    return "/, /hello, /api/time"


# --------------------------------------------------------------------------
def run_checks() -> list[tuple[str, bool, str, str]]:
    db_hint = ("Run scripts/verify_databases.py first. If you modified gol651_exercises, "
               "rebuild it with scripts/restore-exercises (sh or ps1). Run inside the "
               "container: docker compose exec jupyter python scripts/verify_examples.py")
    results = []
    for name in ("mysql_pymysql.py", "mysql_connector.py", "mysql_sqlalchemy.py",
                 "sqlite_examples.py", "duckdb_examples.py"):
        results.append(_run(f"examples/databases/{name}",
                            _script(ROOT / "examples" / "databases" / name), db_hint))
    opt = ROOT / "examples" / "optimization"
    results.append(_run("examples/optimization/production_plan_lp.py",
                        _script(opt / "production_plan_lp.py"),
                        "Check the solver with scripts/verify_solvers.py"))
    results.append(_run("examples/optimization/facility_location_milp.py --compare",
                        _script(opt / "facility_location_milp.py", "--compare"),
                        "Check the solvers with scripts/verify_solvers.py"))
    for nb in sorted((ROOT / "notebooks" / "examples").glob("*.ipynb")):
        results.append(_run(f"notebooks/examples/{nb.name}", _notebook(nb), db_hint))
    results.append(_run("marimo/demo_app.py", _marimo, "Open the app with the marimo profile "
                        "to see the error: docker compose --profile marimo up -d"))
    results.append(_run("streamlit/app.py", _streamlit, db_hint))
    results.append(_run("fastapi/main.py", _fastapi, db_hint))
    results.append(_run("flask/app.py", _flask, "See: docker compose logs flask"))
    return results


def main() -> int:
    print("GOL651 Examples Verification")
    print("=" * 40)
    results = run_checks()
    _print(results)
    failed = sum(1 for r in results if not r[1])
    print("=" * 40)
    print(f"Summary: {len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
