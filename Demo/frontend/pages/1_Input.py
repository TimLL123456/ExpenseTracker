import streamlit as st
import pandas as pd
from datetime import date
from lib.api import process_text, ApiError

st.title("Expense Tracker")
st.header("Add Transactions")

# Check for success flag after rerun
if st.session_state.get("save_success", False):
    st.success(f"✅ All transactions saved successfully!")
    st.balloons()
    st.session_state.save_success = False  # Reset flag

# Multi-line input
text = st.text_area(
    "Enter one or more transaction sentences (one per line):",
    placeholder="e.g.,\nPaid 12.5 for lunch today\nReceived 1000 salary on December 20\nBought groceries for 85.3 yesterday\nSpent 30 on transportation",
    height=200,
)

submitted = st.button("Process Transactions", type="primary")

if submitted:
    if not text.strip():
        st.warning("Please enter at least one transaction sentence.")
        st.stop()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        st.warning("No valid sentences found.")
        st.stop()

    with st.spinner(f"Processing {len(lines)} transaction(s)..."):
        results = []
        errors = []

        for i, sentence in enumerate(lines, 1):
            try:
                result = process_text(
                    text=sentence,
                    base_url=st.session_state.api_base_url,
                    timeout_sec=int(st.session_state.api_timeout_sec),
                )
                extracted = result.get("extracted", {})
                if extracted:
                    extracted["original_sentence"] = sentence
                    results.append(extracted)
                else:
                    errors.append(f"Line {i}: No data extracted from response")
            except ApiError as e:
                errors.append(f"Line {i}: API error - {e}")

        if errors:
            st.error("Some lines failed to process:\n" + "\n".join(errors))

        if results:
            df = pd.DataFrame(results)

            # Convert date string to datetime.date
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

            # Ensure price is float
            df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)

            # Column order
            preferred_order = ["original_sentence", "date", "type", "category", "description", "price"]
            cols = [c for c in preferred_order if c in df.columns] + [c for c in df.columns if c not in preferred_order]
            df = df[cols]

            st.subheader("Review and Edit Transactions")
            st.info("You can edit fields directly. Changes will be saved upon confirmation.")

            edited_df = st.data_editor(
                df,
                num_rows="fixed",
                use_container_width=True,
                column_config={
                    "original_sentence": st.column_config.TextColumn(
                        "Original Sentence",
                        disabled=True,
                    ),
                    "date": st.column_config.DateColumn(
                        "Date",
                        format="YYYY-MM-DD",
                        required=True,
                        default=date.today(),
                    ),
                    "type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["income", "expense"],
                        required=True,
                    ),
                    "category": st.column_config.TextColumn("Category", required=True),
                    "description": st.column_config.TextColumn("Description", required=True),
                    "price": st.column_config.NumberColumn(
                        "Price",
                        format="%.2f",
                        min_value=0.0,
                        step=0.01,
                        required=True,
                    ),
                },
            )

            # Confirm save button with enhanced feedback
            if st.button("Confirm & Save All Transactions", type="primary"):
                # Prevent duplicate saves
                if st.session_state.get("last_saved_df") is not None and edited_df.equals(st.session_state.last_saved_df):
                    st.info("Transactions already saved. No changes detected.")
                    st.stop()

                with st.spinner("Saving transactions to database..."):
                    save_errors = []
                    success_count = 0
                    total = len(edited_df)

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for idx, (_, row) in enumerate(edited_df.iterrows()):
                        try:
                            mock_text = (
                                f"{row['type'].capitalize()} {row['price']:.2f} "
                                f"for {row['description']} on {row['date']} "
                                f"in category {row['category']}"
                            )
                            process_text(
                                text=mock_text,
                                base_url=st.session_state.api_base_url,
                                timeout_sec=int(st.session_state.api_timeout_sec),
                            )
                            success_count += 1
                        except ApiError as e:
                            save_errors.append(f"{row['original_sentence'] or 'Row ' + str(idx+1)}: {e}")
                        finally:
                            progress_bar.progress((idx + 1) / total)
                            status_text.text(f"Processing {idx + 1}/{total}...")

                    st.session_state.last_saved_df = edited_df.copy()

                    if save_errors:
                        st.error(f"⚠️ {success_count}/{total} saved. Failed:\n" + "\n".join(save_errors))
                    else:
                        st.session_state.save_success = True  # Set flag for post-rerun display
                        st.rerun()  # Rerun to clear form and trigger success display
        else:
            st.info("No transactions were successfully extracted.")