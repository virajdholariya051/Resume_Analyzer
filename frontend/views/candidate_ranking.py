"""
Candidate Ranking page - rank, filter, shortlist, and export candidates.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.recruiter_service import RecruiterService
from backend.services.job_service import JobService
from backend.services.resume_service import ResumeService, CANDIDATE_STATUSES
from backend.services.export_service import ExportService
from frontend.components.charts import create_candidate_ranking_chart, STATIC_CHART_CONFIG


def _select_job(job_service):
    """Shared job selector; stores choice in session_state['recruiter_active_job']."""
    jobs = job_service.get_all_jobs()
    if not jobs:
        st.warning("📋 No job descriptions found. Create one under **Job Descriptions**.")
        return None, None

    options = {f"{j['job_title']}" + (f" @ {j['company_name']}" if j['company_name'] else ""): j["job_id"] for j in jobs}
    labels = list(options.keys())

    active = st.session_state.get("recruiter_active_job")
    index = 0
    if active in options.values():
        index = list(options.values()).index(active)

    selected_label = st.selectbox("🎯 Select Job Description", labels, index=index)
    job_id = options[selected_label]
    st.session_state["recruiter_active_job"] = job_id
    return job_id, selected_label


def render_candidate_ranking_page() -> None:
    """Render the candidate ranking page."""
    st.markdown('<h1 class="main-header">🏆 Candidate Ranking</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    recruiter_service = RecruiterService()
    job_service = JobService()
    resume_service = ResumeService()
    export_service = ExportService()

    job_id, job_label = _select_job(job_service)
    if job_id is None:
        return

    candidates = resume_service.get_candidates(user["user_id"])
    if not candidates:
        st.info("📭 No candidates in your pool. Upload resumes under **Upload Resumes**.")
        return

    if st.button("🚀 Rank Candidates", use_container_width=True, type="primary"):
        progress = st.progress(0, text="Analyzing candidates...")

        def _cb(current, total):
            progress.progress(current / total, text=f"Analyzing {current}/{total}...")

        with st.spinner("Ranking candidates against the selected job..."):
            ranked = recruiter_service.rank_candidates(
                user["user_id"], job_id, auto_analyze=True, progress_callback=_cb
            )
        progress.empty()
        st.session_state["ranked_candidates"] = ranked
        st.session_state["ranked_job_id"] = job_id

    # Use cached ranking if available and matches the selected job
    ranked = st.session_state.get("ranked_candidates", [])
    if st.session_state.get("ranked_job_id") != job_id:
        ranked = []

    if not ranked:
        st.info("Click **Rank Candidates** to evaluate your pool against this job.")
        return

    # --- Filters ---
    st.markdown("---")
    st.markdown("### 🔎 Filters")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        min_ats = st.slider("Min ATS Score", 0, 100, 0, 5)
    with fc2:
        min_match = st.slider("Min Match %", 0, 100, 0, 5)
    with fc3:
        status_filter = st.selectbox("Status", ["All"] + CANDIDATE_STATUSES)

    fc4, fc5 = st.columns(2)
    with fc4:
        name_filter = st.text_input("Candidate Name contains", "")
    with fc5:
        skill_filter = st.text_input("Has Skill (e.g., Python)", "")

    filters = {
        "min_ats": min_ats,
        "min_match": min_match,
        "status": status_filter,
        "name": name_filter.strip() or None,
        "skill": skill_filter.strip() or None,
    }
    filtered = recruiter_service.filter_candidates(ranked, filters)

    st.markdown("---")
    st.markdown(f"### 📊 Ranked Candidates ({len(filtered)} shown)")

    # Ranking chart
    st.plotly_chart(create_candidate_ranking_chart(filtered, top_n=10), use_container_width=True, config=STATIC_CHART_CONFIG)

    # Candidate list with status controls
    for c in filtered:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 3])
            col1.markdown(f"### #{c['rank']}")
            col2.markdown(f"**{c['candidate_name']}**  \n`{c['file_name']}`")
            col3.markdown(f"ATS: **{c['ats_score']}**  \nMatch: **{c['job_match_percentage']}%**")
            col4.markdown(f"Score: **{c['rank_score']:.1f}**  \nStatus: **{c['status']}**")
            with col5:
                new_status = st.selectbox(
                    "Set status",
                    CANDIDATE_STATUSES,
                    index=CANDIDATE_STATUSES.index(c["status"]) if c["status"] in CANDIDATE_STATUSES else 0,
                    key=f"status_{c['resume_id']}",
                    label_visibility="collapsed",
                )
                if new_status != c["status"]:
                    if st.button("Update", key=f"upd_{c['resume_id']}"):
                        res = resume_service.update_status(c["resume_id"], new_status)
                        if res["success"]:
                            # update cached ranking entry
                            c["status"] = new_status
                            st.success(res["message"])
                            st.rerun()
                        else:
                            st.error(res["message"])
        st.markdown("---")

    # --- Export ---
    st.markdown("### 📥 Export Report")
    e1, e2, e3 = st.columns(3)
    with e1:
        st.download_button(
            "⬇️ CSV", data=export_service.to_csv(filtered),
            file_name="candidate_ranking.csv", mime="text/csv", use_container_width=True,
        )
    with e2:
        st.download_button(
            "⬇️ Excel", data=export_service.to_excel(filtered),
            file_name="candidate_ranking.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with e3:
        st.download_button(
            "⬇️ PDF", data=export_service.to_pdf(filtered, f"Ranking — {job_label}"),
            file_name="candidate_ranking.pdf", mime="application/pdf", use_container_width=True,
        )
