"""
Admin Dashboard - simple, essential KPIs and charts for system administration.
"""

import streamlit as st
from backend.auth.auth_service import is_admin
from backend.services.admin_service import AdminService
from frontend.components.admin_ui import breadcrumb, kpi_card
from frontend.components.charts import (
    create_time_series_chart,
    create_pie_chart,
    STATIC_CHART_CONFIG,
)


def render_admin_overview() -> None:
    """Render the admin dashboard with essential KPIs and charts.

    Charts read live data on every render, so they refresh automatically as
    users register, upload resumes or run analyses.
    """
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Dashboard")
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)

    service = AdminService()
    kpis = service.get_overview_kpis()

    # ------------------------------------------------------------------ #
    # KPI cards
    # ------------------------------------------------------------------ #
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Total Users", kpis["total_users"], kpis["trends"]["users"])
    with c2:
        kpi_card("Total Recruiters", kpis["total_recruiters"])
    with c3:
        kpi_card("Total Admins", kpis["total_admins"])

    st.write("")

    c4, c5, c6 = st.columns(3)
    with c4:
        kpi_card("Total Uploaded Resumes", kpis["total_resumes"], kpis["trends"]["resumes"])
    with c5:
        kpi_card("Total Resume Analyses", kpis["total_analyses"])
    with c6:
        kpi_card("Active Users Today", kpis["active_users_today"])

    st.markdown("---")

    # ------------------------------------------------------------------ #
    # Essential charts
    # ------------------------------------------------------------------ #
    growth = service.get_user_growth(days=30)
    uploads = service.get_upload_trend(days=30)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            create_time_series_chart(growth["labels"], growth["values"],
                                     "User Registration Trend (30 days)", "Total Users", "#16a34a"),
            use_container_width=True,
            config=STATIC_CHART_CONFIG,
        )
    with col2:
        st.plotly_chart(
            create_time_series_chart(uploads["labels"], uploads["values"],
                                     "Resume Upload Trend (30 days)", "Uploads", "#1f77b4"),
            use_container_width=True,
            config=STATIC_CHART_CONFIG,
        )

    # User role distribution
    role_distribution = kpis.get("role_distribution", {})
    st.plotly_chart(
        create_pie_chart(role_distribution, "User Role Distribution"),
        use_container_width=True,
        config=STATIC_CHART_CONFIG,
    )
