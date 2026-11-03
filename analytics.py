"""
Data analysis module for Personal Expense Tracker.
Uses Pandas and NumPy to compute financial metrics, aggregations, spending trends,
category breakdowns, and budget tracking metrics.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, date
from config import BUDGET_WARNING_THRESHOLD, BUDGET_DANGER_THRESHOLD


def compute_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes overall summary metrics:
    - Total Income
    - Total Expenses
    - Net Balance
    - Savings Rate (%)
    - Total Transactions
    - Average Expense
    - Highest Single Expense
    """
    if df.empty:
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_balance": 0.0,
            "savings_rate": 0.0,
            "transaction_count": 0,
            "avg_expense": 0.0,
            "max_expense": 0.0,
            "avg_daily_expense": 0.0,
        }

    income_df = df[df["type"] == "Income"]
    expense_df = df[df["type"] == "Expense"]

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0
    total_expenses = float(expense_df["amount"].sum()) if not expense_df.empty else 0.0
    net_balance = total_income - total_expenses

    savings_rate = (net_balance / total_income * 100.0) if total_income > 0 else 0.0

    avg_expense = float(expense_df["amount"].mean()) if not expense_df.empty else 0.0
    max_expense = float(expense_df["amount"].max()) if not expense_df.empty else 0.0

    # Calculate average daily expense over distinct active days
    if not expense_df.empty and "date" in expense_df.columns:
        num_days = expense_df["date"].dt.date.nunique()
        avg_daily_expense = total_expenses / num_days if num_days > 0 else total_expenses
    else:
        avg_daily_expense = 0.0

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(net_balance, 2),
        "savings_rate": round(savings_rate, 1),
        "transaction_count": len(df),
        "avg_expense": round(avg_expense, 2),
        "max_expense": round(max_expense, 2),
        "avg_daily_expense": round(avg_daily_expense, 2),
    }


def get_category_breakdown(
    df: pd.DataFrame,
    trans_type: str = "Expense"
) -> pd.DataFrame:
    """
    Aggregates transactions by category.
    Returns DataFrame sorted by Total Amount descending with percentage share.
    """
    filtered = df[df["type"] == trans_type]
    if filtered.empty:
        return pd.DataFrame(columns=["Category", "Total", "Count", "Percentage", "Average"])

    grouped = filtered.groupby("category")["amount"].agg(
        Total="sum",
        Count="count",
        Average="mean"
    ).reset_index()

    total_sum = grouped["Total"].sum()
    grouped["Percentage"] = np.where(total_sum > 0, (grouped["Total"] / total_sum) * 100.0, 0.0)
    grouped = grouped.rename(columns={"category": "Category"})
    grouped = grouped.sort_values(by="Total", ascending=False).reset_index(drop=True)

    grouped["Total"] = grouped["Total"].round(2)
    grouped["Average"] = grouped["Average"].round(2)
    grouped["Percentage"] = grouped["Percentage"].round(1)

    return grouped


def get_highest_spending_category(df: pd.DataFrame) -> Tuple[Optional[str], float, float]:
    """
    Identifies the category with the highest expenditure.
    Returns: (category_name, amount, percentage)
    """
    cat_df = get_category_breakdown(df, trans_type="Expense")
    if cat_df.empty:
        return None, 0.0, 0.0

    top_row = cat_df.iloc[0]
    return top_row["Category"], float(top_row["Total"]), float(top_row["Percentage"])


def get_monthly_trends(df: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """
    Computes monthly totals for Income, Expense, and Net Savings.
    If year is provided, filters for that specific year.
    """
    if df.empty:
        return pd.DataFrame(columns=["Month_Year", "Month_Num", "Year", "Income", "Expense", "Net_Savings"])

    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["date"]):
        data["date"] = pd.to_datetime(data["date"])

    if year:
        data = data[data["date"].dt.year == year]

    if data.empty:
        return pd.DataFrame(columns=["Month_Year", "Month_Num", "Year", "Income", "Expense", "Net_Savings"])

    data["Year"] = data["date"].dt.year
    data["Month_Num"] = data["date"].dt.month
    data["Month_Name"] = data["date"].dt.strftime("%b")
    data["Month_Year"] = data["date"].dt.strftime("%Y-%m")

    # Pivot table by Month_Year and Type
    pivot = data.pivot_table(
        index=["Year", "Month_Num", "Month_Name", "Month_Year"],
        columns="type",
        values="amount",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index()

    if "Income" not in pivot.columns:
        pivot["Income"] = 0.0
    if "Expense" not in pivot.columns:
        pivot["Expense"] = 0.0

    pivot["Net_Savings"] = pivot["Income"] - pivot["Expense"]
    pivot = pivot.sort_values(by=["Year", "Month_Num"]).reset_index(drop=True)

    pivot["Income"] = pivot["Income"].round(2)
    pivot["Expense"] = pivot["Expense"].round(2)
    pivot["Net_Savings"] = pivot["Net_Savings"].round(2)

    return pivot


def get_daily_spending_trend(
    df: pd.DataFrame,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> pd.DataFrame:
    """
    Returns daily expense and income trends for time-series visualization.
    """
    if df.empty:
        return pd.DataFrame(columns=["Date", "Expense", "Income", "Cumulative_Expense"])

    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["date"]):
        data["date"] = pd.to_datetime(data["date"])

    data["Date"] = data["date"].dt.date

    if start_date:
        data = data[data["Date"] >= start_date]
    if end_date:
        data = data[data["Date"] <= end_date]

    if data.empty:
        return pd.DataFrame(columns=["Date", "Expense", "Income", "Cumulative_Expense"])

    pivot = data.pivot_table(
        index="Date",
        columns="type",
        values="amount",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index()

    if "Expense" not in pivot.columns:
        pivot["Expense"] = 0.0
    if "Income" not in pivot.columns:
        pivot["Income"] = 0.0

    pivot = pivot.sort_values(by="Date").reset_index(drop=True)
    pivot["Cumulative_Expense"] = pivot["Expense"].cumsum().round(2)
    pivot["Expense"] = pivot["Expense"].round(2)
    pivot["Income"] = pivot["Income"].round(2)

    return pivot


def get_payment_method_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes spending breakdown across payment methods.
    """
    expense_df = df[df["type"] == "Expense"]
    if expense_df.empty:
        return pd.DataFrame(columns=["Payment_Method", "Total", "Count", "Percentage"])

    grouped = expense_df.groupby("payment_method")["amount"].agg(
        Total="sum",
        Count="count"
    ).reset_index()

    total_sum = grouped["Total"].sum()
    grouped["Percentage"] = np.where(total_sum > 0, (grouped["Total"] / total_sum) * 100.0, 0.0)
    grouped = grouped.rename(columns={"payment_method": "Payment_Method"})
    grouped = grouped.sort_values(by="Total", ascending=False).reset_index(drop=True)

    grouped["Total"] = grouped["Total"].round(2)
    grouped["Percentage"] = grouped["Percentage"].round(1)

    return grouped


def analyze_budgets(
    trans_df: pd.DataFrame,
    budget_df: pd.DataFrame,
    month: int,
    year: int
) -> pd.DataFrame:
    """
    Compares budgeted amounts with actual spending for a given month and year.
    Returns DataFrame with:
    [Category, Budget, Spent, Remaining, Percentage_Used, Status]
    Status: 'Normal' (<80%), 'Warning' (80-99.9%), 'Exceeded' (>=100%)
    """
    cols = ["Category", "Budget", "Spent", "Remaining", "Percentage_Used", "Status"]
    if budget_df.empty:
        return pd.DataFrame(columns=cols)

    # Filter transactions for this month and year
    if trans_df.empty:
        monthly_expenses = pd.DataFrame(columns=["category", "amount"])
    else:
        t_data = trans_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(t_data["date"]):
            t_data["date"] = pd.to_datetime(t_data["date"])
        
        monthly_expenses = t_data[
            (t_data["type"] == "Expense") &
            (t_data["date"].dt.month == month) &
            (t_data["date"].dt.year == year)
        ]

    # Calculate actual spending per category
    spent_by_cat = monthly_expenses.groupby("category")["amount"].sum().to_dict()
    total_spent = float(monthly_expenses["amount"].sum())

    rows = []
    for _, b_row in budget_df.iterrows():
        cat = b_row["category"]
        b_amt = float(b_row["amount"])

        if cat == "Total":
            actual = total_spent
        else:
            actual = spent_by_cat.get(cat, 0.0)

        remaining = b_amt - actual
        pct = (actual / b_amt * 100.0) if b_amt > 0 else (100.0 if actual > 0 else 0.0)

        if pct >= (BUDGET_DANGER_THRESHOLD * 100.0):
            status = "Exceeded"
        elif pct >= (BUDGET_WARNING_THRESHOLD * 100.0):
            status = "Warning"
        else:
            status = "Normal"

        rows.append({
            "Category": cat,
            "Budget": round(b_amt, 2),
            "Spent": round(actual, 2),
            "Remaining": round(remaining, 2),
            "Percentage_Used": round(pct, 1),
            "Status": status
        })

    result_df = pd.DataFrame(rows)
    # Put 'Total' at top if exists, then sorted by Percentage_Used desc
    if not result_df.empty and "Total" in result_df["Category"].values:
        total_part = result_df[result_df["Category"] == "Total"]
        other_part = result_df[result_df["Category"] != "Total"].sort_values(by="Percentage_Used", ascending=False)
        result_df = pd.concat([total_part, other_part], ignore_index=True)

    return result_df
