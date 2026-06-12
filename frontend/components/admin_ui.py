"""
Reusable UI components for the enterprise admin panel:
breadcrumbs, KPI cards with trend indicators, paginated tables, and theming.
"""

from typing import List, Dict, Optional
import math
import streamlit as st
import pandas as pd


def inject_admin_theme() -> None:
    """Inject CSS for the admin workspace, honoring a dark/light toggle."""
    dark = st.session_state.get("admin_dark_mode", False)

    if dark:
        css = """
        <style>
        .admin-kpi {
            background: #1e2128; border: 1px solid #2d323c; border-radius: 12px;
            padding: 1rem 1.2rem; color: #e6e6e6; box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }
        .admin-kpi .kpi-label { font-size: 0.8rem; color: #9aa0aa; }
        .admin-kpi .kpi-value { font-size: 1.7rem; font-weight: 700; color: #ffffff; }
        .admin-breadcrumb { color: #9aa0aa; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .trend-up { color: #2ecc71; font-weight: 600; }
        .trend-down { color: #e74c3c; font-weight: 600; }
        .trend-flat { color: #95a5a6; font-weight: 600; }
        </style>
        """
    else:
        css = """
        <style>
        .admin-kpi {
            background: #ffffff; border: 1px solid #e6e9ef; border-radius: 12px;
            padding: 1rem 1.2rem; color: #1f2933; box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }
        .admin-kpi .kpi-label { font-size: 0.8rem; color: #6b7280; }
        .admin-kpi .kpi-value { font-size: 1.7rem; font-weight: 700; color: #111827; }
        .admin-breadcrumb { color: #6b7280; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .trend-up { color: #16a34a; font-weight: 600; }
        .trend-down { color: #dc2626; font-weight: 600; }
        .trend-flat { color: #6b7280; font-weight: 600; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def breadcrumb(*parts: str) -> None:
    """Render a breadcrumb trail, e.g. breadcrumb('Admin Panel', 'User Management')."""
    trail = "  ›  ".join(parts)
    st.markdown(f"<div class='admin-breadcrumb'>🏠 {trail}</div>", unsafe_allow_html=True)


def kpi_card(label: str, value, trend: Optional[Dict] = None) -> None:
    """
    Render a KPI card with an optional trend indicator.

    Args:
        label: KPI label.
        value: KPI value.
        trend: Optional {'direction': 'up'|'down'|'flat', 'pct': float}.
    """
    trend_html = ""
    if trend:
        arrow = {"up": "↑", "down": "↓", "flat": "→"}.get(trend["direction"], "→")
        cls = {"up": "trend-up", "down": "trend-down", "flat": "trend-flat"}.get(trend["direction"], "trend-flat")
        trend_html = f"<div class='{cls}'>{arrow} {trend['pct']}%</div>"

    st.markdown(
        f"""
        <div class='admin-kpi'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value'>{value}</div>
            {trend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def paginated_table(df: pd.DataFrame, key: str, page_size: int = 10,
                    search_columns: Optional[List[str]] = None) -> None:
    """
    Render a searchable, paginated, sortable data table with CSV export.

    Args:
        df: The DataFrame to display.
        key: Unique key prefix for widgets.
        page_size: Rows per page.
        search_columns: Columns to include in the free-text search.
    """
    if df.empty:
        st.info("No records found.")
        return

    # Search
    if search_columns:
        term = st.text_input("🔍 Search", key=f"{key}_search", placeholder="Type to filter...")
        if term:
            mask = pd.Series(False, index=df.index)
            for col in search_columns:
                if col in df.columns:
                    mask |= df[col].astype(str).str.contains(term, case=False, na=False)
            df = df[mask]

    total = len(df)
    if total == 0:
        st.info("No records match your search.")
        return

    pages = max(1, math.ceil(total / page_size))
    col1, col2 = st.columns([3, 1])
    with col2:
        page = st.number_input("Page", min_value=1, max_value=pages, value=1, step=1, key=f"{key}_page")
    with col1:
        st.caption(f"Showing page {page} of {pages} — {total} record(s)")

    start = (page - 1) * page_size
    end = start + page_size
    st.dataframe(df.iloc[start:end], use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Export CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"{key}_export",
    )
