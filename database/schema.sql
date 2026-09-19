-- =========================================================
-- Inventory Management System - Database Schema (SQLite)
-- =========================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS customers;

CREATE TABLE suppliers (
    supplier_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    contact_email   TEXT,
    phone           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE products (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT,
    price           REAL NOT NULL CHECK (price >= 0),
    stock_quantity  INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level   INTEGER NOT NULL DEFAULT 10,
    supplier_id     INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE,
    phone           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER,
    order_date      TEXT DEFAULT (datetime('now')),
    status          TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','COMPLETED','CANCELLED')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

CREATE TABLE order_items (
    order_item_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL,
    product_id      INTEGER NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
);

-- Index to speed up low-stock lookups and category filters
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_orders_status ON orders(status);

-- =========================================================
-- Trigger: automatically deduct stock when an order_item
-- is inserted (simulates a sale being placed).
-- =========================================================
CREATE TRIGGER trg_deduct_stock
AFTER INSERT ON order_items
BEGIN
    UPDATE products
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
END;

-- =========================================================
-- Trigger: prevent stock from ever going negative
-- (raises an error, rolling back the insert)
-- =========================================================
CREATE TRIGGER trg_check_stock
BEFORE INSERT ON order_items
BEGIN
    SELECT
        CASE
            WHEN (SELECT stock_quantity FROM products WHERE product_id = NEW.product_id) < NEW.quantity
            THEN RAISE(ABORT, 'Insufficient stock for this product')
        END;
END;
