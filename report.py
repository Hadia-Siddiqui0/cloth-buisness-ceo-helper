"""
report.py — the ONE function the dashboard (or anything else) needs to call.

get_full_report() loads every sheet, applies fill rules, runs every check,
generates plain-language explanations, and builds the data-quality summary.
Everything downstream just reads from the dict it returns.
"""

from config import FILE
from loaders import (
    PRODUCTION_LOADERS, load_contractor_invoice, load_petty_cash_ledger,
)
from cleaning import apply_fill_rules
from checks import (
    reconcile_profit, cost_structure_breakdown,
    product_margin_comparison, reconcile_running_balance,
)
from explanations import (
    explain_profit, explain_cost_structure, explain_margins,
    explain_balance, generate_key_insights,
)
from data_quality import generate_data_quality_report


def get_full_report(path=FILE, verbose=False):
    report = {"production": {}, "product_margins": None,
              "contractor_invoice": None, "petty_cash": None}

    for name, loader in PRODUCTION_LOADERS.items():
        df = apply_fill_rules(loader(path))
        profit_result = reconcile_profit(df, label=name, verbose=verbose)
        cost_result = cost_structure_breakdown(df, label=name, verbose=verbose)
        report["production"][name] = {
            "profit": profit_result,
            "cost_structure": cost_result,
            "profit_explanation": explain_profit(profit_result),
            "cost_explanation": explain_cost_structure(cost_result),
        }

    report["product_margins"] = product_margin_comparison(path, verbose=verbose)
    report["margins_explanation"] = explain_margins(report["product_margins"])

    report["contractor_invoice"] = reconcile_running_balance(
        load_contractor_invoice(path), in_col="Amount", out_col="Receive",
        balance_col="Balance", label="Contractor Invoice", verbose=verbose,
    )
    report["contractor_explanation"] = explain_balance(report["contractor_invoice"])

    report["petty_cash"] = reconcile_running_balance(
        load_petty_cash_ledger(path), in_col="Amount Recive", out_col="Used",
        balance_col="Balance", label="Petty Cash Ledger",
        expect_one_row_per_date=False, verbose=verbose,
    )
    report["petty_cash_explanation"] = explain_balance(report["petty_cash"])

    report["key_insights"] = generate_key_insights(report)
    report["data_quality"] = generate_data_quality_report(report)

    return report


if __name__ == "__main__":
    r = get_full_report(verbose=True)
    print("=" * 70)
    print("KEY INSIGHTS")
    for i, insight in enumerate(r["key_insights"], 1):
        print(f"{i}. {insight}")
    print()
    print("=" * 70)
    print(f"DATA QUALITY: {r['data_quality']['quality_score']}% "
          f"({r['data_quality']['checks_passed']}/{r['data_quality']['checks_run']} checks passed)")
    for issue in r["data_quality"]["issues"]:
        print(f" - {issue}")