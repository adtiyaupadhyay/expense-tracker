"""
cli.py
Command-line interface for the Expense Tracker.
Run `python main.py` and choose option 1, or run this file directly.
"""

from datetime import datetime
import db


def prompt_date(prompt_text, default_today=False):
    while True:
        raw = input(prompt_text).strip()
        if not raw and default_today:
            return datetime.now().strftime("%Y-%m-%d")
        if not raw:
            return None
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def add_expense_flow():
    print("\n--- Add Expense ---")
    date = prompt_date("Date (YYYY-MM-DD) [leave blank for today]: ", default_today=True)
    category = input("Category (e.g. Food, Travel, Rent): ").strip().title()
    while True:
        try:
            amount = float(input("Amount: ").strip())
            break
        except ValueError:
            print("Please enter a valid number.")
    description = input("Description (optional): ").strip()

    expense_id = db.add_expense(date, category, amount, description)
    print(f"Expense added with ID {expense_id}.")

    # Budget-threshold alert check, fires immediately after adding
    for cat, spent, limit in db.check_budget_alerts():
        if cat == category:
            print(f"\u26a0 Budget Alert: You have spent \u20b9{spent:.2f} in '{cat}' "
                  f"this month, exceeding your budget of \u20b9{limit:.2f}!")


def view_expenses_flow():
    print("\n--- View Expenses ---")
    print("Leave filters blank to skip them.")
    start_date = prompt_date("Start date (YYYY-MM-DD): ")
    end_date = prompt_date("End date (YYYY-MM-DD): ")
    category = input("Category: ").strip().title() or None

    expenses = db.fetch_expenses(start_date, end_date, category)
    if not expenses:
        print("No expenses found for the given filters.")
        return

    total = 0
    print(f"\n{'ID':<5}{'Date':<12}{'Category':<15}{'Amount':<10}{'Description'}")
    print("-" * 65)
    for exp in expenses:
        print(f"{exp['id']:<5}{exp['date']:<12}{exp['category']:<15}"
              f"{exp['amount']:<10.2f}{exp['description'] or ''}")
        total += exp['amount']
    print("-" * 65)
    print(f"Total: \u20b9{total:.2f}  ({len(expenses)} entries)")


def delete_expense_flow():
    print("\n--- Delete Expense ---")
    try:
        expense_id = int(input("Enter expense ID to delete: ").strip())
    except ValueError:
        print("Invalid ID.")
        return
    if db.delete_expense(expense_id):
        print("Expense deleted.")
    else:
        print("No expense found with that ID.")


def set_budget_flow():
    print("\n--- Set Monthly Budget ---")
    category = input("Category: ").strip().title()
    try:
        limit = float(input("Monthly limit (\u20b9): ").strip())
    except ValueError:
        print("Invalid amount.")
        return
    db.set_budget(category, limit)
    print(f"Budget for '{category}' set to \u20b9{limit:.2f} per month.")


def view_budget_status_flow():
    print("\n--- Budget Status (This Month) ---")
    budgets = db.get_budgets()
    if not budgets:
        print("No budgets set yet.")
        return
    spend = db.get_current_month_spend_by_category()
    print(f"{'Category':<15}{'Spent':<14}{'Limit':<14}{'Status'}")
    print("-" * 55)
    for category, limit in budgets.items():
        spent = spend.get(category, 0)
        status = "\u26a0 OVER BUDGET" if spent > limit else "OK"
        print(f"{category:<15}\u20b9{spent:<13.2f}\u20b9{limit:<13.2f}{status}")


def launch_dashboard_flow():
    print("\nLaunching web dashboard... it will open in your browser automatically.")
    print("(Go back to this terminal and press CTRL+C to stop the server.)")
    import dashboard
    dashboard.run_dashboard(auto_open=True)


MENU = """
========== EXPENSE TRACKER ==========
1. Add Expense
2. View Expenses (with filters)
3. Delete Expense
4. Set Monthly Budget
5. View Budget Status
6. Launch Web Dashboard
7. Exit
======================================
"""


def main():
    db.init_db()
    while True:
        print(MENU)
        choice = input("Choose an option (1-7): ").strip()
        if choice == "1":
            add_expense_flow()
        elif choice == "2":
            view_expenses_flow()
        elif choice == "3":
            delete_expense_flow()
        elif choice == "4":
            set_budget_flow()
        elif choice == "5":
            view_budget_status_flow()
        elif choice == "6":
            launch_dashboard_flow()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
