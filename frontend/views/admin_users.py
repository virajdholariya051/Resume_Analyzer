"""
Admin User Management - all users, by-role views, active/blocked, activity logs,
and full per-user management actions (edit, role, reset password, block, delete).
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin, get_current_user
from backend.services.user_service import UserService, VALID_ROLES
from backend.services.audit_service import AuditService
from frontend.components.admin_ui import breadcrumb, paginated_table


def _users_df(users):
    return pd.DataFrame([
        {
            "ID": u["user_id"], "Name": u["name"], "Email": u["email"],
            "Phone": u["phone"] or "N/A", "Role": u["role"],
            "Status": "Active" if u["is_active"] else "Blocked",
            "Created": u["created_at"],
        }
        for u in users
    ])


def render_admin_users() -> None:
    """Render the user management section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "User Management")
    st.markdown('<h1 class="main-header">👥 User Management</h1>', unsafe_allow_html=True)

    service = UserService()
    all_users = service.get_all_users()

    tabs = st.tabs([
        "All Users", "Job Seekers", "Recruiters", "Admins",
        "Active", "Blocked", "Activity Logs", "Manage User",
    ])

    with tabs[0]:
        paginated_table(_users_df(all_users), "all_users", search_columns=["Name", "Email", "Role"])
    with tabs[1]:
        paginated_table(_users_df([u for u in all_users if u["role"] == "Job Seeker"]),
                        "job_seekers", search_columns=["Name", "Email"])
    with tabs[2]:
        paginated_table(_users_df([u for u in all_users if u["role"] == "Recruiter"]),
                        "recruiters_u", search_columns=["Name", "Email"])
    with tabs[3]:
        paginated_table(_users_df([u for u in all_users if u["role"] == "Admin"]),
                        "admins_u", search_columns=["Name", "Email"])
    with tabs[4]:
        paginated_table(_users_df([u for u in all_users if u["is_active"]]),
                        "active_u", search_columns=["Name", "Email", "Role"])
    with tabs[5]:
        paginated_table(_users_df([u for u in all_users if not u["is_active"]]),
                        "blocked_u", search_columns=["Name", "Email", "Role"])
    with tabs[6]:
        _render_activity_logs()
    with tabs[7]:
        _render_manage_user(service, all_users)


def _render_activity_logs() -> None:
    """Show recent audit/activity logs."""
    st.markdown("### 📜 User Activity Logs")
    logs = AuditService().get_logs(limit=300)
    if logs:
        df = pd.DataFrame([
            {
                "Time": l["timestamp"], "By": l["admin_name"],
                "Action": l["action"], "Target": l["target_user_id"] or "-",
                "IP": l["ip_address"],
            }
            for l in logs
        ])
        paginated_table(df, "activity_logs", search_columns=["By", "Action"])
    else:
        st.info("No activity recorded yet.")


def _render_manage_user(service, all_users) -> None:
    """Per-user management actions."""
    st.markdown("### 🔧 Manage a User")
    if not all_users:
        st.info("No users found.")
        return

    admin = get_current_user()
    admin_id = admin["user_id"]
    options = {f"{u['name']} ({u['email']}) — {u['role']}": u["user_id"] for u in all_users}
    selected_label = st.selectbox("Select user", list(options.keys()))
    selected_id = options[selected_label]
    selected = next(u for u in all_users if u["user_id"] == selected_id)
    is_self = selected_id == admin_id

    # Profile view
    with st.expander("👤 View Profile", expanded=True):
        st.write(f"**Name:** {selected['name']}")
        st.write(f"**Email:** {selected['email']}")
        st.write(f"**Phone:** {selected['phone'] or 'N/A'}")
        st.write(f"**Role:** {selected['role']}")
        st.write(f"**Status:** {'✅ Active' if selected['is_active'] else '🚫 Blocked'}")
        st.write(f"**Member since:** {selected['created_at']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🎚️ Change Role")
        new_role = st.selectbox("New role", VALID_ROLES,
                                index=VALID_ROLES.index(selected["role"]) if selected["role"] in VALID_ROLES else 0)
        if st.checkbox("Confirm role change") and st.button("Apply Role Change", disabled=is_self):
            _flash(service.change_role(admin_id, selected_id, new_role))
        if is_self:
            st.caption("You cannot change your own role.")
    with col2:
        st.markdown("#### 🔌 Block / Unblock")
        if selected["is_active"]:
            if st.button("🚫 Block User", disabled=is_self):
                _flash(service.set_active(admin_id, selected_id, False))
        else:
            if st.button("✅ Unblock User"):
                _flash(service.set_active(admin_id, selected_id, True))

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### 🔑 Reset Password")
        with st.form(f"reset_{selected_id}"):
            pw = st.text_input("New password", type="password")
            pw2 = st.text_input("Confirm", type="password")
            if st.form_submit_button("Reset Password"):
                if pw != pw2:
                    st.error("Passwords do not match.")
                else:
                    _flash(service.reset_password(admin_id, selected_id, pw))
    with col4:
        st.markdown("#### 🗑️ Delete User")
        if st.checkbox(f"Confirm delete {selected['name']}") and st.button("Delete User", disabled=is_self):
            _flash(service.delete_user(selected_id, admin_id))
        if is_self:
            st.caption("You cannot delete your own account.")


def _flash(result: dict) -> None:
    if result.get("success"):
        st.success(result["message"])
        st.rerun()
    else:
        st.error(result["message"])
