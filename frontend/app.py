import streamlit as st

def apply_custom_css():
    """Apply custom CSS for styling the login page."""
    st.markdown("""
        <style>
        .main-container {
            text-align: center;
            padding: 2rem;
        }
        .app-title {
            color: #2e7d32;
            font-size: 2.5rem;
            font-weight: bold;
        }
        .app-subtitle {
            color: #616161;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        .login-button {
            background-color: #4285f4;
            color: white;
            font-size: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            border: none;
            cursor: pointer;
        }
        .login-button:hover {
            background-color: #357abd;
        }
        </style>
    """, unsafe_allow_html=True)

def render_login_in() -> None:

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown('<div class="app-title">Expense Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Track your expenses easily and securely with our app!</div>', unsafe_allow_html=True)

    if st.button("Login with Google", key="google_login", help="Click to sign in with your Google account"):
        st.login("google")

    st.markdown('</div>', unsafe_allow_html=True)

def main() -> None:

    st.set_page_config(page_title="Expense Tracker - Login", page_icon="💸", layout="centered")
    apply_custom_css()

    # Initialize session state for user
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.username = None

    # Check if secrets are configured
    if not st.secrets.get("auth"):
        st.error("Please set [auth] in `secrets.toml`")
        st.stop()

    if not st.user.is_logged_in:
        render_login_in()
        st.stop()

    else:
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