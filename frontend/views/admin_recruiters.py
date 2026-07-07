"""
Admin Recruiter Management - accounts, activity, and performance.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin, get_current_user
from backend.services.user_service import UserService
from backend.services.admin_service import AdminService
from frontend.components.admin_ui import breadcrumb, paginated_table
from frontend.components.charts import create_horizontal_bar_chart, STATIC_CHART_CONFIG


def render_admin_recruiters() -> None:
    """Render the recruiter management section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Recruiter Management")
    st.markdown('<h1 class="main-header">🧑‍💼 Recruiter Management</h1>', unsafe_allow_html=True)

    user_service = UserService()
    admin_service = AdminService()

    tabs = st.tabs(["Recruiter Accounts", "Recruiter Activity", "Recruiter Performance"])

    with tabs[0]:
        _render_accounts(user_service)
    with tabs[1]:
        _render_activity(admin_service)
    with tabs[2]:
        _render_performance(admin_service)


def _render_accounts(user_service) -> None:
    st.markdown("### Create Recruiter")
    admin = get_current_user()
    with st.form("admin_create_recruiter"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone (optional)")
        pw = st.text_input("Password", type="password", placeholder="Min 8 chars, letter + number")
        pw2 = st.text_input("Confirm Password", type="password")
        if st.form_submit_button("Create Recruiter", type="primary"):
            if pw != pw2:
                st.error("Passwords do not match.")
            else:
                res = user_service.create_privileged_user(admin["user_id"], name, email, pw, phone, "Recruiter")
                if res["success"]:
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])

    st.markdown("---")
    st.markdown("### Existing Recruiters")
    recruiters = user_service.get_all_users(role="Recruiter")
    if recruiters:
        df = pd.DataFrame([
            {"ID": r["user_id"], "Name": r["name"], "Email": r["email"],
             "Phone": r["phone"] or "N/A", "Status": "Active" if r["is_active"] else "Blocked",
             "Created": r["created_at"]}
            for r in recruiters
        ])
        paginated_table(df, "recruiter_accounts", search_columns=["Name", "Email"])
    else:
        st.info("No recruiters yet.")


def _render_activity(admin_service) -> None:
    st.markdown("### Recruiter Activity")
    perf = admin_service.get_recruiter_performance()
    if not perf:
        st.info("No recruiter activity yet.")
        return
    df = pd.DataFrame([
        {"Recruiter": p["recruiter"], "Candidates Uploaded": p["candidates"],
         "Analyses Run": p["analyses"], "Shortlisted": p["shortlisted"]}
        for p in perf
    ])
    paginated_table(df, "recruiter_activity", search_columns=["Recruiter"])


def _render_performance(admin_service) -> None:
    st.markdown("### Recruiter Performance")
    perf = admin_service.get_recruiter_performance()
    if not perf:
        st.info("No recruiter data yet.")
        return
    pairs = [(p["recruiter"], p["candidates"]) for p in perf]
    st.plotly_chart(create_horizontal_bar_chart(pairs, "Candidates Sourced by Recruiter"),
                    use_container_width=True, config=STATIC_CHART_CONFIG)
    df = pd.DataFrame([
        {"Recruiter": p["recruiter"], "Candidates": p["candidates"], "Analyses": p["analyses"],
         "Shortlisted": p["shortlisted"], "Avg ATS": p["avg_ats"]}
        for p in perf
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
