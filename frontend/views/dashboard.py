"""
Dashboard page displaying overview stats and analytics.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.analysis_service import AnalysisService
from frontend.components.charts import (
    create_skill_distribution_chart,
    create_analysis_history_chart,
    create_time_series_chart,
    STATIC_CHART_CONFIG,
)


def render_dashboard() -> None:
    """Render the job seeker dashboard with KPI cards and read-only charts.

    All charts read live data from the database on every render, so they
    refresh automatically after a new analysis or resume upload.
    """
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    st.markdown(f"### Welcome back, {user['name']}! 👋")
    st.markdown("---")

    # Get dashboard stats (recomputed each render => automatic refresh).
    analysis_service = AnalysisService()
    stats = analysis_service.get_dashboard_stats(user["user_id"])

    # ------------------------------------------------------------------ #
    # KPI cards
    # ------------------------------------------------------------------ #
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📄 Total Resumes", stats["total_resumes"])
    with col2:
        st.metric("📈 Latest ATS Score", f"{stats['latest_ats_score']}%")
    with col3:
        st.metric("📊 Avg ATS Score", f"{stats['average_ats_score']}%")
    with col4:
        st.metric("🎯 Latest Job Match", f"{stats['latest_match_percentage']}%")
    with col5:
        st.metric("🔍 Total Analyses", stats["total_analyses"])

    st.markdown("---")

    # ------------------------------------------------------------------ #
    # Read-only charts
    # ------------------------------------------------------------------ #
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📈 ATS Score History")
        if stats["ats_history"]:
            fig = create_analysis_history_chart(stats["ats_history"])
            st.plotly_chart(fig, use_container_width=True, config=STATIC_CHART_CONFIG)
        else:
            st.info("No analysis history yet. Run your first analysis!")

    with col_right:
        st.markdown("#### 📤 Resume Upload Timeline")
        timeline = stats["upload_timeline"]
        if timeline["labels"]:
            fig = create_time_series_chart(
                timeline["labels"], timeline["values"],
                "Resume Uploads", "Uploads", "#16a34a",
            )
            st.plotly_chart(fig, use_container_width=True, config=STATIC_CHART_CONFIG)
        else:
            st.info("Upload a resume to see your upload timeline.")

    st.markdown("#### 🧠 Skills Distribution")
    if stats["top_skills"]:
        fig = create_skill_distribution_chart(stats["top_skills"])
        st.plotly_chart(fig, use_container_width=True, config=STATIC_CHART_CONFIG)
    else:
        st.info("Upload and analyze resumes to see skill distribution.")

    # ------------------------------------------------------------------ #
    # Resume Analysis History
    # ------------------------------------------------------------------ #
    st.markdown("---")
    st.markdown("### 🕒 Resume Analysis History")

    if stats["recent_analyses"]:
        for analysis in stats["recent_analyses"]:
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"📅 {analysis['created_at']}")
                with col2:
                    st.write(f"🏷️ {analysis.get('analysis_type', 'Resume + Job Description')}")
                with col3:
                    ats = analysis["ats_score"]
                    color = "score-high" if ats >= 70 else "score-medium" if ats >= 50 else "score-low"
                    st.markdown(f"ATS: <span class='{color}'>{ats}/100</span>", unsafe_allow_html=True)
                with col4:
                    match = analysis["job_match_percentage"]
                    if analysis.get("analysis_type") == "Resume Only":
                        st.markdown("Match: <span>N/A</span>", unsafe_allow_html=True)
                    else:
                        color = "score-high" if match >= 70 else "score-medium" if match >= 50 else "score-low"
                        st.markdown(f"Match: <span class='{color}'>{match}%</span>", unsafe_allow_html=True)
    else:
        st.info("No analyses yet. Upload a resume and run your first analysis!")

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
