import streamlit as st
from datetime import date
from lib.api import get_transactions, ApiError
from lib.state import DEFAULT_BASE_URL, DEFAULT_TIMEOUT_SEC

st.title("Expense Tracker")
st.header("Settings")

st.subheader("API connection")
api_base_url = st.text_input("API base URL", value=st.session_state.api_base_url)
api_timeout = st.number_input(
    "Timeout (seconds)", min_value=3, max_value=120, value=int(st.session_state.api_timeout_sec)
)

st.subheader("Dashboard defaults")
dashboard_days = st.number_input(
    "Dashboard lookback (days)", min_value=1, max_value=3650, value=int(st.session_state.dashboard_days)
)

col1, col2, col3 = st.columns(3)
save = col1.button("Save", type="primary")
test = col2.button("Test connection")
reset = col3.button("Reset defaults")

if save:
    st.session_state.api_base_url = api_base_url.strip() or DEFAULT_BASE_URL
    st.session_state.api_timeout_sec = int(api_timeout)
    st.session_state.dashboard_days = int(dashboard_days)
    st.success("Saved.")

if test:
    try:
        today = date.today().strftime("%Y-%m-%d")
        _ = get_transactions(
            base_url=api_base_url.strip() or DEFAULT_BASE_URL,
            timeout_sec=int(api_timeout),
            date_from=today,
            date_to=today,
        )
        st.success("Connection OK.")
    except ApiError as e:
        st.error(f"Connection failed: {e}")

if reset:
    st.session_state.api_base_url = DEFAULT_BASE_URL
    st.session_state.api_timeout_sec = DEFAULT_TIMEOUT_SEC
    st.session_state.dashboard_days = 30
    st.success("Reset to defaults.")
