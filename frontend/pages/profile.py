"""
User profile management page.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.user_service import UserService


def render_profile_page() -> None:
    """Render the user profile page."""
    st.markdown('<h1 class="main-header">👤 My Profile</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    user_service = UserService()
    user_data = user_service.get_user_by_id(user["user_id"])

    if not user_data:
        st.error("User not found.")
        return

    # Display current profile
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📋 Profile Information")
        st.write(f"**Name:** {user_data['name']}")
        st.write(f"**Email:** {user_data['email']}")
        st.write(f"**Phone:** {user_data['phone'] or 'Not set'}")
        st.write(f"**Role:** {user_data['role']}")
        st.write(f"**Member Since:** {user_data['created_at']}")

    with col2:
        st.markdown("### ✏️ Update Profile")

        with st.form("profile_form"):
            new_name = st.text_input("Full Name", value=user_data["name"])
            new_phone = st.text_input("Phone Number", value=user_data["phone"] or "")
            new_password = st.text_input(
                "New Password (leave empty to keep current)",
                type="password",
                placeholder="Enter new password",
            )
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter new password",
            )
            submit = st.form_submit_button("💾 Update Profile", use_container_width=True)

            if submit:
                if new_password and new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif new_password and len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    result = user_service.update_user(
                        user_id=user["user_id"],
                        name=new_name if new_name != user_data["name"] else None,
                        phone=new_phone,
                        password=new_password if new_password else None,
                    )
                    if result["success"]:
                        st.success(result["message"])
                        # Update session
                        if new_name:
                            st.session_state["user"]["name"] = new_name
                        if new_phone:
                            st.session_state["user"]["phone"] = new_phone
                        st.rerun()
                    else:
                        st.error(result["message"])
