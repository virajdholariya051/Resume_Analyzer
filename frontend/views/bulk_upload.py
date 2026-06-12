"""
Bulk Resume Upload page for recruiters.
"""

import streamlit as st
from backend.auth.auth_service import get_current_user
from backend.services.resume_service import ResumeService


def render_bulk_upload_page() -> None:
    """Render the bulk resume upload page."""
    st.markdown('<h1 class="main-header">📤 Upload Resumes</h1>', unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        st.error("Please login first.")
        return

    resume_service = ResumeService()

    st.markdown("Upload one or many resumes at once. Supported formats: **PDF**, **DOCX** (max 10 MB each).")
    st.caption("Drag and drop multiple files below. Duplicate resumes are detected automatically.")

    uploaded_files = st.file_uploader(
        "Drag & drop resumes here",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Select 1, 10, 50, or 100+ resumes.",
    )

    if uploaded_files:
        st.info(f"📦 {len(uploaded_files)} file(s) ready to upload.")

        if st.button("⬆️ Upload & Process All", use_container_width=True, type="primary"):
            progress_bar = st.progress(0, text="Starting upload...")
            status_area = st.empty()

            def _progress(current, total, filename):
                progress_bar.progress(current / total, text=f"Processing {current}/{total}: {filename}")

            with st.spinner("Processing resumes..."):
                summary = resume_service.bulk_upload_resumes(
                    uploaded_files, user["user_id"], progress_callback=_progress
                )

            progress_bar.progress(1.0, text="Done!")
            status_area.empty()

            # Summary
            st.markdown("---")
            st.markdown("### 📋 Upload Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", summary["total"])
            c2.metric("✅ Succeeded", summary["succeeded"])
            c3.metric("♻️ Duplicates", summary["duplicates"])
            c4.metric("❌ Failed", summary["failed"])

            with st.expander("📄 Per-file details", expanded=True):
                for detail in summary["details"]:
                    icon = {"success": "✅", "duplicate": "♻️", "failed": "❌"}.get(detail["status"], "•")
                    st.write(f"{icon} **{detail['file']}** — {detail['message']}")

            if summary["succeeded"] > 0:
                st.success(
                    f"{summary['succeeded']} resume(s) processed and added to your candidate pool. "
                    "Go to **Candidate Ranking** to evaluate them against a job description."
                )

    st.markdown("---")
    st.markdown("### 📂 Current Candidate Pool")
    candidates = resume_service.get_candidates(user["user_id"])
    if candidates:
        st.write(f"You have **{len(candidates)}** candidate(s) in your pool.")
        for c in candidates[:20]:
            col1, col2, col3 = st.columns([3, 3, 2])
            col1.write(f"👤 {c['candidate_name']}")
            col2.write(f"📄 {c['file_name']}")
            col3.write(f"🏷️ {c['status']}")
        if len(candidates) > 20:
            st.caption(f"...and {len(candidates) - 20} more. View all under Candidate Ranking.")
    else:
        st.info("No resumes uploaded yet.")
