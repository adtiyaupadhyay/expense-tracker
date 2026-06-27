"""
main.py
Entry point for the Expense Tracker project.
"""

import os
import db


def main():
    db.init_db()

    # If running on Render (no terminal input allowed)
    if os.environ.get("RENDER"):
        from dashboard import run_dashboard
        run_dashboard(auto_open=False)
        return

    # Local machine (CLI allowed)
    print("=" * 45)
    print(" EXPENSE TRACKER WITH DASHBOARD")
    print("=" * 45)
    print("1. Start CLI (terminal-based add/view/manage)")
    print("2. Launch Web Dashboard")
    choice = input("Choose an option (1-2) [default: 2]: ").strip() or "2"

    if choice == "2":
        from dashboard import run_dashboard
        run_dashboard(auto_open=True)
    else:
        import cli
        cli.main()


if __name__ == "__main__":
    main()
