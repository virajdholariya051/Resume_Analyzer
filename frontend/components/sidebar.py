"""
Sidebar component providing filter and search functionality.
"""

import streamlit as st
from typing import Dict, Optional


def render_filter_sidebar() -> Optional[Dict]:
    """
    Render a filter sidebar for analysis results.
    
    Returns:
        Dictionary with filter values or None if no filters applied.
    """
    with st.sidebar:
        st.markdown("### 🔍 Filters")

        # ATS Score filter
        ats_range = st.slider(
            "ATS Score Range",
            min_value=0,
            max_value=100,
            value=(0, 100),
            step=5,
            key="filter_ats",
        )

        # Skills filter
        skills_filter = st.text_input(
            "Filter by Skill",
            placeholder="e.g., Python, React",
            key="filter_skill",
        )

        # Date filter
        date_filter = st.selectbox(
            "Upload Date",
            ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
            key="filter_date",
        )

        # Job role filter
        role_filter = st.text_input(
            "Job Role",
            placeholder="e.g., Data Scientist",
            key="filter_role",
        )

        if st.button("Apply Filters", use_container_width=True):
            return {
                "ats_range": ats_range,
                "skills": skills_filter,
                "date": date_filter,
                "role": role_filter,
            }

    return None
