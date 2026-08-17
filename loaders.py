"""
loaders.py — reads each real sheet from the Excel file into a clean
DataFrame. Handles header offsets, embedded notes, and junk rows found
during the data audit. No calculations happen here — just loading.
"""

import pandas as pd
from config import FILE


def load_daily_progress_sheet(path=FILE):
    """Real daily production/cost/profit records, Nov 2017."""
    df = pd.read_excel(path, sheet_name="Daily Progress Sheet", header=2)
    df = df.dropna(how="all")
    df = df[df["Date"] != "Total"]
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    # Rows below the real table are handwritten staffing-assumption notes
    # (e.g. "Helper salary min 15,000"), not data rows — drop them.
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()]
    return df


def load_cmt_sheet(path=FILE):
    """Real daily cost breakdown, more process detail (cutting, embroidery, etc), Oct 2025."""
    df = pd.read_excel(path, sheet_name="CMT", header=2)
    df = df.dropna(how="all")
    df = df[df["Date"] != "Total"]
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()]
    return df


def load_self_made_sheet(path=FILE):
    """Similar structure to Daily Progress Sheet, in-house (non-contracted) production."""
    df = pd.read_excel(path, sheet_name="Self Made ", header=2)  # trailing space in sheet name
    df = df.dropna(how="all")
    df = df[df["Date"] != "Total"]
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()]
    return df


def load_product_costing_sheet(path=FILE):
    """Per-product cloth cost & margin reference table (Sheet4)."""
    df = pd.read_excel(path, sheet_name="Sheet4", header=2)
    df = df.dropna(how="all")
    return df


def load_contractor_invoice(path=FILE):
    """Contractor payment ledger: Amount invoiced / Received / Balance (Sheet3)."""
    df = pd.read_excel(path, sheet_name="Sheet3", header=3)
    df = df.dropna(how="all")
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df


def load_petty_cash_ledger(path=FILE):
    """Balance Sheet tab: day-to-day small expenses, Received / Used / Balance."""
    df = pd.read_excel(path, sheet_name="Balance Sheet", header=2)
    df = df.dropna(how="all")
    has_content = df["Description"].notna() | df["Amount Recive"].notna() | df["Used"].notna()
    df = df[has_content]
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df


# Registry used by app.py and data_quality.py to loop over every real sheet
# without repeating this list in multiple places.
ALL_LOADERS = {
    "Daily Progress Sheet": load_daily_progress_sheet,
    "CMT": load_cmt_sheet,
    "Self Made": load_self_made_sheet,
    "Product Costing (Sheet4)": load_product_costing_sheet,
    "Contractor Invoice (Sheet3)": load_contractor_invoice,
    "Petty Cash (Balance Sheet)": load_petty_cash_ledger,
}

PRODUCTION_LOADERS = {
    "Daily Progress Sheet": load_daily_progress_sheet,
    "CMT": load_cmt_sheet,
    "Self Made": load_self_made_sheet,
}