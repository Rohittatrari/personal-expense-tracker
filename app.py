"""
Main Streamlit application for Personal Expense Tracker.
Combines interactive dashboard, transaction management, budget monitoring,
category customization, data visualization, and CSV export.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

import database
import transactions
import analytics
import visualizations
import sample_data
from config import (
    CURRENCIES,
    DEFAULT_CURRENCY,
    PAYMENT_METHODS,
    BUDGET_WARNING_THRESHOLD,
    BUDGET_DANGER_THRESHOLD,
)

# ==========================================
# Page Configuration & Styling
# ==========================================

st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern card styling, typography, and badges
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6c757d;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #8898aa;
    }
    .income-val { color: #2ecc71; }
    .expense-val { color: #e74c3c; }
    .balance-pos { color: #2980b9; }
    .balance-neg { color: #e74c3c; }
    .badge-normal {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-danger {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Database once
@st.cache_resource
def setup_database():
    database.init_db()
    # Check if empty, automatically seed initial demo data if database is brand new
    if not sample_data.has_sample_data():
        sample_data.seed_sample_data(force=False)
    return True

setup_database()


# ==========================================
# Sidebar Navigation & Settings
# ==========================================

st.sidebar.markdown("# 💰 Expense Tracker")
st.sidebar.caption("Smart Personal Finance & Budgeting")

selected_currency_name = st.sidebar.selectbox(
    "Select Currency",
    options=list(CURRENCIES.keys()),
    index=list(CURRENCIES.keys()).index(DEFAULT_CURRENCY),
)
curr_sym = CURRENCIES[selected_currency_name]

menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "➕ Add Transaction",
        "📋 Manage Transactions",
        "🎯 Budget Management",
        "📈 Reports & Analytics",
        "🏷️ Categories",
        "⚙️ Settings & Data",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption("💡 *Tip: Export your transactions anytime as CSV from the Manage or Settings tab.*")


# ==========================================
# VIEW: Dashboard
# ==========================================

def render_dashboard(curr_sym: str):
    st.title("📊 Financial Dashboard")
    st.caption("Real-time summary of your finances, monthly spending, and category distribution.")

    # Timeframe selector for dashboard
    col_d1, col_d2 = st.columns([2, 2])
    with col_d1:
        time_filter = st.selectbox(
            "Dashboard Timeframe",
            ["All Time", "This Month", "Last 30 Days", "This Year"],
            index=1,
        )

    today = date.today()
    start_dt, end_dt = None, None

    if time_filter == "This Month":
        start_dt = today.replace(day=1)
        end_dt = today
    elif time_filter == "Last 30 Days":
        start_dt = today - timedelta(days=30)
        end_dt = today
    elif time_filter == "This Year":
        start_dt = today.replace(month=1, day=1)
        end_dt = today

    # Fetch data
    df = database.get_transactions(start_date=start_dt, end_date=end_dt)
    metrics = analytics.compute_summary_metrics(df)

    # 1. Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Income</div>
            <div class="metric-value income-val">{curr_sym}{metrics['total_income']:,.2f}</div>
            <div class="metric-sub">Earned in period</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Expenses</div>
            <div class="metric-value expense-val">{curr_sym}{metrics['total_expenses']:,.2f}</div>
            <div class="metric-sub">Spent in period</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        bal_class = "balance-pos" if metrics["net_balance"] >= 0 else "balance-neg"
        bal_sign = "+" if metrics["net_balance"] > 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Current Net Balance</div>
            <div class="metric-value {bal_class}">{bal_sign}{curr_sym}{metrics['net_balance']:,.2f}</div>
            <div class="metric-sub">Income minus Expenses</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Savings Rate</div>
            <div class="metric-value balance-pos">{metrics['savings_rate']:.1f}%</div>
            <div class="metric-sub">{metrics['transaction_count']} total transactions</div>
        </div>
        """, unsafe_allow_html=True)

    # Quick Budget Alert for current month
    budget_df = database.get_budgets(month=today.month, year=today.year)
    if not budget_df.empty:
        all_df = database.get_transactions()
        b_analysis = analytics.analyze_budgets(all_df, budget_df, month=today.month, year=today.year)
        total_b = b_analysis[b_analysis["Category"] == "Total"]
        if not total_b.empty:
            t_row = total_b.iloc[0]
            if t_row["Status"] == "Exceeded":
                st.error(f"🚨 **Monthly Budget Alert**: You have spent **{curr_sym}{t_row['Spent']:,.2f}**, exceeding your total monthly budget of **{curr_sym}{t_row['Budget']:,.2f}** ({t_row['Percentage_Used']}%)!")
            elif t_row["Status"] == "Warning":
                st.warning(f"⚠️ **Monthly Budget Warning**: You have used **{t_row['Percentage_Used']}%** ({curr_sym}{t_row['Spent']:,.2f}) of your **{curr_sym}{t_row['Budget']:,.2f}** monthly budget.")

    # 2. Charts Section
    st.markdown("### 📈 Visual Overview")
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        cat_df = analytics.get_category_breakdown(df, trans_type="Expense")
        if not cat_df.empty:
            fig_pie = visualizations.create_category_pie_chart(cat_df, currency_symbol=curr_sym)
            if fig_pie:
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense transactions recorded for this timeframe.")

    with chart_col2:
        all_trans_df = database.get_transactions()
        monthly_df = analytics.get_monthly_trends(all_trans_df, year=today.year)
        if not monthly_df.empty:
            fig_trend = visualizations.create_monthly_trend_bar_chart(monthly_df, currency_symbol=curr_sym)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No monthly trend data available yet.")

    # 3. Recent Transactions & Quick Highlights
    st.markdown("### 🕒 Recent Activity & Insights")
    row3_c1, row3_c2 = st.columns([2, 1])

    with row3_c1:
        st.subheader("Latest 5 Transactions")
        recent_df = database.get_transactions(limit=5)
        if not recent_df.empty:
            display_recent = recent_df[["date", "type", "category", "amount", "payment_method", "description"]].copy()
            display_recent["date"] = display_recent["date"].dt.strftime("%Y-%m-%d")
            display_recent["amount"] = display_recent.apply(
                lambda r: f"+{curr_sym}{r['amount']:,.2f}" if r["type"] == "Income" else f"-{curr_sym}{r['amount']:,.2f}",
                axis=1
            )
            display_recent.columns = ["Date", "Type", "Category", "Amount", "Method", "Description"]
            st.dataframe(display_recent, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions found.")

    with row3_c2:
        st.subheader("Spending Highlights")
        top_cat, top_amt, top_pct = analytics.get_highest_spending_category(df)
        if top_cat:
            st.markdown(f"🏷️ **Top Spending Category:** `{top_cat}`")
            st.markdown(f"💸 **Total in {top_cat}:** {curr_sym}{top_amt:,.2f} ({top_pct:.1f}% of expenses)")
        st.markdown(f"📊 **Average Expense:** {curr_sym}{metrics['avg_expense']:,.2f}")
        st.markdown(f"💳 **Largest Single Expense:** {curr_sym}{metrics['max_expense']:,.2f}")
        st.markdown(f"📅 **Daily Average Expense:** {curr_sym}{metrics['avg_daily_expense']:,.2f}")


# ==========================================
# VIEW: Add Transaction
# ==========================================

def render_add_transaction(curr_sym: str):
    st.title("➕ Add New Transaction")
    st.caption("Record daily expenses and income with instant validation.")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("add_transaction_form", clear_on_submit=True):
            trans_type = st.radio(
                "Transaction Type",
                ["Expense", "Income"],
                horizontal=True,
            )

            # Fetch existing categories for selected type
            cats = database.get_categories(category_type=trans_type)
            if not cats:
                cats = ["Other"]

            form_c1, form_c2 = st.columns(2)
            with form_c1:
                amount = st.number_input(
                    f"Amount ({curr_sym}) *",
                    min_value=0.01,
                    max_value=10000000.0,
                    value=10.00,
                    step=1.00,
                    format="%.2f",
                )

            with form_c2:
                category = st.selectbox("Category *", options=cats)

            form_c3, form_c4 = st.columns(2)
            with form_c3:
                trans_date = st.date_input("Transaction Date *", value=date.today())

            with form_c4:
                payment_method = st.selectbox("Payment Method *", options=PAYMENT_METHODS)

            description = st.text_area(
                "Description / Note (Optional)",
                placeholder="e.g. Weekly grocery shopping at supermarket",
                max_chars=250,
            )

            submitted = st.form_submit_button("💾 Save Transaction", use_container_width=True)

            if submitted:
                success, msg, new_id = transactions.record_transaction(
                    trans_type=trans_type,
                    amount=amount,
                    category=category,
                    date_val=trans_date,
                    payment_method=payment_method,
                    description=description,
                )
                if success:
                    st.success(f"✅ {msg} (ID: #{new_id})")
                else:
                    st.error(f"❌ {msg}")

    with col2:
        st.info("""
        **Validation Rules:**
        - Amount must be strictly greater than 0.
        - Date must be specified (defaults to today).
        - Category and Payment Method are required.
        - Data is saved directly to the permanent SQLite database.
        """)

        st.markdown("---")
        st.subheader("Quick Add Tips")
        st.markdown("""
        - Need a new category? Head over to **🏷️ Categories** to add custom categories!
        - You can edit or delete this transaction at any time from **📋 Manage Transactions**.
        """)


# ==========================================
# VIEW: Manage Transactions
# ==========================================

def render_manage_transactions(curr_sym: str):
    st.title("📋 Manage Transactions")
    st.caption("Search, filter, view, edit, or delete transactions.")

    # 1. Filters Bar
    with st.expander("🔍 Filter & Search Transactions", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 2])

        with f_col1:
            filter_type = st.selectbox("Type", ["All", "Expense", "Income"], index=0)

        with f_col2:
            all_cats = ["All"] + database.get_categories()
            filter_cat = st.selectbox("Category", all_cats, index=0)

        with f_col3:
            today = date.today()
            date_preset = st.selectbox(
                "Date Range",
                ["All Dates", "This Month", "Last 30 Days", "This Year", "Custom Range"],
                index=0
            )

        with f_col4:
            search_query = st.text_input("Search Description / Method", placeholder="e.g. coffee, salary, card")

        start_date, end_date = None, None
        if date_preset == "This Month":
            start_date = today.replace(day=1)
            end_date = today
        elif date_preset == "Last 30 Days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif date_preset == "This Year":
            start_date = today.replace(month=1, day=1)
            end_date = today
        elif date_preset == "Custom Range":
            custom_c1, custom_c2 = st.columns(2)
            with custom_c1:
                start_date = st.date_input("Start Date", value=today - timedelta(days=30))
            with custom_c2:
                end_date = st.date_input("End Date", value=today)

    # Fetch filtered data
    df = database.get_transactions(
        start_date=start_date,
        end_date=end_date,
        category=filter_cat,
        trans_type=filter_type,
        search=search_query
    )

    # Download CSV Button
    csv_bytes = transactions.export_transactions_csv(df)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="📥 Export Filtered Transactions (CSV)",
        data=csv_bytes,
        file_name=f"transactions_export_{timestamp_str}.csv",
        mime="text/csv",
    )

    # 2. Transactions Table
    if df.empty:
        st.warning("No transactions match the selected filter criteria.")
    else:
        st.write(f"Showing **{len(df)}** transactions:")
        display_df = df.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df["formatted_amount"] = display_df.apply(
            lambda r: f"+{curr_sym}{r['amount']:,.2f}" if r["type"] == "Income" else f"-{curr_sym}{r['amount']:,.2f}",
            axis=1
        )

        table_view = display_df[["id", "date", "type", "category", "formatted_amount", "payment_method", "description"]].rename(
            columns={
                "id": "ID",
                "date": "Date",
                "type": "Type",
                "category": "Category",
                "formatted_amount": "Amount",
                "payment_method": "Payment Method",
                "description": "Description",
            }
        )
        st.dataframe(table_view, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. Edit & Delete Section
    st.subheader("✏️ Edit or Delete a Transaction")
    ed_c1, ed_c2 = st.columns([1, 2])

    with ed_c1:
        selected_id = st.number_input(
            "Enter Transaction ID to Edit/Delete",
            min_value=1,
            step=1,
            value=int(df["id"].iloc[0]) if not df.empty else 1
        )
        action_mode = st.radio("Action", ["Edit", "Delete"], horizontal=True)

    with ed_c2:
        target_trans = database.get_transaction_by_id(int(selected_id))

        if not target_trans:
            st.info(f"Transaction ID #{selected_id} does not exist.")
        else:
            if action_mode == "Delete":
                st.warning(f"Are you sure you want to permanently delete Transaction **#{selected_id}** ({target_trans['type']} - {curr_sym}{target_trans['amount']:,.2f} - {target_trans['category']})?")
                if st.button("🗑️ Confirm Delete", type="primary"):
                    ok, msg = transactions.remove_transaction(int(selected_id))
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            elif action_mode == "Edit":
                st.markdown(f"**Editing Transaction #{selected_id}**")
                with st.form("edit_form"):
                    e_type = st.radio(
                        "Type",
                        ["Expense", "Income"],
                        index=0 if target_trans["type"] == "Expense" else 1,
                        horizontal=True
                    )
                    cats = database.get_categories(category_type=e_type)
                    if target_trans["category"] not in cats:
                        cats.append(target_trans["category"])

                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        e_amt = st.number_input(
                            f"Amount ({curr_sym})",
                            min_value=0.01,
                            value=float(target_trans["amount"]),
                            step=1.00,
                            format="%.2f"
                        )
                    with e_c2:
                        cat_idx = cats.index(target_trans["category"]) if target_trans["category"] in cats else 0
                        e_cat = st.selectbox("Category", options=cats, index=cat_idx)

                    e_c3, e_c4 = st.columns(2)
                    with e_c3:
                        orig_date = datetime.strptime(str(target_trans["date"])[:10], "%Y-%m-%d").date()
                        e_date = st.date_input("Date", value=orig_date)
                    with e_c4:
                        m_idx = PAYMENT_METHODS.index(target_trans["payment_method"]) if target_trans["payment_method"] in PAYMENT_METHODS else 0
                        e_method = st.selectbox("Payment Method", options=PAYMENT_METHODS, index=m_idx)

                    e_desc = st.text_area("Description", value=target_trans["description"] or "")

                    save_btn = st.form_submit_button("💾 Update Transaction", type="primary")
                    if save_btn:
                        ok, msg = transactions.modify_transaction(
                            trans_id=int(selected_id),
                            trans_type=e_type,
                            amount=e_amt,
                            category=e_cat,
                            date_val=e_date,
                            payment_method=e_method,
                            description=e_desc
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")


# ==========================================
# VIEW: Budget Management
# ==========================================

def render_budget_management(curr_sym: str):
    st.title("🎯 Budget Management")
    st.caption("Set monthly spending limits, monitor actual expenses, and receive threshold alerts.")

    today = date.today()
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        sel_month = st.selectbox(
            "Select Month",
            options=list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda m: datetime(2000, m, 1).strftime("%B")
        )
    with c_m2:
        sel_year = st.selectbox(
            "Select Year",
            options=list(range(today.year - 2, today.year + 3)),
            index=2
        )

    # 1. Budget Alerts & Progress Table
    budget_df = database.get_budgets(month=sel_month, year=sel_year)
    trans_df = database.get_transactions()
    analysis_df = analytics.analyze_budgets(trans_df, budget_df, month=sel_month, year=sel_year)

    if not analysis_df.empty:
        # Check alerts
        danger_items = analysis_df[analysis_df["Status"] == "Exceeded"]
        warn_items = analysis_df[analysis_df["Status"] == "Warning"]

        if not danger_items.empty:
            for _, r in danger_items.iterrows():
                st.error(f"🚨 **Budget Exceeded:** `{r['Category']}` spending is **{curr_sym}{r['Spent']:,.2f}**, which exceeds budget **{curr_sym}{r['Budget']:,.2f}** ({r['Percentage_Used']}%)!")

        if not warn_items.empty:
            for _, r in warn_items.iterrows():
                st.warning(f"⚠️ **Budget Warning:** `{r['Category']}` spending has reached **{r['Percentage_Used']}%** ({curr_sym}{r['Spent']:,.2f} / {curr_sym}{r['Budget']:,.2f}).")

        # Visual Chart
        fig_b = visualizations.create_budget_progress_chart(analysis_df, currency_symbol=curr_sym)
        if fig_b:
            st.plotly_chart(fig_b, use_container_width=True)

        # Budget Table with styling
        st.subheader("Budget Tracking Table")
        styled_df = analysis_df.copy()
        styled_df["Budget"] = styled_df["Budget"].apply(lambda v: f"{curr_sym}{v:,.2f}")
        styled_df["Spent"] = styled_df["Spent"].apply(lambda v: f"{curr_sym}{v:,.2f}")
        styled_df["Remaining"] = styled_df["Remaining"].apply(lambda v: f"{curr_sym}{v:,.2f}")
        styled_df["Percentage_Used"] = styled_df["Percentage_Used"].apply(lambda v: f"{v:.1f}%")

        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No budgets defined for {datetime(2000, sel_month, 1).strftime('%B')} {sel_year}. Use the form below to set one!")

    st.markdown("---")

    # 2. Set / Update Budget Form
    st.subheader(f"➕ Set or Update Budget for {datetime(2000, sel_month, 1).strftime('%B')} {sel_year}")
    with st.form("budget_form"):
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            expense_cats = ["Total"] + database.get_categories(category_type="Expense")
            b_cat = st.selectbox("Category to Budget", options=expense_cats)
        with b_c2:
            b_amount = st.number_input(
                f"Budget Limit Amount ({curr_sym}) *",
                min_value=1.0,
                max_value=10000000.0,
                value=500.0,
                step=50.0,
                format="%.2f"
            )

        submit_budget = st.form_submit_button("💾 Save Budget Target", type="primary")
        if submit_budget:
            try:
                database.set_budget(month=sel_month, year=sel_year, category=b_cat, amount=b_amount)
                st.success(f"✅ Budget for `{b_cat}` set to {curr_sym}{b_amount:,.2f} for {datetime(2000, sel_month, 1).strftime('%B')} {sel_year}!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to set budget: {str(e)}")


# ==========================================
# VIEW: Reports & Analytics
# ==========================================

def render_reports_analytics(curr_sym: str):
    st.title("📈 Reports & Analytics")
    st.caption("Deep-dive financial reports, spending trends, and category intelligence.")

    # Timeframe selection
    today = date.today()
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        rep_type = st.radio("Report Level", ["Monthly Report", "Yearly Report"], horizontal=True)
    with r_col2:
        if rep_type == "Monthly Report":
            r_year = st.selectbox("Year", list(range(today.year - 3, today.year + 2)), index=3)
            r_month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1, format_func=lambda m: datetime(2000, m, 1).strftime("%B"))
        else:
            r_year = st.selectbox("Year", list(range(today.year - 3, today.year + 2)), index=3)
            r_month = None

    # Fetch data according to selection
    if rep_type == "Monthly Report":
        start_d = date(r_year, r_month, 1)
        next_month = date(r_year + 1, 1, 1) if r_month == 12 else date(r_year, r_month + 1, 1)
        end_d = next_month - timedelta(days=1)
        period_title = f"{datetime(2000, r_month, 1).strftime('%B')} {r_year}"
    else:
        start_d = date(r_year, 1, 1)
        end_d = date(r_year, 12, 31)
        period_title = f"Year {r_year}"

    df = database.get_transactions(start_date=start_d, end_date=end_d)
    metrics = analytics.compute_summary_metrics(df)

    st.markdown(f"### 📋 Summary for {period_title}")

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Income", f"{curr_sym}{metrics['total_income']:,.2f}")
    m2.metric("Total Expenses", f"{curr_sym}{metrics['total_expenses']:,.2f}")
    m3.metric("Net Savings", f"{curr_sym}{metrics['net_balance']:,.2f}")
    m4.metric("Savings Rate", f"{metrics['savings_rate']:.1f}%")

    if df.empty:
        st.info("No transaction records available for this selected timeframe.")
        return

    # Visualizations Tabs (Plotly vs Matplotlib)
    st.markdown("---")
    st.subheader("📊 Category & Trend Visualizations")
    tab_plotly, tab_matplotlib = st.tabs(["Interactive Charts (Plotly)", "Static Publication Figures (Matplotlib)"])

    cat_df = analytics.get_category_breakdown(df, trans_type="Expense")

    with tab_plotly:
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            fig_p_pie = visualizations.create_category_pie_chart(cat_df, currency_symbol=curr_sym, title=f"Expense Share ({period_title})")
            if fig_p_pie:
                st.plotly_chart(fig_p_pie, use_container_width=True)
            else:
                st.info("No expense data.")

        with p_c2:
            daily_df = analytics.get_daily_spending_trend(df, start_date=start_d, end_date=end_d)
            fig_daily = visualizations.create_daily_spending_chart(daily_df, currency_symbol=curr_sym)
            if fig_daily:
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info("No daily data.")

        # Payment Methods Chart
        pay_df = analytics.get_payment_method_breakdown(df)
        fig_pay = visualizations.create_payment_method_chart(pay_df, currency_symbol=curr_sym)
        if fig_pay:
            st.plotly_chart(fig_pay, use_container_width=True)

    with tab_matplotlib:
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            fig_mat_pie = visualizations.create_matplotlib_category_pie(cat_df, currency_symbol=curr_sym)
            st.pyplot(fig_mat_pie)

        with m_c2:
            all_df = database.get_transactions()
            monthly_trends_df = analytics.get_monthly_trends(all_df, year=r_year)
            fig_mat_trend = visualizations.create_matplotlib_trend_chart(monthly_trends_df, currency_symbol=curr_sym)
            st.pyplot(fig_mat_trend)

    # Detailed Category Breakdown Table
    st.markdown("---")
    st.subheader("📑 Category Expenditure Breakdown")
    if not cat_df.empty:
        table_cats = cat_df.copy()
        table_cats["Total"] = table_cats["Total"].apply(lambda v: f"{curr_sym}{v:,.2f}")
        table_cats["Average"] = table_cats["Average"].apply(lambda v: f"{curr_sym}{v:,.2f}")
        table_cats["Percentage"] = table_cats["Percentage"].apply(lambda v: f"{v:.1f}%")
        st.dataframe(table_cats, use_container_width=True, hide_index=True)


# ==========================================
# VIEW: Categories Management
# ==========================================

def render_categories_management():
    st.title("🏷️ Category Management")
    st.caption("Customize expense and income categories to tailor the tracker to your lifestyle.")

    cat_c1, cat_c2 = st.columns([1, 1])

    with cat_c1:
        st.subheader("➕ Add Custom Category")
        with st.form("add_cat_form", clear_on_submit=True):
            new_cat_name = st.text_input("Category Name *", placeholder="e.g. Pet Care, Subscriptions")
            new_cat_type = st.radio("Category Type *", ["Expense", "Income"], horizontal=True)
            submit_cat = st.form_submit_button("Add Category", type="primary")

            if submit_cat:
                try:
                    success = database.add_category(new_cat_name, new_cat_type)
                    if success:
                        st.success(f"✅ Category '{new_cat_name.title()}' added to {new_cat_type} categories!")
                        st.rerun()
                    else:
                        st.warning(f"Category '{new_cat_name}' already exists.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with cat_c2:
        st.subheader("🗑️ Remove Custom Category")
        detail_cats = database.get_categories_detail()
        custom_cats = [c for c in detail_cats if c["is_default"] == 0]

        if not custom_cats:
            st.info("No custom categories have been added yet. System default categories cannot be deleted.")
        else:
            cat_options = {f"{c['name']} ({c['type']})": c["id"] for c in custom_cats}
            selected_cat_label = st.selectbox("Select custom category to remove", list(cat_options.keys()))
            if st.button("Delete Selected Category", type="secondary"):
                cid = cat_options[selected_cat_label]
                try:
                    database.delete_category(cid)
                    st.success(f"✅ Category '{selected_cat_label}' removed.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Could not delete category: {str(e)}")

    st.markdown("---")
    st.subheader("📋 Current Active Categories")
    exp_col, inc_col = st.columns(2)

    with exp_col:
        st.markdown("**Expense Categories:**")
        exp_list = database.get_categories_detail(category_type="Expense")
        exp_df = pd.DataFrame(exp_list)[["name", "is_default"]]
        exp_df["Type"] = exp_df["is_default"].apply(lambda d: "System Default" if d == 1 else "Custom")
        exp_df = exp_df.rename(columns={"name": "Category"}).drop(columns=["is_default"])
        st.dataframe(exp_df, use_container_width=True, hide_index=True)

    with inc_col:
        st.markdown("**Income Categories:**")
        inc_list = database.get_categories_detail(category_type="Income")
        inc_df = pd.DataFrame(inc_list)[["name", "is_default"]]
        inc_df["Type"] = inc_df["is_default"].apply(lambda d: "System Default" if d == 1 else "Custom")
        inc_df = inc_df.rename(columns={"name": "Category"}).drop(columns=["is_default"])
        st.dataframe(inc_df, use_container_width=True, hide_index=True)


# ==========================================
# VIEW: Settings & Data Management
# ==========================================

def render_settings_and_data(curr_sym: str):
    st.title("⚙️ Settings & Data Operations")
    st.caption("Manage data backups, CSV import/export, and sample demo datasets.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Data Export & Backup")
        st.write("Download all transactions in the database as a CSV backup.")
        all_df = database.get_transactions()
        csv_bytes = transactions.export_transactions_csv(all_df)
        st.download_button(
            label="Download Complete Database (CSV)",
            data=csv_bytes,
            file_name=f"expense_tracker_full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )

        st.markdown("---")
        st.subheader("📤 Import Transactions from CSV")
        st.write("Import existing transaction records from a CSV file.")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        if uploaded_file is not None:
            if st.button("Start CSV Import"):
                imported, skipped, errors = transactions.import_transactions_from_csv(uploaded_file)
                st.success(f"✅ Successfully imported {imported} transactions!")
                if skipped > 0:
                    st.warning(f"⚠️ Skipped {skipped} rows due to validation errors.")
                    with st.expander("Show Import Warnings"):
                        for err in errors[:10]:
                            st.write(err)

    with col2:
        st.subheader("🧪 Demo & Sample Data")
        st.write("Populate the tracker with 60 days of realistic sample transactions, salaries, and budgets to explore all analytics features.")

        if st.button("🎲 Re-Seed Sample Demo Data"):
            count = sample_data.seed_sample_data(force=True)
            st.success(f"✅ Loaded {count} sample transactions and monthly budgets!")
            st.rerun()

        st.markdown("---")
        st.subheader("⚠️ Reset Database")
        st.write("Clear all transaction history, budgets, and custom categories. This will reset the application to fresh factory defaults.")

        confirm_reset = st.checkbox("I understand this will erase all stored transactions.")
        if confirm_reset:
            if st.button("💥 Reset All Data Now", type="secondary"):
                database.reset_all_data()
                st.success("Database has been reset to defaults.")
                st.rerun()


# ==========================================
# Main Router
# ==========================================

if menu == "📊 Dashboard":
    render_dashboard(curr_sym)
elif menu == "➕ Add Transaction":
    render_add_transaction(curr_sym)
elif menu == "📋 Manage Transactions":
    render_manage_transactions(curr_sym)
elif menu == "🎯 Budget Management":
    render_budget_management(curr_sym)
elif menu == "📈 Reports & Analytics":
    render_reports_analytics(curr_sym)
elif menu == "🏷️ Categories":
    render_categories_management()
elif menu == "⚙️ Settings & Data":
    render_settings_and_data(curr_sym)
