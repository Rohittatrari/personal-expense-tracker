"""
Unit and integration tests for Personal Expense Tracker.
Tests database operations, input validation, analytics aggregations, visualization generation, and CSV export.
"""

import unittest
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

import config
import database
import transactions
import analytics
import visualizations
import sample_data


class TestPersonalExpenseTracker(unittest.TestCase):

    def setUp(self):
        # Use an isolated temporary SQLite database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        database.DB_PATH = Path(self.temp_db.name)
        database.init_db()

    def tearDown(self):
        # Clean up temporary database file
        if os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except Exception:
                pass

    def test_database_initialization_and_default_categories(self):
        """Test that database tables are created and default categories exist."""
        exp_cats = database.get_categories(category_type="Expense")
        inc_cats = database.get_categories(category_type="Income")

        for default_cat in config.DEFAULT_EXPENSE_CATEGORIES:
            self.assertIn(default_cat, exp_cats)

        for default_cat in config.DEFAULT_INCOME_CATEGORIES:
            self.assertIn(default_cat, inc_cats)

    def test_category_management(self):
        """Test adding custom category, duplicate handling, and deletion rules."""
        # Add custom category
        success = database.add_category("Crypto Staking", "Income")
        self.assertTrue(success)

        # Test duplicate category handling
        dup_success = database.add_category("Crypto Staking", "Income")
        self.assertFalse(dup_success)

        # Retrieve and verify
        inc_cats = database.get_categories("Income")
        self.assertIn("Crypto Staking", inc_cats)

        # Verify deletion rules
        details = database.get_categories_detail("Income")
        custom_rec = next(c for c in details if c["name"] == "Crypto Staking")
        self.assertEqual(custom_rec["is_default"], 0)

        # Delete custom category
        del_success = database.delete_category(custom_rec["id"])
        self.assertTrue(del_success)
        self.assertNotIn("Crypto Staking", database.get_categories("Income"))

        # Cannot delete default category
        default_rec = next(c for c in details if c["is_default"] == 1)
        with self.assertRaises(ValueError):
            database.delete_category(default_rec["id"])

    def test_transaction_validation(self):
        """Test transaction input validation for various edge cases."""
        # Valid transaction
        valid, msg = transactions.validate_transaction(
            trans_type="Expense",
            amount=45.50,
            category="Food",
            date_val=date.today(),
            payment_method="Credit Card",
            description="Lunch"
        )
        self.assertTrue(valid)
        self.assertEqual(msg, "")

        # Invalid amount (zero or negative)
        valid, msg = transactions.validate_transaction(
            trans_type="Expense",
            amount=0,
            category="Food",
            date_val=date.today(),
            payment_method="Credit Card"
        )
        self.assertFalse(valid)
        self.assertIn("greater than zero", msg)

        # Invalid type
        valid, msg = transactions.validate_transaction(
            trans_type="Investment",
            amount=100,
            category="Food",
            date_val=date.today(),
            payment_method="Credit Card"
        )
        self.assertFalse(valid)

        # Missing category
        valid, msg = transactions.validate_transaction(
            trans_type="Expense",
            amount=50,
            category="",
            date_val=date.today(),
            payment_method="Credit Card"
        )
        self.assertFalse(valid)

    def test_transaction_crud_and_filtering(self):
        """Test inserting, querying, updating, and deleting transactions."""
        # 1. Add transactions
        t1_id = database.add_transaction(
            trans_type="Income",
            amount=3000.0,
            category="Salary",
            date_str="2026-01-01",
            payment_method="Bank Transfer",
            description="Monthly Paycheck"
        )
        self.assertIsNotNone(t1_id)

        t2_id = database.add_transaction(
            trans_type="Expense",
            amount=75.0,
            category="Food",
            date_str="2026-01-05",
            payment_method="Debit Card",
            description="Grocery run"
        )
        self.assertIsNotNone(t2_id)

        # 2. Query transactions
        df_all = database.get_transactions()
        self.assertEqual(len(df_all), 2)

        # Filter by type
        df_exp = database.get_transactions(trans_type="Expense")
        self.assertEqual(len(df_exp), 1)
        self.assertEqual(df_exp.iloc[0]["category"], "Food")

        # Filter by search keyword
        df_search = database.get_transactions(search="Grocery")
        self.assertEqual(len(df_search), 1)

        # 3. Update transaction
        ok = database.update_transaction(
            trans_id=t2_id,
            trans_type="Expense",
            amount=85.0,
            category="Food",
            date_str="2026-01-05",
            payment_method="Debit Card",
            description="Grocery run updated"
        )
        self.assertTrue(ok)
        rec = database.get_transaction_by_id(t2_id)
        self.assertEqual(rec["amount"], 85.0)
        self.assertEqual(rec["description"], "Grocery run updated")

        # 4. Delete transaction
        del_ok = database.delete_transaction(t2_id)
        self.assertTrue(del_ok)
        self.assertEqual(len(database.get_transactions()), 1)

    def test_budget_management_and_threshold_alerts(self):
        """Test setting budgets and tracking warning/danger alert thresholds."""
        # Set monthly budget of 100 for Food in March 2026
        database.set_budget(month=3, year=2026, category="Food", amount=100.0)
        budgets_df = database.get_budgets(month=3, year=2026)
        self.assertEqual(len(budgets_df), 1)

        # Expense of 50 -> 50% (Normal)
        database.add_transaction("Expense", 50.0, "Food", "2026-03-05", "Cash")
        t_df = database.get_transactions()
        analysis = analytics.analyze_budgets(t_df, budgets_df, month=3, year=2026)
        self.assertEqual(analysis.iloc[0]["Status"], "Normal")

        # Add 35 more -> 85 total -> 85% (Warning threshold >= 80%)
        database.add_transaction("Expense", 35.0, "Food", "2026-03-10", "Cash")
        t_df = database.get_transactions()
        analysis = analytics.analyze_budgets(t_df, budgets_df, month=3, year=2026)
        self.assertEqual(analysis.iloc[0]["Status"], "Warning")

        # Add 25 more -> 110 total -> 110% (Exceeded threshold >= 100%)
        database.add_transaction("Expense", 25.0, "Food", "2026-03-15", "Cash")
        t_df = database.get_transactions()
        analysis = analytics.analyze_budgets(t_df, budgets_df, month=3, year=2026)
        self.assertEqual(analysis.iloc[0]["Status"], "Exceeded")

    def test_analytics_metrics(self):
        """Test compute_summary_metrics, category breakdown, and monthly trends."""
        database.add_transaction("Income", 5000.0, "Salary", "2026-02-01", "Bank Transfer")
        database.add_transaction("Expense", 1200.0, "Bills", "2026-02-05", "Bank Transfer")
        database.add_transaction("Expense", 800.0, "Food", "2026-02-10", "Credit Card")

        df = database.get_transactions()
        metrics = analytics.compute_summary_metrics(df)

        self.assertEqual(metrics["total_income"], 5000.0)
        self.assertEqual(metrics["total_expenses"], 2000.0)
        self.assertEqual(metrics["net_balance"], 3000.0)
        self.assertEqual(metrics["savings_rate"], 60.0)
        self.assertEqual(metrics["transaction_count"], 3)

        # Category breakdown
        cat_df = analytics.get_category_breakdown(df, trans_type="Expense")
        self.assertEqual(len(cat_df), 2)
        top_cat, top_amt, top_pct = analytics.get_highest_spending_category(df)
        self.assertEqual(top_cat, "Bills")
        self.assertEqual(top_amt, 1200.0)

        # Monthly trends
        m_df = analytics.get_monthly_trends(df, year=2026)
        self.assertEqual(len(m_df), 1)
        self.assertEqual(m_df.iloc[0]["Income"], 5000.0)
        self.assertEqual(m_df.iloc[0]["Expense"], 2000.0)

    def test_visualizations_generation(self):
        """Test that Plotly and Matplotlib chart generation functions run without errors."""
        database.add_transaction("Income", 4000.0, "Salary", "2026-02-01", "Bank Transfer")
        database.add_transaction("Expense", 300.0, "Food", "2026-02-03", "Cash")
        database.add_transaction("Expense", 150.0, "Travel", "2026-02-04", "UPI")

        df = database.get_transactions()
        cat_df = analytics.get_category_breakdown(df, trans_type="Expense")
        monthly_df = analytics.get_monthly_trends(df, year=2026)
        daily_df = analytics.get_daily_spending_trend(df)
        pay_df = analytics.get_payment_method_breakdown(df)

        # Plotly charts
        fig_pie = visualizations.create_category_pie_chart(cat_df)
        self.assertIsNotNone(fig_pie)

        fig_trend = visualizations.create_monthly_trend_bar_chart(monthly_df)
        self.assertIsNotNone(fig_trend)

        fig_daily = visualizations.create_daily_spending_chart(daily_df)
        self.assertIsNotNone(fig_daily)

        fig_pay = visualizations.create_payment_method_chart(pay_df)
        self.assertIsNotNone(fig_pay)

        # Matplotlib figures
        plt_pie = visualizations.create_matplotlib_category_pie(cat_df)
        self.assertIsNotNone(plt_pie)

        plt_trend = visualizations.create_matplotlib_trend_chart(monthly_df)
        self.assertIsNotNone(plt_trend)

    def test_csv_export(self):
        """Test exporting transactions to CSV format."""
        database.add_transaction("Income", 2500.0, "Salary", "2026-02-01", "Bank Transfer", "Test Pay")
        df = database.get_transactions()
        csv_bytes = transactions.export_transactions_csv(df)
        self.assertTrue(len(csv_bytes) > 0)
        csv_text = csv_bytes.decode("utf-8")
        self.assertIn("Test Pay", csv_text)
        self.assertIn("Salary", csv_text)


if __name__ == "__main__":
    unittest.main()
