"""
test_models.py
Covers the core business logic: CRUD operations, the low-stock report,
and -- most importantly -- that order placement is truly transactional
(a failed order leaves no partial data behind, and stock is only ever
deducted via the database trigger, never by application code directly).

Uses only Python's built-in `unittest` -- no external dependencies,
so `python -m unittest discover tests` works on any machine with Python 3.

Each test runs against its own temporary SQLite file (never the real
database/inventory.db), created fresh in setUp() and deleted in tearDown().
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
sys.path.insert(0, str(SRC_DIR))

import models  # noqa: E402  (import after sys.path tweak, by design)


class InventoryModelsTestCase(unittest.TestCase):
    def setUp(self):
        # Fresh temp db file per test
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp_dir.name) / "test_inventory.db"

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_script = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema_script)
        conn.commit()
        conn.close()

        # Redirect models.get_connection() to point at the temp db for this test
        db_path = self.db_path

        def fake_get_connection():
            c = sqlite3.connect(db_path)
            c.execute("PRAGMA foreign_keys = ON;")
            c.row_factory = sqlite3.Row
            return c

        self._original_get_connection = models.get_connection
        models.get_connection = fake_get_connection

    def tearDown(self):
        models.get_connection = self._original_get_connection
        self._tmp_dir.cleanup()

    # ---------------------------------------------------------------- tests

    def test_add_and_list_products(self):
        models.add_product("Wireless Mouse", "Electronics", 799.0, 50, 10)
        models.add_product("Notebook", "Stationery", 49.0, 100, 20)

        products = models.list_products()
        names = [p["name"] for p in products]

        self.assertEqual(len(products), 2)
        self.assertIn("Wireless Mouse", names)
        self.assertIn("Notebook", names)

    def test_search_products_matches_substring(self):
        models.add_product("Mechanical Keyboard", "Electronics", 3499.0, 20, 5)
        results = models.search_products("key")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Mechanical Keyboard")

    def test_low_stock_report_flags_items_at_or_below_reorder_level(self):
        models.add_product("USB-C Hub", "Electronics", 1299.0, 3, 5)   # low
        models.add_product("Yoga Mat", "Fitness", 999.0, 40, 10)        # fine

        low_stock_names = [p["name"] for p in models.low_stock_report()]
        self.assertIn("USB-C Hub", low_stock_names)
        self.assertNotIn("Yoga Mat", low_stock_names)

    def test_place_order_deducts_stock_via_trigger(self):
        pid = models.add_product("Notebook", "Stationery", 49.0, 100, 20)
        cid = models.add_customer("Ananya Rao", "ananya@example.com")

        models.place_order(cid, [(pid, 5)])

        remaining = models.list_products()[0]["stock_quantity"]
        self.assertEqual(remaining, 95)

    def test_place_order_rolls_back_fully_on_insufficient_stock(self):
        """
        Order two items: the first has enough stock, the second doesn't.
        The whole order (including the first, otherwise-valid item) must
        roll back -- no partial order, no partial stock deduction.
        """
        p1 = models.add_product("Notebook", "Stationery", 49.0, 100, 20)
        p2 = models.add_product("USB-C Hub", "Electronics", 1299.0, 2, 5)  # only 2 in stock
        cid = models.add_customer("Rohit Sharma", "rohit@example.com")

        with self.assertRaises(sqlite3.Error):
            models.place_order(cid, [(p1, 5), (p2, 10)])  # asking for 10, only 2 available

        stock = {p["name"]: p["stock_quantity"] for p in models.list_products()}
        self.assertEqual(stock["Notebook"], 100)   # untouched -- rollback worked
        self.assertEqual(stock["USB-C Hub"], 2)    # untouched

        self.assertEqual(len(models.order_history()), 0)  # no dangling order left behind

    def test_delete_product_removes_it(self):
        pid = models.add_product("Sticky Notes", "Stationery", 29.0, 60, 10)
        models.delete_product(pid)
        self.assertEqual(models.list_products(), [])


if __name__ == "__main__":
    unittest.main()
