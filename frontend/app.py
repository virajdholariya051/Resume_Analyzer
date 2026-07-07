"""
Resume Analyzer - Main Streamlit Application Entry Point.

Provides a role-based, registry-driven navigation system with robust error
handling, logging, and session-state routing for Job Seeker, Recruiter, and
Admin roles.
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
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resume_analyzer")

import streamlit as st

# ---------------------------------------------------------------------------
# Safe imports
# ---------------------------------------------------------------------------
try:
    from database.database import init_db
    from backend.auth.auth_service import (
        is_authenticated,
        get_current_user,
        is_admin,
        is_recruiter,
        get_role,
        logout,
    )
    # Shared / Job Seeker pages
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
    from frontend.views.settings import render_settings_page
    # Recruiter pages
    from frontend.views.recruiter_dashboard import render_recruiter_dashboard
    from frontend.views.bulk_upload import render_bulk_upload_page
    from frontend.views.recruiter_jobs import render_recruiter_jobs_page
    from frontend.views.candidate_ranking import render_candidate_ranking_page
    from frontend.views.top_candidates import render_top_candidates_page
    from frontend.views.candidate_comparison import render_candidate_comparison_page
    from frontend.views.recruiter_reports import render_recruiter_reports_page
    # Admin panel pages (enterprise)
    from frontend.views.admin_overview import render_admin_overview
    from frontend.views.admin_users import render_admin_users
    from frontend.views.admin_resumes import render_admin_resumes
    from frontend.views.admin_recruiters import render_admin_recruiters
    from frontend.views.admin_feedback import render_admin_feedback
    from frontend.views.admin_system_settings import render_admin_system_settings
    from frontend.views.admin_panel_mgmt import render_admin_panel_mgmt
    from frontend.views.admin_monitoring import render_admin_monitoring
    from frontend.components.admin_ui import inject_admin_theme
except Exception as import_error:  # pragma: no cover
    logger.exception("Failed to import application modules")
    st.set_page_config(page_title="Resume Analyzer - Error", page_icon="⚠️")
    st.error("Application failed to start due to an import error.")
    st.code(str(import_error))
    st.stop()


# ---------------------------------------------------------------------------
# Page registry: page_key -> {label, icon, render}
# ---------------------------------------------------------------------------
PAGE_REGISTRY = {
    # Job Seeker / shared
    "dashboard": {"label": "Dashboard", "icon": "📊", "render": render_dashboard},
    "upload": {"label": "Upload Resume", "icon": "📄", "render": render_upload_page},
    "analysis": {"label": "Resume Analysis", "icon": "🔍", "render": render_analysis_page},
    "job_analysis": {"label": "Job Description Analysis", "icon": "📋", "render": render_job_analysis_page},
    "ats_score": {"label": "ATS Score", "icon": "📈", "render": render_ats_score_page},
    "skill_gap": {"label": "Skill Gap Analysis", "icon": "🛠️", "render": render_skill_gap_page},
    "reports": {"label": "Reports", "icon": "📑", "render": render_reports_page},
    "profile": {"label": "Profile", "icon": "👤", "render": render_profile_page},
    "settings": {"label": "Settings", "icon": "⚙️", "render": render_settings_page},
    # Recruiter
    "recruiter_dashboard": {"label": "Dashboard", "icon": "📊", "render": render_recruiter_dashboard},
    "bulk_upload": {"label": "Upload Resumes", "icon": "📤", "render": render_bulk_upload_page},
    "recruiter_jobs": {"label": "Job Descriptions", "icon": "📋", "render": render_recruiter_jobs_page},
    "candidate_ranking": {"label": "Candidate Ranking", "icon": "🏆", "render": render_candidate_ranking_page},
    "top_candidates": {"label": "Top Candidates", "icon": "⭐", "render": render_top_candidates_page},
    "candidate_comparison": {"label": "Candidate Comparison", "icon": "⚖️", "render": render_candidate_comparison_page},
    "recruiter_reports": {"label": "Reports", "icon": "📑", "render": render_recruiter_reports_page},
    # Admin panel (enterprise)
    "admin_overview": {"label": "Overview Dashboard", "icon": "📊", "render": render_admin_overview},
    "admin_users": {"label": "User Management", "icon": "👥", "render": render_admin_users},
    "admin_resumes": {"label": "Resume Management", "icon": "📄", "render": render_admin_resumes},
    "admin_recruiters": {"label": "Recruiter Management", "icon": "🧑‍💼", "render": render_admin_recruiters},
    "admin_feedback": {"label": "Feedback Management", "icon": "💬", "render": render_admin_feedback},
    "admin_system_settings": {"label": "System Settings", "icon": "⚙️", "render": render_admin_system_settings},
    "admin_panel_mgmt": {"label": "Admin Management", "icon": "🛡️", "render": render_admin_panel_mgmt},
    "admin_monitoring": {"label": "System Monitoring", "icon": "🖥️", "render": render_admin_monitoring},
}

# Ordered navigation per role
NAV_BY_ROLE = {
    "Job Seeker": [
        "dashboard", "upload", "analysis", "profile",
    ],
    "Recruiter": [
        "recruiter_dashboard", "bulk_upload", "candidate_ranking",
        "recruiter_reports", "profile",
    ],
    "Admin": [
        "admin_overview", "admin_users", "admin_resumes", "admin_recruiters",
        "admin_feedback", "admin_system_settings",
        "admin_panel_mgmt", "admin_monitoring", "profile",
    ],
}

DEFAULT_PAGE_BY_ROLE = {
    "Job Seeker": "dashboard",
    "Recruiter": "recruiter_dashboard",
    "Admin": "admin_overview",
}


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


def _current_nav() -> list:
    """Return the ordered list of page keys for the current user's role."""
    role = get_role()
    return NAV_BY_ROLE.get(role, NAV_BY_ROLE["Job Seeker"])


def _default_page() -> str:
    """Return the default landing page for the current role."""
    return DEFAULT_PAGE_BY_ROLE.get(get_role(), "dashboard")


def render_sidebar() -> None:
    """Render the role-aware sidebar navigation."""
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

            nav_keys = _current_nav()

            current_page = st.session_state.get("page", _default_page())
            if current_page not in nav_keys:
                current_page = _default_page()
                st.session_state["page"] = current_page

            # One-click button navigation. The active page is highlighted via
            # the "primary" button style. Buttons return True on the same rerun
            # they are clicked, so a single click switches pages immediately.
            for key in nav_keys:
                meta = PAGE_REGISTRY[key]
                label = f"{meta['icon']} {meta['label']}"
                is_active = (key == current_page)
                if st.button(
                    label,
                    key=f"nav_{key}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["page"] = key
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                logger.info("User logged out: %s", user.get("email"))
                logout()
                st.session_state["page"] = "login"
                st.rerun()
        else:
            # Auth navigation (Login / Register) as one-click buttons
            current_page = st.session_state.get("page", "login")
            if current_page not in ("login", "register"):
                current_page = "login"

            for key, label in (("login", "🔐 Login"), ("register", "📝 Register")):
                if st.button(
                    label,
                    key=f"nav_{key}",
                    use_container_width=True,
                    type="primary" if key == current_page else "secondary",
                ):
                    st.session_state["page"] = key
                    st.rerun()

        st.markdown("---")
        st.markdown(
            "<small>Resume Analyzer  <br>© 2026</small>",
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
        /* Left-align sidebar navigation buttons for a clean menu look */
        section[data-testid="stSidebar"] .stButton>button {
            text-align: left;
            justify-content: flex-start;
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

    # Authenticated: enforce access control via the role's allowed nav
    allowed = _current_nav()
    if page not in allowed:
        logger.warning("Access to '%s' denied for role '%s'. Redirecting.", page, get_role())
        page = _default_page()
        st.session_state["page"] = page

    meta = PAGE_REGISTRY.get(page)
    if meta is None:
        page = _default_page()
        st.session_state["page"] = page
        meta = PAGE_REGISTRY[page]

    # Apply the admin workspace theme on admin pages
    if get_role() == "Admin":
        inject_admin_theme()

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
