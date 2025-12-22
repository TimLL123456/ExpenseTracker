import streamlit as st

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SEC = 15

def init_app_state() -> None:
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = DEFAULT_BASE_URL

    if "api_timeout_sec" not in st.session_state:
        st.session_state.api_timeout_sec = DEFAULT_TIMEOUT_SEC

    if "dashboard_days" not in st.session_state:
        st.session_state.dashboard_days = 30
