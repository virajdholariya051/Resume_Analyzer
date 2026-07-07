"""
Candidate Comparison page - side-by-side comparison of selected candidates.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import get_current_user
from backend.services.recruiter_service import RecruiterService
from backend.services.job_service import JobService
from backend.services.resume_service import ResumeService


def render_candidate_comparison_page() -> None:
    """Render the candidate comparison page."""
    st.markdown('<h1 class="main-header">⚖️ Candidate Comparison</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    recruiter_service = RecruiterService()
    job_service = JobService()
    resume_service = ResumeService()

    jobs = job_service.get_all_jobs()
    if not jobs:
        st.warning("📋 No job descriptions found. Create one under **Job Descriptions**.")
        return

    candidates = resume_service.get_candidates(user["user_id"])
    if len(candidates) < 2:
        st.info("📭 You need at least 2 candidates to compare. Upload more resumes.")
        return

    job_options = {f"{j['job_title']}" + (f" @ {j['company_name']}" if j['company_name'] else ""): j["job_id"] for j in jobs}
    selected_job_label = st.selectbox("🎯 Job Description", list(job_options.keys()))
    job_id = job_options[selected_job_label]

    cand_options = {f"{c['candidate_name']} ({c['file_name']})": c["resume_id"] for c in candidates}
    selected = st.multiselect(
        "Select 2 or 3 candidates to compare",
        list(cand_options.keys()),
        max_selections=3,
    )

    if len(selected) < 2:
        st.caption("Select at least 2 candidates.")
        return

    if st.button("⚖️ Compare", use_container_width=True, type="primary"):
        resume_ids = [cand_options[label] for label in selected]
        with st.spinner("Building comparison..."):
            # Ensure analyses exist
            recruiter_service.analysis_service.analyze_batch(resume_ids, job_id, force=False)
            data = recruiter_service.compare_candidates(resume_ids, job_id)
        st.session_state["comparison_data"] = data

    data = st.session_state.get("comparison_data", [])
    if not data:
        return

    st.markdown("---")
    st.markdown("### 📊 Side-by-Side Comparison")

    # Build a transposed comparison table: metrics as rows, candidates as columns
    metrics = [
        ("ATS Score", "ats_score"),
        ("Match %", "job_match_percentage"),
        ("Skill Match", "skill_match"),
        ("Experience Match", "experience_match"),
        ("Education Match", "education_match"),
        ("Certification Match", "certification_match"),
        ("Overall Score", "rank_score"),
        ("Status", "status"),
        ("Skills", "skills"),
        ("Education", "education"),
        ("Certifications", "certifications"),
    ]

    table = {"Metric": [label for label, _ in metrics]}
    for cand in data:
        table[cand["candidate_name"]] = [cand.get(key, "N/A") for _, key in metrics]

    df = pd.DataFrame(table)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Highlight winner by overall score
    numeric = [c for c in data if isinstance(c.get("rank_score"), (int, float))]
    if numeric:
        winner = max(numeric, key=lambda c: c["rank_score"])
        st.success(f"🏆 Best overall match: **{winner['candidate_name']}** (Score: {winner['rank_score']:.1f})")
