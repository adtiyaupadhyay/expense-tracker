"""
dashboard.py
Full web-based Expense Tracker. Everything happens in the browser now:
  - Tab 1: Dashboard      -> bar chart, pie chart, monthly trend, budget alerts
  - Tab 2: Add Expense    -> form (date, category, amount, description)
  - Tab 3: Manage Expenses-> filterable table + delete selected rows
  - Tab 4: Budgets        -> set/update monthly budget per category + status table

The terminal is only used to start the server (`python main.py` or
`python dashboard.py`). After that, the user does everything on the
website at http://127.0.0.1:8050 -- no typing into the Run/output panel.

Run directly with `python dashboard.py`, or via main.py.
"""

import threading
import webbrowser

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output, State, ctx

import db


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_dataframe():
    expenses = db.fetch_expenses()
    if not expenses:
        return pd.DataFrame(columns=["id", "date", "category", "amount", "description"])
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_budget_rows():
    """Rows for the Budgets tab status table: one per category that has
    EITHER a budget set OR spending this month (so new categories show up
    even before a budget is set, and budgeted categories show 0 if unused)."""
    budgets = db.get_budgets()
    spend = db.get_current_month_spend_by_category()
    all_categories = sorted(set(budgets.keys()) | set(spend.keys()) | set(db.get_categories()))
    rows = []
    for cat in all_categories:
        limit = budgets.get(cat)
        spent = spend.get(cat, 0)
        if limit is None:
            status = "No budget set"
        elif spent > limit:
            status = "\u26a0 OVER BUDGET"
        else:
            status = "OK"
        rows.append({
            "category": cat,
            "spent": round(spent, 2),
            "limit": limit if limit is not None else "-",
            "status": status,
        })
    return rows


# ---------------------------------------------------------------------------
# Tab layouts (pure functions -- testable without running the server)
# ---------------------------------------------------------------------------

def render_dashboard_tab():
    df_all = load_dataframe()
    categories = ["All"] + sorted(df_all["category"].unique().tolist()) if not df_all.empty else ["All"]
    min_date = df_all["date"].min() if not df_all.empty else pd.Timestamp.now()
    max_date = df_all["date"].max() if not df_all.empty else pd.Timestamp.now()

    return html.Div([
        html.Div(id="alert-banner", style={"marginBottom": "20px"}),

        html.Div(style={"display": "flex", "gap": "30px", "marginBottom": "30px",
                         "justifyContent": "center", "flexWrap": "wrap"}, children=[
            html.Div([
                html.Label("Date Range"),
                dcc.DatePickerRange(
                    id="date-range",
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                )
            ]),
            html.Div([
                html.Label("Category"),
                dcc.Dropdown(
                    id="category-filter",
                    options=[{"label": c, "value": c} for c in categories],
                    value="All",
                    style={"width": "220px"}
                )
            ]),
        ]),

        html.Div(id="summary-cards", style={"display": "flex", "gap": "20px",
                                             "justifyContent": "center", "marginBottom": "30px",
                                             "flexWrap": "wrap"}),

        html.Div(style={"display": "flex", "flexWrap": "wrap", "gap": "20px",
                         "justifyContent": "center"}, children=[
            dcc.Graph(id="bar-chart", style={"width": "45%", "minWidth": "400px"}),
            dcc.Graph(id="pie-chart", style={"width": "45%", "minWidth": "400px"}),
        ]),

        dcc.Graph(id="trend-line"),
    ])


def render_add_expense_tab():
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    return html.Div(style={"maxWidth": "420px", "margin": "30px auto"}, children=[
        html.H3("Add a New Expense"),

        html.Label("Date"),
        dcc.DatePickerSingle(id="add-date", date=today, display_format="YYYY-MM-DD",
                              style={"marginBottom": "15px", "display": "block"}),

        html.Label("Category"),
        dcc.Input(id="add-category", type="text", placeholder="e.g. Food, Travel, Rent",
                   style={"width": "100%", "marginBottom": "15px", "padding": "8px"}),

        html.Label("Amount (\u20b9)"),
        dcc.Input(id="add-amount", type="number", placeholder="e.g. 250.50",
                   style={"width": "100%", "marginBottom": "15px", "padding": "8px"}),

        html.Label("Description (optional)"),
        dcc.Input(id="add-description", type="text", placeholder="e.g. Lunch with friends",
                   style={"width": "100%", "marginBottom": "20px", "padding": "8px"}),

        html.Button("Add Expense", id="add-expense-btn", n_clicks=0, style={
            "padding": "10px 20px", "backgroundColor": "#2e7d32", "color": "white",
            "border": "none", "borderRadius": "6px", "cursor": "pointer", "fontWeight": "bold"
        }),

        html.Div(id="add-expense-status", style={"marginTop": "18px", "fontWeight": "bold"}),
    ])


def render_manage_expenses_tab():
    categories = ["All"] + db.get_categories()
    return html.Div(style={"maxWidth": "900px", "margin": "20px auto"}, children=[
        html.H3("View & Delete Expenses"),

        html.Div(style={"display": "flex", "gap": "30px", "marginBottom": "20px",
                         "flexWrap": "wrap"}, children=[
            html.Div([
                html.Label("Date Range"),
                dcc.DatePickerRange(id="manage-date-range"),
            ]),
            html.Div([
                html.Label("Category"),
                dcc.Dropdown(id="manage-category-filter",
                             options=[{"label": c, "value": c} for c in categories],
                             value="All", style={"width": "200px"}),
            ]),
        ]),

        dash_table.DataTable(
            id="expenses-table",
            columns=[
                {"name": "ID", "id": "id"},
                {"name": "Date", "id": "date"},
                {"name": "Category", "id": "category"},
                {"name": "Amount (\u20b9)", "id": "amount"},
                {"name": "Description", "id": "description"},
            ],
            data=[],
            row_selectable="multi",
            selected_rows=[],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f0f0f0"},
        ),

        html.Button("\U0001F5D1 Delete Selected", id="delete-selected-btn", n_clicks=0, style={
            "marginTop": "15px", "padding": "10px 20px", "backgroundColor": "#b00020",
            "color": "white", "border": "none", "borderRadius": "6px", "cursor": "pointer",
            "fontWeight": "bold"
        }),

        html.Div(id="manage-status", style={"marginTop": "15px", "fontWeight": "bold"}),
    ])


def render_budget_tab():
    return html.Div(style={"maxWidth": "700px", "margin": "20px auto"}, children=[
        html.H3("Set / Update Monthly Budget"),

        html.Div(style={"display": "flex", "gap": "15px", "alignItems": "flex-end",
                         "flexWrap": "wrap", "marginBottom": "20px"}, children=[
            html.Div([
                html.Label("Category"),
                dcc.Input(id="budget-category", type="text", placeholder="e.g. Food",
                           style={"padding": "8px"}),
            ]),
            html.Div([
                html.Label("Monthly Limit (\u20b9)"),
                dcc.Input(id="budget-limit", type="number", placeholder="e.g. 5000",
                           style={"padding": "8px"}),
            ]),
            html.Button("Set Budget", id="set-budget-btn", n_clicks=0, style={
                "padding": "10px 20px", "backgroundColor": "#1565c0", "color": "white",
                "border": "none", "borderRadius": "6px", "cursor": "pointer", "fontWeight": "bold"
            }),
        ]),

        html.Div(id="budget-status", style={"marginBottom": "20px", "fontWeight": "bold"}),

        html.H3("Current Budget Status (This Month)"),
        dash_table.DataTable(
            id="budget-table",
            columns=[
                {"name": "Category", "id": "category"},
                {"name": "Spent (\u20b9)", "id": "spent"},
                {"name": "Limit (\u20b9)", "id": "limit"},
                {"name": "Status", "id": "status"},
            ],
            data=build_budget_rows(),
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f0f0f0"},
            style_data_conditional=[{
                "if": {"filter_query": '{status} = "\u26a0 OVER BUDGET"'},
                "backgroundColor": "#ffe0e0", "color": "#b00020",
            }],
        ),
    ])


# ---------------------------------------------------------------------------
# Callback logic (pure functions -- testable without a running server)
# ---------------------------------------------------------------------------

def compute_dashboard_outputs(start_date, end_date, category):
    df = load_dataframe()

    if not df.empty:
        mask = pd.Series(True, index=df.index)
        if start_date:
            mask &= df["date"] >= pd.to_datetime(start_date)
        if end_date:
            mask &= df["date"] <= pd.to_datetime(end_date)
        if category and category != "All":
            mask &= df["category"] == category
        df = df[mask]

    if df.empty:
        empty_fig = px.bar(title="No data for selected filters")
        return empty_fig, empty_fig, empty_fig, "", []

    by_category = df.groupby("category", as_index=False)["amount"].sum().sort_values(
        "amount", ascending=False)
    bar_fig = px.bar(by_category, x="category", y="amount",
                      title="Spending by Category", text_auto=".2f",
                      labels={"amount": "Amount (\u20b9)", "category": "Category"})

    pie_fig = px.pie(by_category, names="category", values="amount",
                      title="Category Breakdown", hole=0.35)

    df_month = df.copy()
    df_month["month"] = df_month["date"].dt.to_period("M").astype(str)
    by_month = df_month.groupby("month", as_index=False)["amount"].sum().sort_values("month")
    trend_fig = px.line(by_month, x="month", y="amount", markers=True,
                         title="Monthly Spending Trend",
                         labels={"amount": "Amount (\u20b9)", "month": "Month"})

    alerts = db.check_budget_alerts()
    if alerts:
        alert_text = "  |  ".join(
            f"\u26a0 {cat}: \u20b9{spent:.2f} spent (limit \u20b9{limit:.2f})"
            for cat, spent, limit in alerts
        )
        banner = html.Div(alert_text, style={
            "backgroundColor": "#ffe0e0", "color": "#b00020",
            "padding": "12px", "borderRadius": "8px",
            "textAlign": "center", "fontWeight": "bold"
        })
    else:
        banner = ""

    total_spent = df["amount"].sum()
    avg_per_entry = df["amount"].mean()
    top_category = by_category.iloc[0]["category"]

    def card(title, value):
        return html.Div([
            html.Div(title, style={"fontSize": "13px", "color": "#666"}),
            html.Div(value, style={"fontSize": "22px", "fontWeight": "bold"}),
        ], style={"backgroundColor": "#f5f5f5", "padding": "16px 24px",
                   "borderRadius": "10px", "minWidth": "150px", "textAlign": "center"})

    cards = [
        card("Total Spent", f"\u20b9{total_spent:.2f}"),
        card("Entries", f"{len(df)}"),
        card("Avg / Entry", f"\u20b9{avg_per_entry:.2f}"),
        card("Top Category", top_category),
    ]

    return bar_fig, pie_fig, trend_fig, banner, cards


def handle_add_expense_logic(date, category, amount, description):
    """Returns (status_component, category_value, amount_value, description_value)."""
    if not date or not category or amount in (None, ""):
        warn = html.Div("\u26a0 Please fill in date, category, and amount.",
                         style={"color": "#b00020"})
        return warn, category, amount, description

    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        warn = html.Div("\u26a0 Amount must be a number.", style={"color": "#b00020"})
        return warn, category, amount, description

    category_clean = category.strip().title()
    expense_id = db.add_expense(date, category_clean, amount_val, (description or "").strip())

    msg_parts = [f"\u2705 Added (ID {expense_id}): {category_clean} \u2014 "
                 f"\u20b9{amount_val:.2f} on {date}"]
    over_budget = False
    for cat, spent, limit in db.check_budget_alerts():
        if cat == category_clean:
            over_budget = True
            msg_parts.append(f"\u26a0 Budget Alert: \u20b9{spent:.2f} spent in '{cat}' "
                              f"this month (limit \u20b9{limit:.2f})!")

    status = html.Div(" | ".join(msg_parts),
                       style={"color": "#b00020" if over_budget else "#1b5e20"})
    return status, "", None, ""


def handle_manage_tab_logic(start_date, end_date, category, triggered_id,
                             n_clicks_delete, selected_rows, table_data):
    """Returns (expenses_list, status_component)."""
    status = ""
    if triggered_id == "delete-selected-btn" and n_clicks_delete:
        if not selected_rows:
            status = html.Div("Select at least one row to delete.",
                               style={"color": "#b00020"})
        else:
            ids_to_delete = [table_data[i]["id"] for i in selected_rows]
            for eid in ids_to_delete:
                db.delete_expense(eid)
            status = html.Div(f"Deleted {len(ids_to_delete)} expense(s).",
                               style={"color": "#1b5e20"})

    expenses = db.fetch_expenses(start_date, end_date, category)
    return expenses, status


def handle_budget_tab_logic(triggered_id, n_clicks, category, limit):
    """Returns (status_component, rows, category_value, limit_value)."""
    status = ""
    category_val = category
    limit_val = limit

    if triggered_id == "set-budget-btn" and n_clicks:
        if not category or limit in (None, ""):
            status = html.Div("\u26a0 Enter both category and limit.",
                               style={"color": "#b00020"})
        else:
            try:
                limit_num = float(limit)
                category_clean = category.strip().title()
                db.set_budget(category_clean, limit_num)
                status = html.Div(
                    f"\u2705 Budget for '{category_clean}' set to \u20b9{limit_num:.2f}/month.",
                    style={"color": "#1b5e20"})
                category_val, limit_val = "", None
            except (TypeError, ValueError):
                status = html.Div("\u26a0 Limit must be a number.", style={"color": "#b00020"})

    rows = build_budget_rows()
    return status, rows, category_val, limit_val


# ---------------------------------------------------------------------------
# App assembly
# ---------------------------------------------------------------------------

def build_app():
    db.init_db()

    app = Dash(__name__)
    app.title = "Expense Tracker Dashboard"
    app.config.suppress_callback_exceptions = True  # tabs render components dynamically

    app.layout = html.Div(style={"fontFamily": "Arial, sans-serif", "margin": "20px"}, children=[
        html.H1("\U0001F4B0 Expense Tracker", style={"textAlign": "center"}),

        dcc.Tabs(id="tabs", value="tab-dashboard", children=[
            dcc.Tab(label="\U0001F4CA Dashboard", value="tab-dashboard"),
            dcc.Tab(label="\u2795 Add Expense", value="tab-add"),
            dcc.Tab(label="\U0001F4CB Manage Expenses", value="tab-manage"),
            dcc.Tab(label="\U0001F3AF Budgets", value="tab-budget"),
        ]),

        html.Div(id="tabs-content"),

        # Drives the periodic auto-refresh of charts/tables across all tabs
        dcc.Interval(id="refresh-interval", interval=5000, n_intervals=0),
    ])

    @app.callback(Output("tabs-content", "children"), Input("tabs", "value"))
    def render_tab(tab):
        if tab == "tab-add":
            return render_add_expense_tab()
        elif tab == "tab-manage":
            return render_manage_expenses_tab()
        elif tab == "tab-budget":
            return render_budget_tab()
        return render_dashboard_tab()

    @app.callback(
        Output("bar-chart", "figure"),
        Output("pie-chart", "figure"),
        Output("trend-line", "figure"),
        Output("alert-banner", "children"),
        Output("summary-cards", "children"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("category-filter", "value"),
        Input("refresh-interval", "n_intervals"),
    )
    def update_dashboard(start_date, end_date, category, _n):
        return compute_dashboard_outputs(start_date, end_date, category)

    @app.callback(
        Output("add-expense-status", "children"),
        Output("add-category", "value"),
        Output("add-amount", "value"),
        Output("add-description", "value"),
        Input("add-expense-btn", "n_clicks"),
        State("add-date", "date"),
        State("add-category", "value"),
        State("add-amount", "value"),
        State("add-description", "value"),
        prevent_initial_call=True,
    )
    def add_expense_callback(n_clicks, date, category, amount, description):
        return handle_add_expense_logic(date, category, amount, description)

    @app.callback(
        Output("expenses-table", "data"),
        Output("manage-status", "children"),
        Input("manage-date-range", "start_date"),
        Input("manage-date-range", "end_date"),
        Input("manage-category-filter", "value"),
        Input("refresh-interval", "n_intervals"),
        Input("delete-selected-btn", "n_clicks"),
        State("expenses-table", "selected_rows"),
        State("expenses-table", "data"),
    )
    def manage_tab_callback(start_date, end_date, category, _n, n_clicks_delete,
                             selected_rows, table_data):
        triggered_id = ctx.triggered_id
        return handle_manage_tab_logic(start_date, end_date, category, triggered_id,
                                        n_clicks_delete, selected_rows, table_data)

    @app.callback(
        Output("budget-status", "children"),
        Output("budget-table", "data"),
        Output("budget-category", "value"),
        Output("budget-limit", "value"),
        Input("set-budget-btn", "n_clicks"),
        Input("refresh-interval", "n_intervals"),
        State("budget-category", "value"),
        State("budget-limit", "value"),
    )
    def budget_tab_callback(n_clicks, _n_intervals, category, limit):
        triggered_id = ctx.triggered_id
        return handle_budget_tab_logic(triggered_id, n_clicks, category, limit)

    return app


def run_dashboard(auto_open=True, port=8050):
    """Starts the Dash server. If auto_open=True, opens the default
    browser to the dashboard URL automatically (the 'auto-start' piece)."""
    app = build_app()
    if auto_open:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(debug=False, port=port)


if __name__ == "__main__":
    run_dashboard(auto_open=False)
