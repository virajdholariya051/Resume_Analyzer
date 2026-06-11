"""
Navigation bar component for the application header.
"""

import streamlit as st
from backend.auth.auth_service import is_authenticated, get_current_user


def render_navbar() -> None:
    """Render the top navigation bar."""
    col1, col2, col3 = st.columns([3, 5, 2])

    with col1:
        st.markdown("### 📄 Resume Analyzer")

    with col2:
        if is_authenticated():
            nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
            with nav_col1:
                if st.button("Dashboard", key="nav_dash"):
                    st.session_state["page"] = "dashboard"
                    st.rerun()
            with nav_col2:
                if st.button("Upload", key="nav_upload"):
                    st.session_state["page"] = "upload"
                    st.rerun()
            with nav_col3:
                if st.button("Analysis", key="nav_analysis"):
                    st.session_state["page"] = "analysis"
                    st.rerun()
            with nav_col4:
                if st.button("Profile", key="nav_profile"):
                    st.session_state["page"] = "profile"
                    st.rerun()

    with col3:
        if is_authenticated():
            user = get_current_user()
            st.markdown(f"**{user['name']}**")
