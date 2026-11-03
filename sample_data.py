"""
Sample data generation module for Personal Expense Tracker.
Seeds realistic transactions, income, and budgets across recent months for immediate demo and testing.
"""

from datetime import date, timedelta
import random
import database


def has_sample_data() -> bool:
    """
    Checks if there are any transactions currently in the database.
    """
    df = database.get_transactions(limit=1)
    return not df.empty


def seed_sample_data(force: bool = False) -> int:
    """
    Seeds the database with realistic sample transactions and budgets for demonstration.
    Returns the number of transactions inserted.
    """
    database.init_db()

    if not force and has_sample_data():
        return 0

    today = date.today()
    current_year = today.year
    current_month = today.month

    # Sample transaction templates (Category, Type, min_amt, max_amt, methods, sample descriptions)
    templates = [
        # Incomes
        ("Salary", "Income", 4500.0, 5500.0, ["Bank Transfer"], ["Monthly Tech Company Salary", "Direct Deposit Payroll"]),
        ("Freelance", "Income", 400.0, 1200.0, ["Bank Transfer", "UPI"], ["Website Design Client Payment", "Python Script Consulting", "Technical Writing"]),
        ("Investment", "Income", 150.0, 600.0, ["Bank Transfer"], ["Dividend Payout", "Stock Profit Booking", "Bond Yield Return"]),

        # Expenses
        ("Food", "Expense", 15.0, 120.0, ["Credit Card", "Debit Card", "UPI", "Cash"], ["Grocery Supermarket Haul", "Italian Dinner with Friends", "Daily Starbucks Coffee", "Organic Farm Produce", "Office Lunch Delivery"]),
        ("Travel", "Expense", 20.0, 180.0, ["Credit Card", "UPI", "Digital Wallet"], ["Uber Ride to Airport", "Metro Pass Renewal", "Gas Station Refuel", "Train Ticket Weekend Trip"]),
        ("Shopping", "Expense", 30.0, 250.0, ["Credit Card", "Debit Card", "Digital Wallet"], ["New Running Shoes", "Amazon Home Electronics", "Clothing & Apparel", "Books & Stationery"]),
        ("Education", "Expense", 40.0, 300.0, ["Credit Card", "Bank Transfer"], ["Online Data Science Course", "Professional Certification Fee", "O'Reilly Book Subscription", "Language Learning App"]),
        ("Bills", "Expense", 45.0, 220.0, ["Bank Transfer", "UPI", "Credit Card"], ["High-Speed Fiber Internet", "Electric Utility Bill", "Water & Trash Service", "Mobile Postpaid Plan"]),
        ("Healthcare", "Expense", 25.0, 190.0, ["Credit Card", "Debit Card", "Cash"], ["Monthly Pharmacy Prescription", "Dental Checkup & Cleaning", "Gym Membership", "Multivitamins and Supplements"]),
        ("Entertainment", "Expense", 15.0, 95.0, ["Credit Card", "Digital Wallet", "UPI"], ["Netflix & Spotify Subscription", "IMAX Movie Tickets & Popcorn", "Steam Video Game Purchase", "Concert Entry Ticket"]),
        ("Other", "Expense", 10.0, 75.0, ["Cash", "UPI"], ["Dry Cleaning Service", "Apartment Plant Care", "Postage & Packaging", "Charity Donation"]),
    ]

    inserted_count = 0

    # Generate data spanning past 60 days up to today
    random.seed(42)  # For reproducible realistic data

    for day_offset in range(60, -1, -1):
        trans_date = today - timedelta(days=day_offset)
        date_str = trans_date.strftime("%Y-%m-%d")

        # 1. Monthly salary on the 1st or 28th
        if trans_date.day == 1:
            database.add_transaction(
                trans_type="Income",
                amount=5000.0,
                category="Salary",
                date_str=date_str,
                payment_method="Bank Transfer",
                description="Monthly Company Salary"
            )
            inserted_count += 1

        # 2. Occasional freelance or investment income (twice a month)
        if trans_date.day in (10, 22):
            income_sample = random.choice([t for t in templates if t[1] == "Income" and t[0] != "Salary"])
            amt = round(random.uniform(income_sample[2], income_sample[3]), 2)
            method = random.choice(income_sample[4])
            desc = random.choice(income_sample[5])
            database.add_transaction(
                trans_type="Income",
                amount=amt,
                category=income_sample[0],
                date_str=date_str,
                payment_method=method,
                description=desc
            )
            inserted_count += 1

        # 3. Daily or semi-daily expenses (1 to 3 expenses per day)
        num_expenses = random.choices([1, 2, 3], weights=[0.4, 0.45, 0.15])[0]
        expense_templates = [t for t in templates if t[1] == "Expense"]

        for _ in range(num_expenses):
            # Weighted choice: Food and Bills more frequent
            chosen = random.choice(expense_templates)
            amt = round(random.uniform(chosen[2], chosen[3]), 2)
            method = random.choice(chosen[4])
            desc = random.choice(chosen[5])

            database.add_transaction(
                trans_type="Expense",
                amount=amt,
                category=chosen[0],
                date_str=date_str,
                payment_method=method,
                description=desc
            )
            inserted_count += 1

    # Seed Budgets for current month and previous month
    months_to_budget = [current_month]
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    
    budget_targets = [
        (current_month, current_year),
        (prev_month, prev_year)
    ]

    for m, y in budget_targets:
        database.set_budget(m, y, "Total", 2800.0)
        database.set_budget(m, y, "Food", 650.0)
        database.set_budget(m, y, "Travel", 300.0)
        database.set_budget(m, y, "Shopping", 400.0)
        database.set_budget(m, y, "Education", 250.0)
        database.set_budget(m, y, "Bills", 450.0)
        database.set_budget(m, y, "Healthcare", 250.0)
        database.set_budget(m, y, "Entertainment", 200.0)

    return inserted_count
