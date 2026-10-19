"""GOL651 - FastAPI example API.

Started by the "web" profile:   docker compose --profile web up -d
Interactive documentation:      http://localhost:8000/docs   (Swagger UI)

Endpoints
    GET  /                    information and links
    GET  /health              service status (used by Docker and CI)
    GET  /products            products from MySQL (filters, validated limit)
    GET  /products/{sku}      one product, or 404
    POST /quote               price quote; Pydantic validates the request body

Uvicorn runs with --reload: save this file and the API restarts.
"""

# No "from __future__ import annotations" here: Pydantic and FastAPI read the
# type hints at runtime, and Python 3.12 supports "str | None" natively.

import os
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import URL, create_engine, text

app = FastAPI(
    title="GOL651 API",
    version="2.0",
    description="Teaching API on the GOL651 MySQL schema (database gol651, read-only).",
)


# --- Database -------------------------------------------------------------
@lru_cache(maxsize=1)
def engine():
    """Created once, on first use; the pool is shared by all requests."""
    url = URL.create(
        "mysql+pymysql",
        username=os.environ.get("MYSQL_USER", "gol651"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        host=os.environ.get("DB_HOST", "mysql"),       # Docker service name
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ.get("MYSQL_DATABASE", "gol651"),
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_size=5, pool_pre_ping=True,
                         connect_args={"connect_timeout": 3})


# --- Pydantic models: they validate data and document the API -------------------
class Product(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    unit_price: float = Field(ge=0, description="Price in CAD")
    is_active: bool


class QuoteLine(BaseModel):
    sku: str = Field(min_length=3, max_length=20, examples=["GAN-080"])
    quantity: int = Field(gt=0, le=10_000, description="Must be at least 1")


class QuoteRequest(BaseModel):
    customer_type: Literal["individual", "business"] = "individual"
    lines: list[QuoteLine] = Field(min_length=1)


class QuoteLineResult(BaseModel):
    sku: str
    quantity: int
    unit_price: float
    discount_pct: float
    amount: float


class Quote(BaseModel):
    lines: list[QuoteLineResult]
    total: float


PRODUCT_COLUMNS = "product_id, sku, name, category, unit_price, is_active"


# --- Endpoints --------------------------------------------------------------
@app.get("/")
def root() -> dict[str, object]:
    return {
        "service": "GOL651 API",
        "documentation": "/docs",
        "endpoints": ["/health", "/products", "/products/{sku}", "/quote"],
    }


@app.get("/health")
def health() -> dict[str, str]:
    """'status' describes the API itself; 'database' reports MySQL separately."""
    try:
        with engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 - health must answer even if MySQL is down
        database = "unavailable"
    return {"status": "ok", "database": database}


@app.get("/products", response_model=list[Product])
def list_products(
    category: str | None = Query(None, description="e.g. Sécurité, Emballage"),
    active_only: bool = True,
    limit: int = Query(50, ge=1, le=100),
) -> list[Product]:
    sql = f"SELECT {PRODUCT_COLUMNS} FROM products WHERE 1 = 1"
    params: dict[str, object] = {"limit": limit}
    if category:
        sql += " AND category = :category"   # bound parameter, never string formatting
        params["category"] = category
    if active_only:
        sql += " AND is_active = TRUE"
    sql += " ORDER BY product_id LIMIT :limit"
    with engine().connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [Product(**row) for row in rows]


@app.get("/products/{sku}", response_model=Product)
def get_product(sku: str) -> Product:
    with engine().connect() as conn:
        row = conn.execute(text(f"SELECT {PRODUCT_COLUMNS} FROM products WHERE sku = :sku"),
                           {"sku": sku}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown SKU: {sku}")
    return Product(**row)


@app.post("/quote", response_model=Quote)
def quote(request: QuoteRequest) -> Quote:
    """Business customers get 5 % off any line of 500 $ or more."""
    results = []
    for line in request.lines:
        product = get_product(line.sku)        # 404 if the SKU does not exist
        gross = product.unit_price * line.quantity
        discount = 5.0 if request.customer_type == "business" and gross >= 500 else 0.0
        results.append(QuoteLineResult(
            sku=line.sku, quantity=line.quantity, unit_price=product.unit_price,
            discount_pct=discount, amount=round(gross * (1 - discount / 100), 2)))
    return Quote(lines=results, total=round(sum(r.amount for r in results), 2))
