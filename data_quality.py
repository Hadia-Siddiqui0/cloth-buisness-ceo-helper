"""
data_quality.py — Day 18: a single consolidated data-quality report across
every sheet, in the spirit of spec Section 15 ("Overall Data Quality: 87%").

This re-checks the full report for anything that didn't pass cleanly and
turns it into one summary — the kind of thing you'd show the CEO before he
even looks at his business numbers, so he knows how much to trust them.
"""


def generate_data_quality_report(full_report):
    issues = []
    checks_run = 0
    checks_passed = 0

    # Profit reconciliation, one check per production sheet.
    for name, section in full_report["production"].items():
        pf = section["profit"]
        checks_run += 1
        if pf["mismatch_count"] == 0:
            checks_passed += 1
        else:
            issues.append(
                f"{name}: {pf['mismatch_count']} of {pf['total_rows']} day(s) "
                f"where stated profit doesn't match revenue − cost."
            )

    # Product margin mismatches.
    margins = full_report["product_margins"]
    checks_run += 1
    if margins["mismatch_count"] == 0:
        checks_passed += 1
    else:
        issues.append(f"Product costing: {margins['mismatch_count']} product(s) with cost/profit mismatches.")
    if margins["excluded_count"] > 0:
        issues.append(
            f"Product costing: {margins['excluded_count']} product(s) missing enough data to include — "
            f"{', '.join(margins['excluded_products'])}."
        )

    # Balance reconciliations.
    for key in ("contractor_invoice", "petty_cash"):
        res = full_report[key]
        checks_run += 1
        if res["mismatch_count"] == 0:
            checks_passed += 1
        else:
            issues.append(f"{res['label']}: {res['mismatch_count']} row(s) with balance mismatches.")
        for issue in res["issues"]:
            issues.append(
                f"{res['label']}: {issue['type'].replace('_', ' ')} found on {len(issue['rows'])} row(s)."
            )

    quality_score = round((checks_passed / checks_run) * 100) if checks_run else 0

    return {
        "quality_score": quality_score,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "issues": issues,
        "issue_count": len(issues),
    }