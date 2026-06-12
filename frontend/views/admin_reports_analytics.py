"""
Admin Reports & Analytics - growth, upload trends, score distributions,
AI usage, and monthly summaries.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.admin_service import AdminService
from backend.services.ai_log_service import AILogService
from frontend.components.admin_ui import breadcrumb
from frontend.components.charts import (
    create_time_series_chart,
    create_score_distribution_chart,
)


def render_admin_reports_analytics() -> None:
    """Render the reports & analytics section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Reports & Analytics")
    st.markdown('<h1 class="main-header">📈 Reports & Analytics</h1>', unsafe_allow_html=True)

    service = AdminService()

    days = st.select_slider("Time window (days)", options=[7, 14, 30, 60, 90], value=30)

    tabs = st.tabs([
        "User Growth", "Resume Upload Trends", "ATS Distribution",
        "Match % Trends", "AI Usage", "Monthly Reports",
    ])

    with tabs[0]:
        s = service.get_user_growth(days=days)
        st.plotly_chart(create_time_series_chart(s["labels"], s["values"],
                        f"User Growth ({days} days)", "Total Users", "#16a34a"),
                        use_container_width=True)

    with tabs[1]:
        s = service.get_upload_trend(days=days)
        st.plotly_chart(create_time_series_chart(s["labels"], s["values"],
                        f"Resume Uploads ({days} days)", "Uploads", "#1f77b4"),
                        use_container_width=True)

    with tabs[2]:
        dist = service.get_score_distributions()
        st.plotly_chart(create_score_distribution_chart(dist["ats_scores"],
                        "ATS Score Distribution", "#1f77b4"), use_container_width=True)

    with tabs[3]:
        dist = service.get_score_distributions()
        st.plotly_chart(create_score_distribution_chart(dist["match_scores"],
                        "Match % Distribution", "#ff7f0e"), use_container_width=True)
        s = service.get_daily_analysis_count(days=days)
        st.plotly_chart(create_time_series_chart(s["labels"], s["values"],
                        f"Daily Analyses ({days} days)", "Analyses", "#9b59b6"),
                        use_container_width=True)

    with tabs[4]:
        ai_stats = AILogService().get_stats()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total AI Requests", ai_stats["total_requests"])
        c2.metric("Success Rate", f"{ai_stats['success_rate']}%")
        c3.metric("Avg Latency", f"{ai_stats['avg_processing_ms']} ms")

    with tabs[5]:
        _render_monthly(service)


def _render_monthly(service) -> None:
    st.markdown("### Monthly Summary")
    growth = service.get_user_growth(days=30)
    uploads = service.get_upload_trend(days=30)
    analyses = service.get_daily_analysis_count(days=30)
    kpis = service.get_overview_kpis()

    df = pd.DataFrame({
        "Metric": ["Total Users", "Total Resumes", "Total Analyses",
                   "Avg ATS Score", "Avg Match %", "New Uploads (30d)", "Analyses (30d)"],
        "Value": [
            kpis["total_users"], kpis["total_resumes"], kpis["total_analyses"],
            kpis["average_ats_score"], kpis["average_match_percentage"],
            sum(uploads["values"]), sum(analyses["values"]),
        ],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Export Monthly Report (CSV)",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="monthly_report.csv", mime="text/csv")
