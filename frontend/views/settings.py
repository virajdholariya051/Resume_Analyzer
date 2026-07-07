"""
Settings page - application preferences and account information.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.user_service import UserService


def render_settings_page() -> None:
    """Render the settings page."""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    user_service = UserService()

    tab1, tab2, tab3 = st.tabs(["🎨 Preferences", "🔐 Account", "ℹ️ About"])

    with tab1:
        _render_preferences()
    with tab2:
        _render_account(user, user_service)
    with tab3:
        _render_about()


def _render_preferences() -> None:
    """Render UI preferences."""
    st.markdown("### Display Preferences")

    if "pref_results_per_page" not in st.session_state:
        st.session_state["pref_results_per_page"] = 10

    st.session_state["pref_results_per_page"] = st.slider(
        "Results per page",
        min_value=5,
        max_value=50,
        value=st.session_state["pref_results_per_page"],
        step=5,
    )

    st.checkbox("Show detailed score breakdowns", value=True, key="pref_detailed_scores")
    st.checkbox("Enable email notifications (placeholder)", value=False, key="pref_email_notify")

    st.info("Preferences are stored for your current session.")


def _render_account(user, user_service) -> None:
    """Render account management options."""
    st.markdown("### Account Information")

    user_data = user_service.get_user_by_id(user["user_id"])
    if not user_data:
        st.error("Could not load account information.")
        return

    st.write(f"**Name:** {user_data['name']}")
    st.write(f"**Email:** {user_data['email']}")
    st.write(f"**Role:** {user_data['role']}")
    st.write(f"**Member Since:** {user_data['created_at']}")

    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    st.caption("Account deletion is permanent and cannot be undone.")

    if user_data["role"] == "Admin":
        st.info("Admin accounts cannot be deleted from here.")
        return

    confirm = st.checkbox("I understand this will permanently delete my account.")
    if st.button("🗑️ Delete My Account", disabled=not confirm):
        result = user_service.delete_user(user["user_id"])
        if result["success"]:
            st.success("Account deleted. Logging out...")
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["page"] = "login"
            st.rerun()
        else:
            st.error(result["message"])


def _render_about() -> None:
    """Render about/info section."""
    st.markdown("### About Resume Analyzer")
    st.markdown(
        """
        **Resume Analyzer** helps job seekers optimize their resumes with:
        - 📈 **ATS Score** — measure applicant tracking system compatibility
        - 🎯 **Job Match** — compare your resume against job descriptions
        - 🛠️ **Skill Gap Analysis** — discover skills you need to add
        - 📑 **PDF Reports** — download detailed analysis reports

        **Version:** 1.0.0
        """
    )
    st.caption("© 2024 Resume Analyzer")
