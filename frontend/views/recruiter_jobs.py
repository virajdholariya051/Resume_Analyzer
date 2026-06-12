"""
Job Description Management page for recruiters (create / edit / delete / reuse).
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.job_service import JobService


def render_recruiter_jobs_page() -> None:
    """Render the recruiter job description management page."""
    st.markdown('<h1 class="main-header">📋 Job Descriptions</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    job_service = JobService()

    tab1, tab2 = st.tabs(["➕ Create / Edit", "📂 Saved Jobs"])

    with tab1:
        _render_create_edit(job_service, user)
    with tab2:
        _render_saved(job_service)


def _render_create_edit(job_service, user) -> None:
    """Create a new job or edit an existing one."""
    editing = st.session_state.get("editing_job_id")
    existing = job_service.get_job_by_id(editing) if editing else None

    if existing:
        st.info(f"✏️ Editing: {existing['job_title']}")

    with st.form("job_form"):
        title = st.text_input("Job Title *", value=existing["job_title"] if existing else "")
        company = st.text_input("Company Name", value=existing["company_name"] if existing else "")
        col1, col2 = st.columns(2)
        with col1:
            experience = st.text_input(
                "Experience Required",
                value=existing["experience_required"] if existing else "",
                placeholder="e.g., 3+ years",
            )
        with col2:
            education = st.text_input(
                "Education Requirement",
                value=existing["education_requirement"] if existing else "",
                placeholder="e.g., Bachelor's in CS",
            )
        description = st.text_area(
            "Job Description *",
            value=existing["job_description_text"] if existing else "",
            height=200,
        )
        skills = st.text_input(
            "Required Skills (comma-separated)",
            value=existing["required_skills"] if existing else "",
            placeholder="Leave empty to auto-extract from description",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            submit = st.form_submit_button(
                "💾 Update Job" if existing else "💾 Save Job",
                use_container_width=True,
                type="primary",
            )
        with col_b:
            cancel = st.form_submit_button("Cancel / New", use_container_width=True)

        if submit:
            if not title or not description:
                st.error("Job title and description are required.")
            else:
                if existing:
                    result = job_service.update_job(
                        existing["job_id"], title, description, skills,
                        company, experience, education,
                    )
                else:
                    result = job_service.create_job(
                        title, description, skills, company, experience, education,
                        created_by=user["user_id"],
                    )
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.pop("editing_job_id", None)
                    st.rerun()
                else:
                    st.error(result["message"])

        if cancel:
            st.session_state.pop("editing_job_id", None)
            st.rerun()


def _render_saved(job_service) -> None:
    """List saved jobs with edit/delete actions."""
    jobs = job_service.get_all_jobs()
    if not jobs:
        st.info("No job descriptions saved yet.")
        return

    for job in jobs:
        header = job["job_title"]
        if job["company_name"]:
            header += f" @ {job['company_name']}"
        with st.expander(f"🏢 {header}"):
            if job["experience_required"]:
                st.write(f"**Experience:** {job['experience_required']}")
            if job["education_requirement"]:
                st.write(f"**Education:** {job['education_requirement']}")
            st.write(f"**Required Skills:** {job['required_skills']}")
            st.write(f"**Description:** {job['job_description_text'][:400]}...")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit", key=f"edit_{job['job_id']}", use_container_width=True):
                    st.session_state["editing_job_id"] = job["job_id"]
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"del_{job['job_id']}", use_container_width=True):
                    result = job_service.delete_job(job["job_id"])
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
