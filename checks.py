"""
checks.py — the actual business-logic calculations: profit reconciliation,
cost structure, product margins, and running-balance reconciliation.

Every function returns a plain dict/DataFrame. Nothing is printed unless
verbose=True is passed — that keeps this module safe to import from a
dashboard, a script, or a notebook without unwanted console output.
"""

import pandas as pd

from config import FILE, COST_COLUMNS, PRODUCT_COST_COLUMNS, MISMATCH_TOLERANCE
from loaders import load_product_costing_sheet


def reconcile_profit(df, revenue_col="Total.1", cost_col="Total",
                      profit_col="Profit", label="", verbose=False):
    """Recompute Profit independently and flag rows where it doesn't match
    Revenue - Cost as stated in his sheet."""
    df = df.copy()
    df["computed_profit"] = df[revenue_col] - df[cost_col]
    df["profit_diff"] = (df["computed_profit"] - df[profit_col]).round(2)
    mismatches = df[df["profit_diff"].abs() > MISMATCH_TOLERANCE]

    result = {
        "label": label,
        "data": df,
        "total_rows": len(df),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[["Date", cost_col, revenue_col, profit_col,
                                   "computed_profit", "profit_diff"]],
        "total_revenue": df[revenue_col].sum(),
        "total_cost": df[cost_col].sum(),
        "total_profit": df[profit_col].sum(),
    }

    if verbose:
        print(f"--- Profit reconciliation: {label} ---")
        print(f"Total rows checked: {result['total_rows']}")
        print(f"Mismatches found: {result['mismatch_count']}")
        if result["mismatch_count"]:
            print(result["mismatches"].to_string())
        print()

    return result


def cost_structure_breakdown(df, cost_columns=COST_COLUMNS, label="", verbose=False):
    """What % of total cost each component represents, over the whole period."""
    present = [c for c in cost_columns if c in df.columns]
    totals = df[present].astype(float).sum().sort_values(ascending=False)
    grand_total = totals.sum()
    breakdown = pd.DataFrame({
        "component": totals.index,
        "amount": totals.values,
        "pct": (totals.values / grand_total * 100).round(1) if grand_total else 0,
    })
    breakdown = breakdown[breakdown["amount"] > 0].reset_index(drop=True)

    result = {
        "label": label,
        "breakdown": breakdown,
        "grand_total": grand_total,
        "top_component": breakdown.iloc[0]["component"] if len(breakdown) else None,
        "top_component_pct": breakdown.iloc[0]["pct"] if len(breakdown) else None,
    }

    if verbose:
        print(f"--- Cost structure: {label} ---")
        if grand_total == 0:
            print("No cost data recorded in this sheet.")
        else:
            for _, row in breakdown.iterrows():
                print(f"{row['component']:20s} Rs. {row['amount']:>12,.0f}  ({row['pct']}%)")
            print(f"{'TOTAL':20s} Rs. {grand_total:>12,.0f}")
        print()

    return result


def product_margin_comparison(path=FILE, verbose=False):
    """Recompute product-level cost/profit from Sheet4 and rank by margin %.
    Rows missing key fields are excluded and reported, not silently dropped."""
    df = load_product_costing_sheet(path)

    usable = df.dropna(subset=["Total", "Profit/peace", "Seal/Peace"]).copy()
    excluded = df[~df.index.isin(usable.index)]

    present = [c for c in PRODUCT_COST_COLUMNS if c in usable.columns]
    usable[present] = usable[present].fillna(0)

    usable["computed_total_cost"] = usable[present].sum(axis=1)
    usable["computed_profit"] = usable["Seal/Peace"] - usable["computed_total_cost"]
    usable["total_diff"] = (usable["computed_total_cost"] - usable["Total"]).round(2)
    usable["profit_diff"] = (usable["computed_profit"] - usable["Profit/peace"]).round(2)
    usable["margin_pct"] = (usable["Profit/peace"] / usable["Seal/Peace"] * 100).round(1)

    mismatches = usable[
        (usable["total_diff"].abs() > MISMATCH_TOLERANCE)
        | (usable["profit_diff"].abs() > MISMATCH_TOLERANCE)
    ]
    ranked = usable.sort_values("margin_pct", ascending=False).reset_index(drop=True)

    result = {
        "ranked": ranked[["Cloth ", "Seal/Peace", "computed_total_cost", "Profit/peace",
                           "margin_pct", "Total Peace", "Total Profit"]],
        "usable_count": len(usable),
        "excluded_count": len(excluded),
        "excluded_products": excluded["Cloth "].tolist(),
        "mismatch_count": len(mismatches),
        "best_product": ranked.iloc[0]["Cloth "] if len(ranked) else None,
        "best_margin_pct": ranked.iloc[0]["margin_pct"] if len(ranked) else None,
        "worst_product": ranked.iloc[-1]["Cloth "] if len(ranked) else None,
        "worst_margin_pct": ranked.iloc[-1]["margin_pct"] if len(ranked) else None,
    }

    if verbose:
        print("--- Product margin comparison (Sheet4) ---")
        print(f"Usable products: {result['usable_count']}  |  Excluded: {result['excluded_count']}")
        if result["excluded_count"]:
            print("Excluded:", result["excluded_products"])
        print(f"Mismatches: {result['mismatch_count']}")
        print(result["ranked"].to_string(index=False))
        print()

    return result


def reconcile_running_balance(df, in_col, out_col, balance_col, label="",
                               expect_one_row_per_date=True, verbose=False):
    """Recompute a running balance (previous + in - out) and compare to the
    sheet's own Balance column. Flags duplicate dates (for one-row-per-day
    ledgers) or out-of-order dates (for transaction-level ledgers)."""
    df = df.copy().reset_index(drop=True)
    df[in_col] = df[in_col].fillna(0)
    df[out_col] = df[out_col].fillna(0)

    running = 0.0
    computed = []
    for _, row in df.iterrows():
        running = running + row[in_col] - row[out_col]
        computed.append(running)
    df["computed_balance"] = computed
    df["balance_diff"] = (df["computed_balance"] - df[balance_col]).round(2)

    mismatches = df[df[balance_col].notna() & (df["balance_diff"].abs() > MISMATCH_TOLERANCE)]
    missing_balance = df[df[balance_col].isna()]

    issues = []
    if expect_one_row_per_date:
        dupes = df[df["Date"].notna() & df.duplicated(subset=["Date"], keep=False)]
        if len(dupes):
            issues.append({"type": "duplicate_dates", "rows": dupes})
    else:
        dated = df[df["Date"].notna()].copy()
        out_of_order = dated[dated["Date"] < dated["Date"].shift(1)]
        if len(out_of_order):
            issues.append({"type": "out_of_order_dates", "rows": out_of_order})

    result = {
        "label": label,
        "data": df,
        "total_rows": len(df),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "missing_balance_count": len(missing_balance),
        "issues": issues,
        "final_balance": df["computed_balance"].iloc[-1] if len(df) else None,
    }

    if verbose:
        print(f"--- Balance reconciliation: {label} ---")
        print(f"Total rows: {result['total_rows']}")
        print(f"Mismatches: {result['mismatch_count']}")
        if result["mismatch_count"]:
            print(mismatches.to_string())
        if result["missing_balance_count"]:
            print(f"Rows with no stated Balance: {result['missing_balance_count']}")
        for issue in issues:
            print(f"⚠ {issue['type']} ({len(issue['rows'])} rows)")
        print(f"Final balance: Rs. {result['final_balance']:,.0f}")
        print()

    return result