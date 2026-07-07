"""
Admin Resume Management - view, search, download, and delete resumes,
plus view analysis results.
"""

import os
import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.resume_service import ResumeService
from backend.services.analysis_service import AnalysisService
from backend.services.user_service import UserService
from backend.config.settings import UPLOAD_DIR
from frontend.components.admin_ui import breadcrumb, paginated_table


def render_admin_resumes() -> None:
    """Render the resume management section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Resume Management")
    st.markdown('<h1 class="main-header">📄 Resume Management</h1>', unsafe_allow_html=True)

    resume_service = ResumeService()
    analysis_service = AnalysisService()
    user_service = UserService()

    resumes = resume_service.get_all_resumes()
    users = {u["user_id"]: u for u in user_service.get_all_users()}

    tabs = st.tabs([
        "Uploaded Resumes", "Analysis Results", "Resume Search", "Downloads", "Delete Resume",
    ])

    with tabs[0]:
        _render_uploaded(resumes, users)
    with tabs[1]:
        _render_analysis_results(analysis_service, resumes)
    with tabs[2]:
        _render_search(analysis_service, resumes, users)
    with tabs[3]:
        _render_downloads(resume_service, resumes)
    with tabs[4]:
        _render_delete(resume_service, resumes)


def _render_uploaded(resumes, users) -> None:
    st.markdown("### 📄 Uploaded Resumes")
    if not resumes:
        st.info("No resumes uploaded yet.")
        return
    df = pd.DataFrame([
        {
            "ID": r["resume_id"], "Candidate": r["candidate_name"],
            "File": r["file_name"],
            "Uploaded By": users.get(r["user_id"], {}).get("name", f"#{r['user_id']}"),
            "Status": r["status"], "Date": r["upload_date"],
        }
        for r in resumes
    ])
    paginated_table(df, "uploaded_resumes", search_columns=["Candidate", "File", "Uploaded By"])


def _render_analysis_results(analysis_service, resumes) -> None:
    st.markdown("### 🔍 Resume Analysis Results")
    analyses = analysis_service.get_all_analyses()
    if not analyses:
        st.info("No analyses found.")
        return
    names = {r["resume_id"]: r["candidate_name"] for r in resumes}
    df = pd.DataFrame([
        {
            "Analysis ID": a["analysis_id"],
            "Candidate": names.get(a["resume_id"], f"#{a['resume_id']}"),
            "ATS Score": a["ats_score"], "Match %": a["job_match_percentage"],
            "Date": a["created_at"],
        }
        for a in analyses
    ])
    paginated_table(df, "analysis_results", search_columns=["Candidate"])


def _render_search(analysis_service, resumes, users) -> None:
    st.markdown("### 🔎 Resume Search & Filters")

    # Build a combined dataset: latest analysis per resume
    analyses = analysis_service.get_all_analyses()
    latest = {}
    for a in analyses:  # get_all_analyses is ordered newest first
        latest.setdefault(a["resume_id"], a)

    col1, col2, col3 = st.columns(3)
    with col1:
        min_ats = st.slider("Min ATS Score", 0, 100, 0, 5, key="rs_ats")
    with col2:
        min_match = st.slider("Min Match %", 0, 100, 0, 5, key="rs_match")
    with col3:
        skill_term = st.text_input("Has skill", key="rs_skill")

    rows = []
    rsvc = ResumeService()
    for r in resumes:
        a = latest.get(r["resume_id"])
        ats = a["ats_score"] if a else 0
        match = a["job_match_percentage"] if a else 0
        if ats < min_ats or match < min_match:
            continue
        if skill_term:
            detail = rsvc.get_resume_by_id(r["resume_id"])
            text = (detail or {}).get("resume_text", "").lower()
            if skill_term.lower() not in text:
                continue
        rows.append({
            "ID": r["resume_id"], "Candidate": r["candidate_name"], "File": r["file_name"],
            "Uploaded By": users.get(r["user_id"], {}).get("name", f"#{r['user_id']}"),
            "ATS": ats, "Match %": match, "Date": r["upload_date"],
        })

    if rows:
        paginated_table(pd.DataFrame(rows), "resume_search", search_columns=["Candidate", "File"])
    else:
        st.info("No resumes match the selected filters.")


def _render_downloads(resume_service, resumes) -> None:
    st.markdown("### ⬇️ Resume Downloads")
    if not resumes:
        st.info("No resumes available.")
        return
    options = {f"{r['candidate_name']} — {r['file_name']}": r["resume_id"] for r in resumes}
    selected = st.selectbox("Select resume", list(options.keys()), key="dl_select")
    rid = options[selected]
    detail = resume_service.get_resume_by_id(rid)
    if not detail:
        st.error("Resume not found.")
        return

    file_path = os.path.join(UPLOAD_DIR, detail["file_name"])
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.download_button("⬇️ Download Original File", data=f.read(),
                               file_name=detail["file_name"], key="dl_orig")
    else:
        st.warning("Original file not found on disk (ephemeral storage). Offering extracted text instead.")
        st.download_button("⬇️ Download Extracted Text",
                           data=detail["resume_text"].encode("utf-8"),
                           file_name=f"{detail['file_name']}.txt", key="dl_txt")

    with st.expander("📄 Resume Text Preview"):
        st.text(detail["resume_text"][:3000])


def _render_delete(resume_service, resumes) -> None:
    st.markdown("### 🗑️ Delete Resume")
    if not resumes:
        st.info("No resumes available.")
        return
    options = {f"{r['candidate_name']} — {r['file_name']} (ID {r['resume_id']})": r["resume_id"] for r in resumes}
    selected = st.selectbox("Select resume to delete", list(options.keys()), key="del_select")
    rid = options[selected]
    if st.checkbox("I confirm permanent deletion of this resume.") and st.button("Delete Resume"):
        res = resume_service.delete_resume(rid)
        if res["success"]:
            st.success(res["message"])
            st.rerun()
        else:
            st.error(res["message"])
