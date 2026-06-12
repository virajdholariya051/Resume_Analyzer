"""
Dashboard page displaying overview stats and analytics.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.analysis_service import AnalysisService
from frontend.components.charts import (
    create_skill_distribution_chart,
    create_analysis_history_chart,
    create_ats_score_gauge,
)


def render_dashboard() -> None:
    """Render the dashboard page."""
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    st.markdown(f"### Welcome back, {user['name']}! 👋")
    st.markdown("---")

    # Get dashboard stats
    analysis_service = AnalysisService()
    stats = analysis_service.get_dashboard_stats(user["user_id"])

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📄 Total Resumes",
            value=stats["total_resumes"],
        )
    with col2:
        st.metric(
            label="🔍 Total Analyses",
            value=stats["total_analyses"],
        )
    with col3:
        st.metric(
            label="📈 Avg ATS Score",
            value=f"{stats['average_ats_score']}%",
        )
    with col4:
        st.metric(
            label="🎯 Avg Match %",
            value=f"{stats['average_match_percentage']}%",
        )

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns(2)

    with col_left:
        if stats["top_skills"]:
            fig = create_skill_distribution_chart(stats["top_skills"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload and analyze resumes to see skill distribution.")

    with col_right:
        if stats["recent_analyses"]:
            fig = create_analysis_history_chart(stats["recent_analyses"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analysis history yet. Run your first analysis!")

    # ATS Score gauge (if analyses exist)
    if stats["average_ats_score"] > 0:
        st.markdown("---")
        st.markdown("### 📈 Your Average ATS Score")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            fig = create_ats_score_gauge(int(stats["average_ats_score"]))
            st.plotly_chart(fig, use_container_width=True)

    # Recent analyses table
    st.markdown("---")
    st.markdown("### 🕒 Recent Analyses")

    if stats["recent_analyses"]:
        for analysis in stats["recent_analyses"]:
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"📅 {analysis['created_at']}")
                with col2:
                    ats = analysis["ats_score"]
                    color = "score-high" if ats >= 70 else "score-medium" if ats >= 50 else "score-low"
                    st.markdown(f"ATS: <span class='{color}'>{ats}/100</span>", unsafe_allow_html=True)
                with col3:
                    match = analysis["job_match_percentage"]
                    color = "score-high" if match >= 70 else "score-medium" if match >= 50 else "score-low"
                    st.markdown(f"Match: <span class='{color}'>{match}%</span>", unsafe_allow_html=True)
    else:
        st.info("No analyses yet. Upload a resume and compare it against a job description!")

    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Upload Resume", key="dash_upload", use_container_width=True):
            st.session_state["page"] = "upload"
            st.rerun()
    with col2:
        if st.button("🔍 Run Analysis", key="dash_analysis", use_container_width=True):
            st.session_state["page"] = "analysis"
            st.rerun()
    with col3:
        if st.button("👤 Edit Profile", key="dash_profile", use_container_width=True):
            st.session_state["page"] = "profile"
            st.rerun()
