import html
import json

import streamlit as st
import sys
import os
import pandas as pd

# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

try:
    from auth import create_user, login_user, get_supabase
    from prediction_engine import predict_disease
except Exception as import_error:
    st.error(
        f"The app could not start: "
        f"{type(import_error).__name__}: {import_error}"
    )
    st.stop()


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="GP-MED",
    page_icon="🧬",
    layout="wide"
)


# =========================================================
# DATABASE
# =========================================================

def save_prediction(
    username,
    patient_id,
    disease,
    prediction,
    result,
    gp_score,
    threshold,
    input_data=None
):

    if input_data is not None and not isinstance(input_data, str):
        if hasattr(input_data, "to_dict"):
            input_data = json.dumps(
                input_data.to_dict(orient="records"),
                default=str
            )
        else:
            input_data = json.dumps(input_data, default=str)

    get_supabase().table("predictions").insert({
        "username": username,
        "patient_id": str(patient_id),
        "disease": disease,
        "prediction": str(prediction),
        "result": str(result),
        "gp_score": float(gp_score),
        "threshold": float(threshold),
        "input_data": input_data,
    }).execute()


def get_prediction_history(username):

    res = (
        get_supabase()
        .table("predictions")
        .select(
            "patient_id,disease,prediction,result,"
            "gp_score,threshold,input_data,created_at"
        )
        .eq("username", username)
        .order("created_at", desc=True)
        .execute()
    )

    df = pd.DataFrame(
        res.data,
        columns=[
            "patient_id", "disease", "prediction", "result",
            "gp_score", "threshold", "input_data", "created_at"
        ]
    )

    df["prediction"] = pd.to_numeric(
        df["prediction"],
        errors="coerce"
    ).fillna(0).astype(int)

    return df


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# =========================================================
# CUSTOM STYLE
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --navy: #0b1f3a;
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --bg: #f1f5f9;
        --accent: #0d9488;
        --accent-dark: #0f766e;
    }

    /* ---------- Base ---------- */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    }

    .stApp {
        background: var(--bg);
    }

    #MainMenu, footer, [data-testid="stDeployButton"] {
        visibility: hidden;
        display: none;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    .stApp p, .stApp li, .stApp span, .stApp label {
        color: var(--ink);
    }

    /* ---------- Headings ---------- */
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        color: var(--ink);
        letter-spacing: -0.02em;
        margin: 0 0 0.25rem 0;
        line-height: 1.2;
    }

    .subtitle {
        font-size: 1rem;
        color: var(--muted);
        margin-top: 0;
    }

    .stMarkdown h3 {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--ink);
        letter-spacing: -0.01em;
        margin-top: 0.5rem;
    }

    .stMarkdown h2, .stMarkdown h4 {
        color: var(--ink);
        font-weight: 700;
    }

    hr {
        border-color: var(--line) !important;
        margin: 1.4rem 0 !important;
    }

    /* ---------- Cards (kept for compatibility) ---------- */
    .card {
        padding: 25px;
        border-radius: 16px;
        background-color: #ffffff;
        border: 1px solid var(--line);
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        margin-bottom: 20px;
    }

    .result-box {
        padding: 25px;
        border-radius: 16px;
        background-color: #f0fdfa;
        border: 1px solid #99f6e4;
        margin-top: 20px;
    }

    /* ---------- Metrics ---------- */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }

    [data-testid="stMetricLabel"] p {
        color: var(--muted) !important;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-weight: 800;
        font-size: 1.7rem;
    }

    [data-testid="stMetricValue"] > div {
        white-space: normal;
        line-height: 1.2;
    }

    /* ---------- Inputs ---------- */
    [data-testid="stWidgetLabel"] p {
        color: #334155 !important;
        font-weight: 600;
        font-size: 0.85rem;
    }

    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="select"] > div {
        background: #ffffff !important;
        border-radius: 10px !important;
    }

    [data-baseweb="input"],
    [data-baseweb="select"] > div {
        border: 1px solid #cbd5e1 !important;
    }

    [data-baseweb="input"]:focus-within,
    [data-baseweb="select"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15) !important;
    }

    .stTextInput input,
    .stNumberInput input,
    [data-baseweb="select"] div {
        color: var(--ink) !important;
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent), var(--accent-dark));
        color: #ffffff !important;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 1.2rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        box-shadow: 0 2px 6px rgba(13, 148, 136, 0.25);
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }

    .stButton > button p {
        color: #ffffff !important;
        font-weight: 600;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(13, 148, 136, 0.3);
        border: none;
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* ---------- Tabs ---------- */
    [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--line);
    }

    [data-baseweb="tab"] {
        font-weight: 600;
        padding: 0.6rem 1rem;
    }

    [data-baseweb="tab"] p {
        color: var(--muted) !important;
        font-weight: 600;
    }

    [data-baseweb="tab"][aria-selected="true"] p {
        color: var(--accent-dark) !important;
    }

    [data-baseweb="tab-highlight"] {
        background-color: var(--accent) !important;
    }

    /* ---------- Tables, alerts, charts ---------- */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
        border: 1px solid var(--line);
    }

    [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }

    .stCaption, [data-testid="stCaptionContainer"] p {
        color: var(--muted) !important;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1f3a 0%, #0c3347 100%);
        border-right: none;
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        display: none;
    }

    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
        display: none;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.25rem;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 0.65rem 0.9rem;
        border-radius: 10px;
        width: 100%;
        cursor: pointer;
        transition: background 0.12s ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: rgba(13, 148, 136, 0.35);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label p {
        font-weight: 600;
        font-size: 0.95rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: none;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.16);
        box-shadow: none;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.4rem 0.2rem 0.2rem;
    }

    .brand-logo {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: linear-gradient(135deg, #14b8a6, #0d9488);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
    }

    .brand-name {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        color: #ffffff !important;
        line-height: 1.1;
    }

    .brand-sub {
        font-size: 0.75rem;
        color: #94a3b8 !important;
    }

    .user-chip {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        background: rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 0.7rem 0.8rem;
        margin-top: 0.4rem;
    }

    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #14b8a6;
        color: #ffffff !important;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .user-name {
        font-weight: 600;
        font-size: 0.9rem;
        line-height: 1.2;
        color: #ffffff !important;
    }

    .user-role {
        font-size: 0.75rem;
        color: #94a3b8 !important;
    }

    /* ---------- Login hero ---------- */
    .hero {
        text-align: center;
        padding-bottom: 0.5rem;
    }

    .hero-logo {
        width: 64px;
        height: 64px;
        border-radius: 18px;
        background: linear-gradient(135deg, #14b8a6, #0d9488);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 8px 20px rgba(13, 148, 136, 0.3);
    }

    .hero .main-title {
        font-size: 2.2rem;
    }

    .hero-note {
        font-size: 0.8rem;
        color: var(--muted);
        margin-top: 0.4rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOGIN / SIGN UP
# =========================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 540px !important;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 22px;
            padding: 2.5rem 2.5rem 2rem !important;
            margin-top: 4vh;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
        }
        </style>
        <div class="hero">
            <div class="hero-logo">🧬</div>
            <div class="main-title">GP-MED</div>
            <div class="subtitle">
                Genetic Programming-Based Medical Disease Prediction
            </div>
            <div class="hero-note">
                For research and educational purposes
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        ""
    )

    st.divider()

    login_tab, signup_tab = st.tabs(
        ["🔐 Login", "📝 Create Account"]
    )


    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        st.subheader("Welcome Back")

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
            "Login",
            use_container_width=True
        ):

            user = login_user(
                username,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.user = user

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )


    # =====================================================
    # SIGN UP
    # =====================================================

    with signup_tab:

        st.subheader("Create Your Account")

        full_name = st.text_input(
            "Full Name",
            key="signup_full_name"
        )

        email = st.text_input(
            "Email Address",
            key="signup_email"
        )

        user_type = st.selectbox(
            "Account Type",
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
            "Choose Username",
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
            "Create Account",
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
                        "Account created successfully. "
                        "You can now log in."
                    )

                else:

                    st.error(message)


# =========================================================
# MAIN APPLICATION
# =========================================================

else:

    user = st.session_state.user

    # -----------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------

    _name = html.escape(str(user["full_name"] or ""))
    _role = html.escape(str(user["user_type"] or ""))
    _initial = _name[:1].upper() or "U"

    st.sidebar.markdown(
        f"""
        <div class="brand">
            <div class="brand-logo">🧬</div>
            <div>
                <div class="brand-name">GP-MED</div>
                <div class="brand-sub">Disease Prediction</div>
            </div>
        </div>
        <div class="user-chip">
            <div class="avatar">{_initial}</div>
            <div>
                <div class="user-name">{_name}</div>
                <div class="user-role">{_role}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🩺 New Prediction",
            "📋 Records",
            "👤 Profile"
        ]
    )



    if "page_override" in st.session_state:

        page = st.session_state.page_override

        del st.session_state.page_override
    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()


    # =====================================================
    # DASHBOARD
    # =====================================================

    if page == "🏠 Dashboard":

        st.markdown(
            '<div class="main-title">Dashboard</div>',
            unsafe_allow_html=True
        )

        st.write(
            f"Welcome back, {user['full_name']}."
        )

        history = get_prediction_history(
            user["username"]
        )

        # -------------------------------------------------
        # EMPTY DASHBOARD
        # -------------------------------------------------

        if history.empty:

            st.divider()

            st.info(
                "No prediction records yet. "
                "Make your first prediction to start seeing your analytics."
            )

            st.markdown("### Get started")

            st.write(
                "Your prediction activity, disease distribution, "
                "and recent records will appear here after you make "
                "your first prediction."
            )

            st.markdown(
                """
                **Available disease predictions**

                • Diabetes  
                • Heart Disease  
                • Breast Cancer  
                • Stroke
                """
            )

            st.caption(
                "Use **New Prediction** in the sidebar to begin."
            )

        # -------------------------------------------------
        # DATA-DRIVEN DASHBOARD
        # -------------------------------------------------

        else:

            history["created_at"] = pd.to_datetime(
                history["created_at"],
                errors="coerce"
            )

            now = pd.Timestamp.now()

            total_predictions = len(history)

            positive_predictions = int(
                history["prediction"].sum()
            )

            negative_predictions = (
                total_predictions - positive_predictions
            )

            most_tested = (
                history["disease"].value_counts().idxmax()
                if not history.empty
                else "—"
            )

            # -------------------------------------------------
            # SUMMARY METRICS
            # -------------------------------------------------

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Predictions",
                    total_predictions
                )

            with col2:
                st.metric(
                    "Positive Predictions",
                    positive_predictions
                )

            with col3:
                st.metric(
                    "Negative Predictions",
                    negative_predictions
                )

            with col4:
                st.metric(
                    "Most Tested Disease",
                    most_tested
                )

            st.divider()

            # -------------------------------------------------
            # ACTIVITY + DISEASE DISTRIBUTION
            # -------------------------------------------------

            left, right = st.columns(2)

            with left:

                st.markdown("### Prediction Activity")

                activity = (
                    history
                    .dropna(subset=["created_at"])
                    .assign(
                        date=lambda x:
                        x["created_at"].dt.date
                    )
                    .groupby("date")
                    .size()
                    .rename("Predictions")
                )

                if not activity.empty:
                    st.line_chart(
                        activity,
                        use_container_width=True
                    )

            with right:

                st.markdown("### Disease Distribution")

                disease_distribution = (
                    history["disease"]
                    .value_counts()
                    .rename("Predictions")
                )

                st.bar_chart(
                    disease_distribution,
                    use_container_width=True
                )

            st.divider()

            # -------------------------------------------------
            # RECENT PREDICTIONS
            # -------------------------------------------------

            st.markdown("### Recent Predictions")

            recent = history.head(5).copy()

            recent["created_at"] = (
                recent["created_at"]
                .dt.strftime("%d %b %Y, %I:%M %p")
            )

            recent = recent[
                [
                    "patient_id",
                    "disease",
                    "result",
                    "gp_score",
                    "created_at"
                ]
            ]

            recent.columns = [
                "Patient ID",
                "Disease",
                "Result",
                "GP Decision Score",
                "Date"
            ]

            st.dataframe(
                recent,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "GP Decision Score is the numerical output of the "
                "evolved Genetic Programming model. It is not a probability."
            )


    # =====================================================
    # DISEASE PREDICTION
    # =====================================================

    elif page == "🩺 New Prediction":

        st.markdown(
            '<div class="main-title">Disease Prediction</div>',
            unsafe_allow_html=True
        )

        disease = st.selectbox(
            "Select Disease",
            [
                "Diabetes",
                "Heart Disease",
                "Breast Cancer",
                "Stroke"
            ]
        )

        st.divider()


        # =================================================
        # DIABETES
        # =================================================

        if disease == "Diabetes":

            st.subheader("Diabetes Prediction")

            col1, col2 = st.columns(2)

            with col1:

                age = st.number_input(
                    "Age",
                    min_value=1,
                    max_value=120,
                    value=30
                )

                gender = st.selectbox(
                    "Gender",
                    ["Male", "Female"]
                )

                polyuria = st.selectbox(
                    "Polyuria",
                    ["Yes", "No"]
                )

                polydipsia = st.selectbox(
                    "Polydipsia",
                    ["Yes", "No"]
                )

                sudden_weight_loss = st.selectbox(
                    "Sudden Weight Loss",
                    ["Yes", "No"]
                )

                weakness = st.selectbox(
                    "Weakness",
                    ["Yes", "No"]
                )

                polyphagia = st.selectbox(
                    "Polyphagia",
                    ["Yes", "No"]
                )

                genital_thrush = st.selectbox(
                    "Genital Thrush",
                    ["Yes", "No"]
                )

            with col2:

                visual_blurring = st.selectbox(
                    "Visual Blurring",
                    ["Yes", "No"]
                )

                itching = st.selectbox(
                    "Itching",
                    ["Yes", "No"]
                )

                irritability = st.selectbox(
                    "Irritability",
                    ["Yes", "No"]
                )

                delayed_healing = st.selectbox(
                    "Delayed Healing",
                    ["Yes", "No"]
                )

                partial_paresis = st.selectbox(
                    "Partial Paresis",
                    ["Yes", "No"]
                )

                muscle_stiffness = st.selectbox(
                    "Muscle Stiffness",
                    ["Yes", "No"]
                )

                alopecia = st.selectbox(
                    "Alopecia",
                    ["Yes", "No"]
                )

                obesity = st.selectbox(
                    "Obesity",
                    ["Yes", "No"]
                )

            patient_id = st.text_input(
                "Patient ID"
            )

            if st.button(
                "🔍 Predict Diabetes",
                use_container_width=True
            ):

                input_data = pd.DataFrame([{
                    "Age": age,
                    "Gender": gender,
                    "Polyuria": polyuria,
                    "Polydipsia": polydipsia,
                    "sudden weight loss": sudden_weight_loss,
                    "weakness": weakness,
                    "Polyphagia": polyphagia,
                    "Genital thrush": genital_thrush,
                    "visual blurring": visual_blurring,
                    "Itching": itching,
                    "Irritability": irritability,
                    "delayed healing": delayed_healing,
                    "partial paresis": partial_paresis,
                    "muscle stiffness": muscle_stiffness,
                    "Alopecia": alopecia,
                    "Obesity": obesity
                }])

                result = predict_disease(
                    "Diabetes",
                    input_data
                )

                save_prediction(
                    user["username"],
                    patient_id,
                    result["Disease"],
                    result["Prediction"],
                    result["Result"],
                    result["GP Score"],
                    0,
                    input_data
                )

                st.success(
                    f"Prediction: {result['Result']}"
                )

                st.write(
                    f"GP Score: `{result['GP Score']:.4f}`"
                )


        # =================================================
        # HEART DISEASE
        # =================================================

        elif disease == "Heart Disease":

            st.subheader("Heart Disease Prediction")

            col1, col2 = st.columns(2)

            with col1:

                age = st.number_input(
                    "Age",
                    min_value=1,
                    max_value=120,
                    value=50
                )

                sex = st.selectbox(
                    "Sex",
                    [0, 1],
                    format_func=lambda x:
                    "Female" if x == 0 else "Male"
                )

                cp = st.number_input(
                    "Chest Pain Type (cp)",
                    min_value=0,
                    max_value=3,
                    value=0
                )

                trestbps = st.number_input(
                    "Resting Blood Pressure",
                    min_value=50.0,
                    max_value=250.0,
                    value=120.0
                )

                chol = st.number_input(
                    "Cholesterol",
                    min_value=50.0,
                    max_value=700.0,
                    value=200.0
                )

                fbs = st.selectbox(
                    "Fasting Blood Sugar > 120 mg/dl",
                    [0, 1]
                )

                restecg = st.number_input(
                    "Resting ECG",
                    min_value=0,
                    max_value=2,
                    value=0
                )

            with col2:

                thalach = st.number_input(
                    "Maximum Heart Rate",
                    min_value=50.0,
                    max_value=250.0,
                    value=150.0
                )

                exang = st.selectbox(
                    "Exercise Induced Angina",
                    [0, 1]
                )

                oldpeak = st.number_input(
                    "ST Depression",
                    min_value=0.0,
                    max_value=10.0,
                    value=1.0
                )

                slope = st.number_input(
                    "Slope",
                    min_value=0,
                    max_value=2,
                    value=1
                )

                ca = st.number_input(
                    "Number of Major Vessels (ca)",
                    min_value=0,
                    max_value=4,
                    value=0
                )

                thal = st.number_input(
                    "Thal",
                    min_value=0,
                    max_value=3,
                    value=1
                )

            patient_id = st.text_input(
                "Patient ID"
            )

            if st.button(
                "🔍 Predict Heart Disease",
                use_container_width=True
            ):

                input_data = pd.DataFrame([{
                    "age": age,
                    "sex": sex,
                    "cp": cp,
                    "trestbps": trestbps,
                    "chol": chol,
                    "fbs": fbs,
                    "restecg": restecg,
                    "thalach": thalach,
                    "exang": exang,
                    "oldpeak": oldpeak,
                    "slope": slope,
                    "ca": ca,
                    "thal": thal
                }])

                result = predict_disease(
                    "Heart Disease",
                    input_data
                )

                save_prediction(
                    user["username"],
                    patient_id,
                    result["Disease"],
                    result["Prediction"],
                    result["Result"],
                    result["GP Score"],
                    0,
                    input_data
                )

                st.success(
                    f"Prediction: {result['Result']}"
                )

                st.write(
                    f"GP Score: `{result['GP Score']:.4f}`"
                )


        # =================================================
        # BREAST CANCER
        # =================================================

        elif disease == "Breast Cancer":

            st.subheader("Breast Cancer Prediction")

            st.info(
                "Enter the 30 diagnostic measurements "
                "used by the trained model."
            )

            feature_names = [
                "radius_mean",
                "texture_mean",
                "perimeter_mean",
                "area_mean",
                "smoothness_mean",
                "compactness_mean",
                "concavity_mean",
                "concave_points_mean",
                "symmetry_mean",
                "fractal_dimension_mean",
                "radius_se",
                "texture_se",
                "perimeter_se",
                "area_se",
                "smoothness_se",
                "compactness_se",
                "concavity_se",
                "concave_points_se",
                "symmetry_se",
                "fractal_dimension_se",
                "radius_worst",
                "texture_worst",
                "perimeter_worst",
                "area_worst",
                "smoothness_worst",
                "compactness_worst",
                "concavity_worst",
                "concave_points_worst",
                "symmetry_worst",
                "fractal_dimension_worst"
            ]

            values = {}

            cols = st.columns(3)

            for i, feature in enumerate(feature_names):

                with cols[i % 3]:

                    values[feature] = st.number_input(
                        feature.replace("_", " ").title(),
                        value=0.0,
                        format="%.5f",
                        key=f"breast_{feature}"
                    )

            patient_id = st.text_input(
                "Patient ID",
                key="breast_patient_id"
            )

            if st.button(
                "🔍 Predict Breast Cancer",
                use_container_width=True
            ):

                input_data = pd.DataFrame(
                    [values]
                )

                result = predict_disease(
                    "Breast Cancer",
                    input_data
                )

                save_prediction(
                    user["username"],
                    patient_id,
                    result["Disease"],
                    result["Prediction"],
                    result["Result"],
                    result["GP Score"],
                    0,
                    input_data
                )

                st.success(
                    f"Prediction: {result['Result']}"
                )

                st.write(
                    f"GP Score: `{result['GP Score']:.4f}`"
                )


        # =================================================
        # STROKE
        # =================================================

        elif disease == "Stroke":

            st.subheader("Stroke Prediction")

            col1, col2 = st.columns(2)

            with col1:

                gender = st.selectbox(
                    "Gender",
                    ["Male", "Female", "Other"]
                )

                age = st.number_input(
                    "Age",
                    min_value=0.0,
                    max_value=120.0,
                    value=40.0
                )

                hypertension = st.selectbox(
                    "Hypertension",
                    [0, 1]
                )

                heart_disease = st.selectbox(
                    "Heart Disease",
                    [0, 1]
                )

                ever_married = st.selectbox(
                    "Ever Married",
                    ["Yes", "No"]
                )

            with col2:

                work_type = st.selectbox(
                    "Work Type",
                    [
                        "Private",
                        "Self-employed",
                        "Govt_job",
                        "children",
                        "Never_worked"
                    ]
                )

                residence_type = st.selectbox(
                    "Residence Type",
                    ["Urban", "Rural"]
                )

                avg_glucose_level = st.number_input(
                    "Average Glucose Level",
                    min_value=0.0,
                    value=100.0
                )

                bmi = st.number_input(
                    "BMI",
                    min_value=0.0,
                    value=25.0
                )

                smoking_status = st.selectbox(
                    "Smoking Status",
                    [
                        "formerly smoked",
                        "never smoked",
                        "smokes",
                        "Unknown"
                    ]
                )

            patient_id = st.text_input(
                "Patient ID"
            )

            if st.button(
                "🔍 Predict Stroke",
                use_container_width=True
            ):

                input_data = pd.DataFrame([{
                    "gender": gender,
                    "age": age,
                    "hypertension": hypertension,
                    "heart_disease": heart_disease,
                    "ever_married": ever_married,
                    "work_type": work_type,
                    "Residence_type": residence_type,
                    "avg_glucose_level": avg_glucose_level,
                    "bmi": bmi,
                    "smoking_status": smoking_status
                }])

                result = predict_disease(
                    "Stroke",
                    input_data
                )

                save_prediction(
                    user["username"],
                    patient_id,
                    result["Disease"],
                    result["Prediction"],
                    result["Result"],
                    result["GP Score"],
                    0,
                    input_data
                )

                st.success(
                    f"Prediction: {result['Result']}"
                )

                st.write(
                    f"GP Score: `{result['GP Score']:.4f}`"
                )


    # =====================================================
    # RECORDS
    # =====================================================

    elif page == "📋 Records":

        st.markdown(
            '<div class="main-title">Prediction Records</div>',
            unsafe_allow_html=True
        )

        st.write(
            "View your previous disease prediction records."
        )

        history = get_prediction_history(
            user["username"]
        )

        if history.empty:

            st.info(
                "No prediction records yet. "
                "Make your first prediction to see it here."
            )

        else:

            # -------------------------------------------------
            # DISEASE FILTER
            # -------------------------------------------------

            diseases = ["All Diseases"] + sorted(
                history["disease"].dropna().unique().tolist()
            )

            selected_disease = st.selectbox(
                "Filter by disease",
                diseases
            )

            filtered = history.copy()

            if selected_disease != "All Diseases":

                filtered = filtered[
                    filtered["disease"] == selected_disease
                ]

            # -------------------------------------------------
            # RECORD TABLE
            # -------------------------------------------------

            st.markdown("### Your Records")

            display_records = filtered.copy()

            display_records["created_at"] = pd.to_datetime(
                display_records["created_at"],
                errors="coerce"
            )

            display_records["created_at"] = (
                display_records["created_at"]
                .dt.strftime("%d %b %Y, %I:%M %p")
            )

            display_records = display_records[
                [
                    "patient_id",
                    "disease",
                    "result",
                    "gp_score",
                    "created_at"
                ]
            ]

            display_records.columns = [
                "Patient ID",
                "Disease",
                "Result",
                "GP Decision Score",
                "Date"
            ]

            st.dataframe(
                display_records,
                use_container_width=True,
                hide_index=True
            )


    elif page == "👤 Profile":

        st.markdown(
            '<div class="main-title">'
            'My Profile'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            f"**Full Name:** {user['full_name']}"
        )

        st.write(
            f"**Email:** {user['email']}"
        )

        st.write(
            f"**Username:** {user['username']}"
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
            "GP-MED uses Genetic Programming models "
            "trained on medical datasets for research "
            "and educational purposes."
        )
