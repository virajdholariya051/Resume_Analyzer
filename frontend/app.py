"""
Resume Analyzer - Main Streamlit Application Entry Point.
"""

import sys
import os

# Add project root to path (handles both local and Streamlit Cloud deployment)
# __file__ is frontend/app.py, so parent of parent = Resume_Analyzer root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from database.database import init_db
from backend.auth.auth_service import is_authenticated, get_current_user, is_admin, logout
from frontend.pages.login import render_login_page
from frontend.pages.register import render_register_page
from frontend.pages.dashboard import render_dashboard
from frontend.pages.upload_resume import render_upload_page
from frontend.pages.analysis import render_analysis_page
from frontend.pages.profile import render_profile_page
from frontend.pages.admin import render_admin_page


def initialize_app() -> None:
    """Initialize application state and database."""
    init_db()
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "login"


def render_sidebar() -> None:
    """Render the application sidebar navigation."""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
        st.title("Resume Analyzer")
        st.markdown("---")

        if is_authenticated():
            user = get_current_user()
            st.markdown(f"👤 **{user['name']}**")
            st.markdown(f"📧 {user['email']}")
            st.markdown(f"🏷️ Role: {user['role']}")
            st.markdown("---")

            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state["page"] = "dashboard"
                st.rerun()
            if st.button("📄 Upload Resume", use_container_width=True):
                st.session_state["page"] = "upload"
                st.rerun()
            if st.button("🔍 Analysis", use_container_width=True):
                st.session_state["page"] = "analysis"
                st.rerun()
            if st.button("👤 Profile", use_container_width=True):
                st.session_state["page"] = "profile"
                st.rerun()

            if is_admin():
                st.markdown("---")
                st.markdown("**Admin Panel**")
                if st.button("⚙️ Admin", use_container_width=True):
                    st.session_state["page"] = "admin"
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.session_state["page"] = "login"
                st.rerun()
        else:
            if st.button("🔐 Login", use_container_width=True):
                st.session_state["page"] = "login"
                st.rerun()
            if st.button("📝 Register", use_container_width=True):
                st.session_state["page"] = "register"
                st.rerun()

        st.markdown("---")
        st.markdown(
            "<small>Resume Analyzer v1.0<br>© 2024</small>",
            unsafe_allow_html=True,
        )


def main() -> None:
    """Main application function."""
    st.set_page_config(
        page_title="Resume Analyzer - ATS Score & Job Match",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .score-high { color: #28a745; font-weight: bold; }
        .score-medium { color: #ffc107; font-weight: bold; }
        .score-low { color: #dc3545; font-weight: bold; }
        .stButton>button {
            border-radius: 8px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    initialize_app()
    render_sidebar()

    # Route to correct page
    page = st.session_state.get("page", "login")

    if not is_authenticated():
        if page == "register":
            render_register_page()
        else:
            render_login_page()
    else:
        if page == "dashboard":
            render_dashboard()
        elif page == "upload":
            render_upload_page()
        elif page == "analysis":
            render_analysis_page()
        elif page == "profile":
            render_profile_page()
        elif page == "admin" and is_admin():
            render_admin_page()
        else:
            render_dashboard()


if __name__ == "__main__":
    main()
