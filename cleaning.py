"""
cleaning.py — applies fill rules to loaded sheets.

Blanks in this data mean different things depending on the column, so
nothing gets a blind fillna(0). See config.py for the column lists this
relies on.
"""

from config import COST_COLUMNS


def apply_fill_rules(df):
    """Fill blanks according to what they actually mean, not blindly.
    - Cost columns: blank = not charged that day -> 0
    - Quantity: blank = idle/no-production day -> 0 (meaningful, not missing)
    - Article (product ID) and other identifiers: left as NaN on purpose,
      since inventing a product ID for an idle day would be wrong.
    """
    df = df.copy()
    present_cost_cols = [c for c in COST_COLUMNS if c in df.columns]
    df[present_cost_cols] = df[present_cost_cols].fillna(0)
    if "Quantity" in df.columns:
        df["Quantity"] = df["Quantity"].fillna(0)
    return df