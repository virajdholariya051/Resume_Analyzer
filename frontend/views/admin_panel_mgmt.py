"""
Admin Management - admin accounts, roles, permissions (RBAC), and audit logs.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin, get_current_user
from backend.services.user_service import UserService
from backend.services.audit_service import AuditService
from frontend.components.admin_ui import breadcrumb, paginated_table


# Role -> permissions matrix (RBAC reference)
ROLE_PERMISSIONS = {
    "Admin": [
        "Full system access", "Manage users", "Create admins/recruiters",
        "Change roles", "Manage settings", "View audit logs", "Manage feedback",
    ],
    "Recruiter": [
        "Upload resumes (bulk)", "Rank candidates", "Manage own job descriptions",
        "Shortlist candidates", "Export reports",
    ],
    "Job Seeker": [
        "Upload own resume", "Run resume analysis", "View ATS score", "Edit own profile",
    ],
}


def render_admin_panel_mgmt() -> None:
    """Render the admin management section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Admin Management")
    st.markdown('<h1 class="main-header">🛡️ Admin Management</h1>', unsafe_allow_html=True)

    user_service = UserService()
    audit = AuditService()

    tabs = st.tabs(["Admin Accounts", "Roles", "Permissions", "Audit Logs"])

    with tabs[0]:
        _render_admin_accounts(user_service)
    with tabs[1]:
        _render_roles(user_service)
    with tabs[2]:
        _render_permissions()
    with tabs[3]:
        _render_audit_logs(audit)


def _render_admin_accounts(user_service) -> None:
    st.markdown("### Create Admin")
    admin = get_current_user()
    with st.form("create_admin_account"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone (optional)")
        pw = st.text_input("Password", type="password", placeholder="Min 8 chars, letter + number")
        pw2 = st.text_input("Confirm Password", type="password")
        ack = st.checkbox("I understand this account has full administrative privileges.")
        if st.form_submit_button("Create Admin", type="primary"):
            if pw != pw2:
                st.error("Passwords do not match.")
            elif not ack:
                st.warning("Please acknowledge the privilege notice.")
            else:
                res = user_service.create_privileged_user(admin["user_id"], name, email, pw, phone, "Admin")
                if res["success"]:
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])

    st.markdown("---")
    st.markdown("### Existing Admins")
    admins = user_service.get_all_users(role="Admin")
    df = pd.DataFrame([
        {"ID": a["user_id"], "Name": a["name"], "Email": a["email"],
         "Status": "Active" if a["is_active"] else "Blocked", "Created": a["created_at"]}
        for a in admins
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_roles(user_service) -> None:
    st.markdown("### Role Distribution")
    users = user_service.get_all_users()
    counts = {}
    for u in users:
        counts[u["role"]] = counts.get(u["role"], 0) + 1
    df = pd.DataFrame([{"Role": r, "Users": c} for r, c in counts.items()])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("Use **User Management → Manage User** to change individual roles.")


def _render_permissions() -> None:
    st.markdown("### Role-Based Access Control (RBAC)")
    for role, perms in ROLE_PERMISSIONS.items():
        with st.expander(f"🔑 {role} Permissions", expanded=(role == "Admin")):
            for p in perms:
                st.write(f"- ✅ {p}")
    st.caption("Permissions are enforced in the backend services and the role-based navigation.")


def _render_audit_logs(audit) -> None:
    st.markdown("### Audit Logs")
    logs = audit.get_logs(limit=500)
    if logs:
        df = pd.DataFrame([
            {"Time": l["timestamp"], "By": l["admin_name"], "Action": l["action"],
             "Target User": l["target_user_id"] or "-", "IP": l["ip_address"]}
            for l in logs
        ])
        paginated_table(df, "admin_audit_logs", search_columns=["By", "Action"])
    else:
        st.info("No audit entries yet.")
