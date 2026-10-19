#!/usr/bin/env python3
"""GOL651 - Execute every example: scripts, notebooks and applications.

Run INSIDE the Docker Python container (MySQL must be running):

    docker compose exec jupyter python scripts/verify_examples.py

What is executed
  examples/databases/*.py         each script runs to completion
  examples/optimization/*.py      LP and MILP (MILP compared across 3 solvers)
  notebooks/examples/*.ipynb      every cell, headless (outputs are NOT saved)
  marimo/demo_app.py              "marimo check" + run as a script
  streamlit/app.py + page_*.py    every page rendered (AppTest); order transactions
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


STREAMLIT_PAGES = [
    "page_tuto1_widgets.py", "page_tuto2_layout.py", "page_tuto3_state.py",
    "page_tuto4_cache.py", "page_eoq.py", "page_dashboard.py", "page_orders.py",
    "page_optimization.py",
]


def _streamlit() -> str:
    """Every page of the multipage app renders without exception or warning."""
    os.environ.setdefault("STREAMLIT_LOGGER_LEVEL", "error")
    from streamlit.testing.v1 import AppTest

    for name in list(logging.Logger.manager.loggerDict):
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)
    at = AppTest.from_file(str(ROOT / "streamlit" / "app.py"), default_timeout=120).run()
    if at.exception:
        raise RuntimeError(f"home: {at.exception[0].message}")
    for page in STREAMLIT_PAGES:
        at.switch_page(page).run()
        if at.exception:
            raise RuntimeError(f"{page}: {at.exception[0].message}")
        if at.warning:   # pages show a warning when MySQL is unreachable
            raise RuntimeError(f"{page}: warning: {at.warning[0].value}")
    return f"home + {len(STREAMLIT_PAGES)} pages rendered"


def _streamlit_orders() -> str:
    """Order transactions of the Orders page, then cleanup (gol651_exercises only)."""
    sys.path.insert(0, str(ROOT / "streamlit"))
    import common
    from sqlalchemy import text

    eng = common.engine(common.EXERCISES_DB)

    def stock(pid: int) -> int:
        with eng.connect() as conn:
            return conn.execute(text("SELECT quantity_on_hand FROM inventory "
                                     "WHERE product_id = :p"), {"p": pid}).scalar_one()

    product = 13                                    # GAN-080, large stock
    before = stock(product)
    created = []
    try:
        first = common.place_order(1, product, 5)
        created.append(first)
        if stock(product) != before - 5:
            raise AssertionError("stock was not decreased")
        try:
            common.place_order(1, product, before + 1000)
            raise AssertionError("an order larger than the stock was accepted")
        except common.OrderError:
            pass
        common.set_order_status(first, "shipped")
        try:
            common.cancel_order(first)
            raise AssertionError("a shipped order was cancelled")
        except common.OrderError:
            pass
        second = common.place_order(1, product, 7)
        created.append(second)
        common.cancel_order(second)                 # puts the 7 units back
        if stock(product) != before - 5:
            raise AssertionError("cancel did not restore the stock")
    finally:                                        # leave gol651_exercises as found
        with eng.begin() as conn:
            for order_id in created:
                conn.execute(text("""
                    UPDATE inventory AS i JOIN order_items AS oi ON oi.product_id = i.product_id
                    JOIN orders AS o ON o.order_id = oi.order_id
                    SET i.quantity_on_hand = i.quantity_on_hand + oi.quantity
                    WHERE o.order_id = :oid AND o.status <> 'cancelled'
                """), {"oid": order_id})
                conn.execute(text("DELETE FROM orders WHERE order_id = :oid"), {"oid": order_id})
    if stock(product) != before:
        raise AssertionError("cleanup did not restore the original stock")
    return "create, stock check, ship, cancel rules; data restored"


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
    results.append(_run("streamlit/app.py (all pages)", _streamlit, db_hint))
    results.append(_run("streamlit order transactions", _streamlit_orders, db_hint))
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
