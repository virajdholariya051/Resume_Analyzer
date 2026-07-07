"""
Admin System Settings - resume rules, AI, security, and backup.
"""

import streamlit as st
from backend.auth.auth_service import is_admin, get_current_user
from backend.services.settings_service import SettingsService
from backend.services.audit_service import AuditService
from frontend.components.admin_ui import breadcrumb


def render_admin_system_settings() -> None:
    """Render the system settings section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "System Settings")
    st.markdown('<h1 class="main-header">⚙️ System Settings</h1>', unsafe_allow_html=True)

    settings = SettingsService()
    audit = AuditService()
    admin = get_current_user()
    s = settings.get_all()

    tabs = st.tabs([
        "Resume Rules", "AI Settings", "Security", "Backup",
    ])

    with tabs[0]:
        with st.form("resume_rules"):
            max_size = st.number_input("Max File Size (MB)", 1, 100,
                                       int(s.get("max_file_size_mb", 10) or 10))
            formats = st.text_input("Allowed Formats (comma-separated)",
                                    s.get("allowed_formats", "pdf,docx") or "pdf,docx")
            if st.form_submit_button("💾 Save Resume Rules"):
                settings.set_many({"max_file_size_mb": max_size, "allowed_formats": formats})
                audit.log(admin["user_id"], "Updated Resume Rules settings")
                st.success("Resume rules saved.")

    with tabs[1]:
        with st.form("ai_settings"):
            ats_th = st.slider("ATS Threshold", 0, 100, int(s.get("ats_threshold", 70) or 70))
            match_th = st.slider("Match Threshold", 0, 100, int(s.get("match_threshold", 75) or 75))
            model = st.selectbox("NLP Model", ["en_core_web_sm", "en_core_web_md", "blank"],
                                 index=0)
            if st.form_submit_button("💾 Save AI Settings"):
                settings.set_many({"ats_threshold": ats_th, "match_threshold": match_th, "nlp_model": model})
                audit.log(admin["user_id"], "Updated AI settings")
                st.success("AI settings saved.")

    with tabs[2]:
        with st.form("security_settings"):
            min_len = st.number_input("Password Minimum Length", 6, 32,
                                      int(s.get("password_min_length", 8) or 8))
            timeout = st.number_input("Session Timeout (minutes)", 5, 480,
                                      int(s.get("session_timeout_min", 30) or 30))
            attempts = st.number_input("Login Attempt Limit", 3, 20,
                                       int(s.get("login_attempt_limit", 5) or 5))
            if st.form_submit_button("💾 Save Security Settings"):
                settings.set_many({
                    "password_min_length": min_len,
                    "session_timeout_min": timeout,
                    "login_attempt_limit": attempts,
                })
                audit.log(admin["user_id"], "Updated Security settings")
                st.success("Security settings saved.")

    with tabs[3]:
        with st.form("backup_settings"):
            freq = st.selectbox("Backup Frequency", ["Hourly", "Daily", "Weekly"],
                                index=["Hourly", "Daily", "Weekly"].index(s.get("backup_frequency", "Daily") or "Daily"))
            if st.form_submit_button("💾 Save Backup Settings"):
                settings.set("backup_frequency", freq)
                audit.log(admin["user_id"], "Updated Backup settings")
                st.success("Backup settings saved.")
        st.caption("The SQLite database file can be backed up by copying it from the data directory.")
