"""
explanations.py — Day 15: turns raw check results into plain-language
sentences, the way the spec's "Explain" button is supposed to work.

Every sentence here is built directly from a check's result dict — nothing
is invented or guessed. If a number isn't in the result, it doesn't appear
in the sentence.
"""


def explain_profit(result):
    """Plain-language summary of a profit reconciliation result."""
    label = result["label"]
    if result["mismatch_count"] == 0:
        integrity = f"All {result['total_rows']} recorded days check out — his stated profit matches revenue minus cost every time."
    else:
        integrity = (
            f"{result['mismatch_count']} of {result['total_rows']} days don't add up — "
            f"his stated profit doesn't match revenue minus cost. Worth reviewing those rows with him."
        )
    return (
        f"{label}: total revenue of Rs. {result['total_revenue']:,.0f} against "
        f"Rs. {result['total_cost']:,.0f} in costs, leaving Rs. {result['total_profit']:,.0f} profit. {integrity}"
    )


def explain_cost_structure(result):
    """Plain-language summary of where money is going in a production sheet."""
    label = result["label"]
    if result["grand_total"] == 0 or result["top_component"] is None:
        return f"{label}: no cost data recorded yet."
    return (
        f"{label}: the single biggest cost is {result['top_component']} at "
        f"{result['top_component_pct']}% of total recorded cost (Rs. {result['grand_total']:,.0f} overall)."
    )


def explain_margins(result):
    """Plain-language summary of the product margin comparison."""
    if result["usable_count"] == 0:
        return "No products have complete enough data to compare margins yet."
    text = (
        f"Out of {result['usable_count']} products with complete costing data, "
        f"{result['best_product']} has the strongest margin at {result['best_margin_pct']}%, "
        f"while {result['worst_product']} trails at {result['worst_margin_pct']}%."
    )
    if result["excluded_count"] > 0:
        text += (
            f" {result['excluded_count']} product(s) — {', '.join(result['excluded_products'])} — "
            f"are missing enough cost/price data to include yet."
        )
    return text


def explain_balance(result):
    """Plain-language summary of a running-balance reconciliation (contractor
    invoice or petty cash)."""
    label = result["label"]
    if result["total_rows"] == 0 or result["final_balance"] is None:
        return f"{label}: no rows found in this sheet — nothing to reconcile yet."
    if result["mismatch_count"] == 0:
        integrity = "The running balance checks out with no calculation errors."
    else:
        integrity = f"{result['mismatch_count']} row(s) don't match the expected running balance — worth a closer look."
    text = f"{label}: current balance is Rs. {result['final_balance']:,.0f}. {integrity}"
    for issue in result["issues"]:
        kind = issue["type"].replace("_", " ")
        text += f" Also flagged: {kind} on {len(issue['rows'])} row(s)."
    return text


def generate_key_insights(full_report, max_insights=5):
    """Day 15 / spec Section 19: a short, prioritized list of the most
    important things found across the whole report — not a wall of numbers.
    Priority order: real data problems first (they need attention), then
    the most business-relevant facts (biggest cost driver, best/worst margin).
    """
    insights = []

    # Priority 1: anything mismatched or flagged — these need his attention.
    for name, section in full_report["production"].items():
        pf = section["profit"]
        if pf["mismatch_count"] > 0:
            insights.append(
                f"⚠ {name}: {pf['mismatch_count']} day(s) where recorded profit doesn't match revenue − cost."
            )

    for key in ("contractor_invoice", "petty_cash"):
        res = full_report[key]
        if res["mismatch_count"] > 0:
            insights.append(f"⚠ {res['label']}: {res['mismatch_count']} row(s) with balance mismatches.")
        for issue in res["issues"]:
            insights.append(
                f"⚠ {res['label']}: {issue['type'].replace('_', ' ')} found on {len(issue['rows'])} row(s)."
            )

    # Priority 2: genuinely useful business facts, once problems are listed.
    margins = full_report["product_margins"]
    if margins["usable_count"] > 0:
        insights.append(
            f"{margins['best_product']} earns the best margin ({margins['best_margin_pct']}%), "
            f"nearly {round(margins['best_margin_pct'] / margins['worst_margin_pct'], 1)}x "
            f"the margin of {margins['worst_product']} ({margins['worst_margin_pct']}%)."
        )

    for name, section in full_report["production"].items():
        cs = section["cost_structure"]
        if cs["top_component"]:
            insights.append(
                f"In {name}, {cs['top_component']} is the largest cost driver at {cs['top_component_pct']}%."
            )

    return insights[:max_insights]