"""
Database operations module for Personal Expense Tracker.
Manages SQLite database connections, table initialization, and parameterized CRUD operations.
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import pandas as pd
from config import DB_PATH, DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES


@contextmanager
def get_db_connection():
    """
    Context manager for SQLite database connection.
    Ensures safe commit and close on exit.
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency and foreign keys
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initializes the SQLite database tables and seeds default categories.
    Preserves data if tables already exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('Expense', 'Income')),
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, type)
            );
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('Expense', 'Income')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                year INTEGER NOT NULL CHECK(year >= 2000),
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(month, year, category)
            );
        """)

        # Seed default expense categories
        for cat in DEFAULT_EXPENSE_CATEGORIES:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, type, is_default)
                VALUES (?, 'Expense', 1);
            """, (cat,))

        # Seed default income categories
        for cat in DEFAULT_INCOME_CATEGORIES:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, type, is_default)
                VALUES (?, 'Income', 1);
            """, (cat,))


# ==========================================
# Category CRUD Operations
# ==========================================

def get_categories(category_type: Optional[str] = None) -> List[str]:
    """
    Fetch all category names, optionally filtered by type ('Expense' or 'Income').
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if category_type:
            cursor.execute(
                "SELECT name FROM categories WHERE type = ? ORDER BY is_default DESC, name ASC;",
                (category_type,)
            )
        else:
            cursor.execute("SELECT DISTINCT name FROM categories ORDER BY name ASC;")
        rows = cursor.fetchall()
        return [row["name"] for row in rows]


def get_categories_detail(category_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch full category records including ID, name, type, and default flag.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if category_type:
            cursor.execute(
                "SELECT id, name, type, is_default FROM categories WHERE type = ? ORDER BY is_default DESC, name ASC;",
                (category_type,)
            )
        else:
            cursor.execute(
                "SELECT id, name, type, is_default FROM categories ORDER BY type ASC, is_default DESC, name ASC;"
            )
        return [dict(row) for row in cursor.fetchall()]


def add_category(name: str, category_type: str) -> bool:
    """
    Add a custom category. Returns True on success, False if duplicate.
    """
    clean_name = name.strip().title()
    if not clean_name:
        raise ValueError("Category name cannot be empty.")
    if category_type not in ('Expense', 'Income'):
        raise ValueError("Category type must be 'Expense' or 'Income'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name, type, is_default) VALUES (?, ?, 0);",
                (clean_name, category_type)
            )
            return True
    except sqlite3.IntegrityError:
        return False


def delete_category(category_id: int) -> bool:
    """
    Delete a custom category by its ID. Cannot delete default categories.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_default FROM categories WHERE id = ?;", (category_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Category not found.")
        if row["is_default"] == 1:
            raise ValueError("Cannot delete system default categories.")
        
        cursor.execute("DELETE FROM categories WHERE id = ?;", (category_id,))
        return True


# ==========================================
# Transaction CRUD Operations
# ==========================================

def add_transaction(
    trans_type: str,
    amount: float,
    category: str,
    date_str: str,
    payment_method: str,
    description: str = ""
) -> int:
    """
    Insert a new transaction into the database using parameterized queries.
    Returns the newly created transaction ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (type, amount, category, date, payment_method, description)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (trans_type, round(float(amount), 2), category.strip(), str(date_str), payment_method.strip(), description.strip()))
        return cursor.lastrowid


def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    trans_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Query transactions with flexible filtering parameters. Returns a Pandas DataFrame.
    """
    query = "SELECT id, type, amount, category, date, payment_method, description, created_at FROM transactions WHERE 1=1"
    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(str(start_date))

    if end_date:
        query += " AND date <= ?"
        params.append(str(end_date))

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if trans_type and trans_type != "All":
        query += " AND type = ?"
        params.append(trans_type)

    if search:
        query += " AND (description LIKE ? OR category LIKE ? OR payment_method LIKE ?)"
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY date DESC, id DESC"

    if limit:
        query += f" LIMIT {int(limit)}"

    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def get_transaction_by_id(trans_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve single transaction record by ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?;", (trans_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_transaction(
    trans_id: int,
    trans_type: str,
    amount: float,
    category: str,
    date_str: str,
    payment_method: str,
    description: str = ""
) -> bool:
    """
    Update an existing transaction record by ID using parameterized query.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions
            SET type = ?, amount = ?, category = ?, date = ?, payment_method = ?, description = ?
            WHERE id = ?;
        """, (trans_type, round(float(amount), 2), category.strip(), str(date_str), payment_method.strip(), description.strip(), trans_id))
        return cursor.rowcount > 0


def delete_transaction(trans_id: int) -> bool:
    """
    Delete a transaction by ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?;", (trans_id,))
        return cursor.rowcount > 0


# ==========================================
# Budget CRUD Operations
# ==========================================

def set_budget(month: int, year: int, category: str, amount: float) -> bool:
    """
    Set or update a budget for a given month, year, and category.
    Category can be 'Total' or a specific expense category.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO budgets (month, year, category, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(month, year, category) DO UPDATE SET amount = excluded.amount;
        """, (int(month), int(year), category.strip(), round(float(amount), 2)))
        return True


def get_budgets(month: Optional[int] = None, year: Optional[int] = None) -> pd.DataFrame:
    """
    Retrieve budgets filtered by month and/or year. Returns Pandas DataFrame.
    """
    query = "SELECT id, month, year, category, amount, created_at FROM budgets WHERE 1=1"
    params = []

    if month:
        query += " AND month = ?"
        params.append(int(month))

    if year:
        query += " AND year = ?"
        params.append(int(year))

    query += " ORDER BY year DESC, month DESC, category ASC"

    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def delete_budget(budget_id: int) -> bool:
    """
    Delete a budget record by ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE id = ?;", (budget_id,))
        return cursor.rowcount > 0


# ==========================================
# Maintenance & Seed Helpers
# ==========================================

def reset_all_data() -> None:
    """
    Wipes all transactions, budgets, and custom categories. Re-initializes defaults.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS transactions;")
        cursor.execute("DROP TABLE IF EXISTS budgets;")
        cursor.execute("DROP TABLE IF EXISTS categories;")
    init_db()
