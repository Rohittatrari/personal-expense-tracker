# 💰 Personal Expense Tracker

A modern, responsive, full-featured **Personal Expense Tracker** web application built with Python and Streamlit. The application helps users easily record, manage, analyze, and track daily income, expenses, and monthly budgets with interactive data visualizations and persistent SQLite storage.

---

## 🚀 Key Features

### 1. 📊 Interactive Financial Dashboard
- **Summary Cards**: Real-time display of **Total Income**, **Total Expenses**, **Current Net Balance**, and **Savings Rate (%)**.
- **Visual Analytics**: Interactive Donut chart of category expenses and monthly Income vs. Expense trend bars with Net Savings line.
- **Budget Threshold Alerts**: Instant notifications if monthly expenses approach (>= 80%) or exceed (>= 100%) defined budgets.
- **Recent Activity**: Quick view of latest 5 transactions and spending highlights (top category, average daily expense, largest expense).

### 2. ➕ Add Transactions with Strict Validation
- Record both **Income** and **Expense** entries.
- Fields: Amount, Category, Transaction Date, Payment Method (Cash, Credit Card, Debit Card, Bank Transfer, UPI, Digital Wallet, Other), and Description.
- Input validation prevents negative or zero amounts, invalid dates, and missing required fields.

### 3. 📋 Manage, Edit, and Delete Transactions
- Comprehensive transaction history table with formatted amounts, currency badges, and dates.
- Multi-dimensional filters: Filter by **Transaction Type** (*All, Expense, Income*), **Category**, and **Date Range** (*All Dates, This Month, Last 30 Days, This Year, Custom Range*), plus free-text search.
- Inline **Edit** or **Delete** existing transactions with confirmation.
- **CSV Export**: Instant download of filtered or full transaction records with one click.

### 4. 🏷️ Category Management
- Pre-seeded with 8 standard expense categories: `Food`, `Travel`, `Shopping`, `Education`, `Bills`, `Healthcare`, `Entertainment`, and `Other`.
- Standard income categories: `Salary`, `Freelance`, `Investment`, `Business`, `Gift`, `Other`.
- Add custom categories for tailored expense and income tracking.
- Delete custom categories safely while preserving system defaults.

### 5. 🎯 Budget Management & Warning System
- Set monthly spending budgets for the whole month (`Total`) or per specific category.
- Compares actual expenses against the budget for any selected month and year.
- **Threshold Warnings**:
  - 🟢 **Normal**: Spending below 80% of budget.
  - 🟡 **Warning**: Spending between 80% and 99.9% of budget.
  - 🔴 **Exceeded**: Spending at or over 100% of budget.
- Visual comparative bar chart showing Budget vs. Actual Spent.

### 6. 📈 Reports & Analytics
- Monthly and Yearly financial reports.
- **Dual Visualizations**:
  - **Interactive Plotly**: Donut charts, daily spending trends, cumulative expense lines, payment method breakdowns.
  - **Publication-ready Matplotlib**: Static pie charts and monthly financial comparisons.
- Statistical insights: Highest spending category, average transaction, daily average, and full breakdown tables.

### 7. 💾 Robust SQLite Database
- Parameterized SQL queries (`?`) for secure, injection-safe database operations.
- Persistent data storage across application restarts in `expense_tracker.db`.
- WAL (Write-Ahead Logging) mode enabled for responsive concurrency.

### 8. 📥 Data Export, Import & Demo Seeder
- **Export to CSV**: Export transaction tables with human-readable headers.
- **Import from CSV**: Bulk import transaction data with schema validation.
- **One-Click Demo Data**: Instantly seed 60 days of realistic transactions and budgets to explore all analytics features.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend UI** | Streamlit |
| **Backend & Logic** | Python 3.10+ |
| **Database** | SQLite3 (Persistent, Parameterized) |
| **Data Processing** | Pandas, NumPy |
| **Visualizations** | Plotly & Matplotlib |

---

## 📂 Project Structure

```text
personal expense tracker/
│
├── app.py                   # Streamlit web application & user interface
├── config.py                # Configuration constants, paths, categories & colors
├── database.py              # SQLite connection, schema initialization & parameterized queries
├── transactions.py          # Transaction validation, business rules, CSV export/import
├── analytics.py             # Pandas/NumPy metrics, aggregations & budget comparisons
├── visualizations.py        # Plotly interactive & Matplotlib static chart generators
├── sample_data.py           # Realistic sample dataset seeder (60 days of transactions & budgets)
├── test_expense_tracker.py  # Comprehensive unit & integration test suite
├── requirements.txt         # Project dependencies
└── README.md                # Documentation & usage guide
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python **3.10** or higher installed on your system.
- Git (optional, if cloning from a repository).

### Step 1: Clone or Open the Project Directory
```bash
cd "c:\Users\rohit\Downloads\personal expense tracker"
```

### Step 2: Create a Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Launch the Streamlit web application locally:

```bash
streamlit run app.py
```

Or using the virtual environment directly:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

The application will start and open automatically in your default browser at:
```
Local URL: http://localhost:8501
```

---

## 🧪 Running the Test Suite

The project includes unit and integration tests covering database operations, validation rules, analytics calculations, visualizations, and CSV export.

Run the test suite with:
```bash
python -m unittest test_expense_tracker.py -v
```

All 8 test cases will execute and verify application integrity:
- `test_database_initialization_and_default_categories`
- `test_category_management`
- `test_transaction_validation`
- `test_transaction_crud_and_filtering`
- `test_budget_management_and_threshold_alerts`
- `test_analytics_metrics`
- `test_visualizations_generation`
- `test_csv_export`

---

## 🗄️ Database Architecture

The application uses an SQLite database (`expense_tracker.db`) with three tables:

### 1. `categories` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique category ID |
| `name` | TEXT | NOT NULL | Category name |
| `type` | TEXT | CHECK IN ('Expense', 'Income') | Category type |
| `is_default` | INTEGER | DEFAULT 0 | 1 = System Default, 0 = Custom |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp |

### 2. `transactions` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique transaction ID |
| `type` | TEXT | CHECK IN ('Expense', 'Income') | Transaction type |
| `amount` | REAL | CHECK (amount > 0) | Transaction value |
| `category` | TEXT | NOT NULL | Associated category |
| `date` | TEXT | NOT NULL | Date in YYYY-MM-DD |
| `payment_method` | TEXT | NOT NULL | Payment method |
| `description` | TEXT | | Notes / memo |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp |

### 3. `budgets` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique budget ID |
| `month` | INTEGER | CHECK (1 <= month <= 12) | Budget month |
| `year` | INTEGER | CHECK (year >= 2000) | Budget year |
| `category` | TEXT | NOT NULL | 'Total' or category name |
| `amount` | REAL | CHECK (amount >= 0) | Budget target limit |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp |

---

## 💡 How to Use the Application

1. **Dashboard (`📊 Dashboard`)**:
   - Select your preferred currency from the sidebar dropdown (*USD $, INR ₹, EUR €, GBP £, etc.*).
   - View your financial summary, category donut chart, and monthly trends.
2. **Add Transactions (`➕ Add Transaction`)**:
   - Choose whether it is an Expense or Income.
   - Enter amount, pick a category, select transaction date, and pick the payment method.
   - Click **Save Transaction** to persist it to the SQLite database.
3. **Filter & Edit (`📋 Manage Transactions`)**:
   - Filter transactions by date preset, category, or type.
   - Enter an ID in the bottom panel to edit fields or delete a record.
   - Click **Export Filtered Transactions (CSV)** to download a spreadsheet.
4. **Budget Management (`🎯 Budget Management`)**:
   - Select any month and year to view or set budget targets.
   - Set targets for overall monthly expense (`Total`) or specific categories like `Food` and `Travel`.
   - The system alerts you in Amber when you reach 80% and Red when you exceed 100%.
5. **Reports & Analytics (`📈 Reports & Analytics`)**:
   - Switch between **Monthly** and **Yearly** reports.
   - Toggle between **Interactive Plotly** charts and **Static Matplotlib** figures.
6. **Demo & Reset (`⚙️ Settings & Data`)**:
   - Re-seed sample data anytime to test visualizations with 60 days of realistic records.
