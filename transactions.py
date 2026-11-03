"""
Transaction management module for Personal Expense Tracker.
Handles transaction validation, business rules, CRUD coordination, and CSV export/import.
"""

from datetime import date, datetime
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
from config import PAYMENT_METHODS
import database


def validate_transaction(
    trans_type: str,
    amount: Any,
    category: str,
    date_val: Any,
    payment_method: str,
    description: str = ""
) -> Tuple[bool, str]:
    """
    Validates transaction input fields.
    Returns:
        (is_valid, error_message)
    """
    # 1. Type validation
    if trans_type not in ("Expense", "Income"):
        return False, "Transaction type must be either 'Expense' or 'Income'."

    # 2. Amount validation
    try:
        amt = float(amount)
        if amt <= 0:
            return False, "Amount must be greater than zero."
        if amt > 100_000_000:
            return False, "Amount exceeds maximum allowable limit (100,000,000)."
    except (ValueError, TypeError):
        return False, "Please enter a valid numeric amount."

    # 3. Category validation
    if not category or not str(category).strip():
        return False, "Category is required."

    # 4. Date validation
    if date_val is None:
        return False, "Transaction date is required."
    
    if isinstance(date_val, (date, datetime)):
        trans_date = date_val.strftime("%Y-%m-%d")
    elif isinstance(date_val, str):
        try:
            parsed = datetime.strptime(date_val.strip(), "%Y-%m-%d")
            trans_date = parsed.strftime("%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format. Expected YYYY-MM-DD."
    else:
        return False, "Invalid date provided."

    # Check future date warning or restriction if needed (allow flexible entry up to 1 year ahead)
    try:
        dt = datetime.strptime(trans_date, "%Y-%m-%d").date()
        today = date.today()
        # allow transactions up to 365 days in future
        if (dt - today).days > 365:
            return False, "Date cannot be more than 1 year in the future."
    except Exception:
        pass

    # 5. Payment method validation
    if not payment_method or not str(payment_method).strip():
        return False, "Payment method is required."

    # 6. Description length
    if description and len(str(description).strip()) > 500:
        return False, "Description must not exceed 500 characters."

    return True, ""


def record_transaction(
    trans_type: str,
    amount: float,
    category: str,
    date_val: Any,
    payment_method: str,
    description: str = ""
) -> Tuple[bool, str, Optional[int]]:
    """
    Validates and stores a new transaction.
    Returns: (success, message, new_id)
    """
    is_valid, err = validate_transaction(trans_type, amount, category, date_val, payment_method, description)
    if not is_valid:
        return False, err, None

    date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, (date, datetime)) else str(date_val).strip()

    try:
        new_id = database.add_transaction(
            trans_type=trans_type,
            amount=amount,
            category=category,
            date_str=date_str,
            payment_method=payment_method,
            description=description
        )
        return True, "Transaction recorded successfully!", new_id
    except Exception as e:
        return False, f"Database error: {str(e)}", None


def modify_transaction(
    trans_id: int,
    trans_type: str,
    amount: float,
    category: str,
    date_val: Any,
    payment_method: str,
    description: str = ""
) -> Tuple[bool, str]:
    """
    Validates and updates an existing transaction.
    """
    is_valid, err = validate_transaction(trans_type, amount, category, date_val, payment_method, description)
    if not is_valid:
        return False, err

    date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, (date, datetime)) else str(date_val).strip()

    try:
        success = database.update_transaction(
            trans_id=trans_id,
            trans_type=trans_type,
            amount=amount,
            category=category,
            date_str=date_str,
            payment_method=payment_method,
            description=description
        )
        if success:
            return True, "Transaction updated successfully!"
        return False, "Transaction not found or could not be updated."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def remove_transaction(trans_id: int) -> Tuple[bool, str]:
    """
    Deletes a transaction by ID.
    """
    try:
        success = database.delete_transaction(trans_id)
        if success:
            return True, "Transaction deleted successfully!"
        return False, "Transaction ID not found."
    except Exception as e:
        return False, f"Database error: {str(e)}"


def export_transactions_csv(df: pd.DataFrame) -> bytes:
    """
    Prepares a clean, human-readable CSV byte stream from transactions DataFrame.
    """
    if df.empty:
        export_df = pd.DataFrame(columns=[
            "ID", "Date", "Type", "Category", "Amount", "Payment Method", "Description"
        ])
    else:
        export_df = df.copy()
        # Standardize column names
        rename_map = {
            "id": "ID",
            "date": "Date",
            "type": "Type",
            "category": "Category",
            "amount": "Amount",
            "payment_method": "Payment Method",
            "description": "Description",
        }
        export_df = export_df.rename(columns=rename_map)
        if "Date" in export_df.columns:
            export_df["Date"] = pd.to_datetime(export_df["Date"]).dt.strftime("%Y-%m-%d")

        cols = [c for c in ["ID", "Date", "Type", "Category", "Amount", "Payment Method", "Description"] if c in export_df.columns]
        export_df = export_df[cols]

    return export_df.to_csv(index=False).encode("utf-8")


def import_transactions_from_csv(csv_file) -> Tuple[int, int, List[str]]:
    """
    Imports transactions from an uploaded CSV file.
    Returns: (imported_count, skipped_count, error_messages)
    """
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        return 0, 0, [f"Could not read CSV file: {str(e)}"]

    # Normalize column names
    col_map = {c.strip().lower(): c for c in df.columns}
    required = ["type", "amount", "category", "date"]
    missing = [r for r in required if not any(r in k for k in col_map.keys())]
    if missing:
        return 0, 0, [f"Missing required columns in CSV: {', '.join(missing)}"]

    # Map headers to canonical names
    type_col = next(col_map[k] for k in col_map if "type" in k)
    amt_col = next(col_map[k] for k in col_map if "amount" in k)
    cat_col = next(col_map[k] for k in col_map if "category" in k)
    date_col = next(col_map[k] for k in col_map if "date" in k)
    pay_col = next((col_map[k] for k in col_map if "payment" in k or "method" in k), None)
    desc_col = next((col_map[k] for k in col_map if "desc" in k or "note" in k), None)

    imported = 0
    skipped = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            t_type = str(row[type_col]).strip().capitalize()
            if t_type not in ("Expense", "Income"):
                t_type = "Expense"

            amt = float(row[amt_col])
            cat = str(row[cat_col]).strip()
            d_val = pd.to_datetime(row[date_col]).strftime("%Y-%m-%d")
            p_method = str(row[pay_col]).strip() if pay_col and pd.notna(row[pay_col]) else "Other"
            desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""

            is_valid, err = validate_transaction(t_type, amt, cat, d_val, p_method, desc)
            if not is_valid:
                skipped += 1
                errors.append(f"Row {idx + 1}: {err}")
                continue

            # Ensure category exists in DB
            database.add_category(cat, t_type)

            database.add_transaction(t_type, amt, cat, d_val, p_method, desc)
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Row {idx + 1}: {str(e)}")

    return imported, skipped, errors
