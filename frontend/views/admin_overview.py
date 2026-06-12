"""
Admin Overview Dashboard - KPIs and headline analytics.
"""

import streamlit as st
from backend.auth.auth_service import is_admin
from backend.services.admin_service import AdminService
from frontend.components.admin_ui import breadcrumb, kpi_card
from frontend.components.charts import (
    create_time_series_chart,
    create_score_distribution_chart,
    create_horizontal_bar_chart,
)


def render_admin_overview() -> None:
    """Render the admin overview dashboard."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Overview Dashboard")
    st.markdown('<h1 class="main-header">📊 Overview Dashboard</h1>', unsafe_allow_html=True)

    service = AdminService()
    kpis = service.get_overview_kpis()

    # KPI row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Users", kpis["total_users"], kpis["trends"]["users"])
    with c2:
        kpi_card("Recruiters", kpis["total_recruiters"])
    with c3:
        kpi_card("Admins", kpis["total_admins"])
    with c4:
        kpi_card("Active Users Today", kpis["active_users_today"])

    st.write("")

    # KPI row 2
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi_card("Uploaded Resumes", kpis["total_resumes"], kpis["trends"]["resumes"])
    with c6:
        kpi_card("Total Analyses", kpis["total_analyses"])
    with c7:
        kpi_card("Avg ATS Score", f"{kpis['average_ats_score']}%")
    with c8:
        kpi_card("Avg Match %", f"{kpis['average_match_percentage']}%")

    st.markdown("---")

    # Charts
    growth = service.get_user_growth(days=30)
    uploads = service.get_upload_trend(days=30)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            create_time_series_chart(growth["labels"], growth["values"],
                                     "User Growth (30 days)", "Total Users", "#16a34a"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            create_time_series_chart(uploads["labels"], uploads["values"],
                                     "Resume Uploads (30 days)", "Uploads", "#1f77b4"),
            use_container_width=True,
        )

    dist = service.get_score_distributions()
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(
            create_score_distribution_chart(dist["ats_scores"], "ATS Score Distribution", "#1f77b4"),
            use_container_width=True,
        )
    with col4:
        st.plotly_chart(
            create_score_distribution_chart(dist["match_scores"], "Match % Distribution", "#ff7f0e"),
            use_container_width=True,
        )

    # Top skills
    skills = service.get_skills_analytics(top_n=10)
    if skills["top_skills"]:
        st.plotly_chart(
            create_horizontal_bar_chart(skills["top_skills"], "Top 10 Skills Across Resumes"),
            use_container_width=True,
        )
