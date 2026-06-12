"""
Admin Feedback Center - reviews, bug reports, feature requests, support tickets.
"""

import streamlit as st
from backend.auth.auth_service import is_admin
from backend.services.feedback_service import FeedbackService
from frontend.components.admin_ui import breadcrumb, kpi_card


def render_admin_feedback() -> None:
    """Render the feedback center."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Feedback Center")
    st.markdown('<h1 class="main-header">💬 Feedback Center</h1>', unsafe_allow_html=True)

    service = FeedbackService()
    counts = service.get_counts()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Reviews", counts.get("Review", 0))
    with c2:
        kpi_card("Bug Reports", counts.get("Bug", 0))
    with c3:
        kpi_card("Feature Requests", counts.get("Feature", 0))
    with c4:
        kpi_card("Open Tickets", counts.get("open", 0))

    st.markdown("---")
    tabs = st.tabs(["User Reviews", "Bug Reports", "Feature Requests", "Support Tickets"])
    categories = ["Review", "Bug", "Feature", "Ticket"]
    for tab, category in zip(tabs, categories):
        with tab:
            _render_category(service, category)


def _render_category(service, category) -> None:
    items = service.get_by_category(category)
    if not items:
        st.info(f"No {category.lower()} entries yet.")
        return

    for fb in items:
        status_icon = {"Open": "🟡", "Resolved": "🟢", "Closed": "⚪"}.get(fb["status"], "•")
        title = fb["subject"] or fb["message"][:50]
        with st.expander(f"{status_icon} #{fb['feedback_id']} — {title} ({fb['user_name']}, {fb['created_at']})"):
            if fb["rating"]:
                st.write("⭐" * int(fb["rating"]))
            st.write(fb["message"])
            if fb["admin_reply"]:
                st.info(f"**Admin reply:** {fb['admin_reply']}")

            reply = st.text_input("Reply", key=f"reply_{fb['feedback_id']}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("💬 Send Reply", key=f"send_{fb['feedback_id']}"):
                    _flash(service.reply(fb["feedback_id"], reply))
            with col2:
                if st.button("✅ Resolve", key=f"resolve_{fb['feedback_id']}"):
                    _flash(service.update_status(fb["feedback_id"], "Resolved"))
            with col3:
                if st.button("⚪ Close", key=f"close_{fb['feedback_id']}"):
                    _flash(service.update_status(fb["feedback_id"], "Closed"))
            with col4:
                if st.button("🗑️ Delete", key=f"delfb_{fb['feedback_id']}"):
                    _flash(service.delete(fb["feedback_id"]))


def _flash(result: dict) -> None:
    if result.get("success"):
        st.success(result["message"])
        st.rerun()
    else:
        st.error(result["message"])
