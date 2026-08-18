"""
app.py — the dashboard. Run with:

    streamlit run app.py

Requires all the other .py files (config, loaders, cleaning, checks,
explanations, data_quality, report) in the same folder, and the Excel file
either bundled alongside this script or uploaded through the sidebar.
"""

import streamlit as st
import plotly.express as px

from config import FILE
from report import get_full_report


def fmt_rs(value):
    """Format a Rupee amount safely, even if the value is None (e.g. an
    empty sheet with nothing to reconcile)."""
    if value is None:
        return "N/A"
    return f"Rs. {value:,.0f}"


def biggest_cost_driver_overall(report):
    """Combine the cost-structure breakdown across all three production
    sheets and find the single biggest cost category overall. Used by the
    Day 20 Q&A box — this doesn't calculate anything new, it just re-reads
    numbers report.py already computed."""
    combined = {}
    for section in report["production"].values():
        for _, row in section["cost_structure"]["breakdown"].iterrows():
            combined[row["component"]] = combined.get(row["component"], 0) + row["amount"]
    if not combined:
        return "No cost data has been recorded yet."
    top = max(combined, key=combined.get)
    total = sum(combined.values())
    pct = (combined[top] / total * 100) if total else 0
    return (
        f"Across all production, **{top}** is the biggest cost driver — "
        f"{fmt_rs(combined[top])} ({pct:.1f}% of total recorded cost)."
    )

st.set_page_config(page_title="Business Dashboard", layout="wide", page_icon="📊")

# Sidebar — file selection

st.sidebar.title("📁 Data")
uploaded = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])
data_path = uploaded if uploaded is not None else FILE
st.sidebar.caption(f"Currently using: {'uploaded file' if uploaded else FILE}")

try:
    with st.spinner("Reading and checking your data..."):
        report = get_full_report(path=data_path, verbose=False)
except Exception as e:
    st.error(f"Couldn't read this file. Details: {e}")
    st.stop()

st.title("Business Health Dashboard")
st.caption("Every number below is calculated directly from your uploaded file — nothing is estimated or invented.")


# Data quality banner (Day 18)

dq = report["data_quality"]
if dq["issue_count"] == 0:
    st.success(f"**Data Quality: {dq['quality_score']}%** — all {dq['checks_run']} checks passed, no issues found.")
else:
    st.warning(
        f"**Data Quality: {dq['quality_score']}%** — {dq['checks_passed']}/{dq['checks_run']} checks passed cleanly. "
        f"{dq['issue_count']} thing(s) worth reviewing with him (see bottom of page)."
    )


# Key insights (Day 15/19) — the 3-5 things that matter most, up top

st.subheader("What Stands Out")
for insight in report["key_insights"]:
    st.markdown(f"- {insight}")

st.divider()


# Top metrics — combine all three production sheets

total_revenue = sum(v["profit"]["total_revenue"] for v in report["production"].values())
total_cost = sum(v["profit"]["total_cost"] for v in report["production"].values())
total_profit = sum(v["profit"]["total_profit"] for v in report["production"].values())
outstanding = report["contractor_invoice"]["final_balance"]
petty_cash_balance = report["petty_cash"]["final_balance"]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Revenue", fmt_rs(total_revenue))
col2.metric("Total Cost", fmt_rs(total_cost))
col3.metric("Total Profit", fmt_rs(total_profit))
col4.metric("Outstanding (Contractor)", fmt_rs(outstanding))
col5.metric("Petty Cash Balance", fmt_rs(petty_cash_balance))

st.divider()


# Cost structure per production sheet

st.header("Where Is Money Going?")
tabs = st.tabs(list(report["production"].keys()))

for tab, (name, section) in zip(tabs, report["production"].items()):
    with tab:
        cs = section["cost_structure"]
        pf = section["profit"]

        st.markdown(f"_{section['profit_explanation']}_")
        st.markdown(f"_{section['cost_explanation']}_")

        c1, c2 = st.columns([2, 1])
        with c1:
            if cs["grand_total"] > 0:
                fig = px.bar(
                    cs["breakdown"], x="amount", y="component", orientation="h",
                    text="pct", labels={"amount": "Rs.", "component": ""},
                )
                fig.update_traces(texttemplate="%{text}%", textposition="outside")
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=350,
                                   margin=dict(l=0, r=20, t=10, b=0))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No cost data recorded in this sheet.")

        with c2:
            st.metric("Revenue", f"Rs. {pf['total_revenue']:,.0f}")
            st.metric("Cost", f"Rs. {pf['total_cost']:,.0f}")
            st.metric("Profit", f"Rs. {pf['total_profit']:,.0f}")
            if pf["mismatch_count"] == 0:
                st.success("✓ Profit numbers check out.")
            else:
                st.warning(f"⚠ {pf['mismatch_count']} row(s) don't match.")
                st.dataframe(pf["mismatches"], width="stretch")

st.divider()


# Product margin comparison

st.header("Which Products Earn the Most?")
margins = report["product_margins"]
st.markdown(f"_{report['margins_explanation']}_")

if margins["usable_count"] > 0:
    fig = px.bar(
        margins["ranked"], x="Cloth ", y="margin_pct",
        text="margin_pct", labels={"Cloth ": "Product", "margin_pct": "Margin %"},
        color="margin_pct", color_continuous_scale="Blues",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(height=400, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")

    with st.expander("See full product cost breakdown"):
        st.dataframe(
            margins["ranked"].rename(columns={
                "Cloth ": "Product", "Seal/Peace": "Sale Price",
                "computed_total_cost": "Cost", "Profit/peace": "Profit/piece",
                "margin_pct": "Margin %", "Total Peace": "Pieces Made",
                "Total Profit": "Total Profit",
            }),
            width="stretch",
        )
else:
    st.warning("No products have complete enough cost/price data to compare margins right now.")

if margins["excluded_count"] > 0:
    st.info(
        f"{margins['excluded_count']} product(s) couldn't be included — missing cost/price data: "
        f"{', '.join(margins['excluded_products'])}"
    )

st.divider()


# Payments & data quality issues

st.header("Payments & Ledgers")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Contractor Invoice")
    ci = report["contractor_invoice"]
    st.metric("Outstanding Balance", fmt_rs(ci["final_balance"]))
    st.markdown(f"_{report['contractor_explanation']}_")

with c2:
    st.subheader("Petty Cash")
    pc = report["petty_cash"]
    st.metric("Current Balance", fmt_rs(pc["final_balance"]))
    st.markdown(f"_{report['petty_cash_explanation']}_")

st.divider()


# Quick Questions (Day 20) — NOT a real chatbot. Hardcoded buttons that just
# re-display numbers already calculated above. Kept intentionally simple
# per the 30-day plan; a real conversational chatbot is Milestone 2 (Weeks
# 15-16), once raw material / finished-goods / customer-payment data exists
# for it to actually answer questions about.

st.header("Quick Questions")
st.caption("Pick a question below — every answer is pulled straight from the numbers already on this page, nothing new is calculated.")

qa_questions = {
    "What's my total profit?":
        lambda: f"Total profit across all production is **{fmt_rs(total_profit)}** "
                f"(revenue {fmt_rs(total_revenue)} minus cost {fmt_rs(total_cost)}).",
    "What's my biggest cost driver?":
        lambda: biggest_cost_driver_overall(report),
    "Which product has the best margin?":
        lambda: (f"**{margins['best_product']}** has the strongest margin at "
                  f"{margins['best_margin_pct']}%, vs {margins['worst_product']} at "
                  f"{margins['worst_margin_pct']}%.") if margins["usable_count"] > 0
                 else "Not enough product cost/price data yet to answer this.",
    "How much is outstanding with my contractor?":
        lambda: f"Outstanding contractor balance is **{fmt_rs(outstanding)}**.",
    "What's my petty cash balance?":
        lambda: f"Current petty cash balance is **{fmt_rs(petty_cash_balance)}**.",
    "Can I trust this data right now?":
        lambda: (f"Data quality is **{dq['quality_score']}%** — all {dq['checks_run']} checks passed, no issues found."
                  if dq["issue_count"] == 0 else
                  f"Data quality is **{dq['quality_score']}%** ({dq['checks_passed']}/{dq['checks_run']} checks passed). "
                  f"{dq['issue_count']} thing(s) worth reviewing — see the Data Quality Detail section below."),
}

qa_cols = st.columns(3)
for i, question_text in enumerate(qa_questions):
    if qa_cols[i % 3].button(question_text, use_container_width=True):
        st.session_state["qa_answer"] = qa_questions[question_text]()

if "qa_answer" in st.session_state:
    st.info(st.session_state["qa_answer"])

st.divider()


# Full data quality detail (Day 18)

st.header("Data Quality Detail")
st.markdown(f"**{dq['checks_passed']} / {dq['checks_run']} checks passed** ({dq['quality_score']}%)")
if dq["issues"]:
    for issue in dq["issues"]:
        st.markdown(f"- {issue}")
else:
    st.markdown("No issues found.")

st.caption("This is an early pilot dashboard. Raw material, waste, and shop/wholesale tracking will be added once your newer register data is available.")