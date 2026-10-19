-- =============================================================================
-- GOL651 - Transactions in MySQL (run in MySQL Workbench or phpMyAdmin)
-- =============================================================================
-- Target: gol651_exercises (the practice copy). Run the blocks one at a time
-- and compare the results. Every block leaves the data as it found it.
--
-- Key ideas
--   - InnoDB transactions are ATOMIC: all statements are kept, or none.
--   - START TRANSACTION ... COMMIT    keeps the changes
--   - START TRANSACTION ... ROLLBACK  cancels them
--   - SAVEPOINT                      allows a partial rollback
-- =============================================================================

USE gol651_exercises;

-- -----------------------------------------------------------------------------
-- 1. ROLLBACK: record a sale (new order + line + stock decrease), then cancel.
-- -----------------------------------------------------------------------------
SELECT quantity_on_hand AS stock_before FROM inventory WHERE product_id = 13;

START TRANSACTION;
    INSERT INTO orders (customer_id, order_date, status)
    VALUES (3, '2026-10-15', 'pending');
    SET @new_order = LAST_INSERT_ID();

    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    VALUES (@new_order, 13, 40, 6.50);

    UPDATE inventory SET quantity_on_hand = quantity_on_hand - 40
    WHERE product_id = 13;

    -- Inside the transaction, the changes are visible to this session:
    SELECT quantity_on_hand AS stock_during FROM inventory WHERE product_id = 13;
ROLLBACK;

SELECT quantity_on_hand AS stock_after_rollback FROM inventory WHERE product_id = 13;
SELECT COUNT(*) AS orders_for_new_id FROM orders WHERE order_id = @new_order;

-- -----------------------------------------------------------------------------
-- 2. COMMIT: change a price, keep it, then restore it in a second transaction.
-- -----------------------------------------------------------------------------
START TRANSACTION;
    UPDATE products SET unit_price = unit_price * 1.10 WHERE sku = 'CAS-081';
COMMIT;
SELECT sku, unit_price AS price_after_commit FROM products WHERE sku = 'CAS-081';

START TRANSACTION;
    UPDATE products SET unit_price = 24.90 WHERE sku = 'CAS-081';
COMMIT;

-- -----------------------------------------------------------------------------
-- 3. SAVEPOINT: cancel only the second part of a transaction.
-- -----------------------------------------------------------------------------
START TRANSACTION;
    UPDATE inventory SET quantity_on_hand = quantity_on_hand + 5  WHERE product_id = 14;
    SAVEPOINT after_first_update;
    UPDATE inventory SET quantity_on_hand = quantity_on_hand + 99 WHERE product_id = 15;
    ROLLBACK TO SAVEPOINT after_first_update;    -- cancels the +99 only
    SELECT product_id, quantity_on_hand FROM inventory WHERE product_id IN (14, 15);
ROLLBACK;                                        -- cancels the +5 as well

-- -----------------------------------------------------------------------------
-- 4. A failing statement inside a transaction.
-- -----------------------------------------------------------------------------
-- The CHECK constraint ck_inventory_quantity forbids negative stock: MySQL
-- rejects the UPDATE (error 3819). In a script, ROLLBACK afterwards so that
-- nothing from the transaction is kept.
-- START TRANSACTION;
--     UPDATE inventory SET quantity_on_hand = -1 WHERE product_id = 13;
-- ROLLBACK;

-- Autocommit: outside START TRANSACTION, every statement is committed
-- immediately (@@autocommit = 1 by default).
SELECT @@autocommit AS autocommit_mode;
