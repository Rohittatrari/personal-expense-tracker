"""
Configuration settings for the Personal Expense Tracker.
Contains database paths, default categories, payment methods, and visual styling constants.
"""

from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DB_NAME = "expense_tracker.db"
DB_PATH = BASE_DIR / DB_NAME

# Default Categories
DEFAULT_EXPENSE_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Bills",
    "Healthcare",
    "Entertainment",
    "Other",
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investment",
    "Business",
    "Gift",
    "Other",
]

# Supported Payment Methods
PAYMENT_METHODS = [
    "Cash",
    "Credit Card",
    "Debit Card",
    "Bank Transfer",
    "UPI",
    "Digital Wallet",
    "Other",
]

# Supported Currencies
CURRENCIES = {
    "USD ($)": "$",
    "INR (₹)": "₹",
    "EUR (€)": "€",
    "GBP (£)": "£",
    "CAD ($)": "CA$",
    "AUD ($)": "A$",
    "JPY (¥)": "¥",
}

DEFAULT_CURRENCY = "USD ($)"

# Budget Thresholds
BUDGET_WARNING_THRESHOLD = 0.80  # 80% spending warning
BUDGET_DANGER_THRESHOLD = 1.00   # 100% spending alert

# Visual Theme Colors
COLOR_PALETTE = [
    "#2E86AB",  # Blue
    "#F24236",  # Coral Red
    "#38B000",  # Green
    "#F6AE2D",  # Warm Yellow
    "#8338EC",  # Purple
    "#3A86FF",  # Light Blue
    "#FB5607",  # Orange
    "#FF006E",  # Pink
    "#06D6A0",  # Teal
    "#118AB2",  # Deep Cyan
    "#073B4C",  # Navy
    "#6C757D",  # Gray
]

CATEGORY_COLORS = {
    "Food": "#FF6B6B",
    "Travel": "#4D96FF",
    "Shopping": "#FFD93D",
    "Education": "#6BCB77",
    "Bills": "#FF9F45",
    "Healthcare": "#EE5253",
    "Entertainment": "#9B51E0",
    "Salary": "#2ECC71",
    "Freelance": "#3498DB",
    "Investment": "#1ABC9C",
    "Business": "#F39C12",
    "Gift": "#E84393",
    "Other": "#95A5A6",
}
