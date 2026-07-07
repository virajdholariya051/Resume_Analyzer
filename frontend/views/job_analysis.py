"""
Job Description Analysis page - manage and analyze job descriptions.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.job_service import JobService
from backend.nlp.skill_extractor import SkillExtractor


def render_job_analysis_page() -> None:
    """Render the job description analysis page."""
    st.markdown('<h1 class="main-header">📋 Job Description Analysis</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    job_service = JobService()
    extractor = SkillExtractor()

    tab1, tab2 = st.tabs(["➕ Add / Analyze JD", "📂 Saved Job Descriptions"])

    with tab1:
        _render_add_analyze(job_service, extractor)

    with tab2:
        _render_saved_jobs(job_service)


def _render_add_analyze(job_service, extractor) -> None:
    """Add a new job description and analyze its skills."""
    st.markdown("### Paste a job description to extract required skills")

    title = st.text_input("Job Title", placeholder="e.g., Senior Python Developer")
    description = st.text_area(
        "Job Description Text",
        placeholder="Paste the full job description here...",
        height=220,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Analyze Skills", use_container_width=True):
            if not description.strip():
                st.warning("Please paste a job description first.")
            else:
                try:
                    categorized = extractor.categorize_skills(description)
                    st.session_state["jd_analysis"] = {
                        "technical": categorized["technical"],
                        "soft": categorized["soft"],
                    }
                except Exception as e:
                    st.error(f"Failed to analyze: {e}")

    with col2:
        if st.button("💾 Save Job Description", use_container_width=True, type="primary"):
            if not title.strip() or not description.strip():
                st.warning("Both title and description are required to save.")
            else:
                try:
                    result = job_service.create_job(title, description, "")
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
                except Exception as e:
                    st.error(f"Failed to save: {e}")

    if "jd_analysis" in st.session_state:
        analysis = st.session_state["jd_analysis"]
        st.markdown("---")
        st.markdown("### Extracted Skills")
        col1, col2 = st.columns(2)
        with col1:
            tech = analysis["technical"]
            st.markdown(f"#### 💻 Technical ({len(tech)})")
            if tech:
                for s in tech:
                    st.markdown(f"- {s}")
            else:
                st.caption("No technical skills detected.")
        with col2:
            soft = analysis["soft"]
            st.markdown(f"#### 🤝 Soft ({len(soft)})")
            if soft:
                for s in soft:
                    st.markdown(f"- {s}")
            else:
                st.caption("No soft skills detected.")


def _render_saved_jobs(job_service) -> None:
    """List and manage saved job descriptions."""
    st.markdown("### Saved Job Descriptions")

    jobs = job_service.get_all_jobs()
    if not jobs:
        st.info("No job descriptions saved yet. Add one in the first tab.")
        return

    for job in jobs:
        with st.expander(f"🏢 {job['job_title']}"):
            st.write(f"**Description:** {job['job_description_text'][:400]}...")
            st.write(f"**Required Skills:** {job['required_skills']}")
            if st.button("🗑️ Delete", key=f"jd_del_{job['job_id']}"):
                result = job_service.delete_job(job["job_id"])
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
