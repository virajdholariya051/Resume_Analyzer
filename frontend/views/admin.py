"""
Admin panel for managing users, resumes, analyses, and skills.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.user_service import UserService
from backend.services.resume_service import ResumeService
from backend.services.analysis_service import AnalysisService
from backend.services.job_service import JobService
from database.database import get_db
from database.schema import Skill


def render_admin_page() -> None:
    """Render the admin panel page."""
    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        return

    st.markdown('<h1 class="main-header">⚙️ Admin Panel</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Users", "📄 Resumes", "📊 Analyses", "🏢 Jobs", "🛠️ Skills"
    ])

    with tab1:
        _render_users_tab()
    with tab2:
        _render_resumes_tab()
    with tab3:
        _render_analyses_tab()
    with tab4:
        _render_jobs_tab()
    with tab5:
        _render_skills_tab()


def _render_users_tab() -> None:
    """Render users management tab."""
    st.markdown("### 👥 User Management")

    user_service = UserService()
    users = user_service.get_all_users()

    if users:
        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Delete User")
        user_options = {f"{u['name']} ({u['email']})": u["user_id"] for u in users if u["role"] != "Admin"}
        if user_options:
            selected = st.selectbox("Select user to delete", options=list(user_options.keys()))
            if st.button("🗑️ Delete User", type="secondary"):
                result = user_service.delete_user(user_options[selected])
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
        else:
            st.info("No non-admin users to delete.")
    else:
        st.info("No users found.")


def _render_resumes_tab() -> None:
    """Render resumes management tab."""
    st.markdown("### 📄 All Resumes")

    resume_service = ResumeService()
    resumes = resume_service.get_all_resumes()

    if resumes:
        df = pd.DataFrame(resumes)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.info(f"Total resumes: {len(resumes)}")
    else:
        st.info("No resumes uploaded yet.")


def _render_analyses_tab() -> None:
    """Render analyses overview tab."""
    st.markdown("### 📊 All Analysis Results")

    analysis_service = AnalysisService()
    analyses = analysis_service.get_all_analyses()

    if analyses:
        df = pd.DataFrame(analyses)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_ats = round(sum(a["ats_score"] for a in analyses) / len(analyses), 1)
            st.metric("Avg ATS Score", f"{avg_ats}%")
        with col2:
            avg_match = round(sum(a["job_match_percentage"] for a in analyses) / len(analyses), 1)
            st.metric("Avg Match %", f"{avg_match}%")
        with col3:
            st.metric("Total Analyses", len(analyses))
    else:
        st.info("No analyses performed yet.")


def _render_jobs_tab() -> None:
    """Render job descriptions tab."""
    st.markdown("### 🏢 Job Descriptions")

    job_service = JobService()
    jobs = job_service.get_all_jobs()

    if jobs:
        for job in jobs:
            with st.expander(f"🏢 {job['job_title']} (ID: {job['job_id']})"):
                st.write(f"**Description:** {job['job_description_text'][:500]}")
                st.write(f"**Required Skills:** {job['required_skills']}")
                if st.button("🗑️ Delete", key=f"admin_del_job_{job['job_id']}"):
                    result = job_service.delete_job(job["job_id"])
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    else:
        st.info("No job descriptions found.")


def _render_skills_tab() -> None:
    """Render skills database management tab."""
    st.markdown("### 🛠️ Skills Database")

    db = get_db()
    try:
        skills = db.query(Skill).order_by(Skill.skill_type, Skill.skill_name).all()

        if skills:
            skills_data = [
                {"ID": s.skill_id, "Skill": s.skill_name, "Type": s.skill_type}
                for s in skills
            ]
            df = pd.DataFrame(skills_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            col1, col2 = st.columns(2)
            with col1:
                technical_count = sum(1 for s in skills if s.skill_type == "Technical")
                st.metric("Technical Skills", technical_count)
            with col2:
                soft_count = sum(1 for s in skills if s.skill_type == "Soft")
                st.metric("Soft Skills", soft_count)

        # Add new skill
        st.markdown("---")
        st.markdown("#### ➕ Add New Skill")
        with st.form("add_skill_form"):
            col1, col2 = st.columns(2)
            with col1:
                skill_name = st.text_input("Skill Name")
            with col2:
                skill_type = st.selectbox("Skill Type", ["Technical", "Soft"])
            submit = st.form_submit_button("Add Skill", use_container_width=True)

            if submit:
                if skill_name:
                    existing = db.query(Skill).filter(Skill.skill_name == skill_name).first()
                    if existing:
                        st.error("Skill already exists.")
                    else:
                        new_skill = Skill(skill_name=skill_name, skill_type=skill_type)
                        db.add(new_skill)
                        db.commit()
                        st.success(f"Skill '{skill_name}' added successfully!")
                        st.rerun()
                else:
                    st.error("Skill name is required.")
    finally:
        db.close()
