import streamlit as st

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💸",
    layout="wide"
)

page_1 = st.Page(
    page="C:\### Python Program\ExpenseTracker\draft\Multi-Page\page_1.py",
    title="Page 1",
    default=True
)

page_2 = st.Page(
    page="C:\### Python Program\ExpenseTracker\draft\Multi-Page\page_2.py",
    title="Page 2",
)

pg = st.navigation(
    pages=[
        page_1,
        page_2,
    ]
).run()