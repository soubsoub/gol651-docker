-- =============================================================================
-- GOL651 - Teaching schema: views
-- =============================================================================
-- SQL SECURITY INVOKER: a view runs with the privileges of the person who
-- queries it. In gol651_exercises the views are created by the course user
-- (see 02_teaching_schema.sh), so students can drop, recreate or modify them.
-- =============================================================================

SET NAMES utf8mb4;

-- Total of each order (all statuses), with a 2-decimal amount after discount.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_order_totals AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,
    COUNT(*)                                                           AS line_count,
    SUM(oi.quantity)                                                   AS total_units,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100)), 2) AS order_total
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.customer_id, o.order_date, o.status;

-- Sales per customer, excluding cancelled orders; customers without orders
-- appear with 0 (LEFT JOIN).
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_customer_sales AS
SELECT
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name)  AS customer_name,
    c.company_name,
    c.city,
    COUNT(t.order_id)                       AS order_count,
    COALESCE(SUM(t.order_total), 0)         AS total_sales
FROM customers AS c
LEFT JOIN v_order_totals AS t
       ON t.customer_id = c.customer_id
      AND t.status <> 'cancelled'
GROUP BY c.customer_id, c.first_name, c.last_name, c.company_name, c.city;

-- Products whose stock is at or below the reorder level, with the preferred
-- supplier and its lead time.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_low_stock AS
SELECT
    p.product_id,
    p.sku,
    p.name,
    i.location,
    i.quantity_on_hand,
    i.reorder_level,
    s.name            AS preferred_supplier,
    ps.lead_time_days
FROM products AS p
JOIN inventory AS i
       ON i.product_id = p.product_id
LEFT JOIN product_suppliers AS ps
       ON ps.product_id = p.product_id
      AND ps.is_preferred = TRUE
LEFT JOIN suppliers AS s
       ON s.supplier_id = ps.supplier_id
WHERE p.is_active = TRUE
  AND i.quantity_on_hand <= i.reorder_level;
