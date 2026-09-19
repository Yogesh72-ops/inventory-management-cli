"""
seed_demo.py
Populates the database with a handful of realistic rows so anyone
cloning the repo can immediately explore it (and so your README
screenshots have real data in them).

Run with: python src/seed_demo.py
"""

from database import init_db
import models


def run():
    init_db(force=True)

    s1 = models.add_supplier("TechSource Distributors", "sales@techsource.com", "9876500011")
    s2 = models.add_supplier("Global Office Supplies", "contact@globaloffice.com", "9876500022")

    p1 = models.add_product("Wireless Mouse", "Electronics", 799.0, 50, 10, s1)
    p2 = models.add_product("Mechanical Keyboard", "Electronics", 3499.0, 20, 5, s1)
    p3 = models.add_product("A4 Paper Ream", "Stationery", 299.0, 8, 15, s2)   # already low stock
    p4 = models.add_product("Whiteboard Marker Set", "Stationery", 149.0, 40, 10, s2)
    p5 = models.add_product("USB-C Hub", "Electronics", 1299.0, 3, 5, s1)      # already low stock

    c1 = models.add_customer("Ananya Rao", "ananya@example.com", "9000011111")
    c2 = models.add_customer("Rohit Sharma", "rohit@example.com", "9000022222")

    models.place_order(c1, [(p1, 2), (p2, 1)])
    models.place_order(c2, [(p3, 1), (p4, 3)])

    print("Demo data loaded successfully.")


if __name__ == "__main__":
    run()
