import streamlit as st
from lib.state import init_app_state

st.set_page_config(page_title="Expense Tracker", layout="wide")
init_app_state()

pages = [
    st.Page("pages/1_Input.py", title="Input", icon=":material/add:"),
    st.Page("pages/2_History.py", title="History", icon=":material/history:"),
    st.Page("pages/3_Dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    st.Page("pages/4_Settings.py", title="Settings", icon=":material/settings:"),
]

pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
