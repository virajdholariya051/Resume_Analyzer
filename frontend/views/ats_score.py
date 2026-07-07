"""
ATS Score page - calculates and displays the ATS compatibility score for a resume.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.resume_service import ResumeService
from backend.services.job_service import JobService
from backend.nlp.ats_scorer import ATSScorer
from frontend.components.charts import create_ats_score_gauge, STATIC_CHART_CONFIG


def render_ats_score_page() -> None:
    """Render the standalone ATS score page."""
    st.markdown('<h1 class="main-header">📈 ATS Score</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    resume_service = ResumeService()
    job_service = JobService()
    scorer = ATSScorer()

    resumes = resume_service.get_user_resumes(user["user_id"])
    if not resumes:
        st.warning("📭 You haven't uploaded any resumes yet. Go to **Upload Resume** to get started.")
        return

    st.markdown("Check how well your resume performs against Applicant Tracking Systems (ATS).")

    resume_options = {f"{r['file_name']} ({r['upload_date']})": r["resume_id"] for r in resumes}
    selected_resume = st.selectbox("Select Resume", options=list(resume_options.keys()))
    resume_id = resume_options[selected_resume]

    # Optional: compare against a job description
    jobs = job_service.get_all_jobs()
    job_options = {"None (general scoring)": None}
    job_options.update({j["job_title"]: j["job_id"] for j in jobs})
    selected_job = st.selectbox("Compare against Job Description (optional)", options=list(job_options.keys()))
    job_id = job_options[selected_job]

    if st.button("📊 Calculate ATS Score", use_container_width=True, type="primary"):
        with st.spinner("Calculating ATS score..."):
            try:
                resume = resume_service.get_resume_by_id(resume_id)
                if not resume:
                    st.error("Resume not found.")
                    return

                job_description = ""
                required_skills = None
                if job_id:
                    job = job_service.get_job_by_id(job_id)
                    if job:
                        job_description = job["job_description_text"]
                        required_skills = [s.strip() for s in job["required_skills"].split(",") if s.strip()]

                result = scorer.calculate_ats_score(
                    resume["resume_text"], job_description, required_skills
                )
                st.session_state["ats_result"] = result
            except Exception as e:
                st.error(f"Failed to calculate ATS score: {e}")
                return

    # Display result
    if "ats_result" in st.session_state:
        result = st.session_state["ats_result"]
        st.markdown("---")

        col1, col2 = st.columns([1, 1])
        with col1:
            fig = create_ats_score_gauge(result["overall_score"])
            st.plotly_chart(fig, use_container_width=True, key="ats_page_gauge", config=STATIC_CHART_CONFIG)
        with col2:
            st.markdown("### Result")
            score = result["overall_score"]
            grade = result["grade"]
            color = "score-high" if score >= 70 else "score-medium" if score >= 50 else "score-low"
            st.markdown(f"**Overall Score:** <span class='{color}'>{score}/100</span>", unsafe_allow_html=True)
            st.markdown(f"**Grade:** {grade}")
            if score >= 70:
                st.success("Your resume is ATS-friendly!")
            elif score >= 50:
                st.warning("Decent, but there's room for improvement.")
            else:
                st.error("Your resume needs significant improvement for ATS compatibility.")

        st.markdown("---")
        st.markdown("### 📋 Component Breakdown")
        components = result.get("component_scores", {})
        for key, value in components.items():
            label = key.replace("_", " ").title()
            st.progress(min(1.0, value / 100), text=f"{label}: {round(value)}%")
