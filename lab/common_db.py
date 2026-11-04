"""
lab/common_db.py
================
Shared database helpers for all GOL651 lab models.

Three-tier role
---------------
This module is the **memory tier**.  It owns every connection to MySQL and
exposes only plain Python objects (dicts, DataFrames) to the rest of the code.
No Streamlit import lives here; no PuLP import lives here.

Usage
-----
    from lab.common_db import engine, save_result, fetch_my_results
"""

from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def engine(database: str = "gol651") -> Engine:
    """Return a SQLAlchemy engine for *database* (gol651 or gol651_exercises).

    Credentials are read from environment variables set by Docker Compose
    via the .env file — students do not need to hardcode passwords.
    """
    user     = os.environ.get("MYSQL_USER",          "gol651")
    password = os.environ.get("MYSQL_PASSWORD",      "")
    host     = os.environ.get("DB_HOST",             "mysql")
    port     = int(os.environ.get("DB_PORT",         "3306"))
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(url, pool_pre_ping=True)


# ---------------------------------------------------------------------------
# Write tier — save a solve attempt
# ---------------------------------------------------------------------------

def save_result(
    student_id:      str,
    model_name:      str,
    status:          str,
    objective_value: float | None,
    variables:       dict[str, float] | None,
    solver_params:   dict[str, Any]  | None,
    notes:           str | None = None,
) -> int:
    """Insert one row into gol651_exercises.lab_results.

    Returns the auto-generated result_id.

    Parameters
    ----------
    student_id      : student's name or number, typed at session start
    model_name      : e.g. 'lab_02_production'
    status          : 'Optimal' | 'Infeasible' | 'Unbounded' | 'Not Solved'
    objective_value : optimal objective (None when infeasible/unbounded)
    variables       : dict of decision variable name → optimal value
    solver_params   : dict with keys 'solver', 'time_limit', etc.
    notes           : optional free-text comment
    """
    eng = engine("gol651_exercises")
    sql = text("""
        INSERT INTO lab_results
            (student_id, model_name, status, objective_value,
             variables, solver_params, notes)
        VALUES
            (:student_id, :model_name, :status, :objective_value,
             :variables, :solver_params, :notes)
    """)
    with eng.begin() as conn:
        result = conn.execute(sql, {
            "student_id":      student_id,
            "model_name":      model_name,
            "status":          status,
            "objective_value": objective_value,
            "variables":       json.dumps(variables)    if variables    else None,
            "solver_params":   json.dumps(solver_params) if solver_params else None,
            "notes":           notes,
        })
        return result.lastrowid


# ---------------------------------------------------------------------------
# Read tier — query history
# ---------------------------------------------------------------------------

def fetch_my_results(student_id: str, model_name: str | None = None) -> pd.DataFrame:
    """Return past solve attempts for *student_id*, newest first.

    If *model_name* is given, filter to that model only.
    """
    eng = engine("gol651_exercises")
    where = "WHERE student_id = :sid"
    params: dict[str, Any] = {"sid": student_id}
    if model_name:
        where += " AND model_name = :model"
        params["model"] = model_name
    sql = text(f"""
        SELECT result_id, model_name, solved_at, status,
               objective_value, variables, solver_params, notes
        FROM   lab_results
        {where}
        ORDER  BY solved_at DESC
        LIMIT  50
    """)
    with eng.connect() as conn:
        return pd.read_sql(sql, conn, params=params)
