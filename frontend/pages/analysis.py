"""
Analysis page for running resume analysis against job descriptions.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.resume_service import ResumeService
from backend.services.analysis_service import AnalysisService
from backend.services.job_service import JobService
from backend.services.report_service import ReportService
from frontend.components.charts import (
    create_ats_score_gauge,
    create_job_match_chart,
    create_score_comparison_chart,
)


def render_analysis_page() -> None:
    """Render the analysis page."""
    st.markdown('<h1 class="main-header">🔍 Resume Analysis</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    resume_service = ResumeService()
    analysis_service = AnalysisService()
    job_service = JobService()
    report_service = ReportService()

    # Tab layout
    tab1, tab2, tab3 = st.tabs(["🆕 New Analysis", "📋 Job Descriptions", "📜 History"])

    with tab1:
        _render_new_analysis(user, resume_service, analysis_service, job_service, report_service)

    with tab2:
        _render_job_descriptions(job_service)

    with tab3:
        _render_analysis_history(user, analysis_service)


def _render_new_analysis(user, resume_service, analysis_service, job_service, report_service) -> None:
    """Render the new analysis section."""
    st.markdown("### Run a new analysis")

    # Select resume
    resumes = resume_service.get_user_resumes(user["user_id"])
    if not resumes:
        st.warning("Please upload a resume first.")
        return

    resume_options = {f"{r['file_name']} ({r['upload_date']})": r["resume_id"] for r in resumes}
    
    # Pre-select resume if coming from upload page
    default_idx = 0
    if "selected_resume_id" in st.session_state:
        for idx, (key, rid) in enumerate(resume_options.items()):
            if rid == st.session_state["selected_resume_id"]:
                default_idx = idx
                break

    selected_resume = st.selectbox(
        "Select Resume",
        options=list(resume_options.keys()),
        index=default_idx,
    )
    resume_id = resume_options[selected_resume]

    # Select job description
    jobs = job_service.get_all_jobs()
    if not jobs:
        st.warning("No job descriptions available. Add one in the Job Descriptions tab.")
        return

    job_options = {f"{j['job_title']}": j["job_id"] for j in jobs}
    selected_job = st.selectbox("Select Job Description", options=list(job_options.keys()))
    job_id = job_options[selected_job]

    # Show job details
    job = job_service.get_job_by_id(job_id)
    if job:
        with st.expander("📋 View Job Details"):
            st.write(f"**Title:** {job['job_title']}")
            st.write(f"**Description:** {job['job_description_text']}")
            st.write(f"**Required Skills:** {job['required_skills']}")

    # Run analysis
    if st.button("🚀 Run Analysis", use_container_width=True, type="primary"):
        with st.spinner("Analyzing resume..."):
            result = analysis_service.analyze_resume(resume_id, job_id)

            if result["success"]:
                st.success("Analysis complete!")
                st.session_state["last_analysis"] = result
                st.session_state["last_analysis_resume"] = selected_resume
                st.session_state["last_analysis_job"] = job.get("job_title", "") if job else ""
                st.rerun()
            else:
                st.error(result["message"])

    # Display last analysis if available
    if "last_analysis" in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Analysis Results")
        _display_analysis_results(
            st.session_state["last_analysis"],
            report_service,
            st.session_state.get("last_analysis_resume", ""),
            st.session_state.get("last_analysis_job", ""),
        )


def _display_analysis_results(result: dict, report_service, resume_name: str, job_title: str) -> None:
    """Display analysis results with visualizations."""
    st.markdown("---")

    ats_data = result["ats_score"]
    match_data = result["job_match"]
    strengths = result["strengths"]
    weaknesses = result["weaknesses"]
    parsed = result.get("parsed_resume", {})

    # Score cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📈 ATS Score")
        fig = create_ats_score_gauge(ats_data["overall_score"])
        st.plotly_chart(fig, use_container_width=True, key="analysis_ats_gauge")
        st.markdown(f"**Grade:** {ats_data['grade']}")

    with col2:
        st.markdown("#### 🎯 Job Match")
        fig = create_score_comparison_chart(ats_data["overall_score"], match_data["overall_match"])
        st.plotly_chart(fig, use_container_width=True, key="analysis_score_compare")
        st.markdown(f"**Recommendation:** {match_data['recommendation']}")

    # Job match radar chart
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 Match Breakdown")
        fig = create_job_match_chart(match_data)
        st.plotly_chart(fig, use_container_width=True, key="analysis_match_radar")

    with col2:
        st.markdown("#### 📋 ATS Score Components")
        components = ats_data.get("component_scores", {})
        for key, value in components.items():
            label = key.replace("_", " ").title()
            st.progress(int(value) / 100, text=f"{label}: {round(value)}%")

    # Strengths and Weaknesses
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ Strengths")
        for s in strengths:
            st.markdown(f"- 🟢 {s}")

    with col2:
        st.markdown("#### ⚠️ Areas for Improvement")
        for w in weaknesses:
            st.markdown(f"- 🔴 {w}")

    # Skill Gap Analysis
    skill_gap = match_data.get("skill_gap", {})
    if skill_gap:
        st.markdown("---")
        st.markdown("#### 🛠️ Skill Gap Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ Matched Skills**")
            for s in skill_gap.get("matched", []):
                st.markdown(f"- {s}")
        with col2:
            st.markdown("**❌ Missing Skills**")
            for s in skill_gap.get("missing", []):
                st.markdown(f"- {s}")
        with col3:
            st.markdown("**➕ Additional Skills**")
            for s in skill_gap.get("extra", [])[:10]:
                st.markdown(f"- {s}")

    # Parsed resume info
    if parsed:
        st.markdown("---")
        with st.expander("📝 Parsed Resume Data"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {parsed.get('name', 'N/A')}")
                st.write(f"**Email:** {parsed.get('email', 'N/A')}")
                st.write(f"**Phone:** {parsed.get('phone', 'N/A')}")
                st.write(f"**Languages:** {', '.join(parsed.get('languages', [])) or 'N/A'}")
            with col2:
                st.write(f"**Sections Found:** {', '.join(parsed.get('sections_found', []))}")
                skills = parsed.get("skills", [])
                if skills:
                    st.write(f"**Skills ({len(skills)}):** {', '.join(skills[:15])}")

    # Download reports
    st.markdown("---")
    st.markdown("#### 📥 Download Reports")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Download ATS Report", use_container_width=True):
            report_path = report_service.generate_ats_report(result, resume_name)
            with open(report_path, "rb") as f:
                st.download_button(
                    "💾 Save ATS Report PDF",
                    data=f.read(),
                    file_name="ats_report.pdf",
                    mime="application/pdf",
                )
    with col2:
        if skill_gap and st.button("📄 Download Skill Gap Report", use_container_width=True):
            report_path = report_service.generate_skill_gap_report(skill_gap, resume_name, job_title)
            with open(report_path, "rb") as f:
                st.download_button(
                    "💾 Save Skill Gap Report PDF",
                    data=f.read(),
                    file_name="skill_gap_report.pdf",
                    mime="application/pdf",
                )


def _render_job_descriptions(job_service) -> None:
    """Render job description management section."""
    st.markdown("### 📋 Manage Job Descriptions")

    # Add new job description
    with st.expander("➕ Add New Job Description"):
        with st.form("add_job_form"):
            title = st.text_input("Job Title", placeholder="e.g., Senior Python Developer")
            description = st.text_area(
                "Job Description",
                placeholder="Enter the full job description...",
                height=200,
            )
            skills = st.text_input(
                "Required Skills (comma-separated)",
                placeholder="Python, Django, AWS, Docker (leave empty for auto-extraction)",
            )
            submit = st.form_submit_button("💾 Save Job Description", use_container_width=True)

            if submit:
                if not title or not description:
                    st.error("Title and description are required.")
                else:
                    result = job_service.create_job(title, description, skills)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])

    # List existing jobs
    st.markdown("---")
    jobs = job_service.get_all_jobs()
    if jobs:
        for job in jobs:
            with st.expander(f"🏢 {job['job_title']}"):
                st.write(f"**Description:** {job['job_description_text'][:300]}...")
                st.write(f"**Required Skills:** {job['required_skills']}")
                if st.button("🗑️ Delete", key=f"del_job_{job['job_id']}"):
                    result = job_service.delete_job(job["job_id"])
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    else:
        st.info("No job descriptions yet. Add one above!")


def _render_analysis_history(user, analysis_service) -> None:
    """Render analysis history section."""
    st.markdown("### 📜 Analysis History")

    history = analysis_service.get_analysis_history(user["user_id"])

    if history:
        for item in history:
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"📅 {item['created_at']}")
                with col2:
                    ats = item["ats_score"]
                    color = "🟢" if ats >= 70 else "🟡" if ats >= 50 else "🔴"
                    st.write(f"{color} ATS: {ats}/100")
                with col3:
                    match = item["job_match_percentage"]
                    color = "🟢" if match >= 70 else "🟡" if match >= 50 else "🔴"
                    st.write(f"{color} Match: {match}%")
                with col4:
                    st.write(f"ID: #{item['analysis_id']}")
                st.markdown("---")
    else:
        st.info("No analyses yet. Run your first analysis in the 'New Analysis' tab!")
