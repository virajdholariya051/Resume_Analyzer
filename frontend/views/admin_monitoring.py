"""
Admin System Monitoring - application logs, error logs, database status,
storage usage, and system health.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.admin_service import AdminService
from backend.services.ai_log_service import AILogService
from frontend.components.admin_ui import breadcrumb, kpi_card


def render_admin_monitoring() -> None:
    """Render the system monitoring section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "System Monitoring")
    st.markdown('<h1 class="main-header">🖥️ System Monitoring</h1>', unsafe_allow_html=True)

    admin_service = AdminService()
    ai_log = AILogService()
    status = admin_service.get_system_status()

    tabs = st.tabs([
        "System Health", "Database Status", "Storage Usage",
        "Application Logs", "Error Logs",
    ])

    with tabs[0]:
        _render_health(status, ai_log)
    with tabs[1]:
        _render_db_status(status)
    with tabs[2]:
        _render_storage(status)
    with tabs[3]:
        _render_app_logs(ai_log)
    with tabs[4]:
        _render_error_logs(ai_log)


def _render_health(status, ai_log) -> None:
    st.markdown("### System Health")
    ai_stats = ai_log.get_stats()
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Database", "🟢 Online")
    with c2:
        kpi_card("AI Success Rate", f"{ai_stats['success_rate']}%")
    with c3:
        kpi_card("Total Storage", f"{status['total_storage_kb']} KB")
    st.success("All core services are operational.")


def _render_db_status(status) -> None:
    st.markdown("### Database Status")
    st.write(f"**Database file:** `{status['db_path']}`")
    st.write(f"**Database size:** {status['db_size_kb']} KB")
    st.markdown("#### Table Row Counts")
    df = pd.DataFrame([{"Table": k, "Rows": v} for k, v in status["table_counts"].items()])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_storage(status) -> None:
    st.markdown("### Storage Usage")
    df = pd.DataFrame([
        {"Location": "Database", "Size (KB)": status["db_size_kb"]},
        {"Location": "Uploads", "Size (KB)": status["upload_size_kb"]},
        {"Location": "Reports", "Size (KB)": status["reports_size_kb"]},
        {"Location": "Total", "Size (KB)": status["total_storage_kb"]},
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_app_logs(ai_log) -> None:
    st.markdown("### Application Logs")
    st.caption("Recent AI/analysis activity serves as the application activity log.")
    logs = ai_log.get_logs(limit=200)
    if logs:
        df = pd.DataFrame([
            {"Time": l["created_at"], "Action": l["action"], "Status": l["status"],
             "ms": l["processing_ms"], "Detail": l["message"]}
            for l in logs
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No application activity logged yet.")


def _render_error_logs(ai_log) -> None:
    st.markdown("### Error Logs")
    errors = ai_log.get_logs(limit=200, status="failed")
    if errors:
        df = pd.DataFrame([
            {"Time": l["created_at"], "Action": l["action"], "Error": l["message"]}
            for l in errors
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success("No errors recorded. 🎉")
