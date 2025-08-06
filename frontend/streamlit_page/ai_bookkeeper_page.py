import streamlit as st

st.title("AI Bookkeeper")

user_input: str  = st.text_area(label="Enter Your Income/Expense")

st.write(user_input)
