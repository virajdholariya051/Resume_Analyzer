"""
Registration page for new user signup.
"""

import streamlit as st
from backend.auth.auth_service import register_user


def render_register_page() -> None:
    """Render the registration page."""
    st.markdown('<h1 class="main-header">📄 Resume Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create a new account</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("register_form"):
            st.markdown("#### 📝 Register")
            name = st.text_input("Full Name", placeholder="Enter your full name")
            email = st.text_input("Email Address", placeholder="Enter your email")
            phone = st.text_input("Phone Number (optional)", placeholder="Enter your phone")
            password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            role = st.selectbox("Role", ["Job Seeker", "Admin"])
            submit = st.form_submit_button("Register", use_container_width=True)

            if submit:
                if not name or not email or not password:
                    st.error("Name, email, and password are required.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    result = register_user(name, email, password, phone, role)
                    if result["success"]:
                        st.success(result["message"] + " Please login.")
                        st.session_state["page"] = "login"
                    else:
                        st.error(result["message"])

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center;'>Already have an account? Click <b>Login</b> in the sidebar.</p>",
            unsafe_allow_html=True,
        )
