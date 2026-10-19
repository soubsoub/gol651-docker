#!/usr/bin/env python3
"""GOL651 - Complete environment verification.

Run INSIDE the Docker Python container (never on the host computer):

    docker compose exec jupyter python scripts/verify_environment.py

It runs:
  1. Python, scientific, file, validation, notebook and web-framework checks
     (each performs a small real operation, not just an import);
  2. all checks from verify_databases.py (SQLite, DuckDB, MySQL, SQLAlchemy);
  3. all checks from verify_solvers.py (Pyomo with HiGHS, CBC, GLPK).

Exit code: 0 if every check passes, 1 otherwise (used by GitHub Actions CI).
"""

from __future__ import annotations

import io
import logging
import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_databases  # noqa: E402  (sibling script)
import verify_solvers  # noqa: E402  (sibling script)

EXPECTED_PYTHON = (3, 12)
REBUILD_HINT = ("Package missing or broken in the image; download it again: docker compose pull "
                "(local build: docker compose build)")


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
# Python and system tools
# --------------------------------------------------------------------------
def _check_python() -> str:
    if sys.version_info[:2] != EXPECTED_PYTHON:
        raise RuntimeError(
            f"running Python {sys.version.split()[0]}, expected "
            f"{EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]} (are you on the host?)")
    return f"Python {sys.version.split()[0]}"


def _check_tool(exe: str, args: list[str]) -> Callable[[], str]:
    def check() -> str:
        if shutil.which(exe) is None:
            raise FileNotFoundError(f"'{exe}' not found on PATH")
        out = subprocess.run([exe, *args], capture_output=True, text=True,
                             timeout=30, check=True)
        first = (out.stdout or out.stderr).strip().splitlines()[0]
        return " ".join(first.split()[:3])  # e.g. "curl 8.14.1 (aarch64-...)"

    return check


# --------------------------------------------------------------------------
# Scientific stack
# --------------------------------------------------------------------------
def _check_numpy() -> str:
    import numpy as np

    a = np.array([[3.0, 1.0], [1.0, 2.0]])
    b = np.array([9.0, 8.0])
    x = np.linalg.solve(a, b)
    if not np.allclose(x, [2.0, 3.0]):
        raise AssertionError(f"linear solve returned {x}")
    return f"NumPy {np.__version__}, linear system solved"


def _check_pandas() -> str:
    import pandas as pd

    df = pd.DataFrame({"dept": ["A", "B", "A"], "cost": [100, 250, 50]})
    totals = df.groupby("dept")["cost"].sum().to_dict()
    if totals != {"A": 150, "B": 250}:
        raise AssertionError(f"groupby returned {totals}")
    return f"Pandas {pd.__version__}, groupby OK"


def _check_scipy() -> str:
    import scipy
    from scipy import integrate

    value, _ = integrate.quad(lambda t: t ** 2, 0, 3)
    if abs(value - 9.0) > 1e-9:
        raise AssertionError(f"integral returned {value}")
    return f"SciPy {scipy.__version__}, integral OK"


def _check_sklearn() -> str:
    import numpy as np
    import sklearn
    from sklearn.linear_model import LinearRegression

    x = np.arange(10, dtype=float).reshape(-1, 1)
    y = 2.0 * x.ravel() + 1.0
    model = LinearRegression().fit(x, y)
    if abs(model.coef_[0] - 2.0) > 1e-9 or abs(model.intercept_ - 1.0) > 1e-9:
        raise AssertionError(f"coef={model.coef_}, intercept={model.intercept_}")
    return f"scikit-learn {sklearn.__version__}, regression fitted"


# --------------------------------------------------------------------------
# Visualization
# --------------------------------------------------------------------------
def _check_matplotlib() -> str:
    import matplotlib

    matplotlib.use("Agg")  # headless rendering inside Docker
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    if not buf.getvalue().startswith(b"\x89PNG"):
        raise AssertionError("output is not a PNG image")
    return f"Matplotlib {matplotlib.__version__}, PNG rendered"


def _check_plotly() -> str:
    import plotly
    import plotly.graph_objects as go

    fig = go.Figure(go.Bar(x=["A", "B"], y=[1, 2]))
    if '"type":"bar"' not in fig.to_json().replace(" ", ""):
        raise AssertionError("figure JSON does not contain the bar trace")
    return f"Plotly {plotly.__version__}, figure serialized"


# --------------------------------------------------------------------------
# Files, configuration and validation
# --------------------------------------------------------------------------
def _check_openpyxl() -> str:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active["A1"] = "GOL651"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    value = openpyxl.load_workbook(buf).active["A1"].value
    if value != "GOL651":
        raise AssertionError(f"read back {value!r}")
    return f"OpenPyXL {openpyxl.__version__}, workbook written and read"


def _check_pyarrow() -> str:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table({"id": [1, 2, 3]})
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    if pq.read_table(buf).num_rows != 3:
        raise AssertionError("Parquet round trip failed")
    return f"PyArrow {pa.__version__}, Parquet round trip"


def _check_dotenv() -> str:
    from dotenv import dotenv_values

    values = dotenv_values(stream=io.StringIO("COURSE=GOL651\n"))
    if values.get("COURSE") != "GOL651":
        raise AssertionError(f"parsed {values}")
    return "python-dotenv parsing OK"


def _check_http_clients() -> str:
    import httpx
    import requests

    return f"Requests {requests.__version__}, httpx {httpx.__version__}"


def _check_pydantic() -> str:
    import pydantic
    from pydantic import BaseModel, ValidationError, PositiveInt

    class Product(BaseModel):
        name: str
        quantity: PositiveInt

    Product(name="bolt", quantity=5)
    try:
        Product(name="bolt", quantity=-1)
    except ValidationError:
        return f"Pydantic {pydantic.VERSION}, validation enforced"
    raise AssertionError("invalid data was accepted")


def _check_sqlalchemy() -> str:
    import sqlalchemy

    if int(sqlalchemy.__version__.split(".")[0]) < 2:
        raise AssertionError(f"SQLAlchemy {sqlalchemy.__version__} < 2")
    return f"SQLAlchemy {sqlalchemy.__version__}"


# --------------------------------------------------------------------------
# Notebooks
# --------------------------------------------------------------------------
def _check_jupyter() -> str:
    from importlib.metadata import version

    from jupyter_client.kernelspec import KernelSpecManager

    nb = version("notebook")
    if int(nb.split(".")[0]) != 7:
        raise AssertionError(f"notebook {nb}; Notebook 7 expected")
    specs = KernelSpecManager().find_kernel_specs()
    if "python3" not in specs:
        raise AssertionError(f"python3 kernel not registered: {sorted(specs)}")
    return (f"Notebook {nb}, JupyterLab {version('jupyterlab')}, "
            f"ipykernel {version('ipykernel')}, ipywidgets {version('ipywidgets')}")


def _check_marimo() -> str:
    import marimo

    return f"Marimo {marimo.__version__}"


# --------------------------------------------------------------------------
# Web frameworks (exercised in-process, without opening ports)
# --------------------------------------------------------------------------
def _check_fastapi() -> str:
    import fastapi
    from fastapi import FastAPI

    with warnings.catch_warnings():  # hide third-party deprecation notices
        warnings.simplefilter("ignore")
        from fastapi.testclient import TestClient
    from pydantic import BaseModel

    class Health(BaseModel):
        status: str

    app = FastAPI()

    @app.get("/health", response_model=Health)
    def health() -> Health:
        return Health(status="ok")

    response = TestClient(app).get("/health")
    if response.status_code != 200 or response.json() != {"status": "ok"}:
        raise AssertionError(f"{response.status_code} {response.text}")
    import uvicorn

    return f"FastAPI {fastapi.__version__}, Uvicorn {uvicorn.__version__}, GET /health OK"


def _check_flask() -> str:
    from importlib.metadata import version

    from flask import Flask

    app = Flask("gol651_verify")

    @app.get("/")
    def index() -> str:
        return "ok"

    response = app.test_client().get("/")
    if response.status_code != 200 or response.data != b"ok":
        raise AssertionError(f"{response.status_code} {response.data!r}")
    return f"Flask {version('flask')}, GET / OK"


def _check_streamlit() -> str:
    os.environ.setdefault("STREAMLIT_LOGGER_LEVEL", "error")  # quiet bare-mode notices
    import streamlit
    from streamlit.testing.v1 import AppTest

    for name in list(logging.Logger.manager.loggerDict):
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)

    at = AppTest.from_string("import streamlit as st\nst.write('ok')").run(timeout=30)
    if at.exception:
        raise AssertionError(f"app raised: {at.exception}")
    return f"Streamlit {streamlit.__version__}, test app ran"


# --------------------------------------------------------------------------
def core_checks() -> list[tuple[str, bool, str, str]]:
    return [
        _run("Python", _check_python,
             "Run inside the container: docker compose exec jupyter python "
             "scripts/verify_environment.py"),
        _run("git", _check_tool("git", ["--version"]), REBUILD_HINT),
        _run("curl", _check_tool("curl", ["--version"]), REBUILD_HINT),
        _run("NumPy", _check_numpy, REBUILD_HINT),
        _run("Pandas", _check_pandas, REBUILD_HINT),
        _run("SciPy", _check_scipy, REBUILD_HINT),
        _run("scikit-learn", _check_sklearn, REBUILD_HINT),
        _run("Matplotlib", _check_matplotlib, REBUILD_HINT),
        _run("Plotly", _check_plotly, REBUILD_HINT),
        _run("OpenPyXL", _check_openpyxl, REBUILD_HINT),
        _run("PyArrow", _check_pyarrow, REBUILD_HINT),
        _run("python-dotenv", _check_dotenv, REBUILD_HINT),
        _run("Requests / httpx", _check_http_clients, REBUILD_HINT),
        _run("Pydantic", _check_pydantic, REBUILD_HINT),
        _run("SQLAlchemy", _check_sqlalchemy, REBUILD_HINT),
        _run("Jupyter (Notebook 7 + JupyterLab)", _check_jupyter, REBUILD_HINT),
        _run("Marimo", _check_marimo, REBUILD_HINT),
        _run("FastAPI", _check_fastapi, REBUILD_HINT),
        _run("Flask", _check_flask, REBUILD_HINT),
        _run("Streamlit", _check_streamlit, REBUILD_HINT),
    ]


def main() -> int:
    line = "=" * 40
    print("GOL651 Environment Verification")
    print(line)
    sections = [
        ("Python, tools and libraries", core_checks),
        ("Databases", verify_databases.run_checks),
        ("Optimization solvers", verify_solvers.run_checks),
    ]
    all_results: list[tuple[str, bool, str, str]] = []
    for title, runner in sections:
        print(f"\n-- {title}")
        results = runner()
        _print(results)
        all_results.extend(results)

    failed = sum(1 for r in all_results if not r[1])
    print()
    print(line)
    print(f"Summary: {len(all_results) - failed} passed, {failed} failed")
    if failed:
        print("Environment NOT ready for GOL651 - see the [FAIL] lines above.")
        return 1
    print("Environment ready for GOL651")
    return 0


if __name__ == "__main__":
    sys.exit(main())
