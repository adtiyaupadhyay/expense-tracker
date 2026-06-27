"""
seed_data.py
Optional helper to populate the database with random sample expenses
and budgets, so the dashboard has something to show right away
(useful for screenshots, demos, or interview walkthroughs).

    python seed_data.py
"""

import random
from datetime import datetime, timedelta

import db

CATEGORIES = ["Food", "Travel", "Rent", "Shopping", "Entertainment", "Utilities", "Health"]


def seed(num_entries=120, days_back=180):
    db.init_db()
    today = datetime.now()
    for _ in range(num_entries):
        days_offset = random.randint(0, days_back)
        date = (today - timedelta(days=days_offset)).strftime("%Y-%m-%d")
        category = random.choice(CATEGORIES)
        amount = round(random.uniform(50, 5000), 2)
        db.add_expense(date, category, amount, description=f"Sample {category} expense")

    db.set_budget("Food", 6000)
    db.set_budget("Travel", 4000)
    db.set_budget("Shopping", 5000)
    db.set_budget("Entertainment", 2000)

    print(f"Seeded {num_entries} sample expenses and 4 sample budgets into expenses.db")


if __name__ == "__main__":
    seed()
