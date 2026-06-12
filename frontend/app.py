"""
Resume Analyzer - Main Streamlit Application Entry Point.

Provides a registry-based navigation system with robust error handling,
logging, and session-state-driven routing.
"""

import sys
import os
import logging

# ---------------------------------------------------------------------------
# Path setup (handles both local and Streamlit Cloud deployment)
# __file__ is frontend/app.py, so parent of parent = project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resume_analyzer")

import streamlit as st

# ---------------------------------------------------------------------------
# Safe imports — surface a friendly error instead of a blank crash
# ---------------------------------------------------------------------------
try:
    from database.database import init_db
    from backend.auth.auth_service import (
        is_authenticated,
        get_current_user,
        is_admin,
        logout,
    )
    from frontend.views.login import render_login_page
    from frontend.views.register import render_register_page
    from frontend.views.dashboard import render_dashboard
    from frontend.views.upload_resume import render_upload_page
    from frontend.views.analysis import render_analysis_page
    from frontend.views.job_analysis import render_job_analysis_page
    from frontend.views.ats_score import render_ats_score_page
    from frontend.views.skill_gap import render_skill_gap_page
    from frontend.views.reports import render_reports_page
    from frontend.views.profile import render_profile_page
    from frontend.views.admin import render_admin_page
    from frontend.views.settings import render_settings_page
except Exception as import_error:  # pragma: no cover
    logger.exception("Failed to import application modules")
    st.set_page_config(page_title="Resume Analyzer - Error", page_icon="⚠️")
    st.error("Application failed to start due to an import error.")
    st.code(str(import_error))
    st.stop()


# ---------------------------------------------------------------------------
# Page registry
# Each entry: page_key -> {label, render, icon, admin_only}
# ---------------------------------------------------------------------------
PAGE_REGISTRY = {
    "dashboard": {"label": "Dashboard", "icon": "📊", "render": render_dashboard, "admin_only": False},
    "upload": {"label": "Upload Resume", "icon": "📄", "render": render_upload_page, "admin_only": False},
    "analysis": {"label": "Resume Analysis", "icon": "🔍", "render": render_analysis_page, "admin_only": False},
    "job_analysis": {"label": "Job Description Analysis", "icon": "📋", "render": render_job_analysis_page, "admin_only": False},
    "ats_score": {"label": "ATS Score", "icon": "📈", "render": render_ats_score_page, "admin_only": False},
    "skill_gap": {"label": "Skill Gap Analysis", "icon": "🛠️", "render": render_skill_gap_page, "admin_only": False},
    "reports": {"label": "Reports", "icon": "📑", "render": render_reports_page, "admin_only": False},
    "profile": {"label": "Profile", "icon": "👤", "render": render_profile_page, "admin_only": False},
    "settings": {"label": "Settings", "icon": "⚙️", "render": render_settings_page, "admin_only": False},
    "admin": {"label": "Admin Panel", "icon": "🛡️", "render": render_admin_page, "admin_only": True},
}

DEFAULT_PAGE = "dashboard"


def initialize_app() -> None:
    """Initialize application state and database (once per session)."""
    if "db_initialized" not in st.session_state:
        try:
            init_db()
            st.session_state["db_initialized"] = True
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.exception("Database initialization failed")
            st.error("Database connection failed. Some features may not work.")
            st.code(str(e))

    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "login")


def _visible_pages() -> dict:
    """Return the pages visible to the current user (filters admin-only)."""
    admin = is_admin()
    return {
        key: meta
        for key, meta in PAGE_REGISTRY.items()
        if not meta["admin_only"] or admin
    }


def render_sidebar() -> None:
    """Render the sidebar navigation."""
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

            pages = _visible_pages()
            page_keys = list(pages.keys())
            labels = [f"{pages[k]['icon']} {pages[k]['label']}" for k in page_keys]

            # Determine current selection index
            current_page = st.session_state.get("page", DEFAULT_PAGE)
            if current_page not in pages:
                current_page = DEFAULT_PAGE
            current_index = page_keys.index(current_page)

            selected_label = st.radio(
                "Navigation",
                labels,
                index=current_index,
                label_visibility="collapsed",
            )

            # Map the selected label back to its page key
            selected_index = labels.index(selected_label)
            st.session_state["page"] = page_keys[selected_index]

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                logger.info("User logged out: %s", user.get("email"))
                logout()
                st.session_state["page"] = "login"
                st.rerun()
        else:
            auth_pages = {"login": "🔐 Login", "register": "📝 Register"}
            current_page = st.session_state.get("page", "login")
            if current_page not in auth_pages:
                current_page = "login"
            keys = list(auth_pages.keys())
            labels = list(auth_pages.values())
            selected_label = st.radio(
                "Navigation",
                labels,
                index=keys.index(current_page),
                label_visibility="collapsed",
            )
            st.session_state["page"] = keys[labels.index(selected_label)]

        st.markdown("---")
        st.markdown(
            "<small>Resume Analyzer v1.0<br>© 2024</small>",
            unsafe_allow_html=True,
        )


def _inject_css() -> None:
    """Inject custom CSS styles."""
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


def route_page() -> None:
    """Route to the correct page based on session state, with error handling."""
    page = st.session_state.get("page", "login")

    # Unauthenticated routes
    if not is_authenticated():
        try:
            if page == "register":
                render_register_page()
            else:
                render_login_page()
        except Exception as e:
            logger.exception("Failed to render auth page '%s'", page)
            st.error("Something went wrong loading this page.")
            st.code(str(e))
        return

    # Authenticated routes — resolve from registry
    meta = PAGE_REGISTRY.get(page)

    # Guard: unknown page or admin-only page accessed by non-admin
    if meta is None or (meta["admin_only"] and not is_admin()):
        if meta is None:
            logger.warning("Unknown page requested: '%s'. Falling back to dashboard.", page)
        else:
            logger.warning("Non-admin tried to access admin page. Falling back to dashboard.")
        st.session_state["page"] = DEFAULT_PAGE
        meta = PAGE_REGISTRY[DEFAULT_PAGE]

    try:
        meta["render"]()
    except Exception as e:
        logger.exception("Failed to render page '%s'", page)
        st.error(f"⚠️ Could not load the '{meta['label']}' page.")
        with st.expander("Error details"):
            st.code(str(e))
        st.info("Try selecting another page from the sidebar, or reload the app.")


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="Resume Analyzer - ATS Score & Job Match",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_css()
    initialize_app()
    render_sidebar()
    route_page()


if __name__ == "__main__":
    main()
