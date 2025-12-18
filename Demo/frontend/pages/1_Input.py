import streamlit as st
import pandas as pd
from lib.api import process_text, ApiError

st.title("Expense Tracker")
st.header("Add Transaction")

with st.form("add_tx_form", clear_on_submit=False):
    text = st.text_input(
        "Enter transaction sentence:",
        placeholder="e.g., Paid 12.5 for lunch today",
    )
    submitted = st.form_submit_button("Submit")

if submitted:
    if not text.strip():
        st.warning("Please enter text.")
    else:
        with st.spinner("Processing..."):
            try:
                result = process_text(
                    text=text.strip(),
                    base_url=st.session_state.api_base_url,
                    timeout_sec=int(st.session_state.api_timeout_sec),
                )
                st.success("Transaction stored!")

                extracted = result.get("extracted", {})
                if isinstance(extracted, dict) and extracted:
                    st.subheader("Extracted fields")
                    st.dataframe(pd.DataFrame([extracted]), use_container_width=True)
                else:
                    st.info("No extracted payload returned.")
            except ApiError as e:
                st.error(f"API error: {e}")
