# Expense Tracker With Dashboard

CLI + web-based expense tracker. SQLite-backed storage, Pandas for data
shaping, Plotly/Dash for interactive charts. Pure Python.

**Everything now happens in the browser** -- adding expenses, viewing/filtering,
deleting, and setting budgets are all done through the website, not by
typing into the terminal. The terminal is only used to start the server.

## Features (all in the browser now)
- **Dashboard tab**: bar chart (spend by category), pie chart (category
  breakdown), monthly trend line, date-range + category filters, live
  budget-alert banner, summary cards
- **Add Expense tab**: a form -- date, category, amount, description --
  with a submit button and instant confirmation/budget-alert message
- **Manage Expenses tab**: a filterable, sortable table of every expense
  with checkboxes to select rows and a "Delete Selected" button
- **Budgets tab**: set/update a monthly limit per category, with a live
  status table (OK / Over Budget) for the current month
- **Auto-start**: launching the dashboard automatically opens it in your
  default browser at `http://127.0.0.1:8050`
- Auto-refreshes every 5 seconds, so changes show up without a page reload

## Files
| File | Purpose |
|---|---|
| `db.py` | All SQLite operations (schema, CRUD, filtering, budget checks) |
| `dashboard.py` | The web app -- Dash + Plotly, 4 tabs, all CRUD forms |
| `cli.py` | Optional terminal-only interface (same features, old-school way) |
| `main.py` | Entry point -- defaults to launching the website |
| `seed_data.py` | Optional: fills the DB with ~120 random sample expenses, for demos |

## Setup

```bash
pip install -r requirements.txt
```

Only 3 packages: `dash`, `pandas`, `plotly` -- sqlite3 is built into Python.

## Run

```bash
python main.py
```

Press Enter (or type `2`) at the prompt and the dashboard opens automatically
in your browser. From there, everything is click-and-type on the website:

- **Add Expense** tab -> fill the form -> click "Add Expense"
- **Manage Expenses** tab -> filter by date/category -> tick rows -> "Delete Selected"
- **Budgets** tab -> type category + limit -> "Set Budget"
- **Dashboard** tab -> charts update live based on your filters

You can also skip the menu and go straight to the dashboard:
```bash
python dashboard.py
```

If you ever want the old terminal-only experience instead:
```bash
python cli.py
```

### Want sample data first (for a demo/screenshot)?
```bash
python seed_data.py
python main.py
```
This adds ~120 random expenses across 7 categories plus 4 sample budgets
(Food, Travel, Shopping, Entertainment), so the dashboard isn't empty and
you'll immediately see a couple of "over budget" alerts to show off.

## How it's structured (for your interview prep)
- **`expenses.db`** is created automatically on first run, in the same
  folder -- two tables: `expenses` (id, date, category, amount, description)
  and `budgets` (category, monthly_limit)
- All filtering (date range, category) happens in the **SQL query itself**
  (`db.fetch_expenses`), not in pandas -- this is the "SQLite-backed
  filtering" part of the resume line
- The dashboard's tabs are built dynamically (`dcc.Tabs` + a callback that
  swaps `tabs-content.children`), so each tab's form/table is only created
  when you click it
- Every form on the website (Add Expense, Set Budget, Delete) calls straight
  into the same `db.py` functions the CLI uses -- one source of truth
- Budget alerts are computed fresh on every interaction by comparing this
  month's spend per category against the stored limit (`check_budget_alerts`)
- The whole UI refreshes every 5 seconds via `dcc.Interval`, so if you had
  two browser tabs open, changes in one show up in the other shortly after
