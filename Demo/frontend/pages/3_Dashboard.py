import streamlit as st
import pandas as pd
from datetime import date, timedelta
from lib.api import get_transactions, ApiError

st.title("Expense Tracker")
st.header("Dashboard")

days = int(st.session_state.dashboard_days)
today = date.today()
date_from = (today - timedelta(days=days)).strftime("%Y-%m-%d")
date_to = today.strftime("%Y-%m-%d")

st.caption(f"Showing last {days} days: {date_from} to {date_to}")

try:
    data = get_transactions(
        base_url=st.session_state.api_base_url,
        timeout_sec=int(st.session_state.api_timeout_sec),
        date_from=date_from,
        date_to=date_to,
    )

    if not data:
        st.info("No transactions in the selected period.")
        st.stop()

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)

    income = df.loc[df["type"] == "income", "price"].sum()
    expense = df.loc[df["type"] == "expense", "price"].sum()
    net = income - expense

    c1, c2, c3 = st.columns(3)
    c1.metric("Total income", f"{income:,.2f}")
    c2.metric("Total expense", f"{expense:,.2f}")
    c3.metric("Net", f"{net:,.2f}")

    st.subheader("Expense by category")
    exp = df[df["type"] == "expense"].copy()
    if exp.empty:
        st.info("No expenses to group by category.")
    else:
        by_cat = exp.groupby("category", dropna=False)["price"].sum().sort_values(ascending=False)
        st.bar_chart(by_cat)

    st.subheader("Daily net (income - expense)")
    df["day"] = df["date"].dt.date
    daily = (
        df.pivot_table(index="day", columns="type", values="price", aggfunc="sum", fill_value=0.0)
        .sort_index()
    )
    daily["net"] = daily.get("income", 0.0) - daily.get("expense", 0.0)
    st.line_chart(daily["net"])

except ApiError as e:
    st.error(f"API error: {e}")
