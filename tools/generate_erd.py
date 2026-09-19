"""
generate_erd.py (dev tool, not part of the app)
Draws a simple ER diagram of the schema and saves it to docs/erd.png.
Run with: python tools/generate_erd.py
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)

TABLES = {
    "suppliers": {
        "pos": (0.5, 6.5),
        "fields": ["supplier_id (PK)", "name", "contact_email", "phone"],
    },
    "products": {
        "pos": (4, 6.5),
        "fields": ["product_id (PK)", "name", "category", "price",
                   "stock_quantity", "reorder_level", "supplier_id (FK)"],
    },
    "customers": {
        "pos": (8.5, 6.5),
        "fields": ["customer_id (PK)", "name", "email", "phone"],
    },
    "orders": {
        "pos": (8.5, 2.5),
        "fields": ["order_id (PK)", "customer_id (FK)", "order_date", "status"],
    },
    "order_items": {
        "pos": (4, 2.5),
        "fields": ["order_item_id (PK)", "order_id (FK)",
                   "product_id (FK)", "quantity", "unit_price"],
    },
}

BOX_WIDTH = 2.6
LINE_HEIGHT = 0.32


def draw_table(ax, name, x, y, fields):
    height = 0.5 + LINE_HEIGHT * len(fields)
    box = FancyBboxPatch(
        (x, y - height), BOX_WIDTH, height,
        boxstyle="round,pad=0.05,rounding_size=0.08",
        linewidth=1.4, edgecolor="#2C3E50", facecolor="#EAF2F8",
    )
    ax.add_patch(box)

    ax.text(x + BOX_WIDTH / 2, y - 0.3, name, ha="center", va="top",
             fontsize=11, fontweight="bold", color="#1B2631")
    ax.plot([x + 0.1, x + BOX_WIDTH - 0.1], [y - 0.45, y - 0.45],
            color="#2C3E50", linewidth=1)

    for i, field in enumerate(fields):
        fy = y - 0.45 - LINE_HEIGHT * (i + 0.8)
        weight = "bold" if "(PK)" in field or "(FK)" in field else "normal"
        ax.text(x + 0.15, fy, field, ha="left", va="top",
                fontsize=8.5, fontweight=weight, color="#212F3C")

    return x, y, height


def main():
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Inventory Management CLI - Entity Relationship Diagram",
                 fontsize=13, fontweight="bold", pad=15)

    boxes = {}
    for name, info in TABLES.items():
        x, y = info["pos"]
        boxes[name] = draw_table(ax, name, x, y, info["fields"])

    def connect(t1, t2, label=""):
        x1, y1, h1 = boxes[t1]
        x2, y2, h2 = boxes[t2]
        c1 = (x1 + BOX_WIDTH / 2, y1 - h1)
        c2 = (x2 + BOX_WIDTH / 2, y2)
        if y1 == y2:  # same row -> connect at mid-height sides
            c1 = (x1 + BOX_WIDTH, y1 - h1 / 2)
            c2 = (x2, y2 - h2 / 2)
        ax.annotate(
            "", xy=c2, xytext=c1,
            arrowprops=dict(arrowstyle="-|>", color="#7B241C", lw=1.4),
        )
        if label:
            mx, my = (c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2
            ax.text(mx, my + 0.1, label, fontsize=8, color="#7B241C",
                    ha="center", style="italic")

    connect("suppliers", "products", "1 -- N")
    connect("customers", "orders", "1 -- N")
    connect("orders", "order_items", "1 -- N")
    connect("products", "order_items", "1 -- N")

    plt.tight_layout()
    out_path = DOCS_DIR / "erd.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
