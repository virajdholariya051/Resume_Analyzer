"""
Recruiter Dashboard - candidate pool overview and analytics.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.recruiter_service import RecruiterService
from frontend.components.charts import (
    create_skill_distribution_chart,
    create_score_distribution_chart,
    create_status_pie_chart,
)


def render_recruiter_dashboard() -> None:
    """Render the recruiter dashboard."""
    st.markdown('<h1 class="main-header">📊 Recruiter Dashboard</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    service = RecruiterService()
    stats = service.get_dashboard_stats(user["user_id"])

    st.markdown(f"### Welcome, {user['name']}! 👋")
    st.markdown("---")

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Total Resumes", stats["total_resumes"])
    c2.metric("👥 Total Candidates", stats["total_candidates"])
    c3.metric("📈 Avg ATS Score", f"{stats['average_ats_score']}%")
    c4.metric("🎯 Avg Match %", f"{stats['average_match_percentage']}%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("✅ Shortlisted", stats["shortlisted"])
    c6.metric("❌ Rejected", stats["rejected"])
    c7.metric("🔍 Under Review", stats["under_review"])
    c8.metric("🆕 New", stats["new"])

    st.markdown("---")

    if stats["total_resumes"] == 0:
        st.info("📭 No candidates yet. Head to **Upload Resumes** to add resumes to your pool.")
        return

    # Charts row 1
    col_left, col_right = st.columns(2)
    with col_left:
        if stats["top_skills"]:
            st.plotly_chart(
                create_skill_distribution_chart(stats["top_skills"]),
                use_container_width=True,
            )
        else:
            st.info("No skills extracted yet.")
    with col_right:
        st.plotly_chart(
            create_status_pie_chart(stats["status_counts"]),
            use_container_width=True,
        )

    # Charts row 2
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(
            create_score_distribution_chart(stats["ats_scores"], "ATS Score Distribution", "#1f77b4"),
            use_container_width=True,
        )
    with col_b:
        st.plotly_chart(
            create_score_distribution_chart(stats["match_scores"], "Match % Distribution", "#ff7f0e"),
            use_container_width=True,
        )

    # Recent uploads
    st.markdown("---")
    st.markdown("### 🕒 Recently Uploaded Resumes")
    if stats["recent_uploads"]:
        for item in stats["recent_uploads"]:
            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
            col1.write(f"👤 {item['candidate_name']}")
            col2.write(f"📄 {item['file_name']}")
            col3.write(f"🏷️ {item['status']}")
            col4.write(f"📅 {item['upload_date']}")
    else:
        st.info("No recent uploads.")
