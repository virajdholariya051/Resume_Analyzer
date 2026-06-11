"""
Resume upload page for uploading and processing resume files.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.resume_service import ResumeService


def render_upload_page() -> None:
    """Render the resume upload page."""
    st.markdown('<h1 class="main-header">📄 Upload Resume</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    resume_service = ResumeService()

    # Upload section
    st.markdown("### Upload your resume for analysis")
    st.markdown("Supported formats: **PDF**, **DOCX** | Maximum size: **10 MB**")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx"],
        help="Upload your resume in PDF or DOCX format",
    )

    if uploaded_file is not None:
        # Show file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"📁 **File:** {uploaded_file.name}")
        with col2:
            size_mb = uploaded_file.size / (1024 * 1024)
            st.write(f"📦 **Size:** {size_mb:.2f} MB")
        with col3:
            ext = uploaded_file.name.split(".")[-1].upper()
            st.write(f"📋 **Type:** {ext}")

        if st.button("⬆️ Upload & Process", use_container_width=True, type="primary"):
            with st.spinner("Processing resume..."):
                result = resume_service.upload_resume(uploaded_file, user["user_id"])

                if result["success"]:
                    st.success(result["message"])
                    st.info(f"📝 Extracted {result['text_length']} characters | 🛠️ Found {result['skills_found']} skills")
                else:
                    st.error(result["message"])

    st.markdown("---")

    # Display existing resumes
    st.markdown("### 📂 Your Uploaded Resumes")

    resumes = resume_service.get_user_resumes(user["user_id"])

    if resumes:
        for resume in resumes:
            with st.expander(f"📄 {resume['file_name']} — Uploaded: {resume['upload_date']}"):
                st.write(f"**Resume ID:** {resume['resume_id']}")
                st.write(f"**Preview:**")
                st.text(resume["text_preview"])

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔍 Analyze", key=f"analyze_{resume['resume_id']}", use_container_width=True):
                        st.session_state["selected_resume_id"] = resume["resume_id"]
                        st.session_state["page"] = "analysis"
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{resume['resume_id']}", use_container_width=True):
                        delete_result = resume_service.delete_resume(resume["resume_id"])
                        if delete_result["success"]:
                            st.success(delete_result["message"])
                            st.rerun()
                        else:
                            st.error(delete_result["message"])
    else:
        st.info("No resumes uploaded yet. Upload your first resume above!")
