"""
Recruiter Reports page - export candidate reports and view AI insights.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.recruiter_service import RecruiterService
from backend.services.job_service import JobService
from backend.services.resume_service import ResumeService
from backend.services.export_service import ExportService


def render_recruiter_reports_page() -> None:
    """Render the recruiter reports and AI insights page."""
    st.markdown('<h1 class="main-header">📑 Reports & AI Insights</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    recruiter_service = RecruiterService()
    job_service = JobService()
    resume_service = ResumeService()
    export_service = ExportService()

    jobs = job_service.get_all_jobs()
    if not jobs:
        st.warning("📋 No job descriptions found. Create one under **Job Descriptions**.")
        return

    candidates = resume_service.get_candidates(user["user_id"])
    if not candidates:
        st.info("📭 No candidates in your pool.")
        return

    job_options = {f"{j['job_title']}" + (f" @ {j['company_name']}" if j['company_name'] else ""): j["job_id"] for j in jobs}
    selected_label = st.selectbox("🎯 Job Description", list(job_options.keys()))
    job_id = job_options[selected_label]

    tab1, tab2 = st.tabs(["📥 Export Reports", "🤖 AI Insights"])

    # --- Export ---
    with tab1:
        st.markdown("Generate a ranked report of all candidates for the selected job.")
        if st.button("📊 Generate Report", use_container_width=True, type="primary"):
            with st.spinner("Ranking candidates..."):
                ranked = recruiter_service.rank_candidates(user["user_id"], job_id, auto_analyze=True)
            st.session_state["report_ranked"] = ranked
            st.session_state["report_job_id"] = job_id

        ranked = st.session_state.get("report_ranked", [])
        if st.session_state.get("report_job_id") != job_id:
            ranked = []

        if ranked:
            st.success(f"Report ready for {len(ranked)} candidate(s).")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button(
                    "⬇️ CSV", data=export_service.to_csv(ranked),
                    file_name="candidates.csv", mime="text/csv", use_container_width=True,
                )
            with c2:
                st.download_button(
                    "⬇️ Excel", data=export_service.to_excel(ranked),
                    file_name="candidates.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with c3:
                st.download_button(
                    "⬇️ PDF", data=export_service.to_pdf(ranked, f"Report — {selected_label}"),
                    file_name="candidates.pdf", mime="application/pdf", use_container_width=True,
                )

    # --- AI Insights ---
    with tab2:
        st.markdown("Get AI-style strengths, weaknesses, and recommendations for a candidate.")
        cand_options = {f"{c['candidate_name']} ({c['file_name']})": c["resume_id"] for c in candidates}
        selected_cand = st.selectbox("Select Candidate", list(cand_options.keys()))
        resume_id = cand_options[selected_cand]

        if st.button("🤖 Generate Insights", use_container_width=True):
            with st.spinner("Analyzing candidate..."):
                insights = recruiter_service.generate_insights(resume_id, job_id)
            st.session_state["candidate_insights"] = insights

        insights = st.session_state.get("candidate_insights")
        if insights:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### ✅ Strengths")
                for s in insights["strengths"]:
                    st.markdown(f"- 🟢 {s}")
            with col2:
                st.markdown("#### ⚠️ Weaknesses")
                for w in insights["weaknesses"]:
                    st.markdown(f"- 🔴 {w}")
            with col3:
                st.markdown("#### 💡 Recommendations")
                for r in insights["recommendations"]:
                    st.markdown(f"- 🔵 {r}")
