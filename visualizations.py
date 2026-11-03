"""
Visualization module for Personal Expense Tracker.
Builds high-quality interactive charts with Plotly and static figures with Matplotlib.
"""

import os
import tempfile
# Ensure a writable directory for matplotlib cache
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for web apps
import matplotlib.pyplot as plt
from config import COLOR_PALETTE, CATEGORY_COLORS


# ==========================================
# Plotly Interactive Visualizations
# ==========================================

def create_category_pie_chart(
    cat_df: pd.DataFrame,
    currency_symbol: str = "$",
    title: str = "Expense Distribution by Category"
) -> Optional[go.Figure]:
    """
    Creates an interactive donut chart showing category-wise expenses.
    """
    if cat_df.empty or "Total" not in cat_df.columns:
        return None

    # Map colors if available
    colors = [CATEGORY_COLORS.get(cat, COLOR_PALETTE[i % len(COLOR_PALETTE)]) 
              for i, cat in enumerate(cat_df["Category"])]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=cat_df["Category"],
                values=cat_df["Total"],
                hole=0.45,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Amount: " + currency_symbol + "%{value:,.2f}<br>Share: %{percent}<extra></extra>",
                textfont=dict(size=13),
            )
        ]
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, family="sans-serif")),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=50, b=40, l=20, r=20),
        height=400,
    )
    return fig


def create_monthly_trend_bar_chart(
    monthly_df: pd.DataFrame,
    currency_symbol: str = "$"
) -> Optional[go.Figure]:
    """
    Creates a grouped bar chart comparing Monthly Income vs Expenses with Net Savings line.
    """
    if monthly_df.empty:
        return None

    fig = go.Figure()

    # Income Bars
    fig.add_trace(
        go.Bar(
            x=monthly_df["Month_Year"],
            y=monthly_df["Income"],
            name="Income",
            marker_color="#2ECC71",
            hovertemplate="<b>Income</b>: " + currency_symbol + "%{y:,.2f}<extra></extra>",
        )
    )

    # Expense Bars
    fig.add_trace(
        go.Bar(
            x=monthly_df["Month_Year"],
            y=monthly_df["Expense"],
            name="Expense",
            marker_color="#E74C3C",
            hovertemplate="<b>Expense</b>: " + currency_symbol + "%{y:,.2f}<extra></extra>",
        )
    )

    # Net Savings Trend Line
    fig.add_trace(
        go.Scatter(
            x=monthly_df["Month_Year"],
            y=monthly_df["Net_Savings"],
            name="Net Savings",
            mode="lines+markers",
            line=dict(color="#3498DB", width=3, dash="dot"),
            marker=dict(size=8, color="#3498DB"),
            hovertemplate="<b>Net Savings</b>: " + currency_symbol + "%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Monthly Income vs Expenses & Net Savings", font=dict(size=18)),
        barmode="group",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title=f"Amount ({currency_symbol})"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=50, b=60, l=40, r=20),
        height=420,
    )
    return fig


def create_daily_spending_chart(
    daily_df: pd.DataFrame,
    currency_symbol: str = "$"
) -> Optional[go.Figure]:
    """
    Creates an interactive time-series line and cumulative spending chart.
    """
    if daily_df.empty:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=daily_df["Date"],
            y=daily_df["Expense"],
            name="Daily Expense",
            marker_color="#FF6B6B",
            opacity=0.6,
            hovertemplate="<b>Daily Expense</b>: " + currency_symbol + "%{y:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_df["Date"],
            y=daily_df["Cumulative_Expense"],
            name="Cumulative Expense",
            mode="lines+markers",
            line=dict(color="#8338EC", width=3),
            marker=dict(size=6),
            hovertemplate="<b>Cumulative</b>: " + currency_symbol + "%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Daily & Cumulative Spending Trend", font=dict(size=18)),
        xaxis=dict(title="Date"),
        yaxis=dict(title=f"Amount ({currency_symbol})"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(t=50, b=50, l=40, r=20),
        height=380,
    )
    return fig


def create_budget_progress_chart(
    budget_analysis_df: pd.DataFrame,
    currency_symbol: str = "$"
) -> Optional[go.Figure]:
    """
    Creates horizontal comparison bars for Budget vs Actual Spent.
    """
    if budget_analysis_df.empty:
        return None

    df = budget_analysis_df.copy()
    # Reverse so top item displays at the top of horizontal chart
    df = df.iloc[::-1].reset_index(drop=True)

    fig = go.Figure()

    # Budget bar
    fig.add_trace(
        go.Bar(
            y=df["Category"],
            x=df["Budget"],
            name="Budget",
            orientation="h",
            marker_color="#95A5A6",
            opacity=0.5,
            hovertemplate="<b>Budget</b>: " + currency_symbol + "%{x:,.2f}<extra></extra>",
        )
    )

    # Actual Spent bar
    spent_colors = []
    for status in df["Status"]:
        if status == "Exceeded":
            spent_colors.append("#E74C3C")  # Red
        elif status == "Warning":
            spent_colors.append("#F39C12")  # Amber
        else:
            spent_colors.append("#2ECC71")  # Green

    fig.add_trace(
        go.Bar(
            y=df["Category"],
            x=df["Spent"],
            name="Actual Spent",
            orientation="h",
            marker_color=spent_colors,
            hovertemplate="<b>Spent</b>: " + currency_symbol + "%{x:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Budget vs Actual Spending by Category", font=dict(size=18)),
        barmode="group",
        xaxis=dict(title=f"Amount ({currency_symbol})"),
        yaxis=dict(title="Category"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=50, b=40, l=100, r=20),
        height=max(350, len(df) * 45),
    )
    return fig


def create_payment_method_chart(
    payment_df: pd.DataFrame,
    currency_symbol: str = "$"
) -> Optional[go.Figure]:
    """
    Creates a breakdown of expenses by payment method.
    """
    if payment_df.empty:
        return None

    fig = px.bar(
        payment_df,
        x="Payment_Method",
        y="Total",
        color="Payment_Method",
        text="Total",
        color_discrete_sequence=COLOR_PALETTE,
        title="Expenses by Payment Method"
    )

    fig.update_traces(
        texttemplate=currency_symbol + "%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b>: " + currency_symbol + "%{y:,.2f}<extra></extra>"
    )

    fig.update_layout(
        xaxis=dict(title="Payment Method"),
        yaxis=dict(title=f"Total Spent ({currency_symbol})"),
        showlegend=False,
        margin=dict(t=50, b=40, l=40, r=20),
        height=360,
    )
    return fig


# ==========================================
# Matplotlib Static Figures
# ==========================================

def create_matplotlib_category_pie(
    cat_df: pd.DataFrame,
    currency_symbol: str = "$"
) -> plt.Figure:
    """
    Generates a clean Matplotlib figure for category-wise expense breakdown.
    """
    fig, ax = plt.subplots(figsize=(7, 5), dpi=100)
    if cat_df.empty or "Total" not in cat_df.columns:
        ax.text(0.5, 0.5, "No expense data to display", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    # Take top 6 categories, group remainder into 'Other' if more than 6
    if len(cat_df) > 6:
        top_cats = cat_df.iloc[:5].copy()
        other_sum = cat_df.iloc[5:]["Total"].sum()
        other_row = pd.DataFrame([{"Category": "Other Categories", "Total": other_sum}])
        plot_df = pd.concat([top_cats, other_row], ignore_index=True)
    else:
        plot_df = cat_df.copy()

    colors = [CATEGORY_COLORS.get(c, COLOR_PALETTE[i % len(COLOR_PALETTE)]) 
              for i, c in enumerate(plot_df["Category"])]

    wedges, texts, autotexts = ax.pie(
        plot_df["Total"],
        labels=plot_df["Category"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
        pctdistance=0.75,
    )

    for autotext in autotexts:
        autotext.set_color("black")
        autotext.set_fontsize(9)
        autotext.set_weight("bold")

    for text in texts:
        text.set_fontsize(10)

    ax.set_title("Expense Distribution (Matplotlib)", fontsize=13, weight="bold", pad=15)
    plt.tight_layout()
    return fig


def create_matplotlib_trend_chart(
    monthly_df: pd.DataFrame,
    currency_symbol: str = "$"
) -> plt.Figure:
    """
    Generates a Matplotlib monthly comparison figure.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    if monthly_df.empty:
        ax.text(0.5, 0.5, "No monthly data to display", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    months = monthly_df["Month_Year"]
    x = range(len(months))
    width = 0.35

    ax.bar([i - width/2 for i in x], monthly_df["Income"], width=width, label="Income", color="#2ECC71", alpha=0.9)
    ax.bar([i + width/2 for i in x], monthly_df["Expense"], width=width, label="Expense", color="#E74C3C", alpha=0.9)

    ax.plot(x, monthly_df["Net_Savings"], color="#3498DB", marker="o", linewidth=2, label="Net Savings")

    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=35, ha="right")
    ax.set_ylabel(f"Amount ({currency_symbol})")
    ax.set_title("Monthly Financial Overview (Matplotlib)", fontsize=13, weight="bold")
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    return fig
