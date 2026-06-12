"""
Top Candidates page - view top N candidates for a job description.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import get_current_user
from backend.services.recruiter_service import RecruiterService
from backend.services.job_service import JobService
from frontend.components.charts import create_candidate_ranking_chart


def render_top_candidates_page() -> None:
    """Render the top candidates page."""
    st.markdown('<h1 class="main-header">⭐ Top Candidates</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    recruiter_service = RecruiterService()
    job_service = JobService()

    jobs = job_service.get_all_jobs()
    if not jobs:
        st.warning("📋 No job descriptions found. Create one under **Job Descriptions**.")
        return

    options = {f"{j['job_title']}" + (f" @ {j['company_name']}" if j['company_name'] else ""): j["job_id"] for j in jobs}
    selected_label = st.selectbox("🎯 Select Job Description", list(options.keys()))
    job_id = options[selected_label]

    col1, col2 = st.columns(2)
    with col1:
        top_n = st.selectbox("Show Top", [10, 25, 50], index=0)
    with col2:
        sort_by = st.selectbox("Rank By", ["Overall Score", "ATS Score", "Match Percentage"])

    if st.button("🔄 Load Top Candidates", use_container_width=True, type="primary"):
        progress = st.progress(0, text="Analyzing...")

        def _cb(current, total):
            progress.progress(current / total, text=f"Analyzing {current}/{total}...")

        with st.spinner("Evaluating candidates..."):
            ranked = recruiter_service.rank_candidates(
                user["user_id"], job_id, auto_analyze=True, progress_callback=_cb
            )
        progress.empty()
        st.session_state["top_ranked"] = ranked
        st.session_state["top_job_id"] = job_id

    ranked = st.session_state.get("top_ranked", [])
    if st.session_state.get("top_job_id") != job_id:
        ranked = []

    if not ranked:
        st.info("Click **Load Top Candidates** to evaluate your candidate pool.")
        return

    # Sort according to selection
    sort_key = {
        "Overall Score": "rank_score",
        "ATS Score": "ats_score",
        "Match Percentage": "job_match_percentage",
    }[sort_by]
    ranked = sorted(ranked, key=lambda x: x[sort_key], reverse=True)
    for i, c in enumerate(ranked, start=1):
        c["rank"] = i

    top = ranked[:top_n]

    st.markdown("---")
    st.plotly_chart(create_candidate_ranking_chart(top, top_n=min(top_n, 25)), use_container_width=True)

    # Table
    df = pd.DataFrame([
        {
            "Rank": c["rank"],
            "Candidate": c["candidate_name"],
            "ATS": c["ats_score"],
            "Match %": c["job_match_percentage"],
            "Overall": round(c["rank_score"], 1),
            "Status": c["status"],
        }
        for c in top
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
