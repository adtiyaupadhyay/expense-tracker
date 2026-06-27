"""
main.py
Entry point for the Expense Tracker With Dashboard project.

    python main.py

lets you choose between the CLI (add/view/manage expenses, set budgets)
and the auto-launching web dashboard (bar chart, pie chart, monthly trend,
filters, budget alerts).
"""

import db


def main():
    db.init_db()
    print("=" * 45)
    print(" EXPENSE TRACKER WITH DASHBOARD")
    print("=" * 45)
    print("1. Start CLI (terminal-based add/view/manage)")
    print("2. Launch Web Dashboard (recommended -- add/view/delete/budgets all in browser)")
    choice = input("Choose an option (1-2) [default: 2]: ").strip() or "2"

    if choice == "2":
        import dashboard
        print("\nStarting dashboard... it will open automatically in your browser.")
        dashboard.run_dashboard(auto_open=True)
    else:
        import cli
        cli.main()


if __name__ == "__main__":
    main()
