"""
Skill Gap Analysis page - compares resume skills against job requirements.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.resume_service import ResumeService
from backend.services.job_service import JobService
from backend.services.report_service import ReportService
from backend.nlp.skill_extractor import SkillExtractor


def render_skill_gap_page() -> None:
    """Render the skill gap analysis page."""
    st.markdown('<h1 class="main-header">🛠️ Skill Gap Analysis</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    resume_service = ResumeService()
    job_service = JobService()
    report_service = ReportService()
    extractor = SkillExtractor()

    resumes = resume_service.get_user_resumes(user["user_id"])
    if not resumes:
        st.warning("📭 No resumes found. Upload a resume first.")
        return

    jobs = job_service.get_all_jobs()
    if not jobs:
        st.warning("📋 No job descriptions available. Add one under **Job Description Analysis**.")
        return

    st.markdown("Identify which required skills you have and which ones you're missing.")

    resume_options = {f"{r['file_name']} ({r['upload_date']})": r["resume_id"] for r in resumes}
    selected_resume = st.selectbox("Select Resume", options=list(resume_options.keys()))
    resume_id = resume_options[selected_resume]

    job_options = {j["job_title"]: j["job_id"] for j in jobs}
    selected_job = st.selectbox("Select Target Job", options=list(job_options.keys()))
    job_id = job_options[selected_job]

    if st.button("🔍 Analyze Skill Gap", use_container_width=True, type="primary"):
        with st.spinner("Analyzing skill gap..."):
            try:
                resume = resume_service.get_resume_by_id(resume_id)
                job = job_service.get_job_by_id(job_id)
                if not resume or not job:
                    st.error("Resume or job not found.")
                    return

                resume_skills = extractor.extract_skills(resume["resume_text"])
                required_skills = [s.strip() for s in job["required_skills"].split(",") if s.strip()]
                skill_gap = extractor.get_skill_gap(resume_skills, required_skills)
                match_pct = extractor.calculate_skill_match_percentage(resume_skills, required_skills)

                st.session_state["skill_gap_result"] = {
                    "gap": skill_gap,
                    "match_pct": match_pct,
                    "resume_name": resume["file_name"],
                    "job_title": job["job_title"],
                }
            except Exception as e:
                st.error(f"Failed to analyze skill gap: {e}")
                return

    if "skill_gap_result" in st.session_state:
        data = st.session_state["skill_gap_result"]
        skill_gap = data["gap"]
        st.markdown("---")

        match_pct = data["match_pct"]
        color = "score-high" if match_pct >= 70 else "score-medium" if match_pct >= 50 else "score-low"
        st.markdown(f"### Skill Match: <span class='{color}'>{match_pct}%</span>", unsafe_allow_html=True)
        st.progress(min(1.0, match_pct / 100))

        col1, col2, col3 = st.columns(3)
        with col1:
            matched = skill_gap.get("matched", [])
            st.markdown(f"#### ✅ Matched ({len(matched)})")
            if matched:
                for s in matched:
                    st.markdown(f"- 🟢 {s}")
            else:
                st.caption("No matched skills.")
        with col2:
            missing = skill_gap.get("missing", [])
            st.markdown(f"#### ❌ Missing ({len(missing)})")
            if missing:
                for s in missing:
                    st.markdown(f"- 🔴 {s}")
            else:
                st.caption("No missing skills. Great!")
        with col3:
            extra = skill_gap.get("extra", [])
            st.markdown(f"#### ➕ Additional ({len(extra)})")
            if extra:
                for s in extra[:15]:
                    st.markdown(f"- 🔵 {s}")
            else:
                st.caption("No additional skills.")

        # Download report
        st.markdown("---")
        if st.button("📄 Generate Skill Gap Report", use_container_width=True):
            try:
                report_path = report_service.generate_skill_gap_report(
                    skill_gap, data["resume_name"], data["job_title"]
                )
                with open(report_path, "rb") as f:
                    st.download_button(
                        "💾 Download PDF Report",
                        data=f.read(),
                        file_name="skill_gap_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
