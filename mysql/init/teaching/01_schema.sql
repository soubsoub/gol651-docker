-- =============================================================================
-- GOL651 - Teaching schema: distribution company (structure)
-- =============================================================================
-- Loaded automatically into BOTH databases on first start:
--   gol651            reference copy (keep it intact)
--   gol651_exercises  practice copy (modify or break it freely)
--
-- The file has no USE statement: the target database is chosen by the caller.
-- It is idempotent: existing views and tables are dropped first, so running
-- it again restores a clean structure (see README, "Restore gol651_exercises").
--
-- Relationships demonstrated
--   one-to-one   : products  1 --- 1  inventory
--   one-to-many  : customers 1 --- N  orders
--   many-to-many : orders    N --- M  products   (through order_items)
--                  products  N --- M  suppliers  (through product_suppliers)
--
-- Naming convention for constraints (they appear in error messages):
--   pk_<table>  fk_<table>_<referenced>  uq_<table>_<column>  ck_<table>_<rule>
-- =============================================================================

SET NAMES utf8mb4;

-- --- Drop existing objects (views first, then children before parents) -------
DROP VIEW IF EXISTS v_customer_sales;
DROP VIEW IF EXISTS v_low_stock;
DROP VIEW IF EXISTS v_order_totals;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS product_suppliers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS customers;

-- --- customers -----------------------------------------------------------------
CREATE TABLE customers (
    customer_id    INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    first_name     VARCHAR(50)   NOT NULL,
    last_name      VARCHAR(50)   NOT NULL,
    company_name   VARCHAR(100)  NULL,                 -- NULL for individuals
    email          VARCHAR(120)  NOT NULL,
    phone          VARCHAR(20)   NULL,
    city           VARCHAR(60)   NOT NULL,
    province       CHAR(2)       NOT NULL DEFAULT 'QC',
    customer_type  VARCHAR(10)   NOT NULL DEFAULT 'individual',
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_customers         PRIMARY KEY (customer_id),
    CONSTRAINT uq_customers_email   UNIQUE (email),
    CONSTRAINT ck_customers_type    CHECK (customer_type IN ('individual', 'business')),
    CONSTRAINT ck_customers_company CHECK (customer_type = 'individual' OR company_name IS NOT NULL),
    INDEX idx_customers_city (city)
) ENGINE = InnoDB;

-- --- suppliers -----------------------------------------------------------------
CREATE TABLE suppliers (
    supplier_id    INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name           VARCHAR(100)  NOT NULL,
    contact_email  VARCHAR(120)  NULL,
    city           VARCHAR(60)   NOT NULL,
    province       CHAR(2)       NOT NULL DEFAULT 'QC',
    CONSTRAINT pk_suppliers       PRIMARY KEY (supplier_id),
    CONSTRAINT uq_suppliers_name  UNIQUE (name),
    CONSTRAINT uq_suppliers_email UNIQUE (contact_email)
) ENGINE = InnoDB;

-- --- products ------------------------------------------------------------------
CREATE TABLE products (
    product_id   INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    sku          VARCHAR(20)    NOT NULL,
    name         VARCHAR(100)   NOT NULL,
    category     VARCHAR(40)    NOT NULL,
    unit_price   DECIMAL(10, 2) NOT NULL,
    is_active    BOOLEAN        NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_products        PRIMARY KEY (product_id),
    CONSTRAINT uq_products_sku    UNIQUE (sku),
    CONSTRAINT ck_products_price  CHECK (unit_price >= 0),
    INDEX idx_products_category (category)
) ENGINE = InnoDB;

-- --- product_suppliers (many-to-many: products <-> suppliers) --------------------
CREATE TABLE product_suppliers (
    product_id      INT UNSIGNED      NOT NULL,
    supplier_id     INT UNSIGNED      NOT NULL,
    supplier_cost   DECIMAL(10, 2)    NOT NULL,
    lead_time_days  SMALLINT UNSIGNED NOT NULL DEFAULT 7,
    is_preferred    BOOLEAN           NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_product_suppliers           PRIMARY KEY (product_id, supplier_id),
    CONSTRAINT fk_product_suppliers_products  FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE CASCADE,
    CONSTRAINT fk_product_suppliers_suppliers FOREIGN KEY (supplier_id)
        REFERENCES suppliers (supplier_id) ON DELETE RESTRICT,
    CONSTRAINT ck_product_suppliers_cost      CHECK (supplier_cost >= 0),
    CONSTRAINT ck_product_suppliers_lead      CHECK (lead_time_days BETWEEN 1 AND 120),
    INDEX idx_product_suppliers_supplier (supplier_id)
) ENGINE = InnoDB;

-- --- inventory (one-to-one with products) ------------------------------------------
CREATE TABLE inventory (
    product_id        INT UNSIGNED NOT NULL,
    location          VARCHAR(20)  NOT NULL,
    quantity_on_hand  INT          NOT NULL DEFAULT 0,
    reorder_level     INT          NOT NULL DEFAULT 10,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_inventory           PRIMARY KEY (product_id),
    CONSTRAINT fk_inventory_products  FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE CASCADE,
    CONSTRAINT ck_inventory_quantity  CHECK (quantity_on_hand >= 0),
    CONSTRAINT ck_inventory_reorder   CHECK (reorder_level >= 0)
) ENGINE = InnoDB;

-- --- orders (one-to-many: customers -> orders) --------------------------------------
CREATE TABLE orders (
    order_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id   INT UNSIGNED NOT NULL,
    order_date    DATE         NOT NULL,
    shipped_date  DATE         NULL,
    status        VARCHAR(12)  NOT NULL DEFAULT 'pending',
    CONSTRAINT pk_orders            PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customers  FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id) ON DELETE RESTRICT,
    CONSTRAINT ck_orders_status     CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled')),
    CONSTRAINT ck_orders_dates      CHECK (shipped_date IS NULL OR shipped_date >= order_date),
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_date (order_date)
) ENGINE = InnoDB;

-- --- order_items (many-to-many: orders <-> products) ----------------------------------
CREATE TABLE order_items (
    order_id      INT UNSIGNED   NOT NULL,
    product_id    INT UNSIGNED   NOT NULL,
    quantity      INT            NOT NULL,
    unit_price    DECIMAL(10, 2) NOT NULL,     -- price at the time of the order
    discount_pct  DECIMAL(5, 2)  NOT NULL DEFAULT 0,
    CONSTRAINT pk_order_items           PRIMARY KEY (order_id, product_id),
    CONSTRAINT fk_order_items_orders    FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_products  FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE RESTRICT,
    CONSTRAINT ck_order_items_quantity  CHECK (quantity > 0),
    CONSTRAINT ck_order_items_price     CHECK (unit_price >= 0),
    CONSTRAINT ck_order_items_discount  CHECK (discount_pct BETWEEN 0 AND 100),
    INDEX idx_order_items_product (product_id)
) ENGINE = InnoDB;
