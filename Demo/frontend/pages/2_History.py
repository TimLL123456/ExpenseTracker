import streamlit as st
import pandas as pd
from lib.api import get_transactions, ApiError

st.title("Expense Tracker")
st.header("Transaction History")

col1, col2, col3, col4 = st.columns(4)
with col1:
    filter_type = st.selectbox("Type", options=["All", "income", "expense"], index=0)
with col2:
    filter_category = st.text_input("Category (partial match)", placeholder="e.g., food")
with col3:
    filter_date_from = st.date_input("From Date", value=None)
with col4:
    filter_date_to = st.date_input("To Date", value=None)

fetch = st.button("Fetch History", type="primary")

if fetch:
    try:
        type_ = None if filter_type == "All" else filter_type
        date_from = filter_date_from.strftime("%Y-%m-%d") if filter_date_from else None
        date_to = filter_date_to.strftime("%Y-%m-%d") if filter_date_to else None

        data = get_transactions(
            base_url=st.session_state.api_base_url,
            timeout_sec=int(st.session_state.api_timeout_sec),
            type_=type_,
            category=filter_category.strip() or None,
            date_from=date_from,
            date_to=date_to,
        )

        if not data:
            st.info("No transactions found.")
        else:
            df = pd.DataFrame(data)
            preferred = ["id", "date", "type", "category", "description", "price"]
            cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
            df = df[cols]

            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="transactions.csv",
                mime="text/csv",
            )

    except ApiError as e:
        st.error(f"API error: {e}")
