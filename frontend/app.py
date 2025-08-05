import streamlit as st

# st.json(st.user)

def main():

    # Initialize session state for user
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.placeholder = st.empty()

    # Check if secrets are configured
    if not st.secrets.get("auth"):
        st.error("Please set [auth] in `secrets.toml`")
        st.stop()

    # Sign in
    if not st.user.is_logged_in:
        st.session_state.placeholder.title("Expense Tracker App")
        if st.button("Login"):
            st.login("google")
        st.stop()

    # Store user info to session_state
    st.session_state.logged_in = True
    st.session_state.user_info = st.user
    st.session_state.username = st.user.name
    st.session_state.user_id = st.user.sub

    with st.sidebar:
        # Greeting
        st.header(f"Welcome, {st.session_state.username}!")

        # Logout
        if st.button("Logout"):
            del st.session_state['logged_in']
            st.logout()

    # Page
    ai_bookkeeper_page = st.Page(
        page="./streamlit_page/ai_bookkeeper_page.py",
        title="AI Bookkeeper",
        default=True
    )
    transaction_history_page = st.Page(
        page="./streamlit_page/transaction_history_page.py",
        title="History",
    )
    user_setting_page = st.Page(
        page="./streamlit_page/user_setting_page.py",
        title="Setting",
    )

    st_pages = st.navigation(
        pages=[
            ai_bookkeeper_page,
            transaction_history_page,
            user_setting_page
        ]
    )
    st_pages.run()

if __name__ == "__main__":
    main()