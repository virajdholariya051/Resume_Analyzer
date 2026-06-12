"""
Admin Skills Analytics - common skills, missing skills, demand trends, gaps.
"""

import streamlit as st
import pandas as pd
from backend.auth.auth_service import is_admin
from backend.services.admin_service import AdminService
from frontend.components.admin_ui import breadcrumb
from frontend.components.charts import create_horizontal_bar_chart


def render_admin_skills() -> None:
    """Render the skills analytics section."""
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return

    breadcrumb("Admin Panel", "Skills Analytics")
    st.markdown('<h1 class="main-header">🧠 Skills Analytics</h1>', unsafe_allow_html=True)

    service = AdminService()
    data = service.get_skills_analytics(top_n=20)

    tabs = st.tabs([
        "Most Common Skills", "Missing Skills Trends",
        "Skill Demand Trends", "Skill Gap Analytics",
    ])

    with tabs[0]:
        st.markdown("### Top 20 Skills Across Resumes")
        if data["top_skills"]:
            st.plotly_chart(create_horizontal_bar_chart(data["top_skills"], "Most Common Skills"),
                            use_container_width=True)
            st.dataframe(pd.DataFrame(data["top_skills"], columns=["Skill", "Count"]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No skills data yet.")

    with tabs[1]:
        st.markdown("### Most Missing Skills")
        st.caption("Skills requested by job descriptions but under-supplied by candidate resumes.")
        if data["missing_skills"]:
            st.plotly_chart(create_horizontal_bar_chart(data["missing_skills"], "Skill Shortage (demand - supply)",
                                                        color="#e74c3c"),
                            use_container_width=True)
            st.dataframe(pd.DataFrame(data["missing_skills"], columns=["Skill", "Shortage"]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No skill shortages detected (or no job descriptions defined).")

    with tabs[2]:
        st.markdown("### Skill Demand Trends")
        st.caption("Most-requested skills across all job descriptions.")
        if data["requested_skills"]:
            st.plotly_chart(create_horizontal_bar_chart(data["requested_skills"], "Most Requested Skills",
                                                        color="#16a34a"),
                            use_container_width=True)
        else:
            st.info("No job descriptions defined yet.")

    with tabs[3]:
        st.markdown("### Skill Gap Analytics")
        _render_gap_insights(data)


def _render_gap_insights(data) -> None:
    """Auto-generated insights on the supply/demand skill gap."""
    top = {s for s, _ in data["top_skills"]}
    missing = data["missing_skills"]

    st.markdown("#### 💡 Auto-Generated Insights")
    if missing:
        top_missing = ", ".join(s for s, _ in missing[:5])
        st.warning(f"**Critical gaps:** {top_missing} are in demand but underrepresented in your candidate pool.")
    if data["top_skills"]:
        abundant = ", ".join(s for s, _ in data["top_skills"][:5])
        st.success(f"**Strong supply:** {abundant} are well represented across resumes.")
    if not missing and not data["top_skills"]:
        st.info("Not enough data to generate insights yet.")
