"""
Reports page - view analysis history and download PDF reports.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.analysis_service import AnalysisService
from backend.services.resume_service import ResumeService
from backend.services.job_service import JobService
from backend.services.report_service import ReportService


def render_reports_page() -> None:
    """Render the reports page."""
    st.markdown('<h1 class="main-header">📑 Reports</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    analysis_service = AnalysisService()
    resume_service = ResumeService()
    job_service = JobService()
    report_service = ReportService()

    history = analysis_service.get_analysis_history(user["user_id"])

    if not history:
        st.info("📭 No analysis reports yet. Run an analysis under **Resume Analysis** to generate reports.")
        return

    st.markdown("Download PDF reports for your previous analyses.")
    st.markdown("---")

    # Build lookup maps for names
    resumes = {r["resume_id"]: r["file_name"] for r in resume_service.get_user_resumes(user["user_id"])}
    jobs = {j["job_id"]: j["job_title"] for j in job_service.get_all_jobs()}

    for item in history:
        resume_name = resumes.get(item["resume_id"], f"Resume #{item['resume_id']}")
        job_title = jobs.get(item["job_id"], f"Job #{item['job_id']}")

        with st.expander(f"📊 {resume_name} → {job_title}  |  {item['created_at']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ats = item["ats_score"]
                color = "score-high" if ats >= 70 else "score-medium" if ats >= 50 else "score-low"
                st.markdown(f"**ATS Score:** <span class='{color}'>{ats}/100</span>", unsafe_allow_html=True)
            with col2:
                match = item["job_match_percentage"]
                color = "score-high" if match >= 70 else "score-medium" if match >= 50 else "score-low"
                st.markdown(f"**Job Match:** <span class='{color}'>{match}%</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"**Analysis ID:** #{item['analysis_id']}")

            if item.get("strengths"):
                st.markdown("**Strengths:** " + item["strengths"])
            if item.get("weaknesses"):
                st.markdown("**Areas to Improve:** " + item["weaknesses"])

            # Generate a downloadable report from stored data
            if st.button("📄 Generate PDF Report", key=f"report_{item['analysis_id']}"):
                try:
                    report_data = {
                        "ats_score": {"overall_score": item["ats_score"], "grade": "", "component_scores": {}},
                        "job_match": {"overall_match": item["job_match_percentage"], "skill_gap": {}},
                        "strengths": item["strengths"].split("; ") if item.get("strengths") else [],
                        "weaknesses": item["weaknesses"].split("; ") if item.get("weaknesses") else [],
                    }
                    report_path = report_service.generate_ats_report(report_data, resume_name)
                    with open(report_path, "rb") as f:
                        st.download_button(
                            "💾 Download PDF",
                            data=f.read(),
                            file_name=f"report_{item['analysis_id']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{item['analysis_id']}",
                        )
                except Exception as e:
                    st.error(f"Failed to generate report: {e}")
