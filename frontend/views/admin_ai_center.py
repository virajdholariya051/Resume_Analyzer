"""
Admin AI Analysis Center - monitoring of AI/NLP requests, logs, failures,
model performance, token usage, and NLP statistics.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.ai_log_service import AILogService
from backend.services.settings_service import SettingsService
from frontend.components.admin_ui import breadcrumb, kpi_card, paginated_table
from frontend.components.charts import create_horizontal_bar_chart


def render_admin_ai_center() -> None:
    """Render the AI analysis center."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "AI Analysis Center")
    st.markdown('<h1 class="main-header">🤖 AI Analysis Center</h1>', unsafe_allow_html=True)

    ai_log = AILogService()
    stats = ai_log.get_stats()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total AI Requests", stats["total_requests"])
    with c2:
        kpi_card("Successful", stats["successful"])
    with c3:
        kpi_card("Failed", stats["failed"])
    with c4:
        kpi_card("Avg Processing", f"{stats['avg_processing_ms']} ms")

    st.markdown("---")
    tabs = st.tabs([
        "Analysis History", "AI Logs", "Failed Analyses",
        "Model Performance", "Token Usage", "NLP Statistics",
    ])

    with tabs[0]:
        _render_logs(ai_log, status=None, key="ai_history", title="Recent AI Analysis History")
    with tabs[1]:
        _render_logs(ai_log, status=None, key="ai_logs", title="AI Request Logs")
    with tabs[2]:
        _render_logs(ai_log, status="failed", key="ai_failed", title="Failed Analyses")
    with tabs[3]:
        _render_model_performance(stats)
    with tabs[4]:
        _render_token_usage()
    with tabs[5]:
        _render_nlp_stats(stats)


def _render_logs(ai_log, status, key, title) -> None:
    st.markdown(f"### {title}")
    logs = ai_log.get_logs(limit=300, status=status)
    if not logs:
        st.info("No log entries.")
        return
    df = pd.DataFrame([
        {"Time": l["created_at"], "User": l["user_id"] or "-", "Resume": l["resume_id"] or "-",
         "Action": l["action"], "Status": l["status"], "ms": l["processing_ms"], "Detail": l["message"]}
        for l in logs
    ])
    paginated_table(df, key, search_columns=["Action", "Status", "Detail"])


def _render_model_performance(stats) -> None:
    st.markdown("### Model Performance")
    c1, c2 = st.columns(2)
    with c1:
        kpi_card("Success Rate", f"{stats['success_rate']}%")
    with c2:
        kpi_card("Avg Latency", f"{stats['avg_processing_ms']} ms")
    if stats["most_used"]:
        st.plotly_chart(create_horizontal_bar_chart(stats["most_used"], "Most Used AI Features"),
                        use_container_width=True)


def _render_token_usage() -> None:
    st.markdown("### Token Usage")
    st.info(
        "This deployment uses **local NLP** (spaCy + rule-based scoring), which does "
        "not consume API tokens. Token metering applies only when an external LLM "
        "provider is configured."
    )
    settings = SettingsService()
    st.write(f"**Configured NLP model:** `{settings.get('nlp_model', 'en_core_web_sm')}`")


def _render_nlp_stats(stats) -> None:
    st.markdown("### NLP Statistics")
    st.write(f"- **Total NLP runs:** {stats['total_requests']}")
    st.write(f"- **Successful extractions:** {stats['successful']}")
    st.write(f"- **Failed extractions:** {stats['failed']}")
    st.write(f"- **Extraction success rate:** {stats['success_rate']}%")
    st.caption("Extraction accuracy is rule + model based; figures reflect completed analysis runs.")
