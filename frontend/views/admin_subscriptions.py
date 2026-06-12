"""
Admin Subscription Management - plans, free/premium users, revenue analytics.

NOTE: This deployment does not include a billing/payment integration, so the
subscription tiers below are presented as a configurable framework. Connect a
payment provider (e.g., Stripe) to populate real revenue figures.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.user_service import UserService
from frontend.components.admin_ui import breadcrumb, kpi_card


# Plan framework (configurable). Without a billing integration all users are "Free".
PLANS = [
    {"Plan": "Free", "Price/mo": "$0", "Resume Limit": "5", "AI Analyses": "10/mo"},
    {"Plan": "Premium", "Price/mo": "$19", "Resume Limit": "Unlimited", "AI Analyses": "Unlimited"},
    {"Plan": "Enterprise", "Price/mo": "Custom", "Resume Limit": "Unlimited", "AI Analyses": "Unlimited + API"},
]


def render_admin_subscriptions() -> None:
    """Render the subscription management section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Subscription Management")
    st.markdown('<h1 class="main-header">💳 Subscription Management</h1>', unsafe_allow_html=True)

    st.info(
        "No payment provider is connected. All accounts are currently on the **Free** tier. "
        "The structure below is ready to integrate with a billing system."
    )

    user_service = UserService()
    users = user_service.get_all_users()
    total = len(users)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Free Users", total)
    with c2:
        kpi_card("Premium Users", 0)
    with c3:
        kpi_card("Monthly Revenue", "$0")

    st.markdown("---")
    tabs = st.tabs(["Free Users", "Premium Users", "Subscription Plans", "Revenue Analytics"])

    with tabs[0]:
        df = pd.DataFrame([{"ID": u["user_id"], "Name": u["name"], "Email": u["email"],
                            "Plan": "Free"} for u in users])
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.info("No premium subscribers yet. Connect a billing provider to enable upgrades.")

    with tabs[2]:
        st.dataframe(pd.DataFrame(PLANS), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.metric("Total Revenue", "$0")
        st.caption("Revenue analytics will populate once a payment integration is configured.")
