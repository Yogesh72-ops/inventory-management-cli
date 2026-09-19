"""
models.py
All CRUD / business-logic operations, kept separate from the CLI layer.
Every query is parameterized to avoid SQL injection.
"""

import sqlite3
from database import get_connection


# ---------------------------------------------------------------- Suppliers
def add_supplier(name: str, email: str = None, phone: str = None) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO suppliers (name, contact_email, phone) VALUES (?, ?, ?)",
            (name, email, phone),
        )
        return cur.lastrowid


def list_suppliers():
    conn = get_connection()
    return conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()


# ---------------------------------------------------------------- Products
def add_product(name: str, category: str, price: float, stock: int,
                 reorder_level: int = 10, supplier_id: int = None) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO products (name, category, price, stock_quantity, reorder_level, supplier_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, category, price, stock, reorder_level, supplier_id),
        )
        return cur.lastrowid


def update_product_stock(product_id: int, new_quantity: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE products SET stock_quantity = ? WHERE product_id = ?",
            (new_quantity, product_id),
        )


def delete_product(product_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))


def list_products(category: str = None):
    conn = get_connection()
    if category:
        return conn.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
        ).fetchall()
    return conn.execute("SELECT * FROM products ORDER BY name").fetchall()


def search_products(keyword: str):
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
        (f"%{keyword}%",),
    ).fetchall()


def low_stock_report():
    """Products at or below their reorder level -- a real inventory alert query."""
    conn = get_connection()
    return conn.execute(
        """SELECT p.product_id, p.name, p.stock_quantity, p.reorder_level, s.name AS supplier
           FROM products p
           LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
           WHERE p.stock_quantity <= p.reorder_level
           ORDER BY p.stock_quantity ASC"""
    ).fetchall()


# ---------------------------------------------------------------- Customers
def add_customer(name: str, email: str = None, phone: str = None) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
            (name, email, phone),
        )
        return cur.lastrowid


# ---------------------------------------------------------------- Orders
def place_order(customer_id: int, items: list[tuple[int, int]]) -> int:
    """
    items: list of (product_id, quantity) tuples.
    Wrapped in a single transaction: if any item fails (e.g. insufficient
    stock trigger fires), the whole order rolls back -- nothing is left
    half-applied.
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        cur = conn.execute(
            "INSERT INTO orders (customer_id, status) VALUES (?, 'COMPLETED')",
            (customer_id,),
        )
        order_id = cur.lastrowid

        for product_id, qty in items:
            price_row = conn.execute(
                "SELECT price FROM products WHERE product_id = ?", (product_id,)
            ).fetchone()
            if price_row is None:
                raise ValueError(f"Product {product_id} does not exist")

            conn.execute(
                """INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                   VALUES (?, ?, ?, ?)""",
                (order_id, product_id, qty, price_row["price"]),
            )
        conn.commit()
        return order_id
    except (sqlite3.Error, ValueError) as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def order_history(customer_id: int = None):
    conn = get_connection()
    query = """
        SELECT o.order_id, o.order_date, o.status, c.name AS customer,
               SUM(oi.quantity * oi.unit_price) AS total_amount
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN customers c ON o.customer_id = c.customer_id
    """
    params = ()
    if customer_id:
        query += " WHERE o.customer_id = ?"
        params = (customer_id,)
    query += " GROUP BY o.order_id ORDER BY o.order_date DESC"
    return conn.execute(query, params).fetchall()
