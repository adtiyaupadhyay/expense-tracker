"""
db.py
Handles all SQLite database operations for the Expense Tracker.
Everything else (CLI, dashboard) talks to the database only through
the functions in this file.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_NAME = "expenses.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables if they do not already exist. Safe to call every time."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
        """)
        conn.commit()


def add_expense(date, category, amount, description=""):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)",
            (date, category, amount, description)
        )
        conn.commit()
        return cur.lastrowid


def delete_expense(expense_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return cur.rowcount > 0


def fetch_expenses(start_date=None, end_date=None, category=None):
    """Filtered fetch -- this is the 'SQLite-backed filtering by date range
    and category' piece. Filters are applied in SQL, not in pandas, so it
    scales to large datasets."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY date DESC"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_categories():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
        return [row["category"] for row in cur.fetchall()]


def set_budget(category, monthly_limit):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO budgets (category, monthly_limit)
            VALUES (?, ?)
            ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit
        """, (category, monthly_limit))
        conn.commit()


def get_budgets():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM budgets")
        return {row["category"]: row["monthly_limit"] for row in cur.fetchall()}


def get_current_month_spend_by_category():
    current_month = datetime.now().strftime("%Y-%m")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY category
        """, (current_month,))
        return {row["category"]: row["total"] for row in cur.fetchall()}


def check_budget_alerts():
    """Returns a list of (category, spent, limit) tuples for every category
    that has gone over its monthly budget so far this month."""
    budgets = get_budgets()
    spend = get_current_month_spend_by_category()
    alerts = []
    for category, limit in budgets.items():
        spent = spend.get(category, 0)
        if spent > limit:
            alerts.append((category, spent, limit))
    return alerts
