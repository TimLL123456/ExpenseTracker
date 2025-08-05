import streamlit as st

st.title("Sign in")

if not st.user.is_logged_in:
    if st.button("Login"):
        st.login("google")
else:
    st.json(st.user)

    if st.button("Logout"):
        st.logout()