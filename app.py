import streamlit as st
import sys

# Project path
PROJECT_PATH = "/content/drive/MyDrive/Multi_Disease_Prediction_GP"

if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

from auth import create_user, login_user


# =========================
# PAGE CONFIGURATION
# =========================

st.set_page_config(
    page_title="Multi-Disease Prediction System",
    page_icon="🧬",
    layout="centered"
)


# =========================
# SESSION STATE
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# =========================
# LOGIN / SIGN UP
# =========================

if not st.session_state.logged_in:

    st.title("🧬 Multi-Disease Prediction System")

    st.write(
        "Genetic Programming-Based Medical Data Mining System"
    )

    st.divider()

    tab_login, tab_signup = st.tabs(
        ["🔐 Login", "📝 Sign Up"]
    )


    # =========================
    # LOGIN
    # =========================

    with tab_login:

        st.subheader("Login")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔐 Login",
            use_container_width=True
        ):

            user = login_user(
                username,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.user = user

                st.success(
                    f"Welcome back, {user['full_name']}!"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )


    # =========================
    # SIGN UP
    # =========================

    with tab_signup:

        st.subheader("Create an Account")

        full_name = st.text_input(
            "Full Name",
            key="signup_full_name"
        )

        email = st.text_input(
            "Email Address",
            key="signup_email"
        )

        user_type = st.selectbox(
            "User Type",
            ["Personal", "Organisation"],
            key="signup_user_type"
        )

        organisation_name = ""

        if user_type == "Organisation":

            organisation_name = st.text_input(
                "Organisation Name",
                key="signup_organisation"
            )

        username = st.text_input(
            "Choose a Username",
            key="signup_username"
        )

        password = st.text_input(
            "Create Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm_password"
        )


        if st.button(
            "📝 Create Account",
            use_container_width=True
        ):

            if password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                success, message = create_user(
                    full_name=full_name,
                    email=email,
                    user_type=user_type,
                    organisation_name=organisation_name,
                    username=username,
                    password=password
                )

                if success:

                    st.success(message)

                    st.info(
                        "Your account has been created. "
                        "You can now log in."
                    )

                else:

                    st.error(message)


else:

    # =========================
    # TEMPORARY DASHBOARD
    # =========================

    user = st.session_state.user

    st.title("🏠 Dashboard")

    st.success(
        f"Welcome, {user['full_name']}!"
    )

    st.write(
        f"**Username:** {user['username']}"
    )

    st.write(
        f"**Email:** {user['email']}"
    )

    st.write(
        f"**Account Type:** {user['user_type']}"
    )

    if user["user_type"] == "Organisation":

        st.write(
            f"**Organisation:** "
            f"{user['organisation_name']}"
        )

    st.divider()

    st.info(
        "Prediction dashboard will be connected next."
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()
