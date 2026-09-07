"""
cli.py
Menu-driven command line interface for the Inventory Management System.
Run with:  python src/cli.py
"""

import sqlite3
from database import init_db
import models


MENU = """
==================== INVENTORY MANAGEMENT ====================
 1. Add supplier
 2. Add product
 3. List products
 4. Search products by name
 5. Update stock quantity
 6. Delete product
 7. Low-stock report
 8. Add customer
 9. Place an order
10. View order history
 0. Exit
================================================================
"""


def prompt_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("Please enter a valid whole number.")


def prompt_float(msg: str) -> float:
    while True:
        try:
            return float(input(msg))
        except ValueError:
            print("Please enter a valid number.")


def print_rows(rows):
    if not rows:
        print("  (no results)")
        return
    for row in rows:
        print("  " + " | ".join(f"{k}: {row[k]}" for k in row.keys()))


def handle_choice(choice: str) -> bool:
    """Returns False when the user chooses to exit."""
    if choice == "1":
        name = input("Supplier name: ")
        email = input("Contact email (optional): ") or None
        phone = input("Phone (optional): ") or None
        sid = models.add_supplier(name, email, phone)
        print(f"Supplier added with id {sid}")

    elif choice == "2":
        name = input("Product name: ")
        category = input("Category: ")
        price = prompt_float("Price: ")
        stock = prompt_int("Initial stock: ")
        reorder = prompt_int("Reorder level (e.g. 10): ")
        sup_input = input("Supplier id (leave blank if none): ")
        supplier_id = int(sup_input) if sup_input.strip() else None
        pid = models.add_product(name, category, price, stock, reorder, supplier_id)
        print(f"Product added with id {pid}")

    elif choice == "3":
        cat = input("Filter by category (leave blank for all): ") or None
        print_rows(models.list_products(cat))

    elif choice == "4":
        kw = input("Search keyword: ")
        print_rows(models.search_products(kw))

    elif choice == "5":
        pid = prompt_int("Product id: ")
        qty = prompt_int("New stock quantity: ")
        models.update_product_stock(pid, qty)
        print("Stock updated.")

    elif choice == "6":
        pid = prompt_int("Product id to delete: ")
        models.delete_product(pid)
        print("Product deleted (if it existed).")

    elif choice == "7":
        print_rows(models.low_stock_report())

    elif choice == "8":
        name = input("Customer name: ")
        email = input("Email (optional): ") or None
        phone = input("Phone (optional): ") or None
        cid = models.add_customer(name, email, phone)
        print(f"Customer added with id {cid}")

    elif choice == "9":
        cid = prompt_int("Customer id: ")
        items = []
        print("Enter order items. Leave product id blank to finish.")
        while True:
            pid_input = input("  Product id: ")
            if not pid_input.strip():
                break
            pid = int(pid_input)
            qty = prompt_int("  Quantity: ")
            items.append((pid, qty))
        if not items:
            print("No items entered, order cancelled.")
        else:
            try:
                order_id = models.place_order(cid, items)
                print(f"Order #{order_id} placed successfully.")
            except (sqlite3.Error, ValueError) as e:
                print(f"Order failed and was rolled back: {e}")

    elif choice == "10":
        cid_input = input("Filter by customer id (blank for all): ")
        cid = int(cid_input) if cid_input.strip() else None
        print_rows(models.order_history(cid))

    elif choice == "0":
        return False

    else:
        print("Invalid option, try again.")

    return True


def main():
    init_db()
    running = True
    while running:
        print(MENU)
        choice = input("Choose an option: ").strip()
        running = handle_choice(choice)
    print("Goodbye!")


if __name__ == "__main__":
    main()
