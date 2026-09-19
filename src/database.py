"""
database.py
Handles the SQLite connection and one-time schema initialization.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "inventory.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Return a connection with foreign keys enforced and Row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force: bool = False) -> None:
    """
    Create the database from schema.sql.
    If force=True, drops and recreates all tables (schema.sql already
    contains DROP TABLE IF EXISTS statements, so this is safe to re-run).
    """
    if DB_PATH.exists() and not force:
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_script = f.read()

    conn = get_connection()
    try:
        conn.executescript(schema_script)
        conn.commit()
        print(f"Database initialized at {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db(force=True)
