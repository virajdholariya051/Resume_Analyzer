"""
Login page for user authentication.
"""

import streamlit as st
from backend.auth.auth_service import login_user, set_session


def render_login_page() -> None:
    """Render the login page."""
    st.markdown('<h1 class="main-header">📄 Resume Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Login to your account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            st.markdown("#### 🔐 Login")
            email = st.text_input("Email Address", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    result = login_user(email, password)
                    if result["success"]:
                        set_session(result["user"])
                        st.success(result["message"])
                        # Land on the role-appropriate default page
                        role = result["user"].get("role", "Job Seeker")
                        if role == "Recruiter":
                            st.session_state["page"] = "recruiter_dashboard"
                        elif role == "Admin":
                            st.session_state["page"] = "admin_overview"
                        else:
                            st.session_state["page"] = "dashboard"
                        st.rerun()
                    else:
                        st.error(result["message"])

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center;'>Don't have an account? Click <b>Register</b> in the sidebar.</p>",
            unsafe_allow_html=True,
        )
