"""
Analysis page for running resume analysis.

Supports a guided, multi-step workflow with two analysis modes:
    * Resume Only              - ATS + resume quality + recommendations.
    * Resume + Job Description - the above plus job matching, skill gap
                                 analysis and candidate compatibility.
"""

import logging
import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.resume_service import ResumeService
from backend.services.analysis_service import (
    AnalysisService,
    ANALYSIS_TYPE_RESUME_ONLY,
    ANALYSIS_TYPE_RESUME_JOB,
)
from backend.services.job_service import JobService
from backend.services.report_service import ReportService
from frontend.components.charts import (
    create_ats_score_gauge,
    create_quality_score_gauge,
    create_job_match_chart,
    create_score_comparison_chart,
    STATIC_CHART_CONFIG,
)

logger = logging.getLogger("resume_analyzer.views.analysis")


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
    """Render the guided, multi-step new analysis workflow."""
    st.markdown("### Run a new analysis")

    # ---------------------------------------------------------------- #
    # Step 1 — Choose analysis type
    # ---------------------------------------------------------------- #
    st.markdown("#### Step 1 · Choose Analysis Type")
    analysis_type = st.radio(
        "How would you like to analyze your resume?",
        [ANALYSIS_TYPE_RESUME_ONLY, ANALYSIS_TYPE_RESUME_JOB],
        captions=[
            "Extract info, calculate ATS score, evaluate quality and get recommendations.",
            "Everything in Resume Only, plus job match %, skill gap analysis and compatibility.",
        ],
        key="analysis_type_choice",
    )

    # ---------------------------------------------------------------- #
    # Step 2 — Select resume
    # ---------------------------------------------------------------- #
    st.markdown("#### Step 2 · Select Resume")
    resumes = resume_service.get_user_resumes(user["user_id"])
    if not resumes:
        st.warning("📭 Please upload a resume first (see the **Upload Resume** page).")
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

    # ---------------------------------------------------------------- #
    # Step 3 — Job description (only for Resume + Job Description)
    # ---------------------------------------------------------------- #
    job_id = None
    job_title = ""
    job_mode = None
    if analysis_type == ANALYSIS_TYPE_RESUME_JOB:
        st.markdown("#### Step 3 · Add Job Description")
        job_mode = st.radio(
            "Provide the job description by:",
            ["Select Existing", "Enter New"],
            horizontal=True,
            key="job_input_mode",
        )

        if job_mode == "Select Existing":
            jobs = job_service.get_all_jobs()
            if not jobs:
                st.info("No saved job descriptions. Switch to **Enter New** or add one in the Job Descriptions tab.")
            else:
                job_options = {j["job_title"]: j["job_id"] for j in jobs}
                selected_job = st.selectbox("Select Job Description", options=list(job_options.keys()))
                job_id = job_options[selected_job]
                job_title = selected_job
                job = job_service.get_job_by_id(job_id)
                if job:
                    with st.expander("📋 View Job Details"):
                        st.write(f"**Title:** {job['job_title']}")
                        st.write(f"**Description:** {job['job_description_text']}")
                        st.write(f"**Required Skills:** {job['required_skills']}")
        else:  # Enter New
            job_title = st.text_input("Job Title", placeholder="e.g., Senior Python Developer")
            job_desc_text = st.text_area(
                "Job Description",
                placeholder="Paste the full job description here...",
                height=180,
            )
            job_skills = st.text_input(
                "Required Skills (comma-separated, optional)",
                placeholder="Python, Django, AWS, Docker",
            )
            # Stash ad-hoc inputs for use on submit
            st.session_state["_adhoc_job"] = {
                "title": job_title.strip(),
                "description": job_desc_text.strip(),
                "skills": job_skills.strip(),
            }

    # ---------------------------------------------------------------- #
    # Step 4 — Analyze
    # ---------------------------------------------------------------- #
    st.markdown("#### Step 4 · Analyze")
    if st.button("🚀 Run Analysis", use_container_width=True, type="primary"):
        _run_analysis(
            analysis_type, resume_id, selected_resume, job_mode, job_id,
            job_title, analysis_service, job_service,
        )

    # ---------------------------------------------------------------- #
    # Step 5 — Results
    # ---------------------------------------------------------------- #
    if "last_analysis" in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Analysis Results")
        _display_analysis_results(
            st.session_state["last_analysis"],
            report_service,
            st.session_state.get("last_analysis_resume", ""),
            st.session_state.get("last_analysis_job", ""),
        )


def _run_analysis(analysis_type, resume_id, resume_label, job_mode, job_id,
                  job_title, analysis_service, job_service) -> None:
    """Validate inputs and execute the selected analysis workflow."""
    progress = st.progress(0, text="Starting analysis...")
    try:
        if analysis_type == ANALYSIS_TYPE_RESUME_ONLY:
            progress.progress(30, text="Extracting resume information...")
            result = analysis_service.analyze_resume_only(resume_id, force=True)
            progress.progress(90, text="Evaluating resume quality...")
        else:
            # Resume + Job Description — validate job input first.
            if job_mode == "Enter New":
                adhoc = st.session_state.get("_adhoc_job", {})
                if not adhoc.get("title") or not adhoc.get("description"):
                    progress.empty()
                    st.error("⚠️ Please enter both a Job Title and a Job Description.")
                    return
                progress.progress(20, text="Saving job description...")
                created = job_service.create_job(
                    adhoc["title"], adhoc["description"], adhoc.get("skills", "")
                )
                if not created.get("success"):
                    progress.empty()
                    st.error(created.get("message", "Failed to save job description."))
                    return
                job_id = created.get("job_id")
                job_title = adhoc["title"]
            elif not job_id:
                progress.empty()
                st.error("⚠️ Please select or enter a Job Description to continue.")
                return

            progress.progress(40, text="Matching resume against job description...")
            result = analysis_service.analyze_resume(resume_id, job_id, force=True)
            progress.progress(90, text="Compiling results...")

        if result.get("success"):
            progress.progress(100, text="Done!")
            st.session_state["last_analysis"] = result
            st.session_state["last_analysis_resume"] = resume_label
            st.session_state["last_analysis_job"] = job_title
            progress.empty()
            st.success("✅ Analysis complete!")
            st.rerun()
        else:
            progress.empty()
            st.error(result.get("message", "Analysis failed."))
    except Exception as e:  # pragma: no cover - defensive UI guard
        progress.empty()
        logger.exception("Analysis run failed")
        st.error(f"Something went wrong during analysis: {e}")


def _display_analysis_results(result: dict, report_service, resume_name: str, job_title: str) -> None:
    """Display analysis results, adapting to the selected analysis type."""
    analysis_type = result.get("analysis_type", ANALYSIS_TYPE_RESUME_JOB)
    if analysis_type == ANALYSIS_TYPE_RESUME_ONLY:
        _display_resume_only_results(result, report_service, resume_name)
    else:
        _display_resume_job_results(result, report_service, resume_name, job_title)


def _display_resume_only_results(result: dict, report_service, resume_name: str) -> None:
    """Results view for the Resume Only workflow."""
    ats_data = result["ats_score"]
    parsed = result.get("parsed_resume", {})
    quality = result.get("quality_score", 0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📈 ATS Score")
        st.plotly_chart(
            create_ats_score_gauge(ats_data["overall_score"]),
            use_container_width=True, key="ro_ats_gauge", config=STATIC_CHART_CONFIG,
        )
        st.markdown(f"**Grade:** {ats_data.get('grade', 'N/A')}")
    with col2:
        st.markdown("#### 🏅 Resume Quality Score")
        st.plotly_chart(
            create_quality_score_gauge(quality),
            use_container_width=True, key="ro_quality_gauge", config=STATIC_CHART_CONFIG,
        )

    # Extracted resume information
    st.markdown("---")
    st.markdown("#### 🧠 Skills Found")
    skills = result.get("skills") or parsed.get("skills", [])
    if skills:
        st.write(", ".join(skills))
    else:
        st.info("No skills detected.")

    st.markdown("#### 📚 Resume Details")
    c1, c2 = st.columns(2)
    with c1:
        _section_block("🎓 Education", parsed.get("education"))
        _section_block("💼 Experience", parsed.get("experience"))
    with c2:
        _section_block("📜 Certifications", parsed.get("certifications"))
        _section_block("🛠️ Projects", parsed.get("projects"))

    _render_strengths_weaknesses(result)
    _render_recommendations(result)

    _render_ats_report_download(result, report_service, resume_name)


def _display_resume_job_results(result: dict, report_service, resume_name: str, job_title: str) -> None:
    """Results view for the Resume + Job Description workflow."""
    ats_data = result["ats_score"]
    match_data = result.get("job_match", {})
    parsed = result.get("parsed_resume", {})
    compatibility = result.get("candidate_compatibility", result.get("rank_score", 0))

    # Headline scores
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📈 ATS Score")
        st.plotly_chart(
            create_ats_score_gauge(ats_data["overall_score"]),
            use_container_width=True, key="rj_ats_gauge", config=STATIC_CHART_CONFIG,
        )
        st.markdown(f"**Grade:** {ats_data.get('grade', 'N/A')}")
    with col2:
        st.markdown("#### 🎯 Job Match")
        st.plotly_chart(
            create_score_comparison_chart(ats_data["overall_score"], match_data.get("overall_match", 0)),
            use_container_width=True, key="rj_score_compare", config=STATIC_CHART_CONFIG,
        )
        if match_data.get("recommendation"):
            st.markdown(f"**Recommendation:** {match_data['recommendation']}")

    # Candidate compatibility
    st.markdown("---")
    comp_color = "score-high" if compatibility >= 70 else "score-medium" if compatibility >= 50 else "score-low"
    st.markdown(
        f"#### 🤝 Candidate Compatibility: "
        f"<span class='{comp_color}'>{round(compatibility)}/100</span>",
        unsafe_allow_html=True,
    )

    # Match breakdown + ATS components
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 Match Breakdown")
        st.plotly_chart(
            create_job_match_chart(match_data),
            use_container_width=True, key="rj_match_radar", config=STATIC_CHART_CONFIG,
        )
    with col2:
        st.markdown("#### 📋 ATS Score Components")
        components = ats_data.get("component_scores", {})
        if components:
            for key, value in components.items():
                label = key.replace("_", " ").title()
                st.progress(min(1.0, int(value) / 100), text=f"{label}: {round(value)}%")
        else:
            st.caption("Component breakdown not available for cached results.")

    # Skills found
    st.markdown("---")
    st.markdown("#### 🧠 Skills Found")
    skills = result.get("skills") or parsed.get("skills", [])
    if skills:
        st.write(", ".join(skills))
    else:
        st.info("No skills detected.")

    # Skill gap analysis
    skill_gap = match_data.get("skill_gap", {})
    if skill_gap:
        st.markdown("#### 🛠️ Skill Gap Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ Matched Skills**")
            for s in skill_gap.get("matched", []):
                st.markdown(f"- {s}")
        with col2:
            st.markdown("**❌ Missing Skills**")
            missing = skill_gap.get("missing", [])
            if missing:
                for s in missing:
                    st.markdown(f"- {s}")
            else:
                st.caption("None — great coverage!")
        with col3:
            st.markdown("**➕ Additional Skills**")
            for s in skill_gap.get("extra", [])[:10]:
                st.markdown(f"- {s}")

    _render_strengths_weaknesses(result)
    _render_recommendations(result)
    _render_ats_report_download(result, report_service, resume_name, skill_gap, job_title)


# ---------------------------------------------------------------------------
# Small reusable result components
# ---------------------------------------------------------------------------
def _section_block(title: str, content) -> None:
    """Render an extracted resume section, or a placeholder if empty."""
    st.markdown(f"**{title}**")
    if content:
        preview = content if len(content) <= 600 else content[:600] + "..."
        st.caption(preview)
    else:
        st.caption("Not detected.")


def _render_strengths_weaknesses(result: dict) -> None:
    """Render strengths and weaknesses side by side."""
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ Strengths")
        for s in result.get("strengths", []):
            st.markdown(f"- 🟢 {s}")
    with col2:
        st.markdown("#### ⚠️ Areas for Improvement")
        for w in result.get("weaknesses", []):
            st.markdown(f"- 🔴 {w}")


def _render_recommendations(result: dict) -> None:
    """Render AI improvement recommendations."""
    recommendations = result.get("recommendations", [])
    if not recommendations:
        return
    st.markdown("#### 🤖 AI Recommendations")
    for rec in recommendations:
        st.markdown(f"- 💡 {rec}")


def _render_ats_report_download(result: dict, report_service, resume_name: str,
                                skill_gap: dict = None, job_title: str = "") -> None:
    """Render report download buttons."""
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
                    st.write(f"🏷️ {item.get('analysis_type', 'Resume + Job Description')}")
                with col3:
                    ats = item["ats_score"]
                    color = "🟢" if ats >= 70 else "🟡" if ats >= 50 else "🔴"
                    st.write(f"{color} ATS: {ats}/100")
                with col4:
                    if item.get("analysis_type") == ANALYSIS_TYPE_RESUME_ONLY:
                        st.write("Match: N/A")
                    else:
                        match = item["job_match_percentage"] or 0
                        color = "🟢" if match >= 70 else "🟡" if match >= 50 else "🔴"
                        st.write(f"{color} Match: {match}%")
                st.markdown("---")
    else:
        st.info("No analyses yet. Run your first analysis in the 'New Analysis' tab!")
